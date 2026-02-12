from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from core.action.action_data import ActionFrameData
from core.action.action_manager import ActionManager
from core.context import get_context
from core.entities.base_entity import CombatEntity, Faction
from core.event import (
    ActionEvent,
    EventType,
)
from core.effect.common import TalentEffect, ConstellationEffect
from core.tool import get_current_time


class Character(CombatEntity, ABC):
    """
    角色基类。
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
        self.constellation_level = constellation

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
        # 标准化组件
        # -----------------------------------------------------
        self.skills: Dict[str, Any] = {}
        self.elemental_energy: Any = None
        
        # [新] 动态天赋与固定命座
        self.talents: List[TalentEffect] = [] # 动态列表，支持任意数量天赋
        self.constellations: List[Optional[ConstellationEffect]] = [None] * 6
        
        self.weapon: Any = None
        self.artifact_manager: Any = None
        self.shield_effects: List[Any] = []
        self.on_field = False

        ctx = get_context()
        self.event_engine = ctx.event_engine
        self.action_manager = ActionManager(self, ctx)

        self._setup_character_components()
        self._setup_effects()
        self.apply_effects()
        
        self.current_hp = 0.0

    @abstractmethod
    def _setup_character_components(self) -> None:
        pass

    @abstractmethod
    def _setup_effects(self) -> None:
        """
        [子类必填] 填充 self.talents 列表与 self.constellations 槽位。
        """
        pass

    def apply_effects(self) -> None:
        """
        执行天赋与命座的加载逻辑。
        所有 Effect 对象会依据 character 的等级与命座层级自行判定是否激活。
        """
        # 1. 应用固有天赋
        for t in self.talents:
            if t: t.apply(self)
        
        # 2. 应用命座
        for c in self.constellations:
            if c: c.apply(self)

    def initialize_gear(self) -> None:
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
    # 统一驱动接口
    # -----------------------------------------------------

    def on_frame_update(self) -> None:
        """
        角色每帧逻辑驱动。
        """
        super().on_frame_update()
        
        if self.weapon and hasattr(self.weapon, "on_frame_update"): 
            self.weapon.on_frame_update()
            
        self.action_manager.on_frame_update() # ActionManager 内部也应同步改为此命名
        
        # 驱动技能逻辑
        for skill in self.skills.values():
            if hasattr(skill, "on_frame_update"): skill.on_frame_update()
            
        # 驱动天赋与命座逻辑
        for t in self.talents:
            if t: t.on_frame_update()
        for c in self.constellations:
            if c: c.on_frame_update()

    # -----------------------------------------------------
    # 动作与协议 (保持不变，仅重定向内部调用)
    # -----------------------------------------------------

    def _get_action_data(self, name: str, params: Any) -> ActionFrameData:
        mapping = {"normal_attack":"normal", "elemental_skill":"skill", "elemental_burst":"burst", "charged_attack":"charged", "plunging_attack":"plunging"}
        skill_obj = self.skills.get(mapping.get(name))
        
        # 核心变动：如果技能对象支持 to_action_data，则调用它并传入 params
        if skill_obj and hasattr(skill_obj, "to_action_data"):
            return skill_obj.to_action_data(params)
            
        total_frames = 60
        if skill_obj and hasattr(skill_obj, "total_frames"): total_frames = skill_obj.total_frames
        data = ActionFrameData(name=name, total_frames=total_frames, hit_frames=[])
        if skill_obj: data.origin_skill = skill_obj
        return data

    def elemental_skill(self, params: Any = None) -> bool:
        if self._request_action("elemental_skill", params):
            self.event_engine.publish(ActionEvent(EventType.BEFORE_SKILL, get_current_time(), self, "elemental_skill"))
            return True
        return False

    def elemental_burst(self, params: Any = None) -> bool:
        if self._request_action("elemental_burst", params):
            self.event_engine.publish(ActionEvent(EventType.BEFORE_BURST, get_current_time(), self, "elemental_burst"))
            return True
        return False

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
    def set_artifact(self, artifact: Any) -> None: self.artifact_manager = artifact
    def set_weapon(self, weapon: Any) -> None: self.weapon = weapon
    def add_shield(self, shield: Any) -> None: self.shield_effects.append(shield)
    def remove_shield(self, shield: Any) -> None:
        if shield in self.shield_effects: self.shield_effects.remove(shield)

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name, "level": self.level, "constellation": self.constellation_level}

    def export_state(self) -> dict:
        """导出角色特有状态"""

        base = super().export_state()
        base.update({
            "level": self.level,
            "constellation": self.constellation_level,
            "on_field": self.on_field,
            "energy": self.elemental_energy.current_energy if self.elemental_energy else 0,
            "hp": round(self.current_hp, 1)
        })

        return base

    @classmethod
    def get_action_metadata(cls) -> Dict[str, Any]:
        """
        [V2.3] 获取动作参数元数据（类方法）。
        UI 可以在不实例化角色的情况下获取参数 Schema。
        
        示例返回格式:
        {
            "elemental_skill": {
                "label": "元素战技",
                "params": [
                    {
                        "key": "type", 
                        "label": "施放方式", 
                        "type": "select", 
                        "options": {"Press": "点按", "Hold": "长按"}, # {内部值: 显示标签}
                        "default": "Press"
                    }
                ]
            }
        }
        """
        return {}
