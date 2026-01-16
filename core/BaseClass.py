from abc import ABC, abstractmethod
from character.character import CharacterState
from core.calculation.DamageCalculation import Damage, DamageType
from core.Event import ChargedAttackEvent, DamageEvent, EventBus, EventType, GameEvent, NormalAttackEvent, PlungingAttackEvent
from core.Logger import get_emulation_logger
from core.Tool import GetCurrentTime
import core.Constants as Constants
from typing import List, Dict, Tuple, Optional, Union, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from character.character import Character


# 效果基类
class TalentEffect:
    def __init__(self, name: str) -> None:
        self.name: str = name
        self.character: Optional['Character'] = None

    def apply(self, character: 'Character') -> None:
        self.character = character

    def update(self, target: Any) -> None:
        pass

class ConstellationEffect:
    def __init__(self, name: str) -> None:
        self.name: str = name
        self.character: Optional['Character'] = None

    def apply(self, character: 'Character') -> None:
        self.character = character

    def update(self, target: Any) -> None:
        pass

class ElementalEnergy:
    def __init__(self, character: 'Character', ee: Tuple[str, float] = (Constants.ELEMENT_NONE, 0)) -> None:
        self.character: 'Character' = character
        self.elemental_energy: Tuple[str, float] = ee
        self.current_energy: float = ee[1]

    def is_energy_full(self) -> bool:
        return self.current_energy >= self.elemental_energy[1]
    
    def clear_energy(self) -> None:
        self.current_energy = 0

# 技能基类
class SkillBase(ABC):
    def __init__(self, name: str, total_frames: int, cd: float, lv: int, element: Tuple[str, int], 
                 caster: Optional['Character'] = None, interruptible: bool = False) -> None:
        self.name: str = name
        self.total_frames: int = total_frames    # 总帧数
        self.current_frame: int = 0              # 当前帧
        self.cd: float = cd                         # 冷却时间
        self.cd_timer: float = cd                   # 冷却计时器
        self.last_use_time: float = Constants.NEVER_USED_TIME  # 上次使用时间
        self.cd_frame: int = 1
        self.lv: int = lv
        self.element: Tuple[str, int] = element
        self.damageMultipiler: Union[Dict[int, List[float]], List[float]] = [] # TODO: Fix type definition and potential typo "Multipiler"
        self.interruptible: bool = interruptible  # 是否可打断
        self.caster: Optional['Character'] = caster

    def start(self, caster: 'Character') -> bool:
        # 更新冷却计时器
        self.cd_timer = GetCurrentTime() - self.last_use_time - self.cd_frame
        if self.cd_timer - self.cd < 0:
            get_emulation_logger().log_error(f'{self.name}技能还在冷却中')
            return False  # 技能仍在冷却中
        self.caster = caster
        self.current_frame = 0
        self.last_use_time = GetCurrentTime()

        return True

    def update(self, target: Any) -> bool:
 
        self.current_frame += 1
        if self.current_frame >= self.total_frames:
            self.on_finish()
            return True
        self.on_frame_update(target)
        return False

    @abstractmethod
    def on_frame_update(self, target: Any) -> None: pass
    
    def on_finish(self) -> None: 
        self.current_frame = 0

    def on_interrupt(self) -> None: 
        ...

class EnergySkill(SkillBase):
    def __init__(self, name: str, total_frames: int, cd: float, lv: int, element: Tuple[str, int], 
                 caster: Optional['Character'] = None, interruptible: bool = False) -> None:
        super().__init__(name, total_frames, cd, lv, element, caster, interruptible)

    def start(self, caster: 'Character') -> bool:
        if not super().start(caster):
            return False
        if not self.caster:
             return False
        if self.caster.elemental_energy.is_energy_full():
            self.caster.elemental_energy.clear_energy()
            return True
        get_emulation_logger().log_error(f'{self.name} 能量不够')
        return False
    
    def on_finish(self) -> None:
        super().on_finish()
    
    def on_interrupt(self) -> None:
        super().on_interrupt()

