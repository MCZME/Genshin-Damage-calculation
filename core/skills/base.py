from abc import ABC, abstractmethod
from typing import Any, Tuple, Optional
from core.logger import get_emulation_logger
from core.tool import GetCurrentTime
from core.action.action_data import ActionFrameData

# 技能基类
class SkillBase(ABC):
    def __init__(self, name: str, total_frames: int, cd: int, lv: int, element: Tuple[str, int], 
                 caster: Any = None, interruptible: bool = False):
        self.name = name
        self.total_frames = total_frames    # 总帧数
        self.current_frame = 0              # 当前帧
        self.cd = cd                         # 冷却时间
        self.cd_timer = cd                   # 冷却计时器
        self.last_use_time = -9999  # 上次使用时间
        self.cd_frame = 1
        self.lv = lv
        self.element = element
        self.damageMultipiler = []
        self.interruptible = interruptible  # 是否可打断
        self.caster = caster

    def to_action_data(self) -> ActionFrameData:
        """生成 ASM 动作数据"""
        data = ActionFrameData(
            name=self.name,
            total_frames=self.total_frames
        )
        # 挂载运行时对象以支持旧逻辑回调
        setattr(data, 'runtime_skill_obj', self)
        return data

    def start(self, caster):
        # 更新冷却计时器
        self.cd_timer = GetCurrentTime() - self.last_use_time - self.cd_frame
        if self.cd_timer - self.cd < 0:
            get_emulation_logger().log_error(f'{self.name}技能还在冷却中')
            return False  # 技能仍在冷却中
        self.caster = caster
        self.current_frame = 0
        self.last_use_time = GetCurrentTime()

        return True

    def update(self, target):
        self.current_frame += 1
        if self.current_frame >= self.total_frames:
            self.on_finish()
            return True
        self.on_frame_update(target)
        return False

    @abstractmethod
    def on_frame_update(self, target: Any):
        """ASM 每一帧的回调"""
        pass

    def on_execute_hit(self, target: Any, hit_index: int):
        """
        当 ASM 推进到伤害判定点时触发的回调。
        由具体的子类（如 GenericSkill）实现伤害发布。
        """
        pass

    def on_finish(self):
        self.current_frame = 0

    def on_interrupt(self): 
        ...

class EnergySkill(SkillBase):
    def __init__(self, name, total_frames, cd, lv, element, caster=None, interruptible=False):
        super().__init__(name, total_frames, cd, lv, element, caster, interruptible)

    def start(self, caster):
        if not super().start(caster):
            return False
        if self.caster.elemental_energy.is_energy_full():
            self.caster.elemental_energy.clear_energy()
            return True
        get_emulation_logger().log_error(f'{self.name} 能量不够')
        return False
    
    def on_finish(self):
        return super().on_finish()
    
    def on_interrupt(self):
        return super().on_interrupt()
