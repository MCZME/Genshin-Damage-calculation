from abc import ABC, abstractmethod
from setup.DamageCalculation import Damage, DamageType
from setup.Event import ChargedAttackEvent, DamageEvent, EventBus, EventType, GameEvent, NormalAttackEvent, PlungingAttackEvent
from setup.Logger import get_emulation_logger
from setup.Tool import GetCurrentTime

# 效果基类
class TalentEffect:
    def __init__(self,name):
        self.name = name
        
    def apply(self, character):
        self.character = character

    def update(self,target):
        pass

class ConstellationEffect:
    def __init__(self,name):
        self.name = name

    def apply(self, character):
        self.character = character

    def update(self,target):
        pass

class ElementalEnergy():
    def __init__(self, character,ee=('无',0)):
        self.character = character
        self.elemental_energy = ee
        self.current_energy = ee[1]

    def is_energy_full(self):
        return self.current_energy >= self.elemental_energy[1]
    
    def clear_energy(self):
        self.current_energy = 0

# 技能基类
class SkillBase(ABC):
    def __init__(self, name, total_frames, cd, lv, element, caster=None,interruptible=False):
        self.name = name
        self.total_frames = total_frames    # 总帧数
        self.current_frame = 0              # 当前帧
        self.cd = cd                         # 冷却时间
        self.cd_timer = 0                   # 冷却计时器
        self.last_use_time = 0  # 上次使用时间
        self.cd_frame = 0
        self.lv = lv
        self.element = element
        self.damageMultipiler = []
        self.interruptible = interruptible  # 是否可打断
        self.caster = caster

    def start(self, caster):
        if self.cd_timer > 0:
            get_emulation_logger().log_error(f'{self.name}技能还在冷却中')
            return False  # 技能仍在冷却中
        self.caster = caster
        self.current_frame = 0
        self.last_use_time = GetCurrentTime()

        return True

    def update(self,target):
        # 更新冷却计时器
        if self.cd_timer > 0:
            self.cd_timer -= GetCurrentTime() - self.last_use_time
        if self.current_frame == self.cd_frame:
            self.cd_timer = self.cd
 
        self.current_frame += 1
        if self.current_frame >= self.total_frames:
            self.on_finish()
            return True
        self.on_frame_update(target)
        return False

    @abstractmethod
    def on_frame_update(self,target): pass
    def on_finish(self): 
        self.current_frame = 0
    @abstractmethod
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

class DashSkill(SkillBase):
    def __init__(self, total_frames, v=0,caster=None, interruptible=False):
        super().__init__('冲刺', total_frames, 0, 0, ('无',0), caster, interruptible)
        self.v = v

    def start(self, caster):
        if not super().start(caster):
            return False
        get_emulation_logger().log_skill_use(f"⚡️ {self.caster.name} 开始冲刺")
        EventBus.publish(GameEvent(EventType.BEFORE_DASH, GetCurrentTime(), character=self.caster))
        return True

    def on_frame_update(self,target):
        self.caster.movement += self.v
    
    def on_finish(self):
        get_emulation_logger().log_skill_use(f"⚡️ {self.caster.name} 冲刺结束")
        EventBus.publish(GameEvent(EventType.AFTER_DASH, GetCurrentTime(), character=self.caster))
        return super().on_finish()
    
    def on_interrupt(self):
        return super().on_interrupt()

class JumpSkill(SkillBase):
    def __init__(self, total_frames, caster=None, interruptible=False):
        super().__init__('跳跃', total_frames, 0, 0, ('无',0), caster, interruptible)

    def start(self, caster):
        if not super().start(caster):
            return False

class NormalAttackSkill(SkillBase):
    def __init__(self,lv,cd=0):
        super().__init__(name="普通攻击",total_frames=0,lv=lv,cd=cd,element=('物理',0),interruptible=False)
        self.segment_frames = [0,0,0,0]
        self.damageMultipiler= {}
        # 攻击阶段控制
        self.current_segment = 0               # 当前段数（0-based）
        self.segment_progress = 0              # 当前段进度帧数

    def start(self, caster, n):
        if not super().start(caster):
            return False
        self.current_segment = 0
        self.segment_progress = 0
        self.max_segments = min(n,len(self.segment_frames))           # 实际攻击段数
        self.total_frames = sum(self.segment_frames[:self.max_segments])
        get_emulation_logger().log_skill_use(f"⚔️ 开始第{self.current_segment+1}段攻击")
        
        # 发布普通攻击事件（前段）
        normal_attack_event = NormalAttackEvent(self.caster, frame=GetCurrentTime(),segment=self.current_segment+1)
        EventBus.publish(normal_attack_event)
        return True

    def update(self, target):
        self.current_frame += 1
        if self.on_frame_update(target):
            self.on_finish()
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
        # 结束后重置攻击计时器
        super().on_finish()
        self.current_segment = 0
        
    def _on_segment_end(self,target):
        """完成当前段攻击"""
        # 执行段攻击效果
        self._apply_segment_effect(target)
        get_emulation_logger().log_skill_use(f"✅ 第{self.current_segment+1}段攻击完成")
        # 进入下一段
        if self.current_segment < self.max_segments - 1:
            self.current_segment += 1
            self.segment_progress = 0
            get_emulation_logger().log_skill_use(f"⚔️ 开始第{self.current_segment+1}段攻击")
            # 发布普通攻击事件（前段）
            normal_attack_event = NormalAttackEvent(self.caster, frame=GetCurrentTime(),segment=self.current_segment+1)
            EventBus.publish(normal_attack_event)
        else:
            self.on_finish()
            return True
        return False

    def _apply_segment_effect(self,target):
        # 发布伤害事件
        damage = Damage(self.damageMultipiler[self.current_segment+1][self.lv-1],self.element,DamageType.NORMAL,f'普通攻击 {self.current_segment+1}')
        damage_event = DamageEvent(self.caster,target,damage, frame=GetCurrentTime())
        EventBus.publish(damage_event)

        # 发布普通攻击事件（后段）
        normal_attack_event = NormalAttackEvent(self.caster, frame=GetCurrentTime(),before=False,damage=damage)
        EventBus.publish(normal_attack_event)

    def on_interrupt(self):
        get_emulation_logger().log_error(f"💢 第{self.current_segment+1}段攻击被打断！")
        self.current_segment = self.max_segments  # 直接结束攻击链
 
