from typing import Any, Dict, List, Optional
from core.skills.base import SkillBase
from core.action.action_data import ActionFrameData
from core.systems.contract.attack import (
    AttackConfig,
    HitboxConfig,
    AOEShape,
    StrikeType,
)
from core.systems.contract.damage import Damage
from core.event import GameEvent, EventType
from core.tool import get_current_time


class NormalAttackSkill(SkillBase):
    """
    通用普攻组件 (V2.4 连招支持版)。

    特点：
    1. 无状态设计：通过 ActionManager 追踪连击索引。
    2. 全自动映射：自动关联 data.py 中的帧数与物理配置。
    3. 支持多段命中。
    """

    def __init__(self, lv: int, caster: Any = None):
        super().__init__(lv, caster)
        # 这些属性由具体角色的子类初始化或动态注入
        self.action_frame_data: Dict[str, Any] = {}
        self.attack_data: Dict[str, Any] = {}
        self.multiplier_data: Dict[str, List[float]] = {}
        self.label_map: Dict[str, str] = {}  # "NORMAL_1" -> "一段伤害"

    def to_action_data(
        self, intent: Optional[Dict[str, Any]] = None
    ) -> ActionFrameData:
        """产出当前连击段位的动作数据。"""
        # 段位完全由角色的动作管理器 (ASM) 自动控制
        idx = 1
        if hasattr(self.caster, "action_manager"):
            idx = self.caster.action_manager.combo_counter

        # 核心规范：直接使用原生中文作为索引 Key
        action_key = f"普通攻击{idx}"

        # 2. 提取配置
        f = self.action_frame_data.get(
            action_key,
            {"total_frames": 60, "hit_frames": [15], "interrupt_frames": {"any": 60}},
        )
        name = action_key  # 动作名称与索引 Key 保持一致
        p = self.attack_data.get(name, {})

        # 原生映射逻辑
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
        }

        # 3. 构造物理数据
        return ActionFrameData(
            name=name,
            action_type="normal_attack",
            combo_index=idx,
            total_frames=f["total_frames"],
            hit_frames=f["hit_frames"],
            interrupt_frames=f["interrupt_frames"],
            attack_config=AttackConfig(
                attack_tag=p.get("attack_tag", name),
                icd_tag=p.get("icd_tag", "Default"),
                icd_group=p.get("icd_group", "NormalAttack"),
                strike_type=strike_map.get(p.get("strike_type"), StrikeType.DEFAULT),
                is_ranged=p.get("is_ranged", False),
                hitbox=HitboxConfig(
                    shape=shape_map.get(p.get("shape"), AOEShape.SINGLE),
                    radius=p.get("radius", 0),
                    width=p.get("width", 0),
                    height=p.get("height", 0),
                    length=p.get("length", 0),
                    offset=p.get("offset", (0, 0, 0)),
                ),
            ),
            origin_skill=self,
        )

    def on_execute_hit(self, target: Any, hit_index: int) -> None:
        """根据当前运行动作的 combo_index 分发伤害。"""
        instance = self.caster.action_manager.current_action
        if not instance:
            return

        # 核心修正：instance.data.name 是 "普通攻击1"，我们需要通过 label_map 找到倍率 Key "一段伤害"
        action_name = instance.data.name
        damage_label = self.label_map.get(action_name, action_name)

        # 获取倍率
        m_data = self.multiplier_data.get(damage_label)
        if not m_data:
            return
        multiplier = m_data[1][self.lv - 1]

        # 核心变动：从附魔管理器获取当前生效元素
        current_element = self.caster.get_attack_element()

        # 构造并发布伤害请求 (空间广播模式)
        dmg_obj = Damage(
            element=(current_element, 1.0),
            damage_multiplier=multiplier,
            scaling_stat="攻击力",
            config=instance.data.attack_config,
        )
        dmg_obj.name = damage_label

        # 从 data 中获取原生 element_u
        p = self.attack_data.get(damage_label, {"element_u": 1.0})
        # 修正：必须传入计算出的 current_element 而不是原始的 self.caster.element
        dmg_obj.set_element(current_element, p.get("element_u", 1.0))

        self.caster.event_engine.publish(
            GameEvent(
                EventType.BEFORE_DAMAGE,
                get_current_time(),
                source=self.caster,
                data={"character": self.caster, "damage": dmg_obj},
            )
        )


