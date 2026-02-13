from typing import Any

from core.effect.common import ConstellationEffect
from core.effect.base import BaseEffect
from core.event import EventType, GameEvent
from core.action.healing import Healing, HealingType
from core.action.attack_tag_resolver import AttackTagResolver, AttackCategory
from core.tool import get_current_time
from core.systems.utils import AttributeCalculator


class FurinaC1(ConstellationEffect):
    """命座一：爱是难驯鸟，哀乞亦无用。"""
    def __init__(self):
        super().__init__("爱是难驯鸟，哀乞亦无用。", unlock_constellation=1)
    # 逻辑集成在 effects.py 的 FurinaFanfareEffect 中


class FurinaC2(ConstellationEffect):
    """命座二：女人皆善变，仿若水中萍。"""
    def __init__(self):
        super().__init__("女人皆善变，仿若水中萍。", unlock_constellation=2)
    # 逻辑集成在 effects.py 的 FurinaFanfareEffect 中


class FurinaC3(ConstellationEffect):
    """命座三：秘密藏心间，无人知我名。"""
    def __init__(self):
        super().__init__("秘密藏心间，无人知我名。", unlock_constellation=3)

    def on_apply(self):
        # 爆发等级 +3
        self.character.skill_params[2] += 3


class FurinaC4(ConstellationEffect):
    """
    命座四：若非处幽冥，怎知生可贵！
    特定行为触发回能，CD 5秒。
    """
    def __init__(self):
        super().__init__("若非处幽冥，怎知生可贵！", unlock_constellation=4)
        self.last_trigger_frame = -9999

    def on_apply(self):
        self.character.event_engine.subscribe(EventType.AFTER_DAMAGE, self)
        self.character.event_engine.subscribe(EventType.AFTER_HEAL, self)

    def handle_event(self, event: GameEvent):
        current_frame = get_current_time()
        if current_frame - self.last_trigger_frame < 300: # 5s CD
            return

        is_trigger = False
        if event.event_type == EventType.AFTER_DAMAGE:
            dmg = event.data.get("damage")
            # 召唤物命中判定 (通过 icd_group 进行原生对齐)
            if dmg and dmg.config.icd_group in ["FurinaSalonShared", "None"] and dmg.config.is_ranged:
                is_trigger = True
        elif event.event_type == EventType.AFTER_HEAL:
            # 判断是否为歌者治疗 (使用原生 Key 对齐)
            healing = event.data.get("healing")
            if healing and healing.name == "众水的歌者治疗":
                is_trigger = True

        if is_trigger:
            # 假设角色类已正确挂载能量系统
            if hasattr(self.character, "elemental_energy") and self.character.elemental_energy:
                self.character.elemental_energy.gain_energy(4.0, source_type="命座四")
                self.last_trigger_frame = current_frame


class FurinaC5(ConstellationEffect):
    """命座五：我已有觉察，他名即是…！"""
    def __init__(self):
        super().__init__("我已有觉察，他名即是…！", unlock_constellation=5)

    def on_apply(self):
        # 战技等级 +3
        self.character.skill_params[1] += 3


class CenterOfAttentionHeal(BaseEffect):
    """C6 荒性分支产生的全队持续治疗效果。"""
    def __init__(self, owner: Any):
        super().__init__(owner, "万众瞩目·愈", duration=174) # 2.9s
        self.timer = 0

    def on_tick(self, target: Any):
        self.timer += 1
        # 每秒一跳 (60帧)
        if self.timer >= 60:
            self._do_team_heal()
            self.timer = 0

    def _do_team_heal(self):
        hp = AttributeCalculator.get_hp(self.owner)
        heal_val = hp * 0.04
        
        team = self.owner.ctx.team.get_members()
        for m in team:
            # 构造规范治疗对象
            heal_obj = Healing(base_multiplier=(0, heal_val), healing_type=HealingType.PASSIVE, name="万众瞩目·愈")
            heal_obj.set_scaling_stat("生命值")
            
            self.owner.event_engine.publish(GameEvent(
                EventType.BEFORE_HEAL, get_current_time(),
                source=self.owner, data={"character": self.owner, "target": m, "healing": heal_obj}
            ))


