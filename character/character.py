from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

import core.tool as T
from core.action.action_data import ActionFrameData
from core.action.action_manager import ActionManager
from core.context import get_context
from core.entities.base_entity import CombatEntity, Faction
from core.event import (
    ActionEvent,
    EventBus,
    EventType,
    HealthChangeEvent,
)


class Character(CombatEntity, ABC):
    """
    角色基类。
    作为 CombatEntity 接入场景化引擎，由 CombatSpace 统一驱动生命周期。
    """

    def __init__(
        self,
        id: int = 1,
        level: int = 1,
        skill_params: List[int] = None,
        constellation: int = 0,
        base_data: Dict[str, Any] = None,
        pos: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    ):
        name = base_data.get("name", "Unknown") if base_data else "Unknown"
        super().__init__(
            name=name,
            faction=Faction.PLAYER,
            pos=pos,
            hitbox=(0.3, 1.8) # 角色默认半径 0.3m，高度 1.8m
        )

        self.id = id
        self.level = level
        self.skill_params = skill_params or [1, 1, 1]
        self.constellation = constellation

        # 1. 基础数值乘区
        self.attribute_data = {
            "生命值": 0.0, "固定生命值": 0.0, "攻击力": 0.0, "固定攻击力": 0.0, "防御力": 0.0, "固定防御力": 0.0,
            "元素精通": 0.0, "暴击率": 5.0, "暴击伤害": 50.0, "元素充能效率": 100.0,
            "治疗加成": 0.0, "受治疗加成": 0.0, "火元素伤害加成": 0.0, "水元素伤害加成": 0.0, "雷元素伤害加成": 0.0,
            "冰元素伤害加成": 0.0, "岩元素伤害加成": 0.0, "风元素伤害加成": 0.0, "草元素伤害加成": 0.0,
            "物理伤害加成": 0.0, "生命值%": 0.0, "攻击力%": 0.0, "防御力%": 0.0, "伤害加成": 0.0,
        }

        if base_data:
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
            self.element = "无"
            self.type = "Unknown"

        self.attribute_panel = self.attribute_data.copy()
        self.association: Optional[str] = None

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
        self.shield_effects: List[Any] = []

        ctx = get_context()
        self.event_engine = ctx.event_engine
        self.action_manager = ActionManager(self, ctx)

        self._init_character()
        self.apply_talents()

    @abstractmethod
    def _init_character(self) -> None:
        pass

    def handle_damage(self, damage: Any) -> None:
        """接收伤害协议：处理角色受到的伤害。"""
        damage.set_target(self)
        results = self.apply_elemental_aura(damage)
        damage.data['reaction_results'] = results

    def on_frame_update(self) -> None:
        """实体逻辑主循环 (由 CombatSpace 调用)"""
        super().on_frame_update()
        
        if self.weapon:
            self.weapon.update() # 武器 update 不再需要参数

        self.action_manager.update()

        if self.constellation > 0:
            for i in range(min(self.constellation, 6)):
                eff = getattr(self, "constellation_effects", [None]*6)[i]
                if eff: eff.update()

        self.update_health()

    def update_health(self) -> None:
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

    def set_artifact(self, artifact: Any) -> None:
        self.artifact_manager = artifact
        self.artifact_manager.updatePanel()
        self.artifact_manager.setEffect()

    def set_weapon(self, weapon: Any) -> None:
        self.weapon = weapon
        self.weapon.updatePanel()
        self.weapon.skill()

    def heal(self, amount: float) -> None:
        # 治疗逻辑保持
        pass

    def hurt(self, amount: float) -> None:
        # 扣血逻辑保持
        pass

    def _request_action(self, name: str, params: Any = None) -> bool:
        action_data = self._get_action_data(name, params)
        return self.action_manager.request_action(action_data)

    def _get_action_data(self, name: str, params: Any) -> ActionFrameData:
        total_frames = 60
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
        data = ActionFrameData(name=name, total_frames=total_frames, hit_frames=[])
        if skill_obj: setattr(data, "runtime_skill_obj", skill_obj)
        return data

    def elemental_skill(self) -> None:
        if self._request_action("elemental_skill"):
            EventBus.publish(ActionEvent(EventType.BEFORE_SKILL, T.GetCurrentTime(), self, "elemental_skill"))

    def elemental_burst(self) -> None:
        if self._request_action("elemental_burst"):
            EventBus.publish(ActionEvent(EventType.BEFORE_BURST, T.GetCurrentTime(), self, "elemental_burst"))

    def apply_talents(self) -> None:
        # 天赋应用保持
        pass

    def add_shield(self, shield: Any) -> None: self.shield_effects.append(shield)
    def remove_shield(self, shield: Any) -> None:
        if shield in self.shield_effects: self.shield_effects.remove(shield)

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "level": self.level, "weapon": self.weapon.to_dict() if self.weapon else None}