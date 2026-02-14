from core.effect.common import TalentEffect
from core.event import EventType, GameEvent
from core.systems.contract.healing import Healing, HealingType
from core.tool import get_current_time
from core.systems.utils import AttributeCalculator
from character.FONTAINE.furina.data import MECHANISM_CONFIG


class EndlessWaltz(TalentEffect):
    """
    固有天赋一：停不了的圆舞。
    当场上角色受到溢出治疗且来源非芙宁娜时，全队周期性回复血量。
    """

    def __init__(self):
        super().__init__("停不了的圆舞", unlock_level=20)
        self.active_timer = 0
        self.heal_timer = 0

    def on_apply(self):
        # 订阅全场治疗结果
        self.character.event_engine.subscribe(EventType.AFTER_HEAL, self)

    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.AFTER_HEAL:
            # 条件：来源非芙宁娜 且 是当前场上角色 且 产生溢出
            heal_obj: Healing = event.data.get("healing")
            if (
                heal_obj
                and heal_obj.source != self.character
                and event.target.on_field
                and event.data.get("overflow", 0) > 0
            ):
                # 激活/重置 4 秒效果 (240 帧)
                self.active_timer = 240
                self.heal_timer = 0

    def on_frame_update(self):
        if not self.is_active or self.active_timer <= 0:
            return

        self.active_timer -= 1
        self.heal_timer += 1

        # 每 2 秒 (120 帧) 触发一次治疗
        if self.heal_timer >= 120:
            self._execute_team_healing()
            self.heal_timer = 0

    def _execute_team_healing(self):
        """为全队恢复 2% 最大生命值。"""
        if not self.character.ctx.team:
            return

        members = self.character.ctx.team.get_members()
        for m in members:
            max_hp = AttributeCalculator.get_hp(m)
            heal_val = max_hp * 0.02

            # 发布治疗事件
            heal_obj = Healing(
                base_multiplier=0, healing_type=HealingType.PASSIVE, name=self.name
            )
            heal_obj.final_value = heal_val

            self.character.event_engine.publish(
                GameEvent(
                    EventType.BEFORE_HEAL,
                    get_current_time(),
                    source=self.character,
                    data={
                        "character": self.character,
                        "target": m,
                        "healing": heal_obj,
                    },
                )
            )


class UnheardConfession(TalentEffect):
    """
    固有天赋二：无人听的自白。
    基于 HP 上限提升沙龙成员伤害，缩短歌者治疗间隔。
    """

    def __init__(self):
        super().__init__("无人听的自白", unlock_level=60)

    def on_apply(self):
        # 订阅伤害计算前置
        self.character.event_engine.subscribe(EventType.BEFORE_CALCULATE, self)

    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.BEFORE_CALCULATE:
            dmg_ctx = event.data.get("damage_context")
            # 仅加成芙宁娜战技召唤物的伤害
            if dmg_ctx and dmg_ctx.damage.config.icd_group in [
                "FurinaSalonShared",
                "None",
            ]:
                bonus = self._calculate_dmg_bonus()
                # 使用审计接口注入独立乘区增益
                dmg_ctx.add_modifier(
                    source="固有天赋：无人听的自白",
                    stat="独立乘区系数",
                    value=1 + bonus,
                    op="MULT",
                )

    def on_frame_update(self):
        if not self.is_active:
            return

        # 实时计算间隔缩减并注入芙宁娜实例供实体查询
        reduction_perc = self._calculate_heal_interval_reduction()
        base_interval = MECHANISM_CONFIG["SKILL_HEAL_INTERVAL"]
        # 缩短 X%
        self.character.singer_interval_override = int(
            base_interval * (1 - reduction_perc)
        )

    def _calculate_dmg_bonus(self) -> float:
        """每 1000 点提升 0.7%，上限 28%。"""
        hp = AttributeCalculator.get_hp(self.character)
        bonus = (hp // 1000) * 0.007
        return min(0.28, bonus)

    def _calculate_heal_interval_reduction(self) -> float:
        """每 1000 点降低 0.4%，上限 16%。"""
        hp = AttributeCalculator.get_hp(self.character)
        reduction = (hp // 1000) * 0.004
        return min(0.16, reduction)
