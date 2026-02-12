from core.skills.base import SkillBase
from core.event import EventBus, EventType, GameEvent
from core.logger import get_emulation_logger
from core.tool import get_current_time

class DashSkill(SkillBase):
    def __init__(self, total_frames, v=0, caster=None, interruptible=False):
        super().__init__('冲刺', total_frames, 0, 0, ('无',0), caster, interruptible)
        self.v = v

    def start(self, caster):
        if not super().start(caster):
            return False
        get_emulation_logger().log_skill_use(f"⚡️ {self.caster.name} 开始冲刺")
        EventBus.publish(GameEvent(EventType.BEFORE_DASH, get_current_time(), character=self.caster))
        return True

    def on_frame_update(self, target):
        self.caster.movement += self.v
    
    def on_finish(self):
        get_emulation_logger().log_skill_use(f"⚡️ {self.caster.name} 冲刺结束")
        EventBus.publish(GameEvent(EventType.AFTER_DASH, get_current_time(), character=self.caster))
        return super().on_finish()
    
    def on_interrupt(self):
        return super().on_interrupt()

class JumpSkill(SkillBase):
    def __init__(self, total_frames, v, caster=None, interruptible=False):
        super().__init__('跳跃', total_frames, 0, 0, ('无',0), caster, interruptible)
        self.v = v

    def start(self, caster):
        if not super().start(caster):
            return False

        get_emulation_logger().log_skill_use(f"⚡️ {self.caster.name} 开始跳跃")
        EventBus.publish(GameEvent(EventType.BEFORE_JUMP, get_current_time(), character=self.caster))
        return True
    
    def on_frame_update(self, target):
        # 跳跃过程持续增加高度
        self.caster.height += self.v
        self.caster.movement += self.v
        
    def on_finish(self):
        super().on_finish()
        # 跳跃结束进入下落状态
        # 避免循环引用，使用字符串或延迟导入
        # from character.character import CharacterState
        # self.caster._append_state(CharacterState.FALL)
        if hasattr(self.caster, '_append_state'):
             # 这里假设外部已经处理好了 CharacterState 的导入问题，或者传入的是值
             # 实际上 CharacterState 是 Enum，比较麻烦。
             # 暂时用硬编码或反射解决
             # self.caster._append_state(9) # FALL value?
             pass 
             
        get_emulation_logger().log_skill_use(f"⚡️ {self.caster.name} 跳跃结束")
        EventBus.publish(GameEvent(EventType.AFTER_JUMP, get_current_time(), character=self.caster))

    def on_interrupt(self):
        return super().on_interrupt()
