from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from core.tool import get_current_time


@dataclass
class ICDGroup:
    """ICD (Internal Cooldown) 组别定义。
    
    定义了附着重置的时间阈值以及攻击命中时的附着序列。
    """
    reset_time: float    # 重置时间 (秒)
    sequence: List[int]  # 附着序列 (1 代表产生附着, 0 代表不产生)
    
    @property
    def reset_frames(self) -> int:
        """重置时间转换为仿真帧数。"""
        return int(self.reset_time * 60)


# --- 全局预定义 ICD 组别 ---
ICD_GROUPS: Dict[str, ICDGroup] = {
    # 默认组别: 2.5s 重置, 每 3 次命中触发一次附着 (1, 4, 7...)
    "Default": ICDGroup(2.5, [1, 0, 0]), 
    
    # 独立附着: 每次命中均触发附着
    "Independent": ICDGroup(0.0, [1]),
    
    # 特殊组别: 每 1 秒重置一次 (用于部分持续性伤害)
    "Interval1s": ICDGroup(1.0, [1]),
    
    # 柯莱爆发组别: 3s 重置，长序列
    "ColleiBurst": ICDGroup(3.0, [1, 0, 0, 0, 0, 0, 0, 0, 0]), 
}


@dataclass
class ICDState:
    """ICD 运行时状态记录。"""
    hit_count: int = 0            # 当前组别的命中计数
    last_reset_frame: int = -9999 # 上次序列重置的起始帧


class ICDManager:
    """ICD 管理器。
    
    负责追踪并判定单个实体受到的各类攻击是否符合附着冷却规则。
    每个 CombatEntity 实例持有一个 ICDManager。
    """

    def __init__(self, owner: Any) -> None:
        """初始化管理器。

        Args:
            owner: 所属的战斗实体。
        """
        self.owner = owner
        # 核心存储: (攻击者 ID, ICD 标签) -> 运行时状态
        self.records: Dict[Tuple[int, str], ICDState] = {}

    def check_attachment(self, attacker: Any, tag: str) -> float:
        """判定本次攻击是否能够施加元素附着。

        根据攻击者实例和 ICD 标签计算元素量系数。

        Args:
            attacker: 发起攻击的实体。
            tag: 攻击携带的 ICD 标签 (对应 ICD_GROUPS 的键)。

        Returns:
            float: 元素量系数。1.0 代表附着，0.0 代表受冷却限制不附着。
        """
        # 1. 快速通道：独立附着或无标签
        if tag in ["None", "Independent", None]:
            return 1.0
            
        group = ICD_GROUPS.get(tag, ICD_GROUPS["Default"])
        
        # 2. 获取或创建状态记录 (实现攻击者间的 ICD 隔离)
        key = (id(attacker), tag)
        if key not in self.records:
            self.records[key] = ICDState()
            
        state = self.records[key]
        current_frame = get_current_time()
        
        # 3. 时间重置判定
        if current_frame - state.last_reset_frame >= group.reset_frames:
            state.hit_count = 0
            state.last_reset_frame = current_frame
            
            coeff = self._get_coefficient(group, 0)
            state.hit_count = 1  # 记录本次命中
            self._log_debug(tag, coeff, state.hit_count)
            return float(coeff)
            
        # 4. 序列计数判定
        coeff = self._get_coefficient(group, state.hit_count)
        
        # 推进计数
        state.hit_count += 1
        self._log_debug(tag, coeff, state.hit_count)
        
        return float(coeff)

    def _get_coefficient(self, group: ICDGroup, index: int) -> int:
        """根据当前索引从序列中提取系数 (支持模运算循环)。"""
        if not group.sequence:
            return 1
        return group.sequence[index % len(group.sequence)]

    def _log_debug(self, tag: str, coeff: int, count: int) -> None:
        """记录附着判定的调试日志。"""
        if coeff > 0:
            from core.logger import get_emulation_logger
            get_emulation_logger().log_debug(
                f"[ICD] 标签 {tag} 附着成功 (当前计数: {count})", 
                sender="ICD"
            )

    def reset(self, attacker: Optional[Any] = None, tag: Optional[str] = None) -> None:
        """手动重置特定或全部 ICD 记录。"""
        if attacker and tag:
            key = (id(attacker), tag)
            self.records.pop(key, None)
        elif not attacker and not tag:
            self.records.clear()
