from typing import Any
from core.effect.base import BaseEffect
from core.effect.common import TalentEffect, ConstellationEffect
from core.event import EventHandler, EventType, GameEvent, HealEvent, DamageEvent
from core.team import Team
from core.tool import GetCurrentTime, summon_energy
from core.action.healing import Healing, HealingType
from core.action.damage import Damage, DamageType

class UniversalExaltationEffect(BaseEffect):
    """普世欢腾效果 (大招增益)"""
    def __init__(self, owner: Any, source_char: Any, burst_skill: Any):
        super().__init__(owner, "普世欢腾", duration=18*60)
        self.source_char = source_char
        self.burst_skill = burst_skill
        self.last_applied_fanfare = 0
        
        self.dmg_ratios = [0.07, 0.09, 0.11, 0.13, 0.15, 0.17, 0.19, 0.21, 0.23, 0.25, 0.27, 0.29, 0.31, 0.33, 0.35]
        self.heal_ratios = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.11, 0.12, 0.13, 0.14, 0.15]

    def on_tick(self, target: Any):
        """逐帧动态更新面板"""
        # 先清除上一帧的加成
        self._update_panel(-1)
        # 应用当前气氛值的加成
        self.last_applied_fanfare = self.burst_skill.fanfare_points
        self._update_panel(1)

    def _update_panel(self, sign: int):
        points = self.last_applied_fanfare
        lv_idx = self.burst_skill.lv - 1
        self.owner.attribute_panel['伤害加成'] += sign * points * self.dmg_ratios[lv_idx]
        self.owner.attribute_panel['受治疗加成'] += sign * points * self.heal_ratios[lv_idx]

    def on_remove(self):
        self._update_panel(-1)
        if self.owner == self.source_char:
            self.burst_skill.reset_fanfare()

class PassiveSkillEffect_1(TalentEffect, EventHandler):
    """天赋1：停不了的圆舞"""
    def __init__(self):
        super().__init__("停不了的圆舞")

    def apply(self, character: Any):
        super().apply(character)
        self.character.event_engine.subscribe(EventType.AFTER_HEAL, self)

    def handle_event(self, event: GameEvent):
        # 如果溢出治疗来自非芙宁娜本人
        if (event.data['target'] == Team.current_character and 
            event.source != self.character):
            heal_val = event.data['healing'].final_value
            # 判断是否溢出
            if heal_val > event.data['target'].max_hp - event.data['target'].current_hp:
                EndlessWaltzEffect(self.character).apply()

class EndlessWaltzEffect(BaseEffect):
    """天赋1产生的持续治疗"""
    def __init__(self, owner: Any):
        super().__init__(owner, "停不了的圆舞", duration=4*60)
        self.tick_timer = 0

    def on_tick(self, target: Any):
        self.tick_timer += 1
        if self.tick_timer % 120 == 0: # 每2秒一次
            for member in Team.team:
                h = Healing(2, HealingType.PASSIVE, "停不了的圆舞")
                h.base_value = '生命值'
                self.owner.event_engine.publish(HealEvent(self.owner, member, h, GetCurrentTime()))