class DashSkill(SkillBase):
    def __init__(self, total_frames: int, v: float = 0, caster: Optional['Character'] = None, interruptible: bool = False) -> None:
        super().__init__(Constants.SKILL_NAME_DASH, total_frames, 0, 0, (Constants.ELEMENT_NONE,0), caster, interruptible)
        self.v: float = v

    def start(self, caster: 'Character') -> bool:
        if not super().start(caster):
            return False
        if self.caster:
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
    def __init__(self, total_frames: int, v: float, caster: Optional['Character'] = None, interruptible: bool = False) -> None:
        super().__init__(Constants.SKILL_NAME_JUMP, total_frames, 0, 0, (Constants.ELEMENT_NONE,0), caster, interruptible)
        self.v: float = v

    def start(self, caster: 'Character') -> bool:
        if not super().start(caster):
            return False
        
        if self.caster:
            get_emulation_logger().log_skill_use(f"⚡️ {self.caster.name} 开始跳跃")
            EventBus.publish(GameEvent(EventType.BEFORE_JUMP, GetCurrentTime(), character=self.caster))
        return True
    
    def on_frame_update(self, target):
        # 跳跃过程持续增加高度
        self.caster.height += self.v
        self.caster.movement += self.v
        
    def on_finish(self):
        super().on_finish()
        # 跳跃结束进入下落状态
        from character.character import CharacterState
        self.caster._append_state(CharacterState.FALL)
        get_emulation_logger().log_skill_use(f"⚡️ {self.caster.name} 跳跃结束")
        EventBus.publish(GameEvent(EventType.AFTER_JUMP, GetCurrentTime(), character=self.caster))

    def on_interrupt(self) -> None:
        return super().on_interrupt()

