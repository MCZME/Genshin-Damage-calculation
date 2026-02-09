from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional, Tuple

class ActionState(Enum):
    IDLE = auto()
    STARTUP = auto()
    EXECUTING = auto()
    RECOVERY = auto()
    END = auto()

class StrikeType(Enum):
    """
    打击类型：决定与特定实体或反应的交互。
    """
    DEFAULT = auto()    # 默认
    PIERCE = auto()     # 穿刺
    BLUNT = auto()      # 钝击 (重击/钝器)
    THRUST = auto()     # 突刺
    SLASH = auto()      # 切割

class AOEShape(Enum):
    """
    AOE 形状定义。
    """
    SINGLE = auto()     # 单体
    SPHERE = auto()     # 球体
    CYLINDER = auto()   # 圆柱体
    BOX = auto()        # 长方体

@dataclass
class HitboxConfig:
    """物理碰撞配置"""
    shape: AOEShape = AOEShape.SINGLE
    radius: float = 0.0 # 用于 SPHERE, CYLINDER
    height: float = 0.0 # 用于 CYLINDER, BOX (Y轴)
    width: float = 0.0  # 用于 BOX (X轴)
    length: float = 0.0 # 用于 BOX (Z轴)
    offset: Tuple[float, float, float] = (0.0, 0.0, 0.0) # 相对偏移

@dataclass
class AttackConfig:
    """
    攻击契约 DTO。
    """
    element_u: float = 1.0
    icd_tag: str = "Default"
    icd_sequence: Optional[int] = None
    
    strike_type: StrikeType = StrikeType.DEFAULT
    is_deployable: bool = False
    is_ranged: bool = False
    
    hitbox: HitboxConfig = field(default_factory=HitboxConfig)

@dataclass
class ActionCommand:
    """
    动作意图指令。
    贯穿 UI -> Parser -> Simulator -> Character 的统一载体。
    """
    character_name: str
    action_type: str  # e.g., "skill", "burst", "dash"
    params: Dict[str, Any] = field(default_factory=dict)
    
    # 可选：追踪ID，用于日志或伤害统计
    uuid: str = field(default_factory=lambda: str(id(object()))) 

@dataclass
class ActionFrameData:
    """动作帧数据元数据"""
    name: str
    total_frames: int
    hit_frames: List[int] = field(default_factory=list)
    cancel_windows: Dict[str, int] = field(default_factory=dict)
    attack_config: Optional[AttackConfig] = None
    horizontal_dist: float = 0.0
    vertical_dist: float = 0.0
    # 运行时绑定的技能对象 (用于回调 on_execute_hit 等)
    origin_skill: Optional[Any] = None
