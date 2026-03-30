"""月曜反应处理器模块。"""

import math
from typing import Any

from core.systems.contract.attack import AttackConfig
from core.systems.contract.damage import Damage
from core.systems.contract.reaction import ElementalReactionType
from core.event import EventType, GameEvent
from core.mechanics.aura import Element
from core.tool import get_current_time


class LunarHandler:
    """
    月曜反应处理器。

    处理月绽放、月感电、月结晶等月曜反应。
    """

    def __init__(self):
        self._context: Any = None
        self._engine: Any = None

    def set_context(self, context: Any) -> None:
        """设置仿真上下文。"""
        self._context = context

    def set_engine(self, engine: Any) -> None:
        """设置事件引擎。"""
        self._engine = engine

    def handle_lunar_bloom(self, event: GameEvent, res: Any) -> None:
        """
        处理月绽放反应：
        1. 生成草原核（保持原有绽放机制不变）
        2. 额外触发草露资源恢复

        注：丰穰之核由角色技能触发生成，非月绽放反应直接产物。
        """
        from core.entities.elemental_entities import DendroCoreEntity
        from core.systems.lunar_system import LunarReactionSystem

        target = event.data.get("target")
        source_char = event.source

        if target is None:
            return

        # 生成草原核（保持原有绽放机制）
        core = DendroCoreEntity(
            creator=source_char,
            pos=tuple(target.pos),
        )

        if self._context and self._context.space:
            self._context.space.register(core)

        # 额外触发草露恢复（月绽放特有）
        lunar_system = self._context.get_system(LunarReactionSystem) if self._context else None
        if lunar_system:
            lunar_system.start_grass_dew_recovery()

        # 发布月绽放事件
        if self._engine:
            self._engine.publish(GameEvent(
                event_type=EventType.AFTER_LUNAR_BLOOM,
                frame=get_current_time(),
                source=source_char,
                data={"target": target, "core": core},
            ))

    def handle_lunar_charged(self, event: GameEvent, res: Any) -> None:
        """
        处理月感电反应：
        1. 生成/刷新雷暴云
        2. 取消普通感电的持续攻击
        """
        from core.entities.lunar_entities import ThunderCloudEntity

        target = event.data.get("target")
        source_char = event.source

        if target is None:
            return

        # 取消普通感电状态
        target.aura.is_electro_charged = False

        # 获取或创建雷暴云
        existing_cloud = self._find_nearby_thunder_cloud(target.pos)

        if existing_cloud:
            existing_cloud.refresh()
            existing_cloud.add_source_character(source_char)
        else:
            cloud = ThunderCloudEntity(
                creator=source_char,
                pos=self._calculate_cloud_position(source_char, target),
                source_characters=[source_char],
            )
            if self._context and self._context.space:
                self._context.space.register(cloud)

        # 发布月感电事件
        if self._engine:
            self._engine.publish(GameEvent(
                event_type=EventType.AFTER_LUNAR_CHARGED,
                frame=get_current_time(),
                source=source_char,
                data={"target": target},
            ))

    def handle_lunar_crystallize(self, event: GameEvent, res: Any) -> None:
        """
        处理月结晶反应：
        1. 不生成晶片
        2. 尝试生成月笼（最多3枚）
        3. 累积触发计数
        """
        from core.entities.lunar_entities import LunarCageEntity
        from core.systems.lunar_system import LunarReactionSystem

        target = event.data.get("target")
        source_char = event.source

        if target is None:
            return

        # 计算应生成的月笼数量
        existing_cages = LunarCageEntity.count_nearby_cages(target.pos)
        cages_to_create = max(0, 3 - existing_cages)

        # 生成月笼
        for i in range(cages_to_create):
            cage_pos = self._calculate_cage_position(target.pos, i, cages_to_create)
            cage = LunarCageEntity(
                creator=source_char,
                pos=cage_pos,
            )
            if self._context and self._context.space:
                self._context.space.register(cage)

        # 累积触发计数
        lunar_system = self._context.get_system(LunarReactionSystem) if self._context else None
        if lunar_system:
            triggered, sources = lunar_system.check_and_reset_lunar_cage_counter()
            lunar_system.add_lunar_cage_counter(source_char)

            # 如果达到阈值，触发谐奏攻击
            if triggered:
                LunarCageEntity.trigger_attack(target, sources)

        # 发布月结晶事件
        if self._engine:
            self._engine.publish(GameEvent(
                event_type=EventType.AFTER_LUNAR_CRYSTALLIZE,
                frame=get_current_time(),
                source=source_char,
                data={"target": target, "cages_created": cages_to_create},
            ))

    def handle_lunar_charged_tick(self, event: GameEvent) -> None:
        """
        处理雷暴云攻击：
        - 收集参数，发布 BEFORE_DAMAGE 事件
        - 由 DamageSystem 调用 LunarDamagePipeline 执行多组分计算
        """
        cloud = event.data.get("cloud")
        target = event.data.get("target")
        source_characters = event.data.get("source_characters", [])

        if not source_characters or target is None:
            return

        # 构造 Damage 对象，传递 source_characters 给流水线处理
        dmg = Damage(
            element=(Element.ELECTRO, 0.0),  # 无附着
            config=AttackConfig(attack_tag="月感电"),
            name="月感电",
        )
        dmg.add_data("反应倍率", 1.8)  # 月感电倍率
        dmg.add_data("source_characters", source_characters)
        dmg.set_source(cloud)
        dmg.set_target(target)

        # 发布事件，由 DamageSystem 处理
        if self._engine:
            self._engine.publish(GameEvent(
                event_type=EventType.BEFORE_DAMAGE,
                frame=get_current_time(),
                source=cloud,
                data={"character": cloud, "target": target, "damage": dmg},
            ))

    def handle_lunar_crystallize_attack(self, event: GameEvent) -> None:
        """
        处理月笼谐奏攻击：
        - 收集参数，发布 BEFORE_DAMAGE 事件
        - 由 DamageSystem 调用 LunarDamagePipeline 执行多组分计算
        """
        cage = event.data.get("cage")
        target = event.data.get("target")
        source_characters = event.data.get("source_characters", [])

        if not source_characters or target is None:
            return

        # 构造 Damage 对象，传递 source_characters 给流水线处理
        dmg = Damage(
            element=(Element.GEO, 0.0),  # 无附着
            config=AttackConfig(attack_tag="月结晶"),
            name="月结晶",
        )
        dmg.add_data("反应倍率", 0.96)  # 月结晶倍率
        dmg.add_data("source_characters", source_characters)
        dmg.set_source(cage)
        dmg.set_target(target)

        # 发布事件，由 DamageSystem 处理
        if self._engine:
            self._engine.publish(GameEvent(
                event_type=EventType.BEFORE_DAMAGE,
                frame=get_current_time(),
                source=cage,
                data={"character": cage, "target": target, "damage": dmg},
            ))

    def _find_nearby_thunder_cloud(self, pos: tuple[float, float, float]) -> Any | None:
        """查找附近的雷暴云。"""
        from core.entities.lunar_entities import ThunderCloudEntity

        for cloud in ThunderCloudEntity.active_clouds:
            dx = cloud.pos[0] - pos[0]
            dz = cloud.pos[1] - pos[1]
            if (dx * dx + dz * dz) ** 0.5 <= 8.0:
                return cloud
        return None

    def _calculate_cloud_position(
        self,
        source_char: Any,
        target: Any
    ) -> tuple[float, float, float]:
        """计算雷暴云生成位置。"""
        # 简化：在目标和角色之间生成
        if source_char and target:
            x = (source_char.pos[0] + target.pos[0]) / 2
            z = (source_char.pos[1] + target.pos[1]) / 2
            y = max(source_char.pos[2], target.pos[2]) + 1.0
            return (x, z, y)
        return tuple(target.pos) if target else (0.0, 0.0, 1.0)

    def _calculate_cage_position(
        self,
        target_pos: tuple[float, float, float],
        index: int,
        total: int
    ) -> tuple[float, float, float]:
        """计算月笼生成位置。"""
        radius = 3.0 + (index * 0.25)  # 3~3.5米
        angle = (2 * math.pi * index / total) if total > 0 else 0

        x = target_pos[0] + radius * math.cos(angle)
        z = target_pos[1] + radius * math.sin(angle)
        y = target_pos[2]

        return (x, z, y)
