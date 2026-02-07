from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

class ActionState(Enum):
    IDLE = auto()
    STARTUP = auto()
    EXECUTING = auto()
    RECOVERY = auto()
    END = auto()

class StrikeType(Enum):
    """打击类型：决定与特定实体或反应的交互（如碎冰）"""
    DEFAULT = auto()
    BLUNT = auto()      # 钝击 (用于破盾/碎冰)
    SLASH = auto()      # 斩击
    PIERCE = auto()     # 穿刺

class AOEShape(Enum):
    SINGLE = auto()     # 单体
    CIRCLE = auto()     # 圆形
    SECTOR = auto()     # 扇形
    RECT = auto()       # 矩形

@dataclass
class HitboxConfig:
    """物理碰撞配置"""
    shape: AOEShape = AOEShape.SINGLE
    radius: float = 0.0
    angle: float = 0.0  # 扇形夹角
    offset: Tuple[float, float, float] = (0.0, 0.0, 0.0) # 相对施法者的偏移

@dataclass
class AttackConfig:
    """
    攻击契约 DTO。
    定义了这一击的逻辑属性，不随实时属性变化。
    """
    # 元素属性
    element_u: float = 1.0           # 元素量 (1U, 2U等)
    
    # ICD (元素附着冷却) 控制
    icd_tag: str = "Default"         # ICD 标签 (如 "NormalAttack")
    icd_sequence: Optional[int] = None # 特殊 ICD 序列索引
    
    # 逻辑标签
    strike_type: StrikeType = StrikeType.DEFAULT
    is_deployable: bool = False      # 是否能触发部署物逻辑 (如生成草原核)
    is_ranged: bool = False          # 是否为远程攻击
    
    # 物理配置
    hitbox: HitboxConfig = field(default_factory=HitboxConfig)

@dataclass
class ActionFrameData:
    """动作帧数据元数据"""
    name: str
    total_frames: int
    hit_frames: List[int] = field(default_factory=list)
    cancel_windows: Dict[str, int] = field(default_factory=dict)
    
    # 关联的攻击契约 (可选，部分动作如 Dash 没有攻击契约)
    attack_config: Optional[AttackConfig] = None
    
    # 位移参数
    horizontal_dist: float = 0.0
    vertical_dist: float = 0.0