from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional

# 重新导出搬迁后的物理契约，保持兼容性 (后续逐步清理)
from core.systems.contract.attack import StrikeType, AOEShape, HitboxConfig, AttackConfig

class ActionState(Enum):
    """动作执行的物理状态。"""
    IDLE = auto()      # 空闲
    STARTUP = auto()   # 前摇
    EXECUTING = auto() # 执行中 (伤害发生)
    RECOVERY = auto()  # 后摇
    END = auto()       # 结束

@dataclass
class ActionCommand:
    """
    动作意图指令。
    承载了从 UI 到角色的原始执行请求。
    """
    character_name: str
    action_type: str  # 例如: "normal_attack", "elemental_skill", "dash"
    params: Dict[str, Any] = field(default_factory=dict)
    uuid: str = field(default_factory=lambda: str(id(object())))

@dataclass
class ActionFrameData:
    """
    动作物理元数据。
    描述了一个动作在时间轴上的完整特征。
    """
    name: str
    total_frames: int
    
    action_type: str = "normal_attack" 
    combo_index: int = 0               
    
    hit_frames: List[int] = field(default_factory=list)
    interrupt_frames: Dict[str, int] = field(default_factory=dict)
    
    horizontal_dist: float = 0.0  
    vertical_dist: float = 0.0    
    
    attack_config: Optional[AttackConfig] = None
    tags: List[str] = field(default_factory=list)
    origin_skill: Optional[Any] = None
