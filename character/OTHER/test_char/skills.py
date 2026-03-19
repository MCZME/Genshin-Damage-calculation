from typing import Any, Dict, Optional, List
from core.skills.base import SkillBase, EnergySkill
from core.skills.common import NormalAttackSkill, ChargedAttackSkill, PlungingAttackSkill
from core.action.action_data import ActionFrameData
from core.systems.contract.attack import AttackConfig, HitboxConfig, AOEShape, StrikeType
from core.systems.contract.damage import Damage
from core.event import GameEvent, EventType
from core.tool import get_current_time
from core.mechanics.aura import Element
from character.OTHER.test_char.data import (
    ACTION_FRAME_DATA, 
    ATTACK_DATA, 
    NORMAL_ATTACK_DATA,
    ELEMENTAL_SKILL_DATA,
    ELEMENTAL_BURST_DATA
)
from character.OTHER.test_char.effects import TestAuditSuiteEffect

def _build_attack_config(name: str) -> AttackConfig:
    """从测试角色数据构建攻击契约。"""
    p = ATTACK_DATA.get(name, {})
    shape_map = {
        "球": AOEShape.SPHERE,
        "圆柱": AOEShape.CYLINDER,
        "长方体": AOEShape.BOX,
        "单体": AOEShape.SINGLE,
    }
    strike_map = {
        "默认": StrikeType.DEFAULT,
        "突刺": StrikeType.THRUST,
        "切割": StrikeType.SLASH,
        "钝击": StrikeType.BLUNT,
        "穿刺": StrikeType.PIERCE,
    }
    return AttackConfig(
        attack_tag=p.get("attack_tag", name),
        icd_tag=p.get("icd_tag", "Default"),
        icd_group=p.get("icd_group", "Default"),
        strike_type=strike_map.get(p.get("strike_type"), StrikeType.DEFAULT),
        is_ranged=p.get("is_ranged", False),
        hitbox=HitboxConfig(
            shape=shape_map.get(p.get("shape"), AOEShape.SINGLE),
            radius=p.get("radius", 0.0),
            width=p.get("width", 0.0),
            height=p.get("height", 0.0),
            length=p.get("length", 0.0),
            offset=p.get("offset", (0.0, 0.0, 0.0)),
        ),
    )

class TestCharNormalAttack(NormalAttackSkill):
    def __init__(self, lv: int, caster: Any = None):
        super().__init__(lv, caster)
        self.action_frame_data = ACTION_FRAME_DATA
        self.attack_data = ATTACK_DATA
        # 使用 NORMAL_ATTACK_DATA 中的标准格式 [属性名, [Lv1..Lv15]]
        self.multiplier_data = {
            "一段伤害": NORMAL_ATTACK_DATA["一段伤害"],
            "二段伤害": NORMAL_ATTACK_DATA["二段伤害"],
            "三段伤害": NORMAL_ATTACK_DATA["三段伤害"],
        }
        self.label_map = {
            "普通攻击1": "一段伤害",
            "普通攻击2": "二段伤害",
            "普通攻击3": "三段伤害",
        }

class TestCharChargedAttack(ChargedAttackSkill):
    def __init__(self, lv: int, caster: Any = None):
        super().__init__(lv, caster)
        self.action_frame_data = ACTION_FRAME_DATA
        self.attack_data = ATTACK_DATA
        self.multiplier_data = {
            "重击伤害": NORMAL_ATTACK_DATA["重击伤害"]
        }

class TestCharPlungingAttack(PlungingAttackSkill):
    def __init__(self, lv: int, caster: Any = None):
        super().__init__(lv, caster)
        self.action_frame_data = ACTION_FRAME_DATA
        self.attack_data = ATTACK_DATA
        self.multiplier_data = {
            "下落期间伤害": NORMAL_ATTACK_DATA["下落期间伤害"],
            "低空坠地冲击伤害": NORMAL_ATTACK_DATA["低空坠地冲击伤害"],
            "高空坠地冲击伤害": NORMAL_ATTACK_DATA["高空坠地冲击伤害"],
        }

