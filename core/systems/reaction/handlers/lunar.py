"""月曜反应处理器模块。"""

import math
from typing import Any

from core.systems.contract.attack import AttackConfig
from core.systems.contract.damage import Damage
from core.systems.contract.reaction import ElementalReactionType
from core.event import EventType, GameEvent
from core.mechanics.aura import Element
from core.tool import get_current_time, get_reaction_multiplier


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
        - 每2秒结算一次
        - 基于所有附着来源角色计算加权伤害
        - 通过 DamageSystem 的 LunarDamagePipeline 计算各组分
        """
        cloud = event.data.get("cloud")
        target = event.data.get("target")
        source_characters = event.data.get("source_characters", [])

        if not source_characters or target is None:
            return

        # 为每个角色计算伤害组分（通过 DamageSystem）
        damage_components = []
        for char in source_characters:
            dmg = Damage(
                element=(Element.ELECTRO, 0.0),  # 无附着
                config=AttackConfig(attack_tag="月感电"),
                name="月感电",
            )
            # 通过 data 传递参数给 LunarDamagePipeline
            dmg.add_data("等级系数", get_reaction_multiplier(char.level))
            dmg.add_data("反应倍率", 1.8)  # 反应月感电倍率
            dmg.set_source(char)
            dmg.set_target(target)

            # 触发 DamageSystem 计算
            if self._engine:
                self._engine.publish(GameEvent(
                    event_type=EventType.BEFORE_DAMAGE,
                    frame=get_current_time(),
                    source=char,
                    data={"character": char, "target": target, "damage": dmg},
                ))

            damage_components.append((char, dmg.damage))

        # 加权求和
        final_damage = self._calculate_weighted_damage(damage_components)

        # 应用最终伤害
        self._apply_final_lunar_damage(
            source=cloud,
            target=target,
            damage=final_damage,
            reaction_type=ElementalReactionType.LUNAR_CHARGED,
            element=Element.ELECTRO,
        )

    def handle_lunar_crystallize_attack(self, event: GameEvent) -> None:
        """
        处理月笼谐奏攻击：
        - 基于3次月结晶中参与的角色计算加权伤害
        - 通过 DamageSystem 的 LunarDamagePipeline 计算各组分
        """
        cage = event.data.get("cage")
        target = event.data.get("target")
        source_characters = event.data.get("source_characters", [])

        if not source_characters or target is None:
            return

        # 为每个角色计算伤害组分（通过 DamageSystem）
        damage_components = []
        for char in source_characters:
            dmg = Damage(
                element=(Element.GEO, 0.0),  # 无附着
                config=AttackConfig(attack_tag="月结晶"),
                name="月结晶",
            )
            # 通过 data 传递参数给 LunarDamagePipeline
            dmg.add_data("等级系数", get_reaction_multiplier(char.level))
            dmg.add_data("反应倍率", 0.96)  # 反应月结晶倍率
            dmg.set_source(char)
            dmg.set_target(target)

            # 触发 DamageSystem 计算
            if self._engine:
                self._engine.publish(GameEvent(
                    event_type=EventType.BEFORE_DAMAGE,
                    frame=get_current_time(),
                    source=char,
                    data={"character": char, "target": target, "damage": dmg},
                ))

            damage_components.append((char, dmg.damage))

        # 加权求和
        final_damage = self._calculate_weighted_damage(damage_components)

        # 应用最终伤害
        self._apply_final_lunar_damage(
            source=cage,
            target=target,
            damage=final_damage,
            reaction_type=ElementalReactionType.LUNAR_CRYSTALLIZE,
            element=Element.GEO,
        )

    def _calculate_weighted_damage(
        self,
        damage_components: list[tuple[Any, float]]
    ) -> float:
        """
        加权求和计算月曜伤害。

        公式：最终伤害 = 最高 + 次高÷2 + 其余之和÷12
        """
        if not damage_components:
            return 0.0

        damages = sorted([d[1] for d in damage_components], reverse=True)

        if len(damages) == 1:
            return damages[0]
        elif len(damages) == 2:
            return damages[0] + damages[1] / 2
        else:
            return damages[0] + damages[1] / 2 + sum(damages[2:]) / 12

    def _apply_final_lunar_damage(
        self,
        source: Any,
        target: Any,
        damage: float,
        reaction_type: ElementalReactionType,
        element: Element,
    ) -> None:
        """
        应用最终的月曜伤害（已加权求和）。

        这个方法用于应用加权求和后的最终伤害，
        不再触发 DamageSystem 的计算。
        """
        dmg = Damage(
            damage_multiplier=(0.0,),
            element=(element, 0.0),  # 无附着
            config=AttackConfig(attack_tag=f"{reaction_type.value}伤害"),
            name=reaction_type.value,
        )
        dmg.damage = damage
        dmg.set_source(source)
        dmg.set_target(target)
        # 标记为已计算，跳过 DamageSystem
        dmg.add_data("skip_damage_calculation", True)

        if self._engine:
            self._engine.publish(GameEvent(
                event_type=EventType.BEFORE_DAMAGE,
                frame=get_current_time(),
                source=source,
                data={"character": source, "target": target, "damage": dmg},
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