class PassiveSkillEffect_2(TalentEffect, EventHandler):
    """天赋2：无人听的自白"""
    def __init__(self):
        super().__init__("无人听的自白")

    def apply(self, character: Any):
        super().apply(character)
        self.character.event_engine.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)

    def handle_event(self, event: GameEvent):
        damage = event.data['damage']
        if damage.name in ['乌瑟勋爵','海薇玛夫人','谢贝蕾妲小姐']:
            bonus = min(self.character.max_hp // 1000 * 0.7, 28)
            damage.panel['伤害加成'] += bonus

class ConstellationEffect_1(ConstellationEffect):
    """1命：初始气氛值"""
    def apply(self, character: Any):
        super().apply(character)
        character.Burst.fanfare_max = 400
        character.Burst.fanfare_initial = 150

class ConstellationEffect_2(ConstellationEffect):
    """2命：气氛值获取提速与生命上限提升"""
    def apply(self, character: Any):
        super().apply(character)
        # 覆写气氛值增加逻辑 (250%)
        character.Burst.fanfare_gain_ratio = 2.5

class ConstellationEffect_3(ConstellationEffect):
    """3命：大招等级提升"""
    def apply(self, character: Any):
        super().apply(character)
        character.Burst.lv = min(15, character.Burst.lv + 3)

class ConstellationEffect_4(ConstellationEffect, EventHandler):
    """4命：回能"""
    def __init__(self):
        super().__init__("若非处幽冥")
        self.last_trigger = 0

    def apply(self, character: Any):
        super().apply(character)
        self.character.event_engine.subscribe(EventType.AFTER_DAMAGE, self)
        self.character.event_engine.subscribe(EventType.AFTER_HEAL, self)

    def handle_event(self, event: GameEvent):
        if GetCurrentTime() - self.last_trigger >= 5*60:
            self.last_trigger = GetCurrentTime()
            summon_energy(4, self.character, ('无', 0))

class ConstellationEffect_5(ConstellationEffect):
    """5命：战技等级提升"""
    def apply(self, character: Any):
        super().apply(character)
        character.Skill.lv = min(15, character.Skill.lv + 3)

class ConstellationEffect_6(ConstellationEffect):

    """6命：万众瞩目"""

    def apply(self, character: Any):

        super().apply(character)

        # 实际逻辑由 CenterOfAttentionEffect 实现，在 E 技能开启后触发



class CenterOfAttentionEffect(BaseEffect, EventHandler):

    """6命 - 万众瞩目状态"""

    def __init__(self, owner: Any):

        super().__init__(owner, "万众瞩目", duration=10*60)

        self.count = 0

        self.max_count = 6

        self.last_proc_time = 0



    def on_apply(self):

        self.owner.event_engine.subscribe(EventType.BEFORE_CALCULATE, self)

        self.owner.event_engine.subscribe(EventType.BEFORE_FIXED_DAMAGE, self)

        self.owner.event_engine.subscribe(EventType.AFTER_ATTACK, self)



    def on_remove(self):

        self.owner.event_engine.unsubscribe(EventType.BEFORE_CALCULATE, self)

        self.owner.event_engine.unsubscribe(EventType.BEFORE_FIXED_DAMAGE, self)

        self.owner.event_engine.unsubscribe(EventType.AFTER_ATTACK, self)



    def handle_event(self, event: GameEvent):

        if event.source != self.owner: return

        

        # 1. 处理附魔

        if event.event_type == EventType.BEFORE_CALCULATE:

            damage = event.data['damage']

            if damage.damage_type in [DamageType.NORMAL, DamageType.CHARGED, DamageType.PLUNGING]:

                # 无法被覆盖的水附魔

                damage.element = ('水', 1)

                damage.setDamageData('不可覆盖', True)



        # 2. 处理基于生命上限的伤害提升

        elif event.event_type == EventType.BEFORE_FIXED_DAMAGE:

            damage = event.data['damage']

            if damage.damage_type in [DamageType.NORMAL, DamageType.CHARGED, DamageType.PLUNGING]:

                bonus = self.owner.max_hp * 0.18

                if self.owner.arkhe == '芒性':

                    bonus += self.owner.max_hp * 0.25 # 芒性额外加成

                damage.panel['固定伤害基础值加成'] += bonus

                self.count += 1

                if self.count >= self.max_count: self.remove()



        # 3. 处理后续团队效果 (回血/扣血)

        elif event.event_type == EventType.AFTER_ATTACK:

            now = GetCurrentTime()

            if now - self.last_proc_time >= 0.1*60:

                self.last_proc_time = now

                if self.owner.arkhe == '荒性':

                    # 全队回血

                    CenterOfAttentionHealEffect(self.owner).apply()

                else:

                    # 全队扣血

                    for member in Team.team:

                        self.owner.event_engine.publish(HurtEvent(self.owner, member, 0.01 * member.max_hp, now))



class CenterOfAttentionHealEffect(BaseEffect):

    """6命 - 荒性普攻触发的全队治疗"""

    def __init__(self, owner: Any):

        super().__init__(owner, "万众瞩目_治疗", duration=2.9*60)

        self.tick_timer = 0



    def on_tick(self, target: Any):

        self.tick_timer += 1

        if self.tick_timer % 60 == 0:

            for member in Team.team:

                h = Healing(base_multiplier=4, healing_type=HealingType.BURST, name="万众瞩目_治疗")

                h.base_value = '生命值'

                self.owner.event_engine.publish(HealEvent(self.owner, member, h, GetCurrentTime()))