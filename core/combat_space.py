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

    def unregister(self, entity: CombatEntity):
        if entity not in self._remove_queue:
            self._remove_queue.append(entity)

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
        kwargs 用于覆盖或在没有 config 时传递参数 (保持一定的兼容性)。
        """
        config = damage.config if hasattr(damage, "config") else None
        hb = config.hitbox if config else None
        
        # 1. 提取参数 (优先从 AttackConfig 获取)
        shape = kwargs.get('shape', hb.shape if hb else AOEShape.CIRCLE)
        if isinstance(shape, str): shape = AOEShape[shape] if shape in AOEShape.__members__ else AOEShape.CYLINDER
        
        radius = kwargs.get('radius', hb.radius if hb else 0.5)
        offset = kwargs.get('offset', hb.offset if hb else (0.0, 0.0, 0.0))
        
        # 2. 计算阵营 (默认攻击敌人 + 中立实体)
        target_factions = [Faction.ENEMY, Faction.NEUTRAL]
        if attacker.faction == Faction.ENEMY:
            target_factions = [Faction.PLAYER, Faction.NEUTRAL]
            
        # 3. 计算坐标原点 (考虑偏移)
        rad = math.radians(attacker.facing)
        ox = attacker.pos[0] + offset[0] * math.cos(rad) - offset[1] * math.sin(rad)
        oz = attacker.pos[1] + offset[0] * math.sin(rad) + offset[1] * math.cos(rad)
        origin = (ox, oz)
        
        # 4. 执行检索
        targets = []
        for faction in target_factions:
            if shape in [AOEShape.SPHERE, AOEShape.CYLINDER]:
                targets.extend(self.get_entities_in_range(origin, radius, faction))
            elif shape == AOEShape.BOX:
                length = kwargs.get('length', hb.length if hb else 2.0)
                width = kwargs.get('width', hb.width if hb else 1.0)
                targets.extend(self.get_entities_in_box(origin, length, width, attacker.facing, faction))
            elif shape == AOEShape.SINGLE:
                # 单体攻击逻辑：如果 damage 已经有 target，则直接使用；否则寻找最近目标
                if damage.target:
                    targets.append(damage.target)
                else:
                    closest = self._find_closest(origin, faction)
                    if closest: targets.append(closest)

        # 5. 执行伤害结算
        final_targets = self._apply_selection_strategy(targets, damage.data, origin)
        for t in final_targets:
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
        if not targets: return []
        # 简单的去重
        targets = list(set(targets))
        select_way = data.get('selection_way', 'ALL')
        max_targets = data.get('max_targets', 999)
        if select_way == 'CLOSEST':
            targets.sort(key=lambda e: (e.pos[0]-origin[0])**2 + (e.pos[1]-origin[1])**2)
        return targets[:min(len(targets), max_targets)]