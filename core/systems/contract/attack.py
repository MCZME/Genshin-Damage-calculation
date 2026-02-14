from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Tuple

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
    # [核心] 标签系统
    attack_tag: str = ""               # 唯一主标签 (如 "普通攻击1")
    extra_attack_tags: List[str] = field(default_factory=list) # 额外辅助标签
    
    icd_tag: str = "Default"           # 附着规则标签
    icd_group: str = "Default"         # 共享冷却组 ID
    
    strike_type: StrikeType = StrikeType.DEFAULT
    is_deployable: bool = False        # 是否产生攻击实体
    is_ranged: bool = False
    
    hitbox: HitboxConfig = field(default_factory=HitboxConfig)
