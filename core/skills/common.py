from typing import Any, Dict, List, Union
from core.skills.base import SkillBase
from core.action.damage import Damage, DamageType
from core.action.action_data import ActionFrameData
from core.event import (
    ActionEvent,
    DamageEvent,
    EventType,
)
from core.tool import get_current_time


class NormalAttackSkill(SkillBase):
    def __init__(self, lv: int, cd: int = 0):
        super().__init__(
            name="普通攻击",
            total_frames=0,
            lv=lv,
            cd=cd,
            element=("物理", 0),
            interruptible=False,
        )
        self.segment_frames: List[Union[int, List[int]]] = []
        self.damage_multiplier: Dict[int, List[float]] = {}
        self.end_action_frame = 0

    def to_action_data(self, n: int = 1) -> ActionFrameData:
        hit_frames = []
        cumulative_frame = 0
        n_segments = min(n, len(self.segment_frames))
        for i in range(n_segments):
            seg_config = self.segment_frames[i]
            if isinstance(seg_config, list):
                for f in seg_config: hit_frames.append(cumulative_frame + f)
                cumulative_frame += max(seg_config)
            else:
                cumulative_frame += seg_config
                hit_frames.append(cumulative_frame)
        total_frames = cumulative_frame + self.end_action_frame
        data = ActionFrameData(name="normal_attack", total_frames=total_frames, hit_frames=hit_frames)
        data.origin_skill = self
        return data

    def on_frame_update(self): pass

    def on_execute_hit(self, target: Any, hit_index: int):
        segment = hit_index + 1
        m_list = self.damage_multiplier.get(segment)
        if not m_list: return
        multiplier = m_list[self.lv - 1]
        self.caster.event_engine.publish(ActionEvent(EventType.BEFORE_NORMAL_ATTACK, get_current_time(), self.caster, "normal_attack", segment=segment))
        damage = Damage(damage_multiplier=multiplier, element=self.element, damage_type=DamageType.NORMAL, name=f"普通攻击 第{segment}段")
        self.caster.event_engine.publish(DamageEvent(self.caster, target, damage, get_current_time()))
        self.caster.event_engine.publish(ActionEvent(EventType.AFTER_NORMAL_ATTACK, get_current_time(), self.caster, "normal_attack", segment=segment))


class ChargedAttackSkill(SkillBase):
    def __init__(self, lv: int, total_frames: int = 30, cd: int = 0):
        super().__init__(name="重击", total_frames=total_frames, cd=cd, lv=lv, element=("物理", 0), interruptible=True)
        self.hit_frame = total_frames

    def to_action_data(self) -> ActionFrameData:
        data = ActionFrameData(name="charged_attack", total_frames=self.total_frames, hit_frames=[self.hit_frame])
        data.origin_skill = self
        return data

    def on_frame_update(self): pass

    def on_execute_hit(self, target: Any, hit_index: int):
        self.caster.event_engine.publish(ActionEvent(EventType.BEFORE_CHARGED_ATTACK, get_current_time(), self.caster, "charged_attack"))
        multiplier = getattr(self, "damage_multiplier_list", [0.0]*15)[self.lv - 1]
        damage = Damage(multiplier, self.element, DamageType.CHARGED, "重击")
        self.caster.event_engine.publish(DamageEvent(self.caster, target, damage, get_current_time()))
        self.caster.event_engine.publish(ActionEvent(EventType.AFTER_CHARGED_ATTACK, get_current_time(), self.caster, "charged_attack"))


class PlungingAttackSkill(SkillBase):
    def __init__(self, lv: int, total_frames: int = 53, cd: int = 0):
        super().__init__(name="下落攻击", total_frames=total_frames, cd=cd, lv=lv, element=("物理", 0), interruptible=True)
        self.hit_frames = [int(total_frames * 0.3), 37]
        self.height_type = "低空"

    def to_action_data(self, is_high: bool = False) -> ActionFrameData:
        self.height_type = "高空" if is_high else "低空"
        data = ActionFrameData(name="plunging_attack", total_frames=self.total_frames, hit_frames=self.hit_frames)
        data.origin_skill = self
        return data

    def on_frame_update(self): pass

    def on_execute_hit(self, target: Any, hit_index: int):
        if hit_index == 0: self._apply_during_damage(target)
        elif hit_index == 1: self._apply_impact_damage(target)

    def _apply_during_damage(self, target: Any):
        self.caster.event_engine.publish(ActionEvent(EventType.BEFORE_PLUNGING_ATTACK, get_current_time(), self.caster, "plunging_attack", is_plunging_impact=False))
        multiplier = self.damage_multiplier.get("下坠期间伤害", [0.0]*15)[self.lv - 1]
        damage = Damage(multiplier, self.element, DamageType.PLUNGING, "下落攻击-下坠期间")
        self.caster.event_engine.publish(DamageEvent(self.caster, target, damage, get_current_time()))

    def _apply_impact_damage(self, target: Any):
        key = "高空坠地冲击伤害" if self.height_type == "高空" else "低空坠地冲击伤害"
        multiplier = self.damage_multiplier.get(key, [0.0]*15)[self.lv - 1]
        damage = Damage(multiplier, self.element, DamageType.PLUNGING, f"下落攻击-{self.height_type}")
        self.caster.event_engine.publish(DamageEvent(self.caster, target, damage, get_current_time()))
        self.caster.event_engine.publish(ActionEvent(EventType.AFTER_PLUNGING_ATTACK, get_current_time(), self.caster, "plunging_attack", is_plunging_impact=True))
