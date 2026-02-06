from core.action.damage import DamageType
from core.tool import summon_energy
from weapon.weapon import Weapon
from core.event import EventBus, EventType, EventHandler
from core.effect.stat_modifier import AttackBoostEffect
from core.registry import register_weapon

@register_weapon("沙中伟贤的对答", "长柄武器")
class DialoguesOfTheDesertSages(Weapon, EventHandler):
    ID = 157
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, DialoguesOfTheDesertSages.ID, level, lv)
        self.energy_restore = [8, 10, 12, 14, 16]
        self.last_trigger_frame = -600  # 初始化为-600确保第一次可以触发
        
        EventBus.subscribe(EventType.AFTER_HEAL, self)

    def handle_event(self, event):
        if event.data["healing"].source != self.character:
            return
            
        current_frame = event.frame
        if current_frame - self.last_trigger_frame < 600:  # 10秒=600帧
            return
            
        # 触发能量恢复
        summon_energy(1,self.character,("无",self.energy_restore[self.lv-1]),True,True,0)
        
        self.last_trigger_frame = current_frame
