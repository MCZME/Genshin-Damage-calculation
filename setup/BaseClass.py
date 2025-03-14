from abc import ABC, abstractmethod
from character.character import Character
from setup.DamageCalculation import DamageType
from setup.Event import EventBus, EventType, GameEvent
from enum import Enum, auto

# 天赋效果基类
class TalentEffect:
    def apply(self, character: Character):
        pass

class ConstellationEffect:
    def apply(self, character: Character):
        pass

class SkillSate(Enum):
    OnField = auto()
    OffField = auto()

# 技能基类
class SkillBase(ABC):
    def __init__(self, name, total_frames, cd, lv, element, interruptible=False,state=SkillSate.OnField):
        self.name = name
        self.total_frames = total_frames    # 总帧数
        self.current_frame = 0              # 当前帧
        self.cd = cd                         # 冷却时间
        self.lv = lv
        self.element = element
        self.damageMultipiler = []
        self.interruptible = interruptible  # 是否可打断
        self.state = state
        self.caster = None

    def start(self, caster):
        self.caster = caster
        self.current_frame = 0
        return True

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

class NormalAttackSkill(SkillBase):
    def __init__(self,lv,cd=0):
        super().__init__(name="普通攻击",total_frames=0,lv=lv,cd=cd,element=('物理',0),interruptible=False)
        self.segment_frames = [0,0,0,0]
        self.damageMultipiler= []
        # 攻击阶段控制
        self.current_segment = 0               # 当前段数（0-based）
        self.segment_progress = 0              # 当前段进度帧数

    def start(self, caster,n):
        super().start(caster)
        self.current_segment = 0
        self.segment_progress = 0
        self.max_segments = min(n, 4)           # 实际攻击段数
        self.total_frames = sum(self.segment_frames[:self.max_segments])
        print(f"⚔️ 开始第{self.current_segment+1}段攻击")

    def update(self, target):
        self.current_frame += 1
        if self.on_frame_update(target):
            return True
        return False
    
    def on_frame_update(self,target): 
        # 更新段内进度
        self.segment_progress += 1
        
        # 检测段结束
        if self.segment_progress >= self.segment_frames[self.current_segment]:
            if self._on_segment_end(target):
                return True
        return False
    
    def on_finish(self): 
        pass 
        
    def _on_segment_end(self,target):
        """完成当前段攻击"""
        print(f"✅ 第{self.current_segment+1}段攻击完成")
        
        # 执行段攻击效果
        self._apply_segment_effect(target)
        
        # 进入下一段
        if self.current_segment < self.max_segments - 1:
            self.current_segment += 1
            self.segment_progress = 0
            print(f"⚔️ 开始第{self.current_segment+1}段攻击")
        else:
            self.on_finish()
            return True
        return False

    def _apply_segment_effect(self,target):
        
        # 发布伤害事件
        damage_event = GameEvent(
            EventType.BEFORE_DAMAGE,
            source=self.caster,
            target=target,
            damageType=DamageType.NORMAL,
            skill =self,
            damage = 0
        )
        EventBus.publish(damage_event)
        print(f"🎯 {self.caster.name} 对 {target.name} 造成了 {damage_event.data['damage']} 点伤害")

    def on_interrupt(self):
        print(f"💢 第{self.current_segment+1}段攻击被打断！")
        self.current_segment = self.max_segments  # 直接结束攻击链

    def getDamageMultipiler(self):
        return self.damageMultipiler[self.current_segment][self.lv-1]
    
    def setSegmentFrames(self,frames):
        self.segment_frames = frames
    
    def setDamageMultipiler(self,multipliers):
        self.damageMultipiler = multipliers