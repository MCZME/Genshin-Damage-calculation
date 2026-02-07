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
    采用“标准化组件组装”模型。
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
            name=name, faction=Faction.PLAYER, pos=pos, hitbox=(0.3, 1.8)
        )

        self.id = id
        self.level = level
        self.skill_params = skill_params or [1, 1, 1]
        self.constellation = constellation

        # 1. 属性累加器
        self.attribute_data = {
            "生命值": 0.0, "固定生命值": 0.0, "生命值%": 0.0,
            "攻击力": 0.0, "固定攻击力": 0.0, "攻击力%": 0.0,
            "防御力": 0.0, "固定防御力": 0.0, "防御力%": 0.0,
            "元素精通": 0.0, "暴击率": 5.0, "暴击伤害": 50.0, "元素充能效率": 100.0,
            "治疗加成": 0.0, "受治疗加成": 0.0, "伤害加成": 0.0, "物理伤害加成": 0.0,
            "护盾强效": 0.0
        }
        for el in ["火", "水", "雷", "草", "冰", "岩", "风"]:
            self.attribute_data[f"{el}元素伤害加成"] = 0.0

        if base_data:
            self.element = base_data.get("element", "无")
            self.type = base_data.get("type", "Unknown")
            self.attribute_data["生命值"] = base_data.get("base_hp", 0.0)
            self.attribute_data["攻击力"] = base_data.get("base_atk", 0.0)
            self.attribute_data["防御力"] = base_data.get("base_def", 0.0)
            bt_name = base_data.get("breakthrough_attribute")
            bt_val = base_data.get("breakthrough_value", 0.0)
            if bt_name:
                key = bt_name if bt_name != "元素伤害加成" else f"{self.element}元素伤害加成"
                self.attribute_data[key] = self.attribute_data.get(key, 0.0) + bt_val
        else:
            self.element = "无"
            self.type = "Unknown"

        self.attribute_panel = self.attribute_data.copy()
        
        # -----------------------------------------------------
        # 角色核心组件 (标准化容器)
        # -----------------------------------------------------
        self.skills: Dict[str, Any] = {} # 存放 SkillBase 实例 (normal, skill, burst 等)
        self.elemental_energy: Any = None # 存放 ElementalEnergy 实例
        
        self.weapon: Any = None
        self.artifact_manager: Any = None
        self.shield_effects: List[Any] = []
        self.on_field = False

        # ASM 引擎
        ctx = get_context()
        self.event_engine = ctx.event_engine
        self.action_manager = ActionManager(self, ctx)

        # 2. 执行组件组装钩子 (由子类实现)
        self._setup_character_components()
        self.apply_talents()
        
        self.current_hp = 0.0

    @abstractmethod
    def _setup_character_components(self) -> None:
        """
        [子类必填] 实例化角色的技能组与能量系统并注册到组件容器中。
        """
        pass

    def initialize_gear(self) -> None:
        """完成装备面板合并"""
        self.attribute_panel = self.attribute_data.copy()
        if self.weapon:
            self.weapon.apply_static_stats()
            self.weapon.skill()
        if self.artifact_manager:
            self.artifact_manager.apply_static_stats()
            self.artifact_manager.set_effect()
        from core.systems.utils import AttributeCalculator
        self.current_hp = AttributeCalculator.get_hp(self)

    # -----------------------------------------------------
    # 动作系统重构：直接访问 skills 容器
    # -----------------------------------------------------

    def _get_action_data(self, name: str, params: Any) -> ActionFrameData:
        """从 skills 容器提取技能元数据"""
        # 映射内部逻辑名到 skills 字典 key
        mapping = {
            "normal_attack": "normal",
            "elemental_skill": "skill",
            "elemental_burst": "burst",
            "charged_attack": "charged",
            "plunging_attack": "plunging"
        }
        skill_key = mapping.get(name)
        skill_obj = self.skills.get(skill_key) if skill_key else None
        
        total_frames = 60
        if skill_obj and hasattr(skill_obj, "total_frames"):
            total_frames = skill_obj.total_frames
            
        data = ActionFrameData(name=name, total_frames=total_frames, hit_frames=[])
        if skill_obj: setattr(data, "runtime_skill_obj", skill_obj)
        return data

    # 业务逻辑 (heal, hurt, on_frame_update, etc.) 保持不变
    def on_frame_update(self) -> None:
        super().on_frame_update()
        if self.weapon and hasattr(self.weapon, "update"): self.weapon.update()
        self.action_manager.update()
        # 自动驱动所有技能的内部 CD/状态 (如果技能有 update)
        for skill in self.skills.values():
            if hasattr(skill, "update"): skill.update()
            
        if self.constellation > 0:
            for i in range(min(self.constellation, 6)):
                eff = getattr(self, "constellation_effects", [None]*6)[i]
                if eff and hasattr(eff, "update"): eff.update()

    def set_artifact(self, artifact: Any) -> None: self.artifact_manager = artifact
    def set_weapon(self, weapon: Any) -> None: self.weapon = weapon

    def elemental_skill(self) -> None:
        if self._request_action("elemental_skill"):
            self.event_engine.publish(ActionEvent(EventType.BEFORE_SKILL, T.GetCurrentTime(), self, "elemental_skill"))

    def elemental_burst(self) -> None:
        if self._request_action("elemental_burst"):
            self.event_engine.publish(ActionEvent(EventType.BEFORE_BURST, T.GetCurrentTime(), self, "elemental_burst"))

    def _request_action(self, name: str, params: Any = None) -> bool:
        action_data = self._get_action_data(name, params)
        return self.action_manager.request_action(action_data)

    def skip(self, n: int) -> None: self._request_action("skip", n)
    def dash(self) -> None: self._request_action("dash")
    def jump(self) -> None: self._request_action("jump")
    def normal_attack(self, n: int) -> None: self._request_action("normal_attack", n)
    def charged_attack(self) -> None: self._request_action("charged_attack")
    def plunging_attack(self, is_high: bool = False) -> None: self._request_action("plunging_attack", is_high)

    def handle_damage(self, damage: Any) -> None:
        damage.set_target(self)
        results = self.apply_elemental_aura(damage)
        damage.data['reaction_results'] = results

    def heal(self, amount: float) -> None: pass
    def hurt(self, amount: float) -> None: pass
    def apply_talents(self) -> None: pass
    def add_shield(self, shield: Any) -> None: self.shield_effects.append(shield)
    def remove_shield(self, shield: Any) -> None:
        if shield in self.shield_effects: self.shield_effects.remove(shield)

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name, "level": self.level, "panel": self.attribute_panel}