class NormalAttackSkill(SkillBase):
    def __init__(self, lv: int, cd: float = 0) -> None:
        super().__init__(name=Constants.SKILL_NAME_NORMAL,total_frames=0,lv=lv,cd=cd,element=(Constants.ELEMENT_PHYSICAL,0),interruptible=False)
        self.segment_frames: List[Union[int, List[int]]] = [0,0,0,0]  # 支持数字或列表格式，如[10, [10,11], 30]
        self.damageMultipiler: Dict[int, Union[List[float], List[List[float]]]] = {}  # 格式如{1:[倍率], 2:[倍率1,倍率2], 3:[倍率]}
        # 攻击阶段控制
        self.current_segment: int = 0               # 当前段数（0-based）
        self.segment_progress: int = 0              # 当前段进度帧数
        self.end_action_frame: int = 0 

    def start(self, caster: 'Character', n: int) -> bool:
        if not super().start(caster):
            return False
        self.current_segment = 0
        self.segment_progress = 0
        self.max_segments: int = min(n, len(self.segment_frames))           # 实际攻击段数
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
        if self.caster:
            normal_attack_event = NormalAttackEvent(self.caster, frame=GetCurrentTime(),segment=self.current_segment+1)
            EventBus.publish(normal_attack_event)
        return True

    def update(self, target: Any) -> bool:
        self.current_frame += 1
        if self.current_segment > self.max_segments-1 and self.current_frame >= self.total_frames:
            self.on_finish()
            return True
        if self.current_frame <= self.total_frames - self.end_action_frame:
            self.on_frame_update(target)
        return False
    
    def on_frame_update(self, target: Any) -> None: 
        # 更新段内进度
        self.segment_progress += 1
        # 检测段结束
        segment_frames: int
        if isinstance(self.segment_frames[self.current_segment], list):
             # Type ignore needed becausemypy might not infer the list element type correctly in mixed list
            segment_frames = max(self.segment_frames[self.current_segment]) # type: ignore
        else:
            segment_frames = self.segment_frames[self.current_segment] # type: ignore
        if self.segment_progress >= segment_frames:
            self._on_segment_end(target)
    
    def on_finish(self) -> None: 
        # 结束后重置攻击计时器
        super().on_finish()
        self.current_segment = 0
        
    def _on_segment_end(self, target: Any) -> None:
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
                
        if self.caster:
            get_emulation_logger().log_skill_use(f"✅ 第{segment}段攻击完成")
            # 进入下一段
            if self.current_segment < self.max_segments - 1:
                self.segment_progress = 0
                get_emulation_logger().log_skill_use(f"⚔️ 开始第{self.current_segment+1}段攻击")
                # 发布普通攻击事件（前段）
                normal_attack_event = NormalAttackEvent(self.caster, frame=GetCurrentTime(),segment=self.current_segment+1)
                EventBus.publish(normal_attack_event)
            self.current_segment += 1

    def _apply_segment_effect(self, target: Any, hit_index: int = 0) -> None:
        segment = self.current_segment + 1
        # 获取伤害倍率（支持多段配置）
        multiplier_data = self.damageMultipiler[segment]
        multiplier: float
        if isinstance(multiplier_data, list) and len(multiplier_data) > 0 and isinstance(multiplier_data[0], list):
             # It's a list of lists (multi-hit segment)
             # multiplier_data is List[List[float]]
            multiplier = multiplier_data[hit_index][self.lv-1] # type: ignore
        else:
             # multiplier_data is List[float]
            multiplier = multiplier_data[self.lv-1] # type: ignore
            
        if self.caster:
            # 发布伤害事件
            damage = Damage(multiplier, self.element, DamageType.NORMAL, f'普通攻击 {segment}-{hit_index+1}')
            damage_event = DamageEvent(self.caster,target,damage, frame=GetCurrentTime())
            EventBus.publish(damage_event)

        # 发布普通攻击事件（后段）
        normal_attack_event = NormalAttackEvent(self.caster, frame=GetCurrentTime(),before=False,
                                                damage=damage,segment=self.current_segment+1)
        EventBus.publish(normal_attack_event)

    def on_interrupt(self):
        get_emulation_logger().log_error(f"💢 第{self.current_segment+1}段攻击被打断！")
        self.current_segment = self.max_segments  # 直接结束攻击链
 
class ChargedAttackSkill(SkillBase):
    def __init__(self, lv: int, total_frames: int = 30, cd: float = 0) -> None:
        """
        重击技能基类
        :param charge_frames: 蓄力所需帧数
        """
        super().__init__(name=Constants.SKILL_NAME_CHARGED, 
                        total_frames=total_frames,  # 蓄力帧+攻击动作帧
                        cd=cd,
                        lv=lv,
                        element=(Constants.ELEMENT_PHYSICAL, 0),
                        interruptible=True)
        self.hit_frame: int = total_frames

    def start(self, caster: 'Character') -> bool:
        if not super().start(caster):
            return False
        if self.caster:
            get_emulation_logger().log_skill_use(f"💢 {caster.name} 开始重击")
        return True

    def on_frame_update(self, target: Any) -> None: 
        # 攻击阶段
        if self.current_frame == self.hit_frame:
            self._apply_attack(target)
    
    def _apply_attack(self, target: Any) -> None:
        """应用重击伤害"""
        if self.caster:
            event_before = ChargedAttackEvent(self.caster, frame=GetCurrentTime())
            EventBus.publish(event_before)

            damage = Damage(
                damageMultipiler=self.damageMultipiler[self.lv-1], # type: ignore
                element=self.element,
                damageType=DamageType.CHARGED,
                name=Constants.SKILL_NAME_CHARGED
            )
            damage_event = DamageEvent(self.caster, target, damage, GetCurrentTime())
            EventBus.publish(damage_event)

            event_after = ChargedAttackEvent(self.caster, frame=GetCurrentTime(), before=False)
            EventBus.publish(event_after)

    def on_finish(self):
        super().on_finish()
        get_emulation_logger().log_skill_use("🎯 重击动作完成")

    def on_interrupt(self):
        super().on_interrupt()

