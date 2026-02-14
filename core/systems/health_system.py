from typing import Any, Optional

from core.systems.contract.healing import Healing
from core.context import EventEngine
from core.event import EventType, GameEvent
from core.logger import get_emulation_logger
from core.systems.base_system import GameSystem
from core.systems.utils import AttributeCalculator


class HealingCalculator:
    """
    治疗数值计算辅助类。
    负责根据缩放属性 (攻击力、生命值、防御力) 计算最终治疗量。
    """

    def __init__(self, source: Any, target: Any, healing: Healing):
        self.source = source
        self.target = target
        self.healing = healing

    def _get_base_attr(self) -> float:
        """根据 multiplier_provider 获取基础属性值。"""
        entity = (
            self.source if self.healing.multiplier_provider == "来源" else self.target
        )
        stat = self.healing.scaling_stat

        if stat == "攻击力":
            return AttributeCalculator.get_attack(entity)
        if stat == "生命值":
            return AttributeCalculator.get_hp(entity)
        if stat == "防御力":
            return AttributeCalculator.get_defense(entity)
        return 0.0

    def calculate(self) -> float:
        """执行计算并更新 Healing 对象的 final_value。"""
        base_val = self._get_base_attr()
        m = self.healing.base_multiplier

        # 处理倍率 (百分比 + 固定值) 或 仅百分比
        if isinstance(m, (tuple, list)):
            raw_value = (m[0] / 100.0) * base_val + m[1]
        else:
            raw_value = (m / 100.0) * base_val

        # 应用治疗加成与受治疗加成
        bonus = AttributeCalculator.get_healing_bonus(self.source)
        received_bonus = AttributeCalculator.get_healed_bonus(self.target)

        final_value = raw_value * (1 + bonus) * (1 + received_bonus)
        self.healing.final_value = final_value
        return final_value


class HealthSystem(GameSystem):
    """
    生命值管理系统。
    负责处理全场实体的治疗 (Heal) 与受伤 (Hurt) 结算，并协调护盾吸收。
    """

    def register_events(self, engine: EventEngine) -> None:
        """订阅治疗与受伤的原始事件。"""
        engine.subscribe(EventType.BEFORE_HEAL, self)
        engine.subscribe(EventType.BEFORE_HURT, self)

    def handle_event(self, event: GameEvent) -> None:
        """事件分发处理。"""
        if event.event_type == EventType.BEFORE_HEAL:
            self._handle_heal(event)
        elif event.event_type == EventType.BEFORE_HURT:
            self._handle_hurt(event)

    def _handle_heal(self, event: GameEvent) -> None:
        """处理治疗逻辑。"""
        data = event.data
        source = data.get("character")
        from core.entities.base_entity import CombatEntity

        target: Optional[CombatEntity] = data.get("target")
        healing: Healing = data.get("healing")

        if not target or not healing:
            return

        # 1. 执行数值计算
        calculator = HealingCalculator(source, target, healing)
        calculator.calculate()

        # 2. 调用标准接口执行回复 (不再使用 hasattr)
        target.heal(healing.final_value)

        # 3. 记录日志
        get_emulation_logger().log_heal(source, target, healing)

        # 4. 发布治疗后置事件
        self.engine.publish(
            GameEvent(
                event_type=EventType.AFTER_HEAL,
                frame=event.frame,
                source=source,
                data={"character": source, "target": target, "healing": healing},
            )
        )

    def _handle_hurt(self, event: GameEvent) -> None:
        """处理受伤逻辑 (包含护盾扣除后的实际血量扣除)。"""
        data = event.data
        from core.entities.base_entity import CombatEntity

        target: Optional[CombatEntity] = data.get("target")
        source = data.get("character")
        amount = data.get("amount", 0.0)
        is_ignore_shield = data.get("ignore_shield", False)

        if not target or amount <= 0:
            return

        # 1. 调用标准接口执行扣血 (不再使用 hasattr)
        target.hurt(amount)

        # 2. 记录日志 (根据是否无视护盾调整描述)
        msg_prefix = "🩸 [侵蚀]" if is_ignore_shield else "💔"
        get_emulation_logger().log_info(
            f"{msg_prefix} {target.name} 受到 {round(amount, 1)} 点实际伤害",
            sender="Health",
        )

        # 3. 发布受伤后置事件
        self.engine.publish(
            GameEvent(
                event_type=EventType.AFTER_HURT,
                frame=event.frame,
                source=source,
                data={
                    "character": source,
                    "target": target,
                    "amount": amount,
                    "ignore_shield": is_ignore_shield,
                },
            )
        )
