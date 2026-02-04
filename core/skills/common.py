from core.skills.base import SkillBase
from core.action.damage import Damage, DamageType
from core.event import (ChargedAttackEvent, DamageEvent, EventBus, 
                        EventType, GameEvent, NormalAttackEvent, PlungingAttackEvent)
from core.logger import get_emulation_logger
from core.tool import GetCurrentTime

class NormalAttackSkill(SkillBase):
    def __init__(self, lv, cd=0):
        super().__init__(name="普通攻击", total_frames=0, lv=lv, cd=cd, element=('物理', 0), interruptible=False)
        self.segment_frames = [0, 0, 0, 0]  # 支持数字或列表格式，如[10, [10,11], 30]
        self.damageMultipiler = {}  # 格式如{1:[倍率], 2:[倍率1,倍率2], 3:[倍率]}
        # 攻击阶段控制
        self.current_segment = 0               # 当前段数（0-based）
        self.segment_progress = 0              # 当前段进度帧数
        self.end_action_frame = 0 

    def start(self, caster, n):
        if not super().start(caster):
            return False
        self.current_segment = 0
        self.segment_progress = 0
        self.max_segments = min(n, len(self.segment_frames))           # 实际攻击段数
        # 计算总帧数（支持多帧配置）
        total = 0
        for seg in self.segment_frames[:self.max_segments]:
            if isinstance(seg, list):
                total += max(seg)  # 取多帧配置中的最大值
            else:
                total += seg
        self.total_frames = total + self.end_action_frame
        get_emulation_logger().log_skill_use(f"⚔️ 开始第{self.current_segment+1}段攻击")
        
        # 发布普通攻击事件（前段）
        normal_attack_event = NormalAttackEvent(self.caster, frame=GetCurrentTime(), segment=self.current_segment+1)
        EventBus.publish(normal_attack_event)
        return True

    def update(self, target):
        self.current_frame += 1
        if self.current_segment > self.max_segments-1 and self.current_frame >= self.total_frames:
            self.on_finish()
            return True
        if self.current_frame <= self.total_frames - self.end_action_frame:
            self.on_frame_update(target)
        return False
    
    def on_frame_update(self, target): 
        # 更新段内进度
        self.segment_progress += 1
        # 检测段结束
        if isinstance(self.segment_frames[self.current_segment], list):
            segment_frames = max(self.segment_frames[self.current_segment])
        else:
            segment_frames = self.segment_frames[self.current_segment]
        if self.segment_progress >= segment_frames:
            self._on_segment_end(target)
    
    def on_finish(self): 
        # 结束后重置攻击计时器
        super().on_finish()
        self.current_segment = 0
        
    def _on_segment_end(self, target):
        """完成当前段攻击"""
        segment = self.current_segment + 1
        frame_config = self.segment_frames[self.current_segment]
        
        if isinstance(frame_config, list):
            # 多帧配置，按帧触发多次伤害
            for i, frame in enumerate(frame_config):
                if self.segment_progress >= frame:
                    self._apply_segment_effect(target, hit_index=i)
        else:
            # 单帧配置，在段末触发一次伤害
            if self.segment_progress >= frame_config:
                self._apply_segment_effect(target)
                
        get_emulation_logger().log_skill_use(f"✅ 第{segment}段攻击完成")
        # 进入下一段
        if self.current_segment < self.max_segments - 1:
            self.segment_progress = 0
            get_emulation_logger().log_skill_use(f"⚔️ 开始第{self.current_segment+1}段攻击")
            # 发布普通攻击事件（前段）
            normal_attack_event = NormalAttackEvent(self.caster, frame=GetCurrentTime(), segment=self.current_segment+1)
            EventBus.publish(normal_attack_event)
        self.current_segment += 1

    def _apply_segment_effect(self, target, hit_index=0):
        segment = self.current_segment + 1
        # 获取伤害倍率（支持多段配置）
        multiplier = self.damageMultipiler[segment]
        if isinstance(multiplier[0], list):
            multiplier = multiplier[hit_index][self.lv-1]
        else:
            multiplier = multiplier[self.lv-1]
            
        # 发布伤害事件
        damage = Damage(multiplier, self.element, DamageType.NORMAL, f'普通攻击 {segment}-{hit_index+1}')
        damage_event = DamageEvent(self.caster, target, damage, frame=GetCurrentTime())
        EventBus.publish(damage_event)

        # 发布普通攻击事件（后段）
        normal_attack_event = NormalAttackEvent(self.caster, frame=GetCurrentTime(), before=False,
                                                damage=damage, segment=self.current_segment+1)
        EventBus.publish(normal_attack_event)

    def on_interrupt(self):
        get_emulation_logger().log_error(f"💢 第{self.current_segment+1}段攻击被打断！")
        self.current_segment = self.max_segments  # 直接结束攻击链
 
