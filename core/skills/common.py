from typing import Any, Dict, List, Union
from core.skills.base import SkillBase
from core.action.damage import Damage, DamageType
from core.action.action_data import ActionFrameData
from core.event import (
    ChargedAttackEvent,
    DamageEvent,
    EventBus,
    EventType,
    GameEvent,
    NormalAttackEvent,
    PlungingAttackEvent,
)
from core.logger import get_emulation_logger
from core.tool import GetCurrentTime


class NormalAttackSkill(SkillBase):
    """
    通用普通攻击技能类。
    支持多段攻击配置，并适配 ASM 流程。
    """

    def __init__(self, lv: int, cd: int = 0):
        super().__init__(
            name="普通攻击",
            total_frames=0,
            lv=lv,
            cd=cd,
            element=("物理", 0),
            interruptible=False,
        )
        # 每段攻击的耗时 [seg1_frames, seg2_frames, ...]
        self.segment_frames: List[Union[int, List[int]]] = []
        # 每段攻击的伤害倍率 {1: [lv1..15], 2: [lv1..15], ...}
        self.damage_multiplier: Dict[int, List[float]] = {}
        self.end_action_frame = 0
        
        # 运行时状态 (ASM 模式下主要用于获取当前段位)
        self._current_n_segments = 0

    def to_action_data(self, n: int = 1) -> ActionFrameData:
        """
        根据段数 n 生成 ASM 动作数据。
        将增量段帧数转换为累计命中点。
        """
        self._current_n_segments = min(n, len(self.segment_frames))
        hit_frames = []
        cumulative_frame = 0
        
        for i in range(self._current_n_segments):
            seg_config = self.segment_frames[i]
            if isinstance(seg_config, list):
                # 如果一段内有多个命中点
                for f in seg_config:
                    hit_frames.append(cumulative_frame + f)
                cumulative_frame += max(seg_config)
            else:
                cumulative_frame += seg_config
                hit_frames.append(cumulative_frame)
        
        total_frames = cumulative_frame + self.end_action_frame
        
        data = ActionFrameData(
            name=f"normal_attack_{n}",
            total_frames=total_frames,
            hit_frames=hit_frames
        )
        setattr(data, "runtime_skill_obj", self)
        return data

    def on_frame_update(self, target: Any):
        # 逐帧逻辑已由 ASM 接管
        pass

    def on_execute_hit(self, target: Any, hit_index: int):
        """
        ASM 命中点触发。
        hit_index 对应第几次命中（从 0 开始）。
        """
        # 注意：对于多段攻击，hit_index 需要映射回段位和段内攻击序
        # 这里简化处理：假设 1 段 1 命中
        segment = hit_index + 1
        
        # 获取倍率
        m_list = self.damage_multiplier.get(segment)
        if not m_list: return
        multiplier = m_list[self.lv - 1]

        # 触发前置事件
        self.caster.event_engine.publish(
            NormalAttackEvent(self.caster, GetCurrentTime(), segment=segment)
        )

        # 发布伤害
        damage = Damage(
            damage_multiplier=multiplier,
            element=self.element,
            damage_type=DamageType.NORMAL,
            name=f"普通攻击 第{segment}段"
        )
        self.caster.event_engine.publish(
            DamageEvent(self.caster, target, damage, GetCurrentTime())
        )

        # 触发后置事件
        self.caster.event_engine.publish(
            NormalAttackEvent(self.caster, GetCurrentTime(), before=False, damage=damage, segment=segment)
        )
        get_emulation_logger().log_skill_use(f"✅ 第 {segment} 段攻击完成")


class ChargedAttackSkill(SkillBase):
    """
    通用重击技能类。
    """

    def __init__(self, lv: int, total_frames: int = 30, cd: int = 0):
        super().__init__(
            name="重击",
            total_frames=total_frames,
            cd=cd,
            lv=lv,
            element=("物理", 0),
            interruptible=True,
        )
        self.hit_frame = total_frames # 默认在最后一帧触发

    def to_action_data(self) -> ActionFrameData:
        data = ActionFrameData(
            name="charged_attack",
            total_frames=self.total_frames,
            hit_frames=[self.hit_frame]
        )
        setattr(data, "runtime_skill_obj", self)
        return data

    def on_frame_update(self, target: Any): pass

    def on_execute_hit(self, target: Any, hit_index: int):
        # 发布重击前置事件
        self.caster.event_engine.publish(ChargedAttackEvent(self.caster, GetCurrentTime()))

        multiplier = self.damageMultipiler[self.lv - 1] # 保持旧命名兼容
        damage = Damage(
            damage_multiplier=multiplier,
            element=self.element,
            damage_type=DamageType.CHARGED,
            name="重击"
        )
        
        self.caster.event_engine.publish(
            DamageEvent(self.caster, target, damage, GetCurrentTime())
        )

        # 发布重击后置事件
        self.caster.event_engine.publish(
            ChargedAttackEvent(self.caster, GetCurrentTime(), before=False)
        )
        get_emulation_logger().log_skill_use("🎯 重击动作命中")


class PlungingAttackSkill(SkillBase):
    """
    通用下落攻击技能类。
    """

    def __init__(self, lv: int, total_frames: int = 53, cd: int = 0):
        super().__init__(
            name="下落攻击",
            total_frames=total_frames,
            cd=cd,
            lv=lv,
            element=("物理", 0),
            interruptible=True,
        )
        # 命中帧：下坠期间(30%) 和 坠地冲击(37帧)
        self.hit_frames = [int(total_frames * 0.3), 37]
        self.height_type = "低空"

    def to_action_data(self, is_high: bool = False) -> ActionFrameData:
        self.height_type = "高空" if is_high else "低空"
        data = ActionFrameData(
            name="plunging_attack",
            total_frames=self.total_frames,
            hit_frames=self.hit_frames
        )
        setattr(data, "runtime_skill_obj", self)
        return data

    def on_frame_update(self, target: Any): pass

    def on_execute_hit(self, target: Any, hit_index: int):
        if hit_index == 0:
            self._apply_during_damage(target)
        elif hit_index == 1:
            self._apply_impact_damage(target)

    def _apply_during_damage(self, target: Any):
        clamped_lv = min(max(self.lv, 1), 15) - 1
        damage = Damage(
            damage_multiplier=self.damageMultipiler["下坠期间伤害"][clamped_lv],
            element=self.element,
            damage_type=DamageType.PLUNGING,
            name="下落攻击-下坠期间"
        )
        self.caster.event_engine.publish(DamageEvent(self.caster, target, damage, GetCurrentTime()))

    def _apply_impact_damage(self, target: Any):
        clamped_lv = self.lv - 1
        key = "高空坠地冲击伤害" if self.height_type == "高空" else "低空坠地冲击伤害"
        damage = Damage(
            damage_multiplier=self.damageMultipiler[key][clamped_lv],
            element=self.element,
            damage_type=DamageType.PLUNGING,
            name=f"下落攻击-{self.height_type}"
        )
        self.caster.event_engine.publish(DamageEvent(self.caster, target, damage, GetCurrentTime()))
        get_emulation_logger().log_skill_use(f"💥 {self.caster.name} 下落攻击完成")