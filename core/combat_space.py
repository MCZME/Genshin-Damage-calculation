import math
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from core.mechanics.aura import Element
from core.systems.contract.attack import AOEShape
from core.entities.base_entity import CombatEntity, EntityState, Faction

if TYPE_CHECKING:
    from core.systems.contract.damage import Damage
    from core.team import Team


class CombatSpace:
    """战场空间管理器。

    负责维护场景中所有实体的物理存在，执行空间检索、碰撞判定以及伤害广播逻辑。
    V2.4 重构：现在作为战斗世界管理器，角色由 Team 统一管理，空间仅存储非角色实体（召唤物、敌人等）。
    """

    def __init__(self) -> None:
        """初始化战场空间。"""
        self._entities: Dict[Faction, List[CombatEntity]] = {
            Faction.PLAYER: [], # [重构] 此处仅存放召唤物
            Faction.ENEMY: [],
            Faction.NEUTRAL: []
        }
        self._remove_queue: List[CombatEntity] = []
        self.team: Optional["Team"] = None

    def set_team(self, team: "Team") -> None:
        """注入队伍实例。角色由 Team 逻辑驱动，空间仅在物理计算时查询它。"""
        self.team = team

    def register(self, entity: CombatEntity) -> None:
        """将实体注册到当前空间中（不应包含角色本体）。"""
        if entity not in self._entities[entity.faction]:
            self._entities[entity.faction].append(entity)
            from core.logger import get_emulation_logger
            get_emulation_logger().log_info(
                f"物理实体已注册: {entity.name} (Faction: {entity.faction.name})", 
                sender="Physics"
            )

    def unregister(self, entity: CombatEntity) -> None:
        """从移除队列中标记该实体，待本帧结束时统一注销。"""
        if entity not in self._remove_queue:
            self._remove_queue.append(entity)
            from core.logger import get_emulation_logger
            get_emulation_logger().log_info(
                f"物理实体已注销: {entity.name}", sender="Physics"
            )

    def on_frame_update(self) -> None:
        """每帧驱动逻辑：驱动角色逻辑、物理实体更新并清理非活跃对象。"""
        
        # 1. 驱动所有角色逻辑 (由 Team 统一接管场上/场下驱动)
        if self.team:
            self.team.on_frame_update()

        # 2. 驱动空间内注册的所有物理实体 (召唤物、敌人、中立物)
        for faction_list in self._entities.values():
            for entity in faction_list:
                if entity.state in [EntityState.ACTIVE, EntityState.FINISHING]:
                    entity.update()
                
                if not entity.is_active and entity.state != EntityState.FINISHING:
                    self.unregister(entity)

        # 3. 执行注销队列
        if self._remove_queue:
            for entity in self._remove_queue:
                if entity in self._entities[entity.faction]:
                    self._entities[entity.faction].remove(entity)
            self._remove_queue.clear()

    # ---------------------------------------------------------
    # 物理判定内核 (XZ平面投影) - 已适配 Team 架构
    # ---------------------------------------------------------

    def _get_search_targets(self, faction: Faction) -> List[CombatEntity]:
        """获取检索时的候选实体列表（动态合并场上角色）。"""
        targets = self._entities[faction].copy()
        
        # 如果检索玩家方，自动加入场上角色本体
        if faction == Faction.PLAYER and self.team and self.team.current_character:
            targets.append(self.team.current_character)
            
        return targets

    def get_entities_in_range(
        self, 
        origin: Tuple[float, float], 
        radius: float, 
        faction: Faction
    ) -> List[CombatEntity]:
        """执行圆柱/球体判定。"""
        ox, oz = origin
        results: List[CombatEntity] = []
        
        search_list = self._get_search_targets(faction)
        for e in search_list:
            ex, ez = e.pos[0], e.pos[1]
            dist_sq = (ex - ox)**2 + (ez - oz)**2
            total_r = radius + e.hitbox[0]
            if dist_sq <= total_r * total_r:
                results.append(e)
        return results

    def get_entities_in_box(
        self, 
        origin: Tuple[float, float], 
        length: float, 
        width: float, 
        facing: float, 
        faction: Faction
    ) -> List[CombatEntity]:
        """执行矩形区域判定。"""
        ox, oz = origin
        rad = math.radians(-facing)
        cos_f, sin_f = math.cos(rad), math.sin(rad)
        results: List[CombatEntity] = []
        
        search_list = self._get_search_targets(faction)
        for e in search_list:
            ex, ez = e.pos[0], e.pos[1]
            dx, dz = ex - ox, ez - oz
            
            rx = dx * cos_f - dz * sin_f
            rz = dx * sin_f + dz * cos_f
            
            closest_x = max(0.0, min(rx, length))
            closest_z = max(-width / 2.0, min(rz, width / 2.0))
            
            dist_sq = (rx - closest_x)**2 + (rz - closest_z)**2
            if dist_sq <= e.hitbox[0] * e.hitbox[0]:
                results.append(e)
        return results

    def broadcast_damage(self, attacker: CombatEntity, damage: "Damage") -> None:
        """发起伤害广播。"""
        config = getattr(damage, "config", None)
        if not config:
            return

        hb = config.hitbox
        shape = hb.shape
        radius = hb.radius
        offset = hb.offset
        
        target_factions = [Faction.ENEMY, Faction.NEUTRAL]
        if attacker.faction == Faction.ENEMY:
            target_factions = [Faction.PLAYER, Faction.NEUTRAL]
            
        facing = getattr(attacker, "facing", 0.0)
        rad = math.radians(facing)
        ox = attacker.pos[0] + offset[0] * math.cos(rad) - offset[1] * math.sin(rad)
        oz = attacker.pos[1] + offset[0] * math.sin(rad) + offset[1] * math.cos(rad)
        origin = (ox, oz)
        
        targets: List[CombatEntity] = []
        for faction in target_factions:
            if shape in [AOEShape.SPHERE, AOEShape.CYLINDER]:
                targets.extend(self.get_entities_in_range(origin, radius, faction))
            elif shape == AOEShape.BOX:
                targets.extend(
                    self.get_entities_in_box(origin, hb.length, hb.width, facing, faction)
                )
            elif shape == AOEShape.SINGLE:
                if damage.target:
                    targets.append(damage.target)
                else:
                    closest = self._find_closest(origin, faction)
                    if closest:
                        targets.append(closest)

        final_targets = self._apply_selection_strategy(targets, damage.data, origin)
        
        if final_targets:
            from core.logger import get_emulation_logger
            get_emulation_logger().log_info(
                f"伤害广播命中 {len(final_targets)} 个目标 (AOE: {shape.name})", 
                sender="Physics"
            )
            
        for t in final_targets:
            if not damage.target:
                damage.set_target(t)
            t.handle_damage(damage)

    def broadcast_element(
        self, 
        source: CombatEntity, 
        element: "Element", 
        u_value: float, 
        origin: Tuple[float, float],
        radius: float,
        exclude_target: Optional[CombatEntity] = None
    ) -> None:
        """发起元素广播。"""
        hit_count = 0
        for faction in Faction:
            targets = self.get_entities_in_range(origin, radius, faction)
            for t in targets:
                if t == exclude_target or not t.is_active:
                    continue
                t.aura.apply_element(element, u_value)
                hit_count += 1

        from core.logger import get_emulation_logger
        get_emulation_logger().log_info(
            f"元素广播: {element.value} ({u_value}U), 半径 {radius}m, 命中 {hit_count} 个目标", 
            sender="Physics"
        )

    def _find_closest(self, origin: Tuple[float, float], faction: Faction) -> Optional[CombatEntity]:
        ox, oz = origin
        best_dist = float("inf")
        best_e: Optional[CombatEntity] = None
        
        search_list = self._get_search_targets(faction)
        for e in search_list:
            dist_sq = (e.pos[0] - ox)**2 + (e.pos[1] - oz)**2
            if dist_sq < best_dist:
                best_dist = dist_sq
                best_e = e
        return best_e

    def _apply_selection_strategy(
        self, 
        targets: List[CombatEntity], 
        data: Dict[str, Any], 
        origin: Tuple[float, float]
    ) -> List[CombatEntity]:
        if not targets:
            return []
        targets = list(set(targets))
        select_way = data.get("selection_way", "ALL")
        max_targets = data.get("max_targets", 999)
        if select_way == "CLOSEST":
            targets.sort(
                key=lambda e: (e.pos[0] - origin[0])**2 + (e.pos[1] - origin[1])**2
            )
        return targets[:min(len(targets), max_targets)]

    def get_all_entities(self) -> List[CombatEntity]:
        """获取所有物理实体列表（包含场上角色）。"""
        results: List[CombatEntity] = []
        for faction_list in self._entities.values():
            results.extend(faction_list)
            
        if self.team and self.team.current_character:
            if self.team.current_character not in results:
                results.append(self.team.current_character)
        return results
