from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union

import core.tool as T
from core.action.action_data import ActionFrameData
from core.action.action_manager import ActionManager
from core.context import get_context
from core.elementalReaction.ElementalAura import ElementalAura
from core.event import (
    ElementalBurstEvent,
    ElementalSkillEvent,
    EventBus,
    EventType,
    GameEvent,
    HealChargeEvent,
)
from core.logger import get_emulation_logger


class Character(ABC):
    """
    角色基类。
    所有基础属性 (base_data) 由外部注入，由 ASM (ActionManager) 驱动动作。
    """

    def __init__(
        self,
        id: int = 1,
        level: int = 1,
        skill_params: List[int] = None,
        constellation: int = 0,
        base_data: Dict[str, Any] = None,
    ):
        self.id = id
        self.level = level
        self.skill_params = skill_params or [1, 1, 1]
        self.constellation = constellation

        # 基础属性初始化
        self.attribute_data = {
            "生命值": 0.0,
            "固定生命值": 0.0,
            "攻击力": 0.0,
            "固定攻击力": 0.0,
            "防御力": 0.0,
            "固定防御力": 0.0,
            "元素精通": 0.0,
            "暴击率": 5.0,
            "暴击伤害": 50.0,
            "元素充能效率": 100.0,
            "治疗加成": 0.0,
            "受治疗加成": 0.0,
            "火元素伤害加成": 0.0,
            "水元素伤害加成": 0.0,
            "雷元素伤害加成": 0.0,
            "冰元素伤害加成": 0.0,
            "岩元素伤害加成": 0.0,
            "风元素伤害加成": 0.0,
            "草元素伤害加成": 0.0,
            "物理伤害加成": 0.0,
            "生命值%": 0.0,
            "攻击力%": 0.0,
            "防御力%": 0.0,
            "伤害加成": 0.0,
        }

        # 数据注入
        if base_data:
            self.name = base_data.get("name", "Unknown")
            self.element = base_data.get("element", "无")
            self.type = base_data.get("type", "Unknown")

            self.attribute_data["生命值"] = base_data.get("base_hp", 0.0)
            self.attribute_data["攻击力"] = base_data.get("base_atk", 0.0)
            self.attribute_data["防御力"] = base_data.get("base_def", 0.0)

            bt_name = base_data.get("breakthrough_attribute")
            bt_val = base_data.get("breakthrough_value", 0.0)
            if bt_name:
                if bt_name == "元素伤害加成":
                    self.attribute_data[self.element + bt_name] += bt_val
                else:
                    self.attribute_data[bt_name] = (
                        self.attribute_data.get(bt_name, 0.0) + bt_val
                    )
        else:
            self.name = "Unknown"
            self.element = "无"
            self.type = "Unknown"

        self.attribute_panel = self.attribute_data.copy()
        self.association: Optional[str] = None

        self.aura = ElementalAura()
        self.max_hp = (
            self.attribute_panel["生命值"] * (1 + self.attribute_panel["生命值%"] / 100)
            + self.attribute_panel["固定生命值"]
        )
        self.current_hp = self.max_hp
        
        self.movement = 0.0
        self.height = 0.0
        self.falling_speed = 5.0
        self.on_field = False

        self.weapon: Any = None
        self.artifact_manager: Any = None

        # ASM 引擎初始化
        try:
            ctx = get_context()
        except RuntimeError:
            ctx = None
        self.action_manager = ActionManager(self, ctx)

        self._init_character()
        self.apply_talents()

    @abstractmethod
    def _init_character(self) -> None:
        """初始化角色特有属性 (技能、天赋、命座等)"""
        self.NormalAttack = None
        self.ChargedAttack = None
        self.PlungingAttack = None
        self.Dash = None
        self.Jump = None
        self.Skill = None
        self.Burst = None
        self.talent1 = None
        self.talent2 = None
        self.talent_effects: List[Any] = []
        self.active_effects: List[Any] = []
        self.shield_effects: List[Any] = []
        self.constellation_effects: List[Optional[Any]] = [None] * 6
        self.elemental_energy: Any = None

    def set_artifact(self, artifact: Any) -> None:
        """设置圣遗物管理器"""
        self.artifact_manager = artifact
        self.artifact_manager.updatePanel()
        self.artifact_manager.setEffect()

    def set_weapon(self, weapon: Any) -> None:
        """设置武器"""
        self.weapon = weapon
        self.weapon.updatePanel()
        self.weapon.skill()

    def set_constellation(self, constellation: int) -> None:
        """设置命座等级"""
        self.constellation = constellation

    def heal(self, amount: float) -> None:
        """接收治疗"""
        event = HealChargeEvent(self, amount, T.GetCurrentTime())
        EventBus.publish(event)
        
        origin_hp = self.current_hp
        self.current_hp = min(self.max_hp, self.current_hp + event.data["amount"])
        
        after_event = HealChargeEvent(
            self, self.current_hp - origin_hp, T.GetCurrentTime(), before=False
        )
        EventBus.publish(after_event)

    def hurt(self, amount: float) -> None:
        """受到扣血 (非护盾吸收的直接伤害)"""
        event = HealChargeEvent(self, -amount, T.GetCurrentTime())
        EventBus.publish(event)
        
        origin_hp = self.current_hp
        self.current_hp = max(0.0, self.current_hp + event.data["amount"])
        
        after_event = HealChargeEvent(
            self, self.current_hp - origin_hp, T.GetCurrentTime(), before=False
        )
        EventBus.publish(after_event)

    def _request_action(self, name: str, params: Any = None) -> bool:
        """ASM 统一动作请求入口"""
        action_data = self._get_action_data(name, params)
        return self.action_manager.request_action(action_data)

    def _get_action_data(self, name: str, params: Any) -> ActionFrameData:
        """
        获取动作元数据。
        未来应从数据库或配置文件读取。
        """
        # 基础默认值兼容逻辑
        total_frames = 60
        hit_frames = []

        if name == "normal_attack":
            total_frames = 30
            hit_frames = [10]
        elif name == "elemental_skill":
            total_frames = 60
            hit_frames = [20]
        elif name == "elemental_burst":
            total_frames = 120
            hit_frames = [40]

        data = ActionFrameData(name=name, total_frames=total_frames, hit_frames=hit_frames)
        # 挂载运行时对象以支持旧逻辑回调
        if name == "elemental_skill" and self.Skill:
            setattr(data, "runtime_skill_obj", self.Skill)
        elif name == "elemental_burst" and self.Burst:
            setattr(data, "runtime_skill_obj", self.Burst)
        elif name == "normal_attack" and self.NormalAttack:
            setattr(data, "runtime_skill_obj", self.NormalAttack)
            
        return data

    def skip(self, n: int) -> None:
        """跳过指定帧数"""
        self._request_action("skip", n)

    def dash(self) -> None:
        """执行冲刺"""
        self._request_action("dash")

    def jump(self) -> None:
        """执行跳跃"""
        self._request_action("jump")

    def normal_attack(self, n: int) -> None:
        """执行普通攻击 (n 段)"""
        self._request_action("normal_attack", n)

    def charged_attack(self) -> None:
        """执行重击"""
        self._request_action("charged_attack")

    def plunging_attack(self, is_high: bool = False) -> None:
        """执行下落攻击"""
        self._request_action("plunging_attack", is_high)

    def elemental_skill(self) -> None:
        """执行元素战技"""
        self._request_action("elemental_skill")
        skill_event = ElementalSkillEvent(self, T.GetCurrentTime())
        EventBus.publish(skill_event)

    def elemental_burst(self) -> None:
        """执行元素爆发"""
        self._request_action("elemental_burst")
        burst_event = ElementalBurstEvent(self, T.GetCurrentTime())
        EventBus.publish(burst_event)

    def apply_talents(self) -> None:
        """应用固有天赋效果"""
        if self.level >= 20:
            self.talent_effects.append(self.talent1)
        if self.level >= 60:
            self.talent_effects.append(self.talent2)
            
        for effect in self.talent_effects:
            if effect is not None:
                effect.apply(self)
                
        if self.constellation > 0:
            for effect in self.constellation_effects[: self.constellation]:
                if effect is not None:
                    effect.apply(self)

    def update(self, target: Any) -> None:
        """每帧更新逻辑"""
        # 1. 更新效果与元素附着
        self._update_effects(target)
        self.aura.update()
        if self.weapon is not None:
            self.weapon.update(target)

        # 2. 驱动 ASM
        self.action_manager.update()

        # 3. 处理命座更新 (如果需要每帧更新)
        if self.constellation > 0:
            for effect in self.constellation_effects[: self.constellation]:
                if effect is not None:
                    effect.update(target)

        # 4. 状态同步与血量更新
        self.update_health()

    def update_health(self) -> None:
        """更新血量百分比 (应对最大生命值变化)"""
        current_max_hp = (
            self.attribute_panel["生命值"] * (1 + self.attribute_panel["生命值%"] / 100)
            + self.attribute_panel["固定生命值"]
        )

        if self.max_hp != current_max_hp:
            if self.max_hp > 0:
                self.current_hp = self.current_hp * current_max_hp / self.max_hp
            else:
                self.current_hp = current_max_hp
            self.max_hp = current_max_hp

    def _update_effects(self, target: Any) -> None:
        """内部方法：更新所有活动效果"""
        remove_effects = []
        for effect in self.active_effects:
            effect.update(target)
            if not effect.is_active:
                remove_effects.append(effect)
        for effect in remove_effects:
            self.remove_effect(effect)

        remove_shields = []
        for shield in self.shield_effects:
            shield.update(target)
            if not shield.is_active:
                remove_shields.append(shield)
        for shield in remove_shields:
            self.remove_shield(shield)

        for talent in self.talent_effects:
            if talent is not None:
                talent.update(target)

    def add_effect(self, effect: Any) -> None:
        """添加一个活动效果"""
        self.active_effects.append(effect)

    def remove_effect(self, effect: Any) -> None:
        """移除一个活动效果"""
        if effect in self.active_effects:
            self.active_effects.remove(effect)

    def add_shield(self, shield: Any) -> None:
        """添加一个护盾"""
        self.shield_effects.append(shield)

    def remove_shield(self, shield: Any) -> None:
        """移除一个护盾"""
        if shield in self.shield_effects:
            self.shield_effects.remove(shield)

    def to_dict(self) -> Dict[str, Any]:
        """将角色状态序列化为字典"""
        return {
            "id": self.id,
            "level": self.level,
            "skill_params": self.skill_params,
            "constellation": self.constellation,
            "weapon": self.weapon.to_dict() if self.weapon else None,
            "artifacts": self.artifact_manager.to_dict() if self.artifact_manager else None,
        }