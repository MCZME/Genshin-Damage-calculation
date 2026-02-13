from typing import Any, Dict, List, Optional

from core.skills.base import SkillBase, EnergySkill
from core.skills.common import NormalAttackSkill, ChargedAttackSkill, PlungingAttackSkill
from core.action.action_data import ActionFrameData, AttackConfig, HitboxConfig, AOEShape
from core.action.damage import Damage
from core.event import GameEvent, EventType
from core.tool import get_current_time
from character.FONTAINE.furina.data import (
    ACTION_FRAME_DATA, ATTACK_DATA, MECHANISM_CONFIG,
    NORMAL_ATTACK_DATA, ELEMENTAL_SKILL_DATA, ELEMENTAL_BURST_DATA
)
from character.FONTAINE.furina.entities import SalonMember, SingerOfManyWaters
from character.FONTAINE.furina.effects import FurinaFanfareEffect


class FurinaNormalAttack(NormalAttackSkill):
    """普通攻击：独舞之邀。"""

    def __init__(self, lv: int, caster: Any) -> None:
        super().__init__(lv, caster)
        self.action_frame_data = ACTION_FRAME_DATA
        self.attack_data = ATTACK_DATA
        self.multiplier_data = NORMAL_ATTACK_DATA
        self.label_map = {
            "NORMAL_1": "普通攻击1",
            "NORMAL_2": "普通攻击2",
            "NORMAL_3": "普通攻击3",
            "NORMAL_4": "普通攻击4"
        }


class FurinaChargedAttack(ChargedAttackSkill):
    """重击：切换始基力。"""

    def __init__(self, lv: int, caster: Any) -> None:
        super().__init__(lv, caster)
        self.action_frame_data = ACTION_FRAME_DATA
        self.attack_data = ATTACK_DATA
        self.multiplier_data = NORMAL_ATTACK_DATA

    def on_execute_hit(self, target: Any, hit_index: int) -> None:
        """命中后执行始基力切换。"""
        super().on_execute_hit(target, hit_index)
        
        # 始基力切换逻辑
        instance = self.caster.action_manager.current_action
        if instance and instance.elapsed_frames >= MECHANISM_CONFIG["ARKHE_SWITCH_FRAME"]:
            self.caster.arkhe_mode = "芒" if self.caster.arkhe_mode == "荒" else "荒"
            self.caster.arkhe = f"{self.caster.arkhe_mode}性"
            # 同步战技召唤物
            if "skill" in self.caster.skills:
                self.caster.skills["skill"].sync_summons()


class FurinaPlungingAttack(PlungingAttackSkill):
    """下落攻击。"""

    def __init__(self, lv: int, caster: Any) -> None:
        super().__init__(lv, caster)
        self.action_frame_data = ACTION_FRAME_DATA
        self.attack_data = ATTACK_DATA
        self.multiplier_data = NORMAL_ATTACK_DATA