class PolearmChargedAttackSkill(ChargedAttackSkill):
    def __init__(self, lv: int, total_frames: int = 30, cd: float = 0) -> None:
        """
        长柄武器重击技能 - 两段攻击
        :param lv: 技能等级
        :param total_frames: 总帧数
        :param cd: 冷却时间
        """
        super().__init__(lv, total_frames, cd)
        self.normal_hit_frame: int = 0  # 第一段攻击帧
        self.charged_hit_frame: int = total_frames  # 第二段攻击帧

    def start(self, caster: 'Character') -> bool:
        if not super().start(caster):
            return False
        
        if self.caster:
            normal_attack_event = NormalAttackEvent(self.caster, frame=GetCurrentTime(), segment=1, before=False)
            EventBus.publish(normal_attack_event)

        return True

    def on_frame_update(self, target: Any) -> None:
        # 第一段普通攻击
        if self.current_frame == self.normal_hit_frame:
            self._apply_normal_attack(target)
            if self.caster:
                event = ChargedAttackEvent(self.caster, frame=GetCurrentTime())
                EventBus.publish(event)
        
        # 第二段重击攻击
        if self.current_frame == self.charged_hit_frame:
            self._apply_charged_attack(target)

    def _apply_normal_attack(self, target: Any) -> None:
        """应用第一段普通攻击"""
        if self.caster:
            damage = Damage(
                damageMultipiler=self.damageMultipiler[0][self.lv-1], # type: ignore
                element=self.element,
                damageType=DamageType.NORMAL,
                name='长柄武器重击-第一段'
            )
            damage_event = DamageEvent(self.caster, target, damage, GetCurrentTime())
            EventBus.publish(damage_event)

            # 发布普通攻击事件
            normal_attack_event = NormalAttackEvent(self.caster, frame=GetCurrentTime(), segment=1, before=False)
            EventBus.publish(normal_attack_event)

    def _apply_charged_attack(self, target: Any) -> None:
        """应用第二段重击攻击"""
        if self.caster:
            damage = Damage(
                damageMultipiler=self.damageMultipiler[1][self.lv-1], # type: ignore
                element=self.element,
                damageType=DamageType.CHARGED,
                name=Constants.SKILL_NAME_CHARGED
            )
            damage_event = DamageEvent(self.caster, target, damage, GetCurrentTime())
            EventBus.publish(damage_event)

            event = ChargedAttackEvent(self.caster, frame=GetCurrentTime(), before=False)
            EventBus.publish(event)

