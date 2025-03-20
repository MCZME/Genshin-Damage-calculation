from character.character import Character
from setup.Event import EventBus, NightSoulBlessingEvent, NightSoulConsumptionEvent
from setup.Tool import GetCurrentTime


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
        """安全消耗夜魂值并触发事件"""
        if not self.Nightsoul_Blessing:
            return False

        # 发布消耗事件
        actual_amount = min(amount, self.current_night_soul)
        event =NightSoulConsumptionEvent(
            character=self,
            amount=actual_amount,
            frame=GetCurrentTime()
        )
        EventBus.publish(event)
        if event.cancelled:
            return True
        
        self.current_night_soul -= actual_amount
        EventBus.publish(NightSoulConsumptionEvent(
            character=self,
            amount=actual_amount,
            frame=GetCurrentTime(),
            before=False
        ))
        
        # 自动退出加持状态检测
        if self.current_night_soul <= 0:
            self.chargeNightsoulBlessing()
        return True
    
    def gain_night_soul(self, amount):
        """获得夜魂值"""
        if not self.Nightsoul_Blessing:
            self.chargeNightsoulBlessing()
        self.current_night_soul = min(
            self.max_night_soul, 
            self.current_night_soul + amount
        )

    def chargeNightsoulBlessing(self):
        if self.Nightsoul_Blessing:
            self.after_nightsoulBlessingevent = NightSoulBlessingEvent(self, frame=GetCurrentTime(), before=False)
            EventBus.publish(self.after_nightsoulBlessingevent)
            self.Nightsoul_Blessing = False
        else:
            self.before_nightsoulBlessingevent = NightSoulBlessingEvent(self, frame=GetCurrentTime())
            EventBus.publish(self.before_nightsoulBlessingevent)
            self.Nightsoul_Blessing = True
            print(f"🌙 夜魂加持")