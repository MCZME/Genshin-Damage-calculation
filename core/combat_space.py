import math
from typing import List, Dict, Tuple, Optional, Any
from core.entities.base_entity import CombatEntity, Faction, EntityState

class CombatSpace:
    """
    战场空间管理器。
    负责实体的注册、空间检索、伤害广播以及生命周期驱动。
    """
    def __init__(self):
        self._entities: Dict[Faction, List[CombatEntity]] = {
            Faction.PLAYER: [],
            Faction.ENEMY: [],
            Faction.NEUTRAL: []
        }
        self._remove_queue: List[CombatEntity] = []

    def register(self, entity: CombatEntity):
        if entity not in self._entities[entity.faction]:
            self._entities[entity.faction].append(entity)

    def unregister(self, entity: CombatEntity):
        if entity not in self._remove_queue:
            self._remove_queue.append(entity)

    def update(self):
        for faction_list in self._entities.values():
            for entity in faction_list:
                if entity.is_active:
                    entity.update()
                else:
                    self.unregister(entity)
        
        if self._remove_queue:
            for entity in self._remove_queue:
                if entity in self._entities[entity.faction]:
                    self._entities[entity.faction].remove(entity)
            self._remove_queue.clear()

    # ---------------------------------------------------------
    # 高级空间检索逻辑 (计入 hitbox_radius)
    # ---------------------------------------------------------

    def get_entities_in_range(self, 
                             origin: Tuple[float, float], 
                             radius: float, 
                             faction: Faction) -> List[CombatEntity]:
        """
        圆形 AOE vs 实体圆
        判定：距离 <= 攻击半径 + 实体半径
        """
        ox, oz = origin
        results = []
        
        for e in self._entities[faction]:
            ex, ez = e.pos[0], e.pos[1]
            dist_sq = (ex - ox)**2 + (ez - oz)**2
            
            # 攻击的总有效半径
            total_r = radius + e.hitbox_radius
            if dist_sq <= total_r * total_r:
                results.append(e)
        return results

    def get_entities_in_sector(self,
                              origin: Tuple[float, float],
                              radius: float,
                              facing: float,
                              fan_angle: float,
                              faction: Faction) -> List[CombatEntity]:
        """
        扇形 AOE vs 实体圆
        判定：
        1. 距离在 (攻击半径 + 实体半径) 内
        2. 目标圆心角度在 (攻击角度区间 + 实体半径贡献的角度偏移) 内
        """
        ox, oz = origin
        half_angle = fan_angle / 2
        results = []
        
        for e in self._entities[faction]:
            ex, ez = e.pos[0], e.pos[1]
            dx, dz = ex - ox, ez - oz
            dist_sq = dx*dx + dz*dz
            
            # 1. 距离初筛
            total_r = radius + e.hitbox_radius
            if dist_sq > total_r * total_r:
                continue
                
            # 距离过近直接命中
            if dist_sq < 0.0001:
                results.append(e)
                continue
            
            # 2. 角度判定
            dist = math.sqrt(dist_sq)
            target_angle = math.degrees(math.atan2(dz, dx))
            angle_diff = abs((target_angle - facing + 180) % 360 - 180)
            
            # 计算由于实体体积产生的角度增量 (近似值)
            # theta = arcsin(r / d)
            angle_offset = math.degrees(math.asin(min(1.0, e.hitbox_radius / dist))) if dist > e.hitbox_radius else 90
            
            if angle_diff <= half_angle + angle_offset:
                results.append(e)
        return results

    def get_entities_in_box(self,
                           origin: Tuple[float, float],
                           length: float,
                           width: float,
                           facing: float,
                           faction: Faction) -> List[CombatEntity]:
        """
        矩形 AOE vs 实体圆
        判定：
        将目标点转换到矩形本地坐标系，判定点(圆心)到矩形的距离是否小于等于实体的碰撞半径。
        """
        ox, oz = origin
        rad = math.radians(-facing)
        cos_f = math.cos(rad)
        sin_f = math.sin(rad)
        results = []
        
        for e in self._entities[faction]:
            ex, ez = e.pos[0], e.pos[1]
            dx, dz = ex - ox, ez - oz
            
            # 转换到本地坐标系 (rx 为长度方向, rz 为宽度方向)
            # 假设 origin 是矩形底部中心
            rx = dx * cos_f - dz * sin_f
            rz = dx * sin_f + dz * cos_f
            
            # 寻找点到矩形的最短距离 (Clamp 算法)
            closest_x = max(0, min(rx, length))
            closest_z = max(-width/2, min(rz, width/2))
            
            dist_sq = (rx - closest_x)**2 + (rz - closest_z)**2
            if dist_sq <= e.hitbox_radius * e.hitbox_radius:
                results.append(e)
        return results

    # ---------------------------------------------------------
    # 伤害广播与派发 (更新：处理偏移)
    # ---------------------------------------------------------

    def broadcast_damage(self, attacker: CombatEntity, damage: Any):
        config = damage.data
        shape = config.get('aoe_shape', 'CIRCLE')
        radius = config.get('radius', 0.5)
        faction = config.get('target_faction', Faction.ENEMY)
        
        # 处理位置偏移 (Position Offset)
        # 假设 config['offset'] = (前进方向偏移, 侧向偏移)
        offset = config.get('offset', (0.0, 0.0))
        rad = math.radians(attacker.facing)
        ox = attacker.pos[0] + offset[0] * math.cos(rad) - offset[1] * math.sin(rad)
        oz = attacker.pos[1] + offset[0] * math.sin(rad) + offset[1] * math.cos(rad)
        origin = (ox, oz)
        
        targets = []
        if shape == 'CIRCLE':
            targets = self.get_entities_in_range(origin, radius, faction)
        elif shape == 'SECTOR':
            targets = self.get_entities_in_sector(origin, radius, attacker.facing, config.get('fan_angle', 90), faction)
        elif shape == 'BOX':
            targets = self.get_entities_in_box(origin, config.get('length', 2.0), config.get('width', 1.0), attacker.facing, faction)
        
        final_targets = self._apply_selection_strategy(targets, config, origin)
        for t in final_targets:
            t.handle_damage(damage)

    def _apply_selection_strategy(self, targets: List[CombatEntity], config: Dict, origin: Tuple[float, float]) -> List[CombatEntity]:
        if not targets: return []
        select_way = config.get('selection_way', 'ALL')
        max_targets = config.get('max_targets', 999)
        if select_way == 'CLOSEST':
            targets.sort(key=lambda e: (e.pos[0]-origin[0])**2 + (e.pos[1]-origin[1])**2)
        return targets[:min(len(targets), max_targets)]