class ChargedAttackSkill(SkillBase):
    def __init__(self, lv, total_frames=30, cd=0):
        """
        重击技能基类
        """
        super().__init__(name="重击", 
                        total_frames=total_frames, 
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
    
    def _apply_attack(self, target):
        """应用重击伤害"""
        event = ChargedAttackEvent(self.caster, frame=GetCurrentTime())
        EventBus.publish(event)

        damage = Damage(
            damage_multiplier=self.damageMultipiler[self.lv-1],
            element=self.element,
            damage_type=DamageType.CHARGED,
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

class PolearmChargedAttackSkill(ChargedAttackSkill):
    def __init__(self, lv, total_frames=30, cd=0):
        """
        长柄武器重击技能 - 两段攻击
        """
        super().__init__(lv, total_frames, cd)
        self.normal_hit_frame = 0  # 第一段攻击帧
        self.charged_hit_frame = total_frames  # 第二段攻击帧

    def start(self, caster):
        if not super().start(caster):
            return False
        
        normal_attack_event = NormalAttackEvent(self.caster, frame=GetCurrentTime(), segment=1, before=False)
        EventBus.publish(normal_attack_event)

        return True

    def on_frame_update(self, target):
        # 第一段普通攻击
        if self.current_frame == self.normal_hit_frame:
            self._apply_normal_attack(target)
            event = ChargedAttackEvent(self.caster, frame=GetCurrentTime())
            EventBus.publish(event)
        
        # 第二段重击攻击
        if self.current_frame == self.charged_hit_frame:
            self._apply_charged_attack(target)

    def _apply_normal_attack(self, target):
        """应用第一段普通攻击"""
        damage = Damage(
            damage_multiplier=self.damageMultipiler[0][self.lv-1],
            element=self.element,
            damage_type=DamageType.NORMAL,
            name='长柄武器重击-第一段'
        )
        damage_event = DamageEvent(self.caster, target, damage, GetCurrentTime())
        EventBus.publish(damage_event)

        # 发布普通攻击事件
        normal_attack_event = NormalAttackEvent(self.caster, frame=GetCurrentTime(), segment=1, before=False)
        EventBus.publish(normal_attack_event)

    def _apply_charged_attack(self, target):
        """应用第二段重击攻击"""

        damage = Damage(
            damage_multiplier=self.damageMultipiler[1][self.lv-1],
            element=self.element,
            damage_type=DamageType.CHARGED,
            name=f'重击'
        )
        damage_event = DamageEvent(self.caster, target, damage, GetCurrentTime())
        EventBus.publish(damage_event)

        event = ChargedAttackEvent(self.caster, frame=GetCurrentTime(), before=False)
        EventBus.publish(event)

class PlungingAttackSkill(SkillBase):
    def __init__(self, lv, total_frames=53, cd=0):
        super().__init__(name="下落攻击", 
                        total_frames=total_frames, 
                        cd=cd,
                        lv=lv,
                        element=('物理', 0),
                        interruptible=True)
        self.hit_frame = 37
        self.damageMultipiler = {
            '下坠期间伤害': [],
            '低空坠地冲击伤害': [],
            '高空坠地冲击伤害': []
        }
        self.height_type = '低空'
        
    def start(self, caster, is_high=False):
        """启动下落攻击并设置高度类型"""
        if not super().start(caster):
            return False
        # is_high = caster.height > 80
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
        self.caster.height = 0
        # 暂时注释掉状态修改，避免循环引用
        # from character.character import CharacterState
        # if CharacterState.FALL in self.caster.state:
        #     self.caster.state.remove(CharacterState.FALL)
        EventBus.publish(GameEvent(EventType.AFTER_FALLING, GetCurrentTime(),character = self.caster))
        self.caster.height = 0

    def on_interrupt(self):
        get_emulation_logger().log_error("💢 下落攻击被打断")
        super().on_interrupt()