class FurinaElementalSkill(SkillBase):
    """元素战技：孤心沙龙。"""

    def __init__(self, lv: int, caster: Any) -> None:
        super().__init__(lv, caster)
        self.active_summons: List[Any] = []
        self.remaining_frames = 0

    def to_action_data(self, intent: Optional[Dict[str, Any]] = None) -> ActionFrameData:
        mode = self.caster.arkhe_mode
        frame_key = "SKILL_OUSIA" if mode == "荒" else "SKILL_PNEUMA"
        f = ACTION_FRAME_DATA[frame_key]
        
        mult = 0.0
        attack_cfg = None
        if mode == "荒":
            mult = ELEMENTAL_SKILL_DATA["荒性泡沫伤害"][1][self.lv - 1]
            p = ATTACK_DATA["元素战技"]
            attack_cfg = AttackConfig(
                attack_tag=p["attack_tag"],
                icd_tag=p["icd_tag"],
                icd_group=p["icd_group"],
                hitbox=HitboxConfig(shape=AOEShape.SPHERE, radius=p["radius"])
            )

        return ActionFrameData(
            name="元素战技",
            action_type="elemental_skill",
            total_frames=f["total_frames"],
            hit_frames=f["hit_frames"],
            interrupt_frames=f["interrupt_frames"],
            damage_multiplier=mult,
            scaling_stat="生命值",
            attack_config=attack_cfg,
            origin_skill=self
        )

    def on_execute_hit(self, target: Any, hit_index: int) -> None:
        if self.caster.action_manager.current_action.data.attack_config:
            dmg_obj = Damage(
                element=("水", 1.0),
                damage_multiplier=self.caster.action_manager.current_action.data.damage_multiplier,
                scaling_stat="生命值",
                config=self.caster.action_manager.current_action.data.attack_config,
                name="荒性泡沫伤害"
            )
            dmg_obj.set_element("水", ATTACK_DATA["元素战技"]["element_u"])
            self.caster.event_engine.publish(GameEvent(EventType.BEFORE_DAMAGE, get_current_time(), 
                                                      source=self.caster, data={"character": self.caster, "damage": dmg_obj}))

        self.remaining_frames = 1800
        self.sync_summons()

    def sync_summons(self) -> None:
        for s in self.active_summons: s.finish()
        self.active_summons.clear()

        if self.remaining_frames <= 0: return

        mode = self.caster.arkhe_mode
        if mode == "荒":
            for name in ["乌瑟勋爵伤害", "海薇玛夫人伤害", "谢贝蕾妲小姐伤害"]:
                m = SalonMember(name.replace("伤害", ""), self.caster, self.caster.ctx, name)
                m.life_frame = self.remaining_frames
                self.caster.ctx.space.register(m)
                self.active_summons.append(m)
        else:
            s = SingerOfManyWaters(self.caster, self.caster.ctx)
            s.life_frame = self.remaining_frames
            self.caster.ctx.space.register(s)
            self.active_summons.append(s)

    def on_frame_update(self) -> None:
        if self.remaining_frames > 0:
            self.remaining_frames -= 1


class FurinaElementalBurst(EnergySkill):
    """元素爆发：万众狂欢。"""

    def to_action_data(self, intent: Optional[Dict[str, Any]] = None) -> ActionFrameData:
        f = ACTION_FRAME_DATA["ELEMENTAL_BURST"]
        p = ATTACK_DATA["元素爆发"]
        mult = ELEMENTAL_BURST_DATA["技能伤害"][1][self.lv - 1]

        return ActionFrameData(
            name="元素爆发",
            action_type="elemental_burst",
            total_frames=f["total_frames"],
            hit_frames=f["hit_frames"],
            interrupt_frames=f["interrupt_frames"],
            damage_multiplier=mult,
            scaling_stat="生命值",
            attack_config=AttackConfig(
                attack_tag=p["attack_tag"],
                icd_tag=p["icd_tag"],
                icd_group=p["icd_group"],
                hitbox=HitboxConfig(shape=AOEShape.SPHERE, radius=p["radius"])
            ),
            origin_skill=self
        )

    def on_execute_hit(self, target: Any, hit_index: int) -> None:
        dmg_obj = Damage(
            element=("水", 1.0),
            damage_multiplier=ELEMENTAL_BURST_DATA["技能伤害"][1][self.lv - 1],
            scaling_stat="生命值",
            config=self.caster.action_manager.current_action.data.attack_config,
            name="万众狂欢伤害"
        )
        dmg_obj.set_element("水", ATTACK_DATA["元素爆发"]["element_u"])
        self.caster.event_engine.publish(GameEvent(EventType.BEFORE_DAMAGE, get_current_time(), 
                                                  source=self.caster, data={"character": self.caster, "damage": dmg_obj}))

        window = MECHANISM_CONFIG["BURST_FANFARE_WINDOW"]
        duration = window[1] - window[0]
        eff = FurinaFanfareEffect(self.caster, duration=duration)
        eff.apply()
