from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple


class ActionState(Enum):
    """动作执行的物理状态。"""
    IDLE = auto()      # 空闲
    STARTUP = auto()   # 前摇
    EXECUTING = auto() # 执行中 (伤害发生)
    RECOVERY = auto()  # 后摇
    END = auto()       # 结束


class StrikeType(Enum):
    """打击类型：决定与特定实体或反应的物理交互。"""
    DEFAULT = auto()
    PIERCE = auto()     # 穿刺 (弓箭)
    BLUNT = auto()      # 钝击 (重剑/爆炸)
    THRUST = auto()     # 突刺 (长枪)
    SLASH = auto()      # 切割 (单手剑)


class AOEShape(Enum):
    """伤害范围形状定义。"""
    SINGLE = auto()     # 锁定单体
    SPHERE = auto()     # 球体
    CYLINDER = auto()   # 圆柱体 (XZ圆判定，Y高度判定)
    BOX = auto()        # 长方体


@dataclass
class HitboxConfig:
    """物理碰撞配置。"""
    shape: AOEShape = AOEShape.SINGLE
    radius: float = 0.0
    height: float = 0.0
    width: float = 0.0
    length: float = 0.0
    offset: Tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass
class AttackConfig:
    """
    攻击行为契约。
    定义了一次攻击的物理与元素本质。
    """
    element_u: float = 1.0
    icd_tag: str = "Default"      # 附着规则标签 (决定重置时间与序列)
    icd_group: str = "Default"    # 共享冷却组 ID (决定谁和谁共用计数器)
    
    strike_type: StrikeType = StrikeType.DEFAULT
    is_deployable: bool = False  # 是否能触发生成部署物 (如草原核)
    is_ranged: bool = False      # 是否为远程攻击
    
    hitbox: HitboxConfig = field(default_factory=HitboxConfig)


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
    
    描述了一个动作在时间轴上的完整特征，是仿真引擎驱动物理更新的核心依据。
    """
    name: str
    total_frames: int
    
    # 伤害触发时间点 (帧序列)
    hit_frames: List[int] = field(default_factory=list)
    
    # [核心] 中断窗口映射表
    # Key: 衔接动作类型 (如 "dash", "elemental_skill")
    # Value: 该动作最早可在第几帧被该衔接动作取消
    interrupt_frames: Dict[str, int] = field(default_factory=dict)
    
    # 物理位移相关
    horizontal_dist: float = 0.0  # 向前位移距离
    vertical_dist: float = 0.0    # 垂直位移 (下落攻击用)
    
    # 关联配置
    attack_config: Optional[AttackConfig] = None
    
    # 元数据标签 (如 "AERIAL", "IFRAME")
    tags: List[str] = field(default_factory=list)
    
    # 运行时绑定的源逻辑对象 (回调使用)
    origin_skill: Optional[Any] = None
