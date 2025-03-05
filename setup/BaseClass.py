from abc import ABC, abstractmethod
from character.character import Character

# 天赋效果基类
class TalentEffect:
    def apply(self, character: Character):
        pass

class ConstellationEffect:
    def apply(self, character: Character):
        pass

# 技能基类
class SkillBase(ABC):
    def __init__(self, name, total_frames, lv, element, interruptible=False):
        self.name = name
        self.total_frames = total_frames    # 总帧数
        self.current_frame = 0              # 当前帧
        self.lv = lv
        self.element = element
        self.damageMultipiler = []
        self.interruptible = interruptible  # 是否可打断
    
    def getDamageMultipiler(self):
        return self.damageMultipiler(self.lv)

    def start(self, caster):
        self.caster = caster
        self.current_frame = 0

    def update(self,target):
        self.current_frame += 1
        if self.current_frame >= self.total_frames:
            self.on_finish()
            return True
        self.on_frame_update(target)
        return False

    @abstractmethod
    def on_frame_update(self,target): pass
    @abstractmethod
    def on_finish(self): pass
    @abstractmethod
    def on_interrupt(self): pass
