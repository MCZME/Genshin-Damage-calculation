import math
from typing import List, Dict, Tuple, Optional, Any
from core.entities.base_entity import CombatEntity, Faction, EntityState

class CombatSpace:
    """
    战场空间管理器。
    支持圆柱体 (Cylinder) 碰撞箱模型。
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
    # 空间检索逻辑 (计入 hitbox 元组: (半径, 高度))
    # ---------------------------------------------------------

    def get_entities_in_range(self, 
                             origin: Tuple[float, float], 
                             radius: float, 
                             faction: Faction) -> List[CombatEntity]:
        """圆形 AOE vs 实体圆"""
        ox, oz = origin
        results = []
        for e in self._entities[faction]:
            ex, ez = e.pos[0], e.pos[1]
            dist_sq = (ex - ox)**2 + (ez - oz)**2
            # e.hitbox[0] 是半径
            total_r = radius + e.hitbox[0]
            if dist_sq <= total_r * total_r:
                results.append(e)
        return results

    def get_entities_in_sector(self,
                              origin: Tuple[float, float],
                              radius: float,
                              facing: float,
                              fan_angle: float,
                              faction: Faction) -> List[CombatEntity]:
        """扇形 AOE vs 实体圆"""
        ox, oz = origin
        half_angle = fan_angle / 2
        results = []
        for e in self._entities[faction]:
            ex, ez = e.pos[0], e.pos[1]
            dx, dz = ex - ox, ez - oz
            dist_sq = dx*dx + dz*dz
            total_r = radius + e.hitbox[0]
            if dist_sq > total_r * total_r: continue
            if dist_sq < 0.0001:
                results.append(e); continue
            dist = math.sqrt(dist_sq)
            target_angle = math.degrees(math.atan2(dz, dx))
            angle_diff = abs((target_angle - facing + 180) % 360 - 180)
            angle_offset = math.degrees(math.asin(min(1.0, e.hitbox[0] / dist))) if dist > e.hitbox[0] else 90
            if angle_diff <= half_angle + angle_offset:
                results.append(e)
        return results

    def get_entities_in_box(self,
                           origin: Tuple[float, float],
                           length: float,
                           width: float,
                           facing: float,
                           faction: Faction) -> List[CombatEntity]:
        """矩形 AOE vs 实体圆"""
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

    def broadcast_damage(self, attacker: CombatEntity, damage: Any):
        config = damage.data
        shape = config.get('aoe_shape', 'CIRCLE')
        radius = config.get('radius', 0.5)
        faction = config.get('target_faction', Faction.ENEMY)
        
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
