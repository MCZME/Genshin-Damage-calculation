from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from core.tool import get_current_time


@dataclass
class ICDGroup:
    """ICD 规则组定义。
    定义了附着重置的时间阈值以及攻击命中时的附着序列。
    """

    reset_time: float  # 重置时间 (秒)
    sequence: List[int]  # 附着序列 (1 代表产生附着, 0 代表不产生)

    @property
    def reset_frames(self) -> int:
        return int(self.reset_time * 60)


# --- 全局附着规则映射 ---
ICD_RULES: Dict[str, ICDGroup] = {
    # 默认组别: 2.5s 重置, 每 3 次命中触发一次附着 (1, 4, 7...)
    "Default": ICDGroup(2.5, [1, 0, 0]),
    # 独立附着: 每次命中均触发附着
    "Independent": ICDGroup(0.0, [1]),
    # 芙宁娜战技规则: 30s 重置, 每 2 次命中附着 1 次, 上限 12 次 (共 24 次命中判定)
    "FurinaElementalSkill": ICDGroup(30.0, [1, 0] * 12),
}


@dataclass
class ICDState:
    """ICD 运行时状态记录。"""

    hit_count: int = 0  # 当前组别的命中计数
    last_reset_frame: int = -9999  # 上次序列重置的起始帧


class ICDManager:
    """ICD 管理器 (V2.4 共享组版)。

    支持多动作、多实体共享同一个附着冷却计数器。
    """

    def __init__(self, owner: Any) -> None:
        self.owner = owner
        # 核心存储: (来源 ID, 共享组别名) -> 运行时状态
        self.records: Dict[Tuple[int, str], ICDState] = {}

    def check_attachment(self, attacker: Any, icd_tag: str, icd_group: str) -> float:
        """判定本次攻击是否能够施加元素附着。

        Args:
            attacker: 发起攻击的实体 (可能是召唤物)。
            icd_tag: 附着规则标签 (用于查找 ICD_RULES)。
            icd_group: 共享冷却组 ID (决定谁和谁共用计数器)。

        Returns:
            float: 元素量系数 (1.0 或 0.0)。
        """
        # 1. 快速通道
        if icd_tag in ["None", "Independent", None]:
            return 1.0

        rule = ICD_RULES.get(icd_tag, ICD_RULES["Default"])

        # 2. 确定真实的来源 ID (Root Source)
        # 如果攻击者是召唤物，其 ICD 通常基于主人
        source_id = id(attacker)
        if hasattr(attacker, "owner") and attacker.owner:
            source_id = id(attacker.owner)

        # 3. 获取或创建共享状态
        # Key 不再包含具体动作名，而是使用传入的 icd_group
        key = (source_id, icd_group)
        if key not in self.records:
            self.records[key] = ICDState()

        state = self.records[key]
        current_frame = get_current_time()

        # 4. 时间重置判定
        if current_frame - state.last_reset_frame >= rule.reset_frames:
            state.hit_count = 0
            state.last_reset_frame = current_frame

            coeff = self._get_coefficient(rule, 0)
            state.hit_count = 1
            return float(coeff)

        # 5. 序列计数判定
        coeff = self._get_coefficient(rule, state.hit_count)
        state.hit_count += 1

        return float(coeff)

    def _get_coefficient(self, rule: ICDGroup, index: int) -> int:
        """根据当前索引从序列中提取系数。

        如果索引超过了序列定义的长度，则不再提供附着 (返回 0)。
        这用于实现类似芙宁娜战技这种有总附着次数上限的规则。
        """
        if not rule.sequence:
            return 1

        if index < len(rule.sequence):
            return rule.sequence[index]

        return 0
