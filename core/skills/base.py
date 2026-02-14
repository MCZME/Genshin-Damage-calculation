from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from core.action.action_data import ActionFrameData


class SkillBase(ABC):
    """
    技能逻辑基类 (V2.3.1 动作工厂版)。

    负责管理技能等级与冷却状态，并根据玩家意图 (Intent) 产出物理动作描述。
    物理状态 (帧推进、中断判定) 由 ActionManager 统一负责。
    """

    def __init__(self, lv: int, caster: Any = None) -> None:
        """初始化技能。

        Args:
            lv: 技能当前等级 (1-15)。
            caster: 技能的施放者 (角色实例)。
        """
        self.lv: int = lv
        self.caster: Any = caster
        self.last_use_frame: int = -9999

    @abstractmethod
    def to_action_data(
        self, intent: Optional[Dict[str, Any]] = None
    ) -> ActionFrameData:
        """
        [核心接口] 将逻辑意图转换为物理动作数据。

        子类应在此处从对应的 data.py 中读取帧数、中断帧 (interrupt_frames)
        以及配置 AttackConfig。

        Args:
            intent: 玩家下发的意图参数字典。

        Returns:
            ActionFrameData: 包含所有物理参数的动作描述块。
        """
        pass

    def can_cast(self) -> bool:
        """
        检查技能是否满足施放条件 (如 CD、能量)。
        具体逻辑由子类 (如 EnergySkill) 扩展。
        """
        # TODO: 实装基础 CD 判定
        return True

    def on_execute_hit(self, target: Any, hit_index: int) -> None:
        """
        [回调] 当动作状态机运行到伤害发生帧 (hit_frames) 时触发。

        子类可在此处处理伤害之外的副作用 (如回能、叠层)。

        Args:
            target: 受击目标。
            hit_index: 当前是该动作的第几次命中。
        """
        pass

    def on_frame_update(self) -> None:
        """
        [回调] 角色每帧驱动逻辑。
        用于处理持续性的技能逻辑 (如某些技能开启后的计时器)。
        """
        pass


class EnergySkill(SkillBase):
    """
    具备能量消耗特性的技能 (通常为元素爆发)。
    """

    def can_cast(self) -> bool:
        """检查能量是否已满。"""
        if not super().can_cast():
            return False

        if hasattr(self.caster, "elemental_energy"):
            return self.caster.elemental_energy.is_energy_full()
        return True

    def consume_energy(self) -> None:
        """消耗并清空施法者的能量。"""
        if hasattr(self.caster, "elemental_energy"):
            self.caster.elemental_energy.clear_energy()
