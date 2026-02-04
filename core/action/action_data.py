from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Dict, Optional

class ActionState(Enum):
    """动作状态机状态"""
    IDLE = auto()        # 空闲
    STARTUP = auto()     # 前摇 (不可取消)
    EXECUTING = auto()   # 执行中 (判定点可能在此阶段)
    RECOVERY = auto()    # 后摇 (通常可被取消)
    END = auto()         # 动作自然结束

@dataclass
class ActionFrameData:
    """
    动作帧数据元数据。
    定义了一个动作在时间轴上的关键特征。
    """
    name: str
    total_frames: int              # 自然结束的总帧数
    
    # 伤害判定点 (相对于动作开始的帧数)
    hit_frames: List[int] = field(default_factory=list)
    
    # 取消窗口: 当下一个动作类型满足条件时，最早可以中断当前动作的帧数
    # Key: 动作类型或 EventType (如 EventType.BEFORE_JUMP)
    # Value: 取消点帧数
    cancel_windows: Dict[str, int] = field(default_factory=dict)
    
    # 位移元数据 (用于特殊机制)
    horizontal_dist: float = 0.0
    vertical_dist: float = 0.0
    
    # 卡肉参数 (Hitlag)
    hitlag_frames: int = 0         # 产生的卡肉停顿帧数
    hitlag_extend_buffs: bool = True # 是否延长身上的 Buff
