import math
from typing import List, Dict, Tuple, Optional, Any
from core.entities.base_entity import CombatEntity, Faction, EntityState

class CombatSpace:
    """
    战场空间管理器。
    负责实体的注册、空间检索、伤害广播以及生命周期驱动。
    """
    def __init__(self):
        # 按阵营索引实体，加速广播时的筛选
        self._entities: Dict[Faction, List[CombatEntity]] = {
            Faction.PLAYER: [],
            Faction.ENEMY: [],
            Faction.NEUTRAL: []
        }
        
        # 待移除队列，用于在一帧结束时安全清理
        self._remove_queue: List[CombatEntity] = []

    def register(self, entity: CombatEntity):
        """将实体注册到场景中"""
        if entity not in self._entities[entity.faction]:
            self._entities[entity.faction].append(entity)
            # 建立反向引用（可选，如果 CombatEntity 需要感知 Space）
            # entity.space = self

    def unregister(self, entity: CombatEntity):
        """将实体从场景中标记为移除"""
        if entity not in self._remove_queue:
            self._remove_queue.append(entity)

    def update(self):
        """
        每帧驱动场景内所有实体的逻辑。
        """
        # 1. 驱动所有活跃实体
        for faction_list in self._entities.values():
            for entity in faction_list:
                if entity.is_active:
                    entity.update()
                else:
                    self.unregister(entity)
        
        # 2. 清理已销毁的实体
        if self._remove_queue:
            for entity in self._remove_queue:
                if entity in self._entities[entity.faction]:
                    self._entities[entity.faction].remove(entity)
            self._remove_queue.clear()

    # ---------------------------------------------------------
    # 空间检索逻辑 (解析几何实现)
    # ---------------------------------------------------------

    def get_entities_in_range(self, 
                             origin: Tuple[float, float], 
                             radius: float, 
                             faction: Faction) -> List[CombatEntity]:
        """
        圆形范围检索 (最常用)
        """
        ox, oz = origin
        r_sq = radius * radius
        results = []
        
        # 仅遍历目标阵营，显著减少压力状态下的计算量
        for e in self._entities[faction]:
            ex, ez = e.pos[0], e.pos[1]
            # 使用平方距离比较，规避 math.sqrt 性能开销
            if (ex - ox)**2 + (ez - oz)**2 <= r_sq:
                results.append(e)
        return results

    def get_entities_in_sector(self,
                              origin: Tuple[float, float],
                              radius: float,
                              facing: float,
                              fan_angle: float,
                              faction: Faction) -> List[CombatEntity]:
        """
        扇形范围检索 (用于挥砍等具有方向性的攻击)
        """
        ox, oz = origin
        r_sq = radius * radius
        half_angle = fan_angle / 2
        results = []
        
        for e in self._entities[faction]:
            ex, ez = e.pos[0], e.pos[1]
            dx, dz = ex - ox, ez - oz
            dist_sq = dx*dx + dz*dz
            
            if dist_sq <= r_sq:
                # 距离过近（几乎重合）直接命中，避免 atan2 抖动
                if dist_sq < 0.0001:
                    results.append(e)
                    continue
                    
                # 计算目标点相对于原点的夹角
                target_angle = math.degrees(math.atan2(dz, dx))
                # 规范化角度差至 [-180, 180]
                angle_diff = (target_angle - facing + 180) % 360 - 180
                
                if abs(angle_diff) <= half_angle:
                    results.append(e)
        return results

    def get_entities_in_box(self,
                           origin: Tuple[float, float],
                           length: float,
                           width: float,
                           facing: float,
                           faction: Faction) -> List[CombatEntity]:
        """
        矩形范围检索 (OBB 判定)
        """
        ox, oz = origin
        rad = math.radians(-facing) # 逆向旋转用于坐标对齐
        cos_f = math.cos(rad)
        sin_f = math.sin(rad)
        results = []
        
        for e in self._entities[faction]:
            ex, ez = e.pos[0], e.pos[1]
            dx, dz = ex - ox, ez - oz
            
            # 旋转至 AABB 坐标系
            rx = dx * cos_f - dz * sin_f
            rz = dx * sin_f + dz * cos_f
            
            # 判定是否在矩形内 (假设 origin 是矩形底部的中心)
            if 0 <= rx <= length and -width/2 <= rz <= width/2:
                results.append(e)
        return results

    # ---------------------------------------------------------
    # 伤害广播与派发
    # ---------------------------------------------------------

    def broadcast_damage(self, attacker: CombatEntity, damage: Any):
        """
        核心派发入口：根据 AttackConfig 广播伤害
        """
        # 从 damage.data 提取几何参数 (未来可封装进 AttackConfig 对象)
        config = damage.data
        shape = config.get('aoe_shape', 'CIRCLE')
        radius = config.get('radius', 0.5)
        faction = config.get('target_faction', Faction.ENEMY)
        
        # 1. 确定原点 (考虑偏移)
        # 暂时简单处理：使用攻击者位置
        origin = (attacker.pos[0], attacker.pos[1])
        
        # 2. 执行空间检索
        targets = []
        if shape == 'CIRCLE':
            targets = self.get_entities_in_range(origin, radius, faction)
        elif shape == 'SECTOR':
            targets = self.get_entities_in_sector(origin, radius, attacker.facing, config.get('fan_angle', 90), faction)
        elif shape == 'BOX':
            targets = self.get_entities_in_box(origin, config.get('length', 2.0), config.get('width', 1.0), attacker.facing, faction)
        
        # 3. 索敌与选择逻辑 (Selection Strategy)
        final_targets = self._apply_selection_strategy(targets, config, origin)
        
        # 4. 派发执行
        for t in final_targets:
            t.handle_damage(damage)

    def _apply_selection_strategy(self, targets: List[CombatEntity], config: Dict, origin: Tuple[float, float]) -> List[CombatEntity]:
        """
        处理索敌限制 (如：虽然范围内有5个怪，但技能是单体)
        """
        if not targets:
            return []
            
        select_way = config.get('selection_way', 'ALL') # ALL, CLOSEST, LOW_HP
        max_targets = config.get('max_targets', 999)
        
        if select_way == 'CLOSEST':
            targets.sort(key=lambda e: (e.pos[0]-origin[0])**2 + (e.pos[1]-origin[1])**2)
            return targets[:min(len(targets), max_targets)]
        
        # 默认返回所有 (AOE)
        return targets[:min(len(targets), max_targets)]
