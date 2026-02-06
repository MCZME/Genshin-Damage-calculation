import random
from core.logger import get_emulation_logger
from core.team import Team

from core.event import EventBus, EventHandler, EventType
from core.effect.stat_modifier import AttackBoostEffect
import core.tool as T
from weapon.weapon import Weapon
from core.registry import register_weapon

@register_weapon("溢彩心念", "法器")
class VividNotions(Weapon, EventHandler):
    ID = 215
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, VividNotions.ID, level, lv)
        self.character.attribute_panel["攻击力%"] += [28,35,42,49,56][lv-1]
        
        # 效果状态
        self.morning_effect = MorningGlowEffect(self.character,lv)  # 初霞之彩
        self.dusk_effect = DuskGlowEffect(self.character,lv)       # 苍暮之辉
        self.remove_timer = 0       # 效果移除计时器
        
        # 订阅事件
        EventBus.subscribe(EventType.BEFORE_SKILL, self)
        EventBus.subscribe(EventType.BEFORE_BURST, self)
        EventBus.subscribe(EventType.BEFORE_PLUNGING_ATTACK, self)

    def handle_event(self, event):
        if event.data["character"] != self.character:
            return
            
        # 元素战技/爆发触发苍暮之辉
        if event.event_type in (EventType.BEFORE_SKILL, EventType.BEFORE_BURST):
            self.dusk_effect.duration = 900  # 重置持续时间
            self.dusk_effect.apply()  
        # 下落攻击触发初霞之彩
        elif event.event_type == EventType.BEFORE_PLUNGING_ATTACK:
            self.morning_effect.duration = 900  # 重置持续时间
            self.morning_effect.apply()
