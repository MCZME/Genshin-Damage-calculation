import math
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from core.systems.contract.attack import AOEShape
from core.entities.base_entity import CombatEntity, EntityState, Faction

if TYPE_CHECKING:
    from core.systems.contract.damage import Damage


class CombatSpace:
    """战场空间管理器。

    负责维护场景中所有实体的物理存在，执行空间检索、碰撞判定以及伤害广播逻辑。
    """

    def __init__(self) -> None:
        """初始化战场空间。"""
        self._entities: Dict[Faction, List[CombatEntity]] = {
            Faction.PLAYER: [],
            Faction.ENEMY: [],
            Faction.NEUTRAL: []
        }
        self._remove_queue: List[CombatEntity] = []

    def register(self, entity: CombatEntity) -> None:
        """将实体注册到当前空间中。

        Args:
            entity: 待注册的战斗实体。
        """
        if entity not in self._entities[entity.faction]:
            self._entities[entity.faction].append(entity)
            from core.logger import get_emulation_logger
            get_emulation_logger().log_info(
                f"实体已注册: {entity.name} (Faction: {entity.faction.name})", 
                sender="Physics"
            )

    def unregister(self, entity: CombatEntity) -> None:
        """从移除队列中标记该实体，待本帧结束时统一注销。

        Args:
            entity: 待注销的战斗实体。
        """
        if entity not in self._remove_queue:
            self._remove_queue.append(entity)
            from core.logger import get_emulation_logger
            get_emulation_logger().log_info(
                f"实体已注销: {entity.name}", sender="Physics"
            )

    def update(self) -> None:
        """每帧驱动逻辑：更新实体状态并清理非活跃对象。"""
        for faction_list in self._entities.values():
            for entity in faction_list:
                # 仅驱动活跃状态或正在结束状态的实体
                if entity.state in [EntityState.ACTIVE, EntityState.FINISHING]:
                    entity.update()
                
                # 自动清理已失活的实体
                if not entity.is_active and entity.state != EntityState.FINISHING:
                    self.unregister(entity)

        # 执行注销队列
        if self._remove_queue:
            for entity in self._remove_queue:
                if entity in self._entities[entity.faction]:
                    self._entities[entity.faction].remove(entity)
            self._remove_queue.clear()

    # ---------------------------------------------------------
    # 物理判定内核 (XZ平面投影)
    # ---------------------------------------------------------

    def get_entities_in_range(
        self, 
        origin: Tuple[float, float], 
        radius: float, 
        faction: Faction
    ) -> List[CombatEntity]:
        """执行圆柱/球体判定。

        Args:
            origin: 判定中心坐标 (x, z)。
            radius: 判定半径。
            faction: 检索的目标阵营。

        Returns:
            List[CombatEntity]: 范围内的实体列表。
        """
        ox, oz = origin
        results: List[CombatEntity] = []
        for e in self._entities[faction]:
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
        """执行矩形区域判定。

        Args:
            origin: 矩形起始中心点。
            length: 矩形长度 (朝向方向)。
            width: 矩形宽度 (垂直朝向方向)。
            facing: 矩形朝向角度。
            faction: 检索的目标阵营。

        Returns:
            List[CombatEntity]: 范围内的实体列表。
        """
        ox, oz = origin
        rad = math.radians(-facing)
        cos_f, sin_f = math.cos(rad), math.sin(rad)
        results: List[CombatEntity] = []
        
        for e in self._entities[faction]:
            ex, ez = e.pos[0], e.pos[1]
            dx, dz = ex - ox, ez - oz
            
            # 转换到局部坐标系
            rx = dx * cos_f - dz * sin_f
            rz = dx * sin_f + dz * cos_f
            
            # 找到最近点
            closest_x = max(0.0, min(rx, length))
            closest_z = max(-width / 2.0, min(rz, width / 2.0))
            
            dist_sq = (rx - closest_x)**2 + (rz - closest_z)**2
            if dist_sq <= e.hitbox[0] * e.hitbox[0]:
                results.append(e)
        return results

    def broadcast_damage(self, attacker: CombatEntity, damage: "Damage") -> None:
        """根据伤害对象的 AttackConfig 发起全场广播。

        V2.3: 物理参数严格由 AttackConfig 提供，UI 或逻辑层不再通过外部注入。

        Args:
            attacker: 发起攻击的实体。
            damage: 伤害对象。
        """
        config = getattr(damage, "config", None)
        if not config:
            from core.logger import get_emulation_logger
            get_emulation_logger().log_info(
                "警告: 伤害对象缺失 AttackConfig，无法执行广播", sender="Physics"
            )
            return

        hb = config.hitbox
        shape = hb.shape
        radius = hb.radius
        offset = hb.offset
        
        # 1. 计算目标阵营 (默认玩家打敌人，反之亦然)
        target_factions = [Faction.ENEMY, Faction.NEUTRAL]
        if attacker.faction == Faction.ENEMY:
            target_factions = [Faction.PLAYER, Faction.NEUTRAL]
            
        # 2. 计算坐标原点 (基于攻击者当前朝向进行偏移转换)
        facing = getattr(attacker, "facing", 0.0)
        rad = math.radians(facing)
        ox = attacker.pos[0] + offset[0] * math.cos(rad) - offset[1] * math.sin(rad)
        oz = attacker.pos[1] + offset[0] * math.sin(rad) + offset[1] * math.cos(rad)
        origin = (ox, oz)
        
        # 3. 执行物理检索
        targets: List[CombatEntity] = []
        for faction in target_factions:
            if shape in [AOEShape.SPHERE, AOEShape.CYLINDER]:
                targets.extend(self.get_entities_in_range(origin, radius, faction))
            elif shape == AOEShape.BOX:
                targets.extend(
                    self.get_entities_in_box(origin, hb.length, hb.width, facing, faction)
                )
            elif shape == AOEShape.SINGLE:
                # SINGLE 模式优先使用已确定的 target，否则寻找最近目标
                if damage.target:
                    targets.append(damage.target)
                else:
                    closest = self._find_closest(origin, faction)
                    if closest:
                        targets.append(closest)

        # 4. 执行筛选策略与伤害分发
        final_targets = self._apply_selection_strategy(targets, damage.data, origin)
        
        if final_targets:
            from core.logger import get_emulation_logger
            get_emulation_logger().log_info(
                f"伤害广播命中 {len(final_targets)} 个目标 (AOE: {shape.name})", 
                sender="Physics"
            )
            
        for t in final_targets:
            # 建立引用并驱动实体的伤害处理逻辑 (ICD/反应)
            if not damage.target:
                damage.set_target(t)
            t.handle_damage(damage)

    def _find_closest(self, origin: Tuple[float, float], faction: Faction) -> Optional[CombatEntity]:
        """寻找距离指定点最近的阵营实体。"""
        ox, oz = origin
        best_dist = float("inf")
        best_e: Optional[CombatEntity] = None
        for e in self._entities[faction]:
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
        """根据动作意图筛选最终受击列表。"""
        if not targets:
            return []
            
        # 去重
        targets = list(set(targets))
        
        select_way = data.get("selection_way", "ALL")
        max_targets = data.get("max_targets", 999)
        
        if select_way == "CLOSEST":
            targets.sort(
                key=lambda e: (e.pos[0] - origin[0])**2 + (e.pos[1] - origin[1])**2
            )
            
        return targets[:min(len(targets), max_targets)]

    def get_all_entities(self) -> List[CombatEntity]:
        """获取当前场景中活跃的所有阵营实体列表。

        Returns:
            List[CombatEntity]: 所有实体汇总列表。
        """
        results: List[CombatEntity] = []
        for faction_list in self._entities.values():
            results.extend(faction_list)
        return results
