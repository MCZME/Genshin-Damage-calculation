from abc import ABC
from typing import Any, Tuple
from core.logger import get_emulation_logger
from core.tool import GetCurrentTime
from core.action.action_data import ActionFrameData

# 技能基类
class SkillBase(ABC):
    def __init__(self, name: str, total_frames: int, cd: int, lv: int, element: Tuple[str, int], 
                 caster: Any = None, interruptible: bool = False):
        self.name = name
        self.total_frames = total_frames
        self.current_frame = 0
        self.cd = cd
        self.last_use_time = -9999
        self.lv = lv
        self.element = element
        self.interruptible = interruptible
        self.caster = caster

    def to_action_data(self) -> ActionFrameData:
        data = ActionFrameData(name=self.name, total_frames=self.total_frames)
        setattr(data, 'runtime_skill_obj', self)
        return data

    def start(self, caster):
        self.caster = caster
        # 冷却判定逻辑 (此处可扩展)
        return True

    def on_frame_update(self):
        """
        统一每帧驱动接口。
        不再接收 target 参数，改为从 self.caster.ctx 感知战场。
        """
        pass

    def on_execute_hit(self, target: Any, hit_index: int):
        """
        伤害判定点触发。
        target 参数暂时保留以兼容当前的广播分发逻辑。
        """
        pass

    def on_finish(self):
        self.current_frame = 0

class EnergySkill(SkillBase):
    def start(self, caster):
        if not super().start(caster): return False
        if hasattr(self.caster, "elemental_energy"):
            if self.caster.elemental_energy.is_energy_full():
                self.caster.elemental_energy.clear_energy()
                return True
        return False