from enum import Enum
from typing import Any, Dict, Optional, Tuple, Union
from core.mechanics.aura import Element
from core.action.action_data import AttackConfig

class DamageType(Enum):
    NORMAL = "普通攻击"
    CHARGED = "重击"
    SKILL = "元素战技"
    BURST = "元素爆发"
    PLUNGING = "下落攻击"
    REACTION = "剧变反应"

class Damage:
    """
    伤害/攻击对象。
    封装了攻击契约 (AttackConfig) 与实时计算结果。
    """
    def __init__(self, 
                 damage_multiplier: Any, 
                 element: Tuple[Element, float], 
                 damage_type: DamageType, 
                 name: str,
                 config: Optional[AttackConfig] = None,
                 **kwargs):
        self.name = name
        self.damage_multiplier = damage_multiplier
        self.damage_type = damage_type
        
        # 1. 核心契约 (如果未传入，则创建一个默认配置)
        self.config = config or AttackConfig()
        
        # 2. 元素信息 (同步初始 U 值到 config)
        self.element = element 
        if element:
            self.config.element_u = element[1]

        # 3. 运行状态
        self.damage: float = 0.0
        self.base_value: Union[str, Tuple[str, str]] = '攻击力'
        self.panel: Dict[str, Any] = {}
        self.data: Dict[str, Any] = kwargs
        
        self.source = None
        self.target = None
        
        # 反应相关数据 (由反应系统填充)
        self.reaction_results: List[Any] = []

    def set_source(self, source):
        self.source = source

    def set_target(self, target):
        self.target = target

    def set_base_value(self, base_value):
        self.base_value = base_value

    def add_data(self, key: str, value: Any):
        self.data[key] = value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "damage": round(self.damage, 2),
            "element": self.element[0].name if self.element else "None",
            "type": self.damage_type.value
        }
