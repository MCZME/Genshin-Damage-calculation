from core.action.damage import DamageType
from weapon.weapon import Weapon
from core.event import EventBus, EventType, EventHandler
from core.registry import register_weapon

@register_weapon("「渔获」", "长柄武器")
class TheCatch(Weapon, EventHandler):
    ID = 151
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, TheCatch.ID, level, lv)
        self.burst_bonus = [16,20,24,28,32]
        self.critical_bonus = [6,7.5,9,10.5,12]
        
        # 订阅伤害加成计算前事件
        EventBus.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)
        EventBus.subscribe(EventType.BEFORE_CRITICAL, self)

    def handle_event(self, event):
        if event.data["character"] != self.character:
            return
        # 只处理元素爆发类型的伤害
        if event.event_type == EventType.BEFORE_DAMAGE_BONUS and event.data["damage"].damage_type == DamageType.BURST:
            event.data["damage"].panel["伤害加成"] += self.burst_bonus[self.lv-1]
            event.data["damage"].setDamageData("渔获_伤害加成", self.burst_bonus[self.lv-1])
        elif event.event_type == EventType.BEFORE_CRITICAL and event.data["damage"].damage_type == DamageType.BURST:
            event.data["damage"].panel["暴击率"] += self.critical_bonus[self.lv-1]
            event.data["damage"].setDamageData("渔获_暴击率", self.critical_bonus[self.lv-1])
