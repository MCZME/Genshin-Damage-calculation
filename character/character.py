from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union

import core.tool as T
from core.action.action_data import ActionFrameData
from core.action.action_manager import ActionManager
from core.context import get_context
from core.mechanics.aura import ElementalAura
from core.event import (
    ActionEvent,
    DamageEvent,
    EventBus,
    EventType,
    GameEvent,
    HealthChangeEvent,
    HealEvent,
)
from core.logger import get_emulation_logger


class Character(ABC):
    """
    角色基类。
    完全由 ASM (ActionManager) 驱动，遵循 snake_case 命名规范。
    基础属性通过构造函数 base_data 注入。
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

        # 1. 基础属性初始化
        self.attribute_data = {
            "生命值": 0.0, "固定生命值": 0.0, "攻击力": 0.0, "固定攻击力": 0.0, "防御力": 0.0, "固定防御力": 0.0,
            "元素精通": 0.0, "暴击率": 5.0, "暴击伤害": 50.0, "元素充能效率": 100.0,
            "治疗加成": 0.0, "受治疗加成": 0.0, "火元素伤害加成": 0.0, "水元素伤害加成": 0.0, "雷元素伤害加成": 0.0,
            "冰元素伤害加成": 0.0, "岩元素伤害加成": 0.0, "风元素伤害加成": 0.0, "草元素伤害加成": 0.0,
            "物理伤害加成": 0.0, "生命值%": 0.0, "攻击力%": 0.0, "防御力%": 0.0, "伤害加成": 0.0,
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
                    self.attribute_data[bt_name] = self.attribute_data.get(bt_name, 0.0) + bt_val
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

        # ASM 引擎与事件引擎初始化
        try:
            ctx = get_context()
            self.event_engine = ctx.event_engine
        except RuntimeError:
            ctx = None
            self.event_engine = None
            
        self.action_manager = ActionManager(self, ctx)

        self._init_character()
        self.apply_talents()

    @abstractmethod
    def _init_character(self) -> None:
        """初始化角色特有属性 (子类实现)"""
        pass

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
        event = HealthChangeEvent(
            event_type=EventType.BEFORE_HEALTH_CHANGE,
            frame=T.GetCurrentTime(),
            source=self,
            amount=amount
        )
        EventBus.publish(event)
        
        origin_hp = self.current_hp
        self.current_hp = min(self.max_hp, self.current_hp + event.amount)
        
        after_event = HealthChangeEvent(
            event_type=EventType.AFTER_HEALTH_CHANGE,
            frame=T.GetCurrentTime(),
            source=self,
            amount=self.current_hp - origin_hp
        )
        EventBus.publish(after_event)

    def hurt(self, amount: float) -> None:
        """受到直接扣血"""
        event = HealthChangeEvent(
            event_type=EventType.BEFORE_HEALTH_CHANGE,
            frame=T.GetCurrentTime(),
            source=self,
            amount=-amount
        )
        EventBus.publish(event)
        
        origin_hp = self.current_hp
        self.current_hp = max(0.0, self.current_hp + event.amount)
        
        after_event = HealthChangeEvent(
            event_type=EventType.AFTER_HEALTH_CHANGE,
            frame=T.GetCurrentTime(),
            source=self,
            amount=self.current_hp - origin_hp
        )
        EventBus.publish(after_event)

    def _request_action(self, name: str, params: Any = None) -> bool:
        """ASM 统一动作请求入口"""
        action_data = self._get_action_data(name, params)
        return self.action_manager.request_action(action_data)

    def _get_action_data(self, name: str, params: Any) -> ActionFrameData:
        """获取动作元数据 (对接旧技能对象进行桥接)"""
        total_frames = 60
        hit_frames = []

        skill_obj = None
        if name == "normal_attack": skill_obj = getattr(self, "NormalAttack", None)
        elif name == "elemental_skill": skill_obj = getattr(self, "Skill", None)
        elif name == "elemental_burst": skill_obj = getattr(self, "Burst", None)
        elif name == "charged_attack": skill_obj = getattr(self, "ChargedAttack", None)
        elif name == "plunging_attack": skill_obj = getattr(self, "PlungingAttack", None)
        elif name == "dash": skill_obj = getattr(self, "Dash", None)
        elif name == "jump": skill_obj = getattr(self, "Jump", None)

        if skill_obj and hasattr(skill_obj, "total_frames"):
            total_frames = skill_obj.total_frames

        data = ActionFrameData(name=name, total_frames=total_frames, hit_frames=hit_frames)
        if skill_obj:
            setattr(data, "runtime_skill_obj", skill_obj)
            
        return data

    # 动作入口
    def skip(self, n: int) -> None: self._request_action("skip", n)
    def dash(self) -> None: self._request_action("dash")
    def jump(self) -> None: self._request_action("jump")
    def normal_attack(self, n: int) -> None: self._request_action("normal_attack", n)
    def charged_attack(self) -> None: self._request_action("charged_attack")
    def plunging_attack(self, is_high: bool = False) -> None: self._request_action("plunging_attack", is_high)

    def elemental_skill(self) -> None:
        if self._request_action("elemental_skill"):
            EventBus.publish(ActionEvent(
                event_type=EventType.BEFORE_SKILL,
                frame=T.GetCurrentTime(),
                source=self,
                action_name="elemental_skill"
            ))

    def elemental_burst(self) -> None:
        if self._request_action("elemental_burst"):
            EventBus.publish(ActionEvent(
                event_type=EventType.BEFORE_BURST,
                frame=T.GetCurrentTime(),
                source=self,
                action_name="elemental_burst"
            ))

    def apply_talents(self) -> None:
        """应用固有天赋与命座效果"""
        talents = []
        if self.level >= 20 and getattr(self, "talent1", None): talents.append(self.talent1)
        if self.level >= 60 and getattr(self, "talent2", None): talents.append(self.talent2)
        for t in talents: t.apply(self)
        
        if self.constellation > 0:
            for i in range(min(self.constellation, 6)):
                eff = getattr(self, "constellation_effects", [None]*6)[i]
                if eff: eff.apply(self)

    def update(self, target: Any) -> None:
        """每帧更新逻辑"""
        self._update_effects(target)
        self.aura.update()
        if self.weapon:
            self.weapon.update(target)

        # 驱动 ASM
        self.action_manager.update()

        if self.constellation > 0:
            for i in range(min(self.constellation, 6)):
                eff = getattr(self, "constellation_effects", [None]*6)[i]
                if eff: eff.update(target)

        self.update_health()

    def update_health(self) -> None:
        """更新血量状态"""
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
        """更新所有活动效果"""
        for attr in ["active_effects", "shield_effects"]:
            effect_list = getattr(self, attr, [])
            expired = []
            for eff in effect_list:
                eff.update(target)
                if not getattr(eff, "is_active", True):
                    expired.append(eff)
            for eff in expired:
                if attr == "active_effects": self.remove_effect(eff)
                else: self.remove_shield(eff)

    def add_effect(self, effect: Any) -> None: self.active_effects.append(effect)
    def remove_effect(self, effect: Any) -> None:
        if effect in self.active_effects: self.active_effects.remove(effect)

    def add_shield(self, shield: Any) -> None: self.shield_effects.append(shield)
    def remove_shield(self, shield: Any) -> None:
        if shield in self.shield_effects: self.shield_effects.remove(shield)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "level": self.level,
            "skill_params": self.skill_params,
            "constellation": self.constellation,
            "weapon": self.weapon.to_dict() if self.weapon else None,
            "artifacts": self.artifact_manager.to_dict() if self.artifact_manager else None,
        }