class TestCharElementalSkill(SkillBase):
    def to_action_data(self, intent: Optional[Dict[str, Any]] = None) -> ActionFrameData:
        test_mode = intent.get("test_mode", "基础计算") if intent else "基础计算"
        f = ACTION_FRAME_DATA["元素战技"]
        attack_key = "元素战技" if test_mode != "多属性点积" else "混合缩放测试"
        
        return ActionFrameData(
            name=f"元素战技({test_mode})",
            action_type="elemental_skill",
            total_frames=f["total_frames"],
            hit_frames=f["hit_frames"],
            interrupt_frames=f["interrupt_frames"],
            attack_config=AttackConfig(
                attack_tag=ATTACK_DATA[attack_key]["attack_tag"],
                icd_tag=ATTACK_DATA[attack_key].get("icd_tag", "Default"),
                icd_group=ATTACK_DATA[attack_key].get("icd_group", "Default"),
                strike_type=StrikeType.DEFAULT,
                is_ranged=ATTACK_DATA[attack_key].get("is_ranged", False),
                hitbox=HitboxConfig(
                    shape=AOEShape.SPHERE, 
                    radius=ATTACK_DATA[attack_key].get("radius", 5.0)
                )
            ) if attack_key in ATTACK_DATA else _build_attack_config(attack_key),
            origin_skill=self,
            tags=[test_mode] # 使用 tags 传递模式，避免修改核心 ActionFrameData
        )

    def on_execute_hit(self, target: Any, hit_index: int) -> None:
        instance = self.caster.action_manager.current_action
        # 从 tags 中恢复测试模式
        test_mode = instance.data.tags[0] if instance.data.tags else "基础计算"
        
        mult_data = (ELEMENTAL_SKILL_DATA["技能伤害"][1][self.lv-1],)
        scaling = ("攻击力",)
        
        if test_mode == "多属性点积":
            mult_data = (
                ELEMENTAL_SKILL_DATA["混合缩放倍率"][1][self.lv-1],
                ELEMENTAL_SKILL_DATA["混合缩放精通"][1][self.lv-1]
            )
            scaling = ("攻击力", "元素精通")
        elif test_mode == "攻防倍率测试":
            mult_data = (
                ELEMENTAL_SKILL_DATA["攻防缩放攻击"][1][self.lv-1],
                ELEMENTAL_SKILL_DATA["攻防缩放防御"][1][self.lv-1]
            )
            scaling = ("攻击力", "防御力")

        attack_key = "元素战技" if test_mode != "多属性点积" else "混合缩放测试"
            
        # 模式触发测试效果
        if test_mode == "全乘区Buff":
            exists = any(e.name == "审计验证套件" for e in self.caster.active_effects)
            if not exists:
                eff = TestAuditSuiteEffect(self.caster, mode=test_mode)
                eff.apply()
            
        dmg_obj = Damage(
            element=(Element.ANEMO, 1.0),
            damage_multiplier=mult_data,
            scaling_stat=scaling,
            config=instance.data.attack_config,
            name=f"战技伤害({test_mode})"
        )
        if attack_key in ATTACK_DATA:
            dmg_obj.set_element(Element.ANEMO, ATTACK_DATA[attack_key].get("element_u", 1.0))
        
        self.caster.event_engine.publish(
            GameEvent(
                EventType.BEFORE_DAMAGE,
                get_current_time(),
                source=self.caster,
                data={"character": self.caster, "damage": dmg_obj},
            )
        )

        from character.OTHER.test_char.effects import TestDebuffEffect
        # 将减益施加给目标 (Target)
        exists = any(e.name == "极致穿透减益" for e in dmg_obj.target.active_effects)
        if not exists:
            eff = TestDebuffEffect(dmg_obj.target)
            eff.apply()


class TestCharElementalBurst(EnergySkill):
    def to_action_data(self, intent: Optional[Dict[str, Any]] = None) -> ActionFrameData:
        test_mode = intent.get("test_mode", "基础计算") if intent else "基础计算"
        f = ACTION_FRAME_DATA["元素爆发"]
        attack_key = "元素爆发" if test_mode != "剧变反应测试" else "剧变反应测试"
        
        return ActionFrameData(
            name="元素爆发" if test_mode != "剧变反应测试" else "剧变反应测试",
            action_type="elemental_burst",
            total_frames=f["total_frames"],
            hit_frames=f["hit_frames"],
            interrupt_frames=f["interrupt_frames"],
            attack_config=AttackConfig(
                attack_tag=ATTACK_DATA[attack_key]["attack_tag"],
                icd_tag=ATTACK_DATA[attack_key].get("icd_tag", "Default"),
                icd_group=ATTACK_DATA[attack_key].get("icd_group", "Default"),
                strike_type=StrikeType.DEFAULT,
                is_ranged=ATTACK_DATA[attack_key].get("is_ranged", False),
                hitbox=HitboxConfig(
                    shape=AOEShape.SPHERE, 
                    radius=ATTACK_DATA[attack_key].get("radius", 10.0)
                )
            ) if attack_key in ATTACK_DATA else _build_attack_config(attack_key),
            origin_skill=self,
            tags=[test_mode]
        )

    def on_execute_hit(self, target: Any, hit_index: int) -> None:
        instance = self.caster.action_manager.current_action
        test_mode = instance.data.tags[0] if instance.data.tags else "基础计算"
        
        if hit_index == 0:
            # 增幅反应测试模式下，第一段改为水，为后续火伤打蒸发做铺垫
            el = Element.HYDRO if test_mode == "增幅反应测试" else Element.ANEMO
            dmg_obj = Damage(
                element=(el, 1.0),
                damage_multiplier=(ELEMENTAL_BURST_DATA["技能伤害"][1][self.lv-1],),
                scaling_stat=("攻击力",),
                config=instance.data.attack_config,
                name="爆发伤害(水)" if test_mode == "增幅反应测试" else "爆发伤害(风)"
            )
        elif hit_index == 1:
            dmg_obj = Damage(
                element=(Element.PYRO, 1.0),
                damage_multiplier=(ELEMENTAL_BURST_DATA["火伤害"][1][self.lv-1],),
                scaling_stat=("攻击力",),
                config=instance.data.attack_config,
                name="爆发伤害(火)"
            )
        elif hit_index == 2:
            dmg_obj = Damage(
                element=(Element.ELECTRO, 1.0),
                damage_multiplier=(ELEMENTAL_BURST_DATA["雷伤害"][1][self.lv-1],),
                scaling_stat=("攻击力",),
                config=instance.data.attack_config,
                name="爆发伤害(雷)"
            )
        else:
            return

        attack_key = "元素爆发" if test_mode != "剧变反应测试" else "剧变反应测试"
        if attack_key in ATTACK_DATA and hit_index == 0:
             dmg_obj.set_element(dmg_obj.element[0], ATTACK_DATA[attack_key].get("element_u", 1.0))
        elif hit_index > 0:
             # 为火/雷伤害设置默认元素附着强度
             dmg_obj.set_element(dmg_obj.element[0], 1.0)
        
        self.caster.event_engine.publish(
            GameEvent(
                EventType.BEFORE_DAMAGE,
                get_current_time(),
                source=self.caster,
                data={"character": self.caster, "damage": dmg_obj},
            )
        )
