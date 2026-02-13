from dataclasses import dataclass
from typing import Optional, Any
from core.mechanics.aura import Element

@dataclass
class ShieldConfig:
    """
    护盾配置契约。
    """
    base_hp: float              # 基础护盾量
    element: Element            # 护盾元素类型 (影响吸收效率)
    duration: int               # 持续帧数
    name: str = "通用护盾"
    creator: Optional[Any] = None # 产生护盾的实体 (用于计算护盾强效)
