from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from core.tool import get_current_time

@dataclass
class ICDGroup:
    """ICD 冷却组别定义"""
    reset_time: float    # 重置时间 (秒)
    sequence: List[int]  # 元素量系数序列 (1代表附着, 0代表不附着)
    
    @property
    def reset_frames(self) -> int:
        return int(self.reset_time * 60)

# 全局预定义组别 (可扩展)
ICD_GROUPS: Dict[str, ICDGroup] = {
    # 默认组别: 2.5s重置, 第1,4,7...次附着 (3次一循环)
    "Default": ICDGroup(2.5, [1, 0, 0]), 
    
    # 独立附着: 0s重置, 每次都附着
    "Independent": ICDGroup(0.0, [1]),
    
    # 特殊组别: 柯莱爆发 (3s重置, 仅第1次附着)
    "ColleiBurst": ICDGroup(3.0, [1, 0, 0, 0, 0, 0, 0, 0, 0]), 
    
    # 特殊组别: 莫娜普攻 (2.5s重置, 默认3hit)
    "MonaNormal": ICDGroup(2.5, [1, 0, 0]),
}

@dataclass
class ICDState:
    """ICD 运行时状态"""
    hit_count: int = 0       # 当前计数
    last_reset_frame: int = -9999 # 上次重置时间的帧数

class ICDManager:
    """
    ICD 管理器 (高精度版)。
    负责管理该实体受到的所有攻击的附着冷却状态。
    """
    def __init__(self, owner):
        self.owner = owner
        # 核心存储结构: 
        # Key: (攻击者实例ID, ICD标签)
        # Value: ICDState 对象
        self.records: Dict[Tuple[int, str], ICDState] = {}

    def check_attachment(self, attacker: Any, tag: str) -> float:
        """
        根据攻击者和标签，计算本次攻击的元素量系数。
        返回: 1.0 (附着), 0.0 (不附着)
        """
        # 1. 独立附着快速通道 (兼容旧逻辑的 None)
        if tag in ["None", "Independent", None]:
            return 1.0
            
        group = ICD_GROUPS.get(tag, ICD_GROUPS["Default"])
        
        # 获取状态记录 (基于攻击者ID隔离)
        key = (id(attacker), tag)
        if key not in self.records:
            self.records[key] = ICDState()
            
        state = self.records[key]
        current_frame = get_current_time()
        
        # 2. 时间重置判定
        # 如果距离上次重置超过了时限，或者从未重置过
        if current_frame - state.last_reset_frame >= group.reset_frames:
            from core.logger import get_emulation_logger
            get_emulation_logger().log_debug(f"组别 {tag} 时间重置 (上次: {state.last_reset_frame})", sender="ICD")
            
            state.hit_count = 0
            state.last_reset_frame = current_frame
            # 重置后，计数从0开始，应用序列第0位系数
            coeff = self._get_coefficient(group, 0)
            # 命中计数加1
            state.hit_count += 1
            self._log_attachment(tag, coeff, state.hit_count)
            return float(coeff)
            
        # 3. 序列计数判定
        # 获取当前计数对应的系数
        coeff = self._get_coefficient(group, state.hit_count)
        
        # 命中计数加1
        state.hit_count += 1
        self._log_attachment(tag, coeff, state.hit_count)
        
        return float(coeff)

    def _log_attachment(self, tag: str, coeff: int, count: int):
        """内部辅助：记录附着判定日志"""
        if coeff > 0:
            # 仅在调试级别记录，避免淹没普通日志
            from core.logger import get_emulation_logger
            get_emulation_logger().log_debug(f"[ICD] {tag} 附着成功 (计数: {count})", sender="ICD")

    def _get_coefficient(self, group: ICDGroup, index: int) -> int:
        """从序列中获取系数，支持循环或末位保持"""
        if not group.sequence:
            return 1
        
        # 逻辑: 大于序列长度时，循环读取? 还是保持末位?
        # 文档: "大于序列上限的攻击都使用序列最末尾的系数" -> ❌ 这通常是针对特殊序列
        # 标准默认组: [1,0,0] 实际上是循环的 100100100
        # 为了通用性，我们采用模运算循环 (Default行为)
        # 但对于特殊序列 (如 Collei)，我们需要明确定义。
        # 现阶段采用模运算循环，符合绝大多数 "3 hit" 规则。
        seq_idx = index % len(group.sequence)
        return group.sequence[seq_idx]

    def reset(self, attacker: Any = None, tag: Optional[str] = None):
        """手动重置状态"""
        if attacker and tag:
            key = (id(attacker), tag)
            if key in self.records: del self.records[key]
        elif not attacker and not tag:
            self.records.clear()
