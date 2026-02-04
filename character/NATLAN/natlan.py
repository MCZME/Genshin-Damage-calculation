from character.character import Character
from core.event import EventBus, NightSoulBlessingEvent, NightSoulChangeEvent
from core.logger import get_emulation_logger
from core.tool import GetCurrentTime


class Natlan(Character):
    def __init__(self, id=1, level=1, skill_params=[1,1,1], constellation=0):
        super().__init__(id, level, skill_params, constellation)
        self.association = '纳塔'
    
    def _init_character(self):
        super()._init_character()
        self.max_night_soul = 80 # 夜魂值上限
        self.current_night_soul = 0
        self.Nightsoul_Blessing = False # 夜魂加持状态
        self.time_accumulator = 0   # 时间累积器

    def consume_night_soul(self, amount):
        """消耗夜魂值"""
        # 发布消耗事件
        actual_amount = min(amount, self.current_night_soul)
        event =NightSoulChangeEvent(
            character=self,
            amount=-actual_amount,
            frame=GetCurrentTime()
        )
        EventBus.publish(event)
        if event.cancelled:
            return
        
        self.current_night_soul -= actual_amount
        EventBus.publish(NightSoulChangeEvent(
            character=self,
            amount=-actual_amount,
            frame=GetCurrentTime(),
            before=False
        ))
    
    def gain_night_soul(self, amount):
        """获得夜魂值"""
        actual_amount = min(amount, self.max_night_soul - self.current_night_soul)
        EventBus.publish(NightSoulChangeEvent(
            character=self,
            amount=actual_amount,
            frame=GetCurrentTime(),
            before=False
        ))

        self.current_night_soul += actual_amount

        EventBus.publish(NightSoulChangeEvent(
            character=self,
            amount=actual_amount,
            frame=GetCurrentTime(),
            before=False
        ))

    def chargeNightsoulBlessing(self):
        if self.Nightsoul_Blessing:
            self.romve_NightSoulBlessing()
        else:
            self.gain_NightSoulBlessing()

    def gain_NightSoulBlessing(self):
        self.before_nightsoulBlessingevent = NightSoulBlessingEvent(self, frame=GetCurrentTime())
        EventBus.publish(self.before_nightsoulBlessingevent)
        self.Nightsoul_Blessing = True
        get_emulation_logger().log_effect(f"🌙 夜魂加持")

    def romve_NightSoulBlessing(self):
        self.after_nightsoulBlessingevent = NightSoulBlessingEvent(self, frame=GetCurrentTime(), before=False)
        EventBus.publish(self.after_nightsoulBlessingevent)
        self.Nightsoul_Blessing = False
        get_emulation_logger().log_effect(f"🌙 {self.name}夜魂加持结束")