class ChargedAttackSkill(SkillBase):
    def __init__(self, lv, total_frames=30, cd=0):
        """
        重击技能基类
        :param charge_frames: 蓄力所需帧数
        """
        super().__init__(name="重击", 
                        total_frames=total_frames,  # 蓄力帧+攻击动作帧
                        cd=cd,
                        lv=lv,
                        element=('物理', 0),
                        interruptible=True)
        self.hit_frame = total_frames

    def start(self, caster):
        if not super().start(caster):
            return False
        get_emulation_logger().log_skill_use(f"💢 {caster.name} 开始重击")
        return True

    def on_frame_update(self, target): 
        # 攻击阶段
        if self.current_frame == self.hit_frame:
            self._apply_attack(target)
            return True
        return False

    def _apply_attack(self, target):
        """应用重击伤害"""
        event = ChargedAttackEvent(self.caster, frame=GetCurrentTime())
        EventBus.publish(event)

        damage = Damage(
            damageMultipiler=self.damageMultipiler[self.lv-1],
            element=self.element,
            damageType=DamageType.CHARGED,
            name=f'重击'
        )
        damage_event = DamageEvent(self.caster, target, damage, GetCurrentTime())
        EventBus.publish(damage_event)

        event = ChargedAttackEvent(self.caster, frame=GetCurrentTime(), before=False)
        EventBus.publish(event)

    def on_finish(self):
        super().on_finish()
        get_emulation_logger().log_skill_use("🎯 重击动作完成")

    def on_interrupt(self):
        super().on_interrupt()

class PlungingAttackSkill(SkillBase):
    def __init__(self, lv, total_frames=30, cd=0):
        super().__init__(name="下落攻击", 
                        total_frames=total_frames, 
                        cd=cd,
                        lv=lv,
                        element=('物理', 0),
                        interruptible=True)
        self.hit_frame = total_frames
        self.damageMultipiler = {
            '下坠期间伤害': [],
            '低空坠地冲击伤害': [],
            '高空坠地冲击伤害': []
        }
        self.height_type = '低空'  # 默认低空
        
    def start(self, caster, is_high=False):
        """启动下落攻击并设置高度类型"""
        if not super().start(caster):
            return False
        self.height_type = '高空' if is_high else '低空'
        get_emulation_logger().log_skill_use(f"🦅 {caster.name} 发动{self.height_type}下落攻击")
        event = PlungingAttackEvent(self.caster, frame=GetCurrentTime(),is_plunging_impact=False)
        EventBus.publish(event)
        return True

    def on_frame_update(self, target):
        # 在总帧数的30%时触发下坠期间伤害
        if self.current_frame == int(self.total_frames * 0.3):
            self._apply_during_damage(target)
            event = PlungingAttackEvent(self.caster, frame=GetCurrentTime(), before=False,is_plunging_impact=False)
            EventBus.publish(event)
            event = PlungingAttackEvent(self.caster, frame=GetCurrentTime())
            EventBus.publish(event)
        
        # 在最后一帧触发坠地冲击伤害
        if self.current_frame == self.hit_frame:
            self._apply_impact_damage(target)
            event = PlungingAttackEvent(self.caster, frame=GetCurrentTime(), before=False)
            EventBus.publish(event)
            return True
        return False

    def _apply_during_damage(self, target):
        """下坠期间持续伤害"""
        # 确保等级不超过数据范围（1-15级）
        clamped_lv = min(max(self.lv, 1), 15) - 1
        damage = Damage(
            self.damageMultipiler['下坠期间伤害'][clamped_lv] ,  
            self.element,
            DamageType.PLUNGING,
            '下落攻击-下坠期间'
        )
        EventBus.publish(DamageEvent(self.caster, target, damage, GetCurrentTime()))

    def _apply_impact_damage(self, target):
        """坠地冲击伤害"""
        clamped_lv = self.lv - 1
        damage_type_key = '高空坠地冲击伤害' if self.height_type == '高空' else '低空坠地冲击伤害'
        
        damage = Damage(
            self.damageMultipiler[damage_type_key][clamped_lv],
            self.element,
            DamageType.PLUNGING,
            f'下落攻击-{self.height_type}'
        )
        EventBus.publish(DamageEvent(self.caster, target, damage, GetCurrentTime()))

    def on_finish(self):
        super().on_finish()
        EventBus.publish(PlungingAttackEvent(self.caster, frame=GetCurrentTime(), before=False))
        get_emulation_logger().log_skill_use(f"💥 {self.caster.name} 下落攻击完成")

    def on_interrupt(self):
        get_emulation_logger().log_error("💢 下落攻击被打断")
        super().on_interrupt()
