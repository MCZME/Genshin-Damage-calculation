from core.effect.common import ConstellationEffect
from core.event import EventType, GameEvent
from character.FONTAINE.furina.effects import FurinaCenterOfAttentionEffect


class FurinaC1(ConstellationEffect):
    """命座一：爱是难驯鸟，哀乞亦无用。"""

    def __init__(self):
        super().__init__("爱是难驯鸟，哀乞亦无用。", unlock_constellation=1)


class FurinaC2(ConstellationEffect):
    """命座二：女人皆善变，仿若水中萍。"""

    def __init__(self):
        super().__init__("女人皆善变，仿若水中萍。", unlock_constellation=2)


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
        from core.tool import get_current_time

        current_frame = get_current_time()
        if current_frame - self.last_trigger_frame < 300:  # 5s CD
            return

        is_trigger = False
        if event.event_type == EventType.AFTER_DAMAGE:
            dmg = event.data.get("damage")
            # 召唤物命中判定 (通过 icd_group 进行原生对齐)
            if (
                dmg
                and dmg.config.icd_group in ["FurinaSalonShared", "None"]
                and dmg.config.is_ranged
            ):
                is_trigger = True
        elif event.event_type == EventType.AFTER_HEAL:
            # 判断是否为歌者治疗
            healing = event.data.get("healing")
            if healing and healing.name == "众水的歌者治疗":
                is_trigger = True

        if is_trigger:
            if (
                hasattr(self.character, "elemental_energy")
                and self.character.elemental_energy
            ):
                self.character.elemental_energy.gain_energy(4.0, source_type="命座四")
                self.last_trigger_frame = current_frame


class FurinaC5(ConstellationEffect):
    """命座五：我已有觉察，他名即是…！"""

    def __init__(self):
        super().__init__("我已有觉察，他名即是…！", unlock_constellation=5)

    def on_apply(self):
        # 战技等级 +3
        self.character.skill_params[1] += 3


class FurinaC6(ConstellationEffect):
    """命座六：诸君听我颂，共举爱之杯！"""

    def __init__(self):
        super().__init__("诸君听我颂，共举爱之杯！", unlock_constellation=6)

    def on_apply(self):
        # 施放战技时获得状态
        self.character.event_engine.subscribe(EventType.BEFORE_SKILL, self)

    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.BEFORE_SKILL:
            # 触发 6 命核心效果状态机 (逻辑已收拢至 effects.py)
            FurinaCenterOfAttentionEffect(self.character).apply()