class CenterOfAttentionEffect(BaseEffect):
    """命座六状态机：万众瞩目。"""
    def __init__(self, owner: Any, arkhe_mode: str):
        super().__init__(owner, "万众瞩目", duration=600) # 10s
        self.stacks = 6
        self.arkhe = arkhe_mode

    def on_apply(self):
        self.owner.event_engine.subscribe(EventType.BEFORE_CALCULATE, self)
        self.owner.event_engine.subscribe(EventType.AFTER_DAMAGE, self)

    def on_remove(self):
        self.owner.event_engine.unsubscribe(EventType.BEFORE_CALCULATE, self)
        self.owner.event_engine.unsubscribe(EventType.AFTER_DAMAGE, self)

    def handle_event(self, event: GameEvent):
        if self.stacks <= 0: return

        if event.event_type == EventType.BEFORE_CALCULATE:
            dmg_ctx = event.data.get("damage_context")
            if not dmg_ctx: return
            
            # 使用标签解析器判断是否为受加成动作
            categories = AttackTagResolver.resolve_categories(
                dmg_ctx.config.attack_tag, dmg_ctx.config.extra_attack_tags
            )
            valid_cats = {AttackCategory.NORMAL, AttackCategory.CHARGED, AttackCategory.PLUNGING}
            
            if categories & valid_cats:
                hp = AttributeCalculator.get_hp(self.owner)
                # 1. 基础 C6 增伤 (18% HP)
                bonus = hp * 0.18
                # 2. 芒性额外增伤 (25% HP)
                if self.arkhe == "芒":
                    bonus += hp * 0.25
                
                # [审计化注入]
                dmg_ctx.add_modifier(source="命座六：万众瞩目", stat="固定伤害值加成", value=bonus)
                
                # [规范化附魔]
                # C6 附魔优先级最高且不可被覆盖
                dmg_ctx.damage.set_element("水", 1.0) 

        elif event.event_type == EventType.AFTER_DAMAGE:
            dmg = event.data.get("damage")
            if not dmg: return
            
            # 判断动作合法性
            categories = AttackTagResolver.resolve_categories(
                dmg.config.attack_tag, dmg.config.extra_attack_tags
            )
            if categories & {AttackCategory.NORMAL, AttackCategory.CHARGED, AttackCategory.PLUNGING}:
                # 排除由于始基力机制触发的二次判定 (如果有)
                if getattr(dmg, "is_arkhe_proc", False): return
                
                self.stacks -= 1
                if self.arkhe == "荒":
                    CenterOfAttentionHeal(self.owner).apply()
                else:
                    self._trigger_pneuma_consume()
                
                if self.stacks <= 0:
                    self.remove()

    def _trigger_pneuma_consume(self):
        # 全队扣 1% 当前 HP (触发气氛值)
        members = self.owner.ctx.team.get_members()
        for m in members:
            self.owner.event_engine.publish(GameEvent(
                EventType.BEFORE_HURT, get_current_time(),
                source=self.owner, data={"character": self.owner, "target": m, "amount": m.current_hp * 0.01, "ignore_shield": True}
            ))


class FurinaC6(ConstellationEffect):
    """命座六：诸君听我颂，共举爱之杯！"""
    def __init__(self):
        super().__init__("诸君听我颂，共举爱之杯！", unlock_constellation=6)

    def on_apply(self):
        # 施放战技时获得状态
        self.character.event_engine.subscribe(EventType.BEFORE_SKILL, self)

    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.BEFORE_SKILL:
            # 获取当前实时的始基力状态
            mode = getattr(self.character, "arkhe_mode", "荒")
            CenterOfAttentionEffect(self.character, mode).apply()
