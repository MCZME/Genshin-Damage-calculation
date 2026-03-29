from typing import Any, Dict, Optional
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
    """测试角色元素战技 - 可选择雷/岩/草元素，CD为0。"""

    # 元素类型映射
    ELEMENT_MAP = {
        "雷": Element.ELECTRO,
        "岩": Element.GEO,
        "草": Element.DENDRO,
    }

    def __init__(self, lv: int, caster: Any = None):
        super().__init__(lv, caster)
        self.cd_frames = 0  # CD 为 0

    def to_action_data(self, intent: Optional[Dict[str, Any]] = None) -> ActionFrameData:
        element_type = intent.get("element_type", "雷") if intent else "雷"
        f = ACTION_FRAME_DATA["元素战技"]
        attack_key = "元素战技"

        return ActionFrameData(
            name=f"元素战技({element_type})",
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
            ),
            origin_skill=self,
            tags=[element_type]
        )

    def on_execute_hit(self, target: Any, hit_index: int) -> None:
        instance = self.caster.action_manager.current_action
        element_type = instance.data.tags[0] if instance.data.tags else "雷"

        element = self.ELEMENT_MAP.get(element_type, Element.ELECTRO)

        dmg_obj = Damage(
            element=(element, 1.0),
            damage_multiplier=(ELEMENTAL_SKILL_DATA["技能伤害"][1][self.lv - 1],),
            scaling_stat=("攻击力",),
            config=instance.data.attack_config,
            name=f"战技伤害({element_type})"
        )
        dmg_obj.set_element(element, 1.0)

        self.caster.event_engine.publish(
            GameEvent(
                EventType.BEFORE_DAMAGE,
                get_current_time(),
                source=self.caster,
                data={"character": self.caster, "damage": dmg_obj},
            )
        )


class TestCharElementalBurst(EnergySkill):
    """测试角色元素爆发 - 可选择雷/岩/草元素，CD为0，无能量消耗。"""

    # 元素类型映射
    ELEMENT_MAP = {
        "雷": Element.ELECTRO,
        "岩": Element.GEO,
        "草": Element.DENDRO,
    }

    def __init__(self, lv: int, caster: Any = None):
        super().__init__(lv, caster)
        self.cd_frames = 0  # CD 为 0
        self.energy_cost = 0  # 无能量消耗

    def to_action_data(self, intent: Optional[Dict[str, Any]] = None) -> ActionFrameData:
        element_type = intent.get("element_type", "雷") if intent else "雷"
        f = ACTION_FRAME_DATA["元素爆发"]
        attack_key = "元素爆发"

        return ActionFrameData(
            name=f"元素爆发({element_type})",
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
            ),
            origin_skill=self,
            tags=[element_type]
        )

    def on_execute_hit(self, target: Any, hit_index: int) -> None:
        instance = self.caster.action_manager.current_action
        element_type = instance.data.tags[0] if instance.data.tags else "雷"

        element = self.ELEMENT_MAP.get(element_type, Element.ELECTRO)

        dmg_obj = Damage(
            element=(element, 1.0),
            damage_multiplier=(ELEMENTAL_BURST_DATA["技能伤害"][1][self.lv - 1],),
            scaling_stat=("攻击力",),
            config=instance.data.attack_config,
            name=f"爆发伤害({element_type})"
        )
        dmg_obj.set_element(element, 1.0)

        self.caster.event_engine.publish(
            GameEvent(
                EventType.BEFORE_DAMAGE,
                get_current_time(),
                source=self.caster,
                data={"character": self.caster, "damage": dmg_obj},
            )
        )