class ChargedAttackSkill(SkillBase):
    """通用重击基类。"""

    def __init__(self, lv: int, caster: Any = None):
        super().__init__(lv, caster)
        self.action_frame_data: Dict[str, Any] = {}
        self.attack_data: Dict[str, Any] = {}
        self.multiplier_data: Dict[str, List[float]] = {}

    def to_action_data(
        self, intent: Optional[Dict[str, Any]] = None
    ) -> ActionFrameData:
        # 统一命名规范：使用 '重击'
        f = self.action_frame_data.get(
            "重击",
            {"total_frames": 60, "hit_frames": [30], "interrupt_frames": {"any": 60}},
        )
        name = "重击"
        p = self.attack_data.get(name, {})

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
        }

        return ActionFrameData(
            name=name,
            action_type="charged_attack",
            total_frames=f["total_frames"],
            hit_frames=f["hit_frames"],
            interrupt_frames=f["interrupt_frames"],
            attack_config=AttackConfig(
                attack_tag=p.get("attack_tag", name),
                icd_tag=p.get("icd_tag", "Default"),
                icd_group=p.get("icd_group", "ChargedAttack"),
                strike_type=strike_map.get(p.get("strike_type"), StrikeType.DEFAULT),
                hitbox=HitboxConfig(
                    shape=shape_map.get(p.get("shape"), AOEShape.SINGLE),
                    radius=p.get("radius", 0),
                    offset=p.get("offset", (0, 0, 0)),
                ),
            ),
            origin_skill=self,
        )

    def on_execute_hit(self, target: Any, hit_index: int) -> None:
        instance = self.caster.action_manager.current_action
        if not instance:
            return

        m_data = self.multiplier_data.get("重击伤害")
        if not m_data:
            return
        multiplier = m_data[1][self.lv - 1]

        # 核心变动：支持附魔
        current_element = self.caster.get_attack_element()

        dmg_obj = Damage(
            element=(current_element, 1.0),
            damage_multiplier=multiplier,
            scaling_stat="攻击力",
            config=instance.data.attack_config,
        )
        dmg_obj.name = "重击伤害"

        p = self.attack_data.get("重击", {"element_u": 1.0})
        # 修正：使用当前计算出的元素
        dmg_obj.set_element(current_element, p.get("element_u", 1.0))

        self.caster.event_engine.publish(
            GameEvent(
                EventType.BEFORE_DAMAGE,
                get_current_time(),
                source=self.caster,
                data={"character": self.caster, "damage": dmg_obj},
            )
        )


class PlungingAttackSkill(SkillBase):
    """
    通用下落攻击组件 (V2.4 物理高度驱动版)。
    """

    def __init__(self, lv: int, caster: Any = None):
        super().__init__(lv, caster)
        self.action_frame_data: Dict[str, Any] = {}
        self.attack_data: Dict[str, Any] = {}
        self.multiplier_data: Dict[str, List[float]] = {}

        self.fall_speed = 0.6
        self.path_damage_interval = 20
        self.path_timer = 0

    def can_cast(self) -> bool:
        """准入：必须在空中。"""
        if not self.caster:
            return False
        return self.caster.pos[2] > 0.1

    def to_action_data(
        self, intent: Optional[Dict[str, Any]] = None
    ) -> ActionFrameData:
        start_height = self.caster.pos[2]
        # 内部根据高度自动判定模式
        mode = "高空" if start_height > 2.0 else "低空"

        return ActionFrameData(
            name=f"下落攻击-{mode}",
            action_type="plunging_attack",
            total_frames=240,  # 作为一个长持续动作，靠落地或超时结束
            hit_frames=[],
            interrupt_frames={"any": 240},
            data={"mode": mode, "start_height": start_height},
            origin_skill=self,
        )

    def on_frame_update(self) -> None:
        if not self.caster:
            return

        # 检查当前是否在执行本技能发起的下落攻击
        if not hasattr(self.caster, "action_manager"):
            return
        instance = self.caster.action_manager.current_action
        if not instance or instance.data.origin_skill != self:
            return

        # 1. 下坠物理模拟
        self.caster.pos[2] = max(0.0, self.caster.pos[2] - self.fall_speed)

        # 2. 路径伤害触发
        self.path_timer += 1
        if self.path_timer >= self.path_damage_interval and self.caster.pos[2] > 0:
            self._trigger_plunge_damage("下落期间伤害")
            self.path_timer = 0

        # 3. 落地判定
        if self.caster.pos[2] <= 0:
            # 直接从动作实例的快照数据中提取 mode，确保前后一致性
            mode = instance.data.data.get("mode", "低空")
            self._trigger_plunge_damage(f"{mode}坠地冲击伤害")
            self.caster.action_manager._terminate_current("LANDED")

    def _trigger_plunge_damage(self, label: str):
        m_data = self.multiplier_data.get(label)
        if not m_data:
            return
        multiplier = m_data[1][self.lv - 1]

        p = self.attack_data.get(label, {"element_u": 1.0})
        dmg_obj = Damage(
            element=(self.caster.element, p.get("element_u", 1.0)),
            damage_multiplier=multiplier,
            scaling_stat="攻击力",
            name=label,
        )

        self.caster.event_engine.publish(
            GameEvent(
                EventType.BEFORE_DAMAGE,
                get_current_time(),
                source=self.caster,
                data={"character": self.caster, "damage": dmg_obj},
            )
        )


class SkipSkill(SkillBase):
    """
    通用跳过/等待组件。
    用于在动作序列中插入一段空闲时间。
    """

    def __init__(self, lv: int = 1, caster: Any = None):
        super().__init__(lv, caster)

    def to_action_data(
        self, intent: Optional[Dict[str, Any]] = None
    ) -> ActionFrameData:
        frames = intent.get("frames", 1) if intent else 1
        return ActionFrameData(
            name="等待",
            action_type="skip",
            total_frames=frames,
            hit_frames=[],
            interrupt_frames={"any": frames},  # 强制等待完整时长，不可中途打断
            origin_skill=self,
        )