class PlungingAttackSkill(SkillBase):
    def __init__(self, lv: int, total_frames: int = 53, cd: float = 0) -> None:
        super().__init__(name=Constants.SKILL_NAME_PLUNGING, 
                        total_frames=total_frames, 
                        cd=cd,
                        lv=lv,
                        element=(Constants.ELEMENT_PHYSICAL, 0),
                        interruptible=True)
        self.hit_frame: int = 37
        self.damageMultiplier: Dict[str, List[float]] = { # type: ignore
            Constants.PLUNGING_DMG_DURING: [],
            Constants.PLUNGING_DMG_IMPACT_LOW: [],
            Constants.PLUNGING_DMG_IMPACT_HIGH: []
        }
        self.height_type: str = Constants.PLUNGING_LOW
        
    def start(self, caster: 'Character', is_high: bool = False) -> bool:
        """启动下落攻击并设置高度类型"""
        if not super().start(caster):
            return False
        # is_high = caster.height > 80
        self.height_type = Constants.PLUNGING_HIGH if is_high else Constants.PLUNGING_LOW
        if self.caster:
            get_emulation_logger().log_skill_use(f"🦅 {caster.name} 发动{self.height_type}下落攻击")
            event = PlungingAttackEvent(self.caster, frame=GetCurrentTime(),is_plunging_impact=False)
            EventBus.publish(event)
        return True

    def on_frame_update(self, target: Any) -> None:
        # 在总帧数的30%时触发下坠期间伤害
        if self.current_frame == int(self.total_frames * 0.3):
            self._apply_during_damage(target)
            if self.caster:
                event_during_after = PlungingAttackEvent(self.caster, frame=GetCurrentTime(), before=False,is_plunging_impact=False)
                EventBus.publish(event_during_after)
                event_impact = PlungingAttackEvent(self.caster, frame=GetCurrentTime())
                EventBus.publish(event_impact)
        
        # 在最后一帧触发坠地冲击伤害
        if self.current_frame == self.hit_frame:
            self._apply_impact_damage(target)
            if self.caster:
                event = PlungingAttackEvent(self.caster, frame=GetCurrentTime(), before=False)
                EventBus.publish(event)

    def _apply_during_damage(self, target: Any) -> None:
        """下坠期间持续伤害"""
        # 确保等级不超过数据范围（1-15级）
        clamped_lv = min(max(self.lv, 1), 15) - 1
        # damageMultiplier here is Dict[str, List[float]]
        damage_val = self.damageMultiplier[Constants.PLUNGING_DMG_DURING][clamped_lv] # type: ignore
        damage = Damage(
            damage_val ,  
            self.element,
            DamageType.PLUNGING,
            '下落攻击-下坠期间'
        )
        if self.caster:
            EventBus.publish(DamageEvent(self.caster, target, damage, GetCurrentTime()))

    def _apply_impact_damage(self, target: Any) -> None:
        """坠地冲击伤害"""
        clamped_lv = self.lv - 1
        damage_type_key = Constants.PLUNGING_DMG_IMPACT_HIGH if self.height_type == Constants.PLUNGING_HIGH else Constants.PLUNGING_DMG_IMPACT_LOW
        
        damage_val = self.damageMultiplier[damage_type_key][clamped_lv] # type: ignore
        damage = Damage(
            damage_val,
            self.element,
            DamageType.PLUNGING,
            f'下落攻击-{self.height_type}'
        )
        if self.caster:
           EventBus.publish(DamageEvent(self.caster, target, damage, GetCurrentTime()))

    def on_finish(self) -> None:
        super().on_finish()
        if self.caster:
            EventBus.publish(PlungingAttackEvent(self.caster, frame=GetCurrentTime(), before=False))
            get_emulation_logger().log_skill_use(f"💥 {self.caster.name} 下落攻击完成")
            self.caster.height = 0
            from character.character import CharacterState
            if CharacterState.FALL in self.caster.state:
                self.caster.state.remove(CharacterState.FALL)
                EventBus.publish(GameEvent(EventType.AFTER_FALLING, GetCurrentTime(),character = self.caster))
                self.caster.height = 0

    def on_interrupt(self) -> None:
        get_emulation_logger().log_error("💢 下落攻击被打断")
        super().on_interrupt()

class Infusion:
    def __init__(self, attach_sequence: List[int] = [1, 0, 0], interval: float = 2.5*60, max_attach: int = 8) -> None:
        self.attach_sequence: List[int] = attach_sequence
        self.sequence_pos: int = 0
        self.last_attach_time: float = 0
        self.interval: float = interval
        self.max_attach: int = max_attach
        self.infusion_count: int = 0
    
    def apply_infusion(self) -> int:
        current_time = GetCurrentTime()
        should_attach = False
        
        if self.sequence_pos < len(self.attach_sequence):
            should_attach = self.attach_sequence[self.sequence_pos] == 1
            self.sequence_pos += 1
        else:
            self.sequence_pos = 0
            should_attach = self.attach_sequence[self.sequence_pos] == 1
            self.sequence_pos += 1
        
        self.infusion_count += 1
        
        if current_time - self.last_attach_time >= self.interval:
            should_attach = True
            self.infusion_count = 0
            self.last_attach_time = current_time
        
        if self.infusion_count > self.max_attach:
            should_attach = False
        
        return 1 if should_attach else 0
