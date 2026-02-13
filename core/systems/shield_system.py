from typing import Any, List

from core.systems.contract.shield import ShieldConfig
from core.effect.common import ShieldEffect
from core.event import EventType, GameEvent
from core.mechanics.aura import Element
from core.systems.base_system import GameSystem
from core.context import EventEngine


class ShieldSystem(GameSystem):
    """
    护盾系统中心。
    统一处理全场实体的护盾生成、伤害吸收分发以及生命周期管理。
    """

    def register_events(self, engine: EventEngine) -> None:
        """订阅受伤前置事件，以便拦截并扣除护盾量。"""
        # 我们假设 HealthSystem 在扣血前发布 BEFORE_HURT
        engine.subscribe(EventType.BEFORE_HURT, self)

    def add_shield(self, target: Any, config: ShieldConfig) -> ShieldEffect:
        """为目标实体添加一个护盾。

        Args:
            target: 目标战斗实体。
            config: 护盾配置参数。

        Returns:
            ShieldEffect: 生成的护盾效果实例。
        """
        # 1. 计算护盾强效 (来自创建者)
        shield_strength = 0.0
        if config.creator:
            shield_strength = getattr(config.creator, "attribute_data", {}).get("护盾强效", 0.0)
        
        # 2. 计算最终吸收量
        final_hp = config.base_hp * (1 + shield_strength / 100.0)
        
        # 3. 创建并应用效果
        effect = ShieldEffect(target, config.name, config.element, final_hp, config.duration)
        effect.apply()
        
        from core.logger import get_emulation_logger
        get_emulation_logger().log_info(
            f"{target.name} 获得了护盾: {config.name} (吸收量: {round(final_hp, 1)})", 
            sender="Shield"
        )
        return effect

    def handle_event(self, event: GameEvent) -> None:
        """处理受伤事件，执行护盾吸收逻辑。"""
        if event.event_type == EventType.BEFORE_HURT:
            self._absorb_damage(event)

    def _absorb_damage(self, event: GameEvent) -> None:
        """核心吸收逻辑：多盾同时扣除。"""
        # 1. 卫语句：检查是否无视护盾 (如侵蚀/流血效果)
        if event.data.get("ignore_shield", False):
            return

        target = event.data.get("target")
        if not target or not hasattr(target, "shield_effects") or not target.shield_effects:
            return

        # 这里的 amount 是原始伤害值
        raw_damage = event.data.get("amount", 0.0)
        damage_element = event.data.get("element", Element.NONE)
        
        max_absorbed = 0.0
        active_shields: List[ShieldEffect] = list(target.shield_effects)

        for shield in active_shields:
            # 1. 计算针对该伤害元素的吸收倍率
            absorption_mult = self._get_absorption_multiplier(shield.element, damage_element)
            
            # 2. 计算该护盾实际需要扣除的血量
            # 实际扣除 = 伤害 / 吸收倍率
            to_deduct = raw_damage / absorption_mult
            
            # 3. 记录该护盾能吸收的最大原始伤害量
            absorbed_this_time = min(raw_damage, shield.current_hp * absorption_mult)
            max_absorbed = max(max_absorbed, absorbed_this_time)
            
            # 4. 扣除护盾值
            shield.current_hp -= to_deduct
            
            # 5. 检查破碎
            if shield.current_hp <= 0:
                shield.remove()

        # 6. 修正事件中的伤害量
        # 剩余伤害 = 原始伤害 - 护盾吸收掉的最高伤害量
        remaining_damage = max(0.0, raw_damage - max_absorbed)
        event.data["amount"] = remaining_damage
        
        if max_absorbed > 0:
            from core.logger import get_emulation_logger
            get_emulation_logger().log_info(
                f"护盾吸收了 {round(max_absorbed, 1)} 点伤害，剩余伤害: {round(remaining_damage, 1)}", 
                sender="Shield"
            )

    def _get_absorption_multiplier(self, shield_el: Element, damage_el: Element) -> float:
        """获取元素吸收倍率。
        
        - 属性匹配 (如冰盾抗冰): 250%
        - 岩盾 (对全元素): 150%
        - 其他情况: 100%
        """
        if shield_el == Element.GEO:
            return 1.5
        if shield_el == damage_el and shield_el != Element.NONE:
            return 2.5
        return 1.0
