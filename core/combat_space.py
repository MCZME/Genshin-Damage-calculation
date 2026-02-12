import math
from typing import List, Dict, Tuple, Optional, Any
from core.entities.base_entity import CombatEntity, Faction, EntityState
from core.action.action_data import AOEShape

class CombatSpace:
    """
    战场空间管理器。
    支持多种碰撞几何体判定。
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
            from core.logger import get_emulation_logger
            get_emulation_logger().log_info(f"实体已注册: {entity.name} (Faction: {entity.faction.name})", sender="Physics")

    def unregister(self, entity: CombatEntity):
        if entity not in self._remove_queue:
            self._remove_queue.append(entity)
            from core.logger import get_emulation_logger
            get_emulation_logger().log_info(f"实体已注销: {entity.name}", sender="Physics")

    def update(self):
        for faction_list in self._entities.values():
            for entity in faction_list:
                if entity.state in [EntityState.ACTIVE, EntityState.FINISHING]:
                    entity.update()
                
                if not entity.is_active and entity.state != EntityState.FINISHING:
                    self.unregister(entity)
        if self._remove_queue:
            for entity in self._remove_queue:
                if entity in self._entities[entity.faction]:
                    self._entities[entity.faction].remove(entity)
            self._remove_queue.clear()

    # ---------------------------------------------------------
    # 物理判定内核
    # ---------------------------------------------------------

    def get_entities_in_range(self, origin: Tuple[float, float], radius: float, faction: Faction) -> List[CombatEntity]:
        """圆柱/球体判定 (XZ平面投影)"""
        ox, oz = origin
        results = []
        for e in self._entities[faction]:
            ex, ez = e.pos[0], e.pos[1]
            dist_sq = (ex - ox)**2 + (ez - oz)**2
            total_r = radius + e.hitbox[0]
            if dist_sq <= total_r * total_r:
                results.append(e)
        return results

    def get_entities_in_box(self, origin: Tuple[float, float], length: float, width: float, facing: float, faction: Faction) -> List[CombatEntity]:
        """矩形判定"""
        ox, oz = origin
        rad = math.radians(-facing)
        cos_f, sin_f = math.cos(rad), math.sin(rad)
        results = []
        for e in self._entities[faction]:
            ex, ez = e.pos[0], e.pos[1]
            dx, dz = ex - ox, ez - oz
            rx = dx * cos_f - dz * sin_f
            rz = dx * sin_f + dz * cos_f
            closest_x = max(0, min(rx, length))
            closest_z = max(-width/2, min(rz, width/2))
            dist_sq = (rx - closest_x)**2 + (rz - closest_z)**2
            if dist_sq <= e.hitbox[0] * e.hitbox[0]:
                results.append(e)
        return results

    def broadcast_damage(self, attacker: CombatEntity, damage: Any, **kwargs):
        """
        根据 Damage 对象的 AttackConfig 发起广播。
        V2.3: 物理参数必须由 AttackConfig 提供，UI 与 Logic 层不再通过 data 字典传递。
        """
        config = getattr(damage, "config", None)
        if not config:
            from core.logger import get_emulation_logger
            get_emulation_logger().log_info(f"警告: 伤害对象缺失 AttackConfig，无法执行广播", sender="Physics")
            return

        hb = config.hitbox
        shape = hb.shape
        radius = hb.radius
        offset = hb.offset
        
        # 1. 计算目标阵营
        target_factions = [Faction.ENEMY, Faction.NEUTRAL]
        if attacker.faction == Faction.ENEMY:
            target_factions = [Faction.PLAYER, Faction.NEUTRAL]
            
        # 2. 计算坐标原点 (基于攻击者当前朝向)
        facing = getattr(attacker, 'facing', 0.0)
        rad = math.radians(facing)
        ox = attacker.pos[0] + offset[0] * math.cos(rad) - offset[1] * math.sin(rad)
        oz = attacker.pos[1] + offset[0] * math.sin(rad) + offset[1] * math.cos(rad)
        origin = (ox, oz)
        
        # 3. 执行检索
        targets = []
        for faction in target_factions:
            if shape in [AOEShape.SPHERE, AOEShape.CYLINDER]:
                targets.extend(self.get_entities_in_range(origin, radius, faction))
            elif shape == AOEShape.BOX:
                targets.extend(self.get_entities_in_box(origin, hb.length, hb.width, facing, faction))
            elif shape == AOEShape.SINGLE:
                # SINGLE 模式下，如果已有确定的 target 则直接添加，否则寻找最近目标
                if damage.target:
                    targets.append(damage.target)
                else:
                    closest = self._find_closest(origin, faction)
                    if closest:
                        targets.append(closest)

        # 4. 执行伤害结算
        # Selection Strategy (如: 仅选最近的一个目标)
        final_targets = self._apply_selection_strategy(targets, damage.data, origin)
        if final_targets:
            from core.logger import get_emulation_logger
            get_emulation_logger().log_info(f"伤害广播命中 {len(final_targets)} 个目标 (AOE: {shape.name})", sender="Physics")
            
        for t in final_targets:
            # 在广播阶段建立对 target 的引用，并执行实体的伤害处理接口
            if not damage.target:
                damage.set_target(t)
            t.handle_damage(damage)

    def _find_closest(self, origin: Tuple[float, float], faction: Faction) -> Optional[CombatEntity]:
        ox, oz = origin
        best_dist = float('inf')
        best_e = None
        for e in self._entities[faction]:
            dist_sq = (e.pos[0]-ox)**2 + (e.pos[1]-oz)**2
            if dist_sq < best_dist:
                best_dist = dist_sq
                best_e = e
        return best_e

    def _apply_selection_strategy(self, targets: List[CombatEntity], data: Dict, origin: Tuple[float, float]) -> List[CombatEntity]:
        if not targets:
            return []
        targets = list(set(targets))
        select_way = data.get('selection_way', 'ALL')
        max_targets = data.get('max_targets', 999)
        if select_way == 'CLOSEST':
            targets.sort(key=lambda e: (e.pos[0]-origin[0])**2 + (e.pos[1]-origin[1])**2)
        return targets[:min(len(targets), max_targets)]

    def get_all_entities(self) -> List[CombatEntity]:
        """获取场景中所有活跃实体。"""
        results = []
        for faction_list in self._entities.values():
            results.extend(faction_list)
        return results
