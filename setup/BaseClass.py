from abc import ABC, abstractmethod
from enum import Enum, auto
from character.character import Character

# 角色状态枚举
class CharacterState(Enum):
    IDLE = auto()        # 空闲状态
    CASTING = auto()      # 施法中
    SKILL_ACTIVE = auto() # 技能持续效果中
    BURST = auto()        # 大招释放中

# 天赋效果基类
class TalentEffect:
    def apply(self, character: Character):
        pass

class ConstellationEffect:
    def apply(self, character: Character):
        pass

# 技能基类
class SkillBase(ABC):
    def __init__(self, name, total_frames, interruptible=False, stamina_cost=0):
        self.name = name
        self.total_frames = total_frames    # 总帧数
        self.current_frame = 0              # 当前帧
        self.interruptible = interruptible  # 是否可打断
        self.stamina_cost = stamina_cost    # 体力消耗

    def start(self, caster):
        self.caster = caster
        self.current_frame = 0

    def update(self):
        self.current_frame += 1
        if self.current_frame >= self.total_frames:
            self.on_finish()
            return True
        self.on_frame_update()
        return False

    @abstractmethod
    def on_frame_update(self): pass
    @abstractmethod
    def on_finish(self): pass
    @abstractmethod
    def on_interrupt(self): pass
