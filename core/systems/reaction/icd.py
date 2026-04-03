"""受击 ICD 管理模块。"""

from typing import Any

from core.systems.contract.reaction import ElementalReactionType
from core.tool import get_current_time


class ICDManager:
    """
    受击 ICD 管理器。

    管理剧变反应伤害的受击冷却。
    规则：0.5秒内最多受2次同类反应伤害。
    """

    def __init__(self):
        # 剧变反应受击 ICD 配置: (时间窗口帧数, 最大受击次数)
        # 0.5s 内最多受 2 次同类反应伤害
        self._REACTION_ICD_WINDOW = 30
        self._REACTION_MAX_HITS = 2

        # 运行时状态记录:
        # Key: (目标实体ID, 反应类型) -> [最后重置帧, 当前窗口内受击次数]
        self._target_reaction_records: dict[
            tuple[int, ElementalReactionType], list[int]
        ] = {}

    def check(self, target: Any, r_type: ElementalReactionType) -> bool:
        """
        检查特定目标对特定剧变伤害的受击 ICD。

        Args:
            target: 受击目标
            r_type: 反应类型

        Returns:
            True 如果可以造成伤害，False 如果被 ICD 阻挡
        """
        key = (id(target), r_type)
        current_frame = get_current_time()

        if key not in self._target_reaction_records:
            self._target_reaction_records[key] = [current_frame, 1]
            return True

        record = self._target_reaction_records[key]
        last_reset_frame = record[0]
        hit_count = record[1]

        if current_frame - last_reset_frame > self._REACTION_ICD_WINDOW:
            record[0] = current_frame
            record[1] = 1
            return True

        if hit_count < self._REACTION_MAX_HITS:
            record[1] += 1
            return True

        return False

    def reset(self, target: Any, r_type: ElementalReactionType) -> None:
        """重置特定目标的 ICD 记录。"""
        key = (id(target), r_type)
        if key in self._target_reaction_records:
            del self._target_reaction_records[key]
