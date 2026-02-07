from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any, Dict

class ReactionCategory(Enum):
    """反应类别，决定了系统如何应用该反应"""
    AMPLIFYING = auto()      # 增幅类 (蒸发, 融化) -> 乘法加成
    ADDITIVE = auto()        # 加算类 (超激化, 蔓激化) -> 基础伤害加成
    TRANSFORMATIVE = auto()  # 剧变类 (超载, 感电, 超导, 扩散, 碎冰, 绽放等) -> 独立伤害
    STATUS = auto()          # 状态类 (冻结, 结晶, 燃烧) -> 改变目标状态或生成对象

class ElementalReactionType(Enum):
    """具体反应类型映射"""
    VAPORIZE = "蒸发"
    MELT = "融化"
    OVERLOAD = "超载"
    ELECTRO_CHARGED = "感电"
    SUPERCONDUCT = "超导"
    SWIRL = "扩散"
    CRYSTALLIZE = "结晶"
    BURNING = "燃烧"
    BLOOM = "绽放"
    HYPERBLOOM = "超绽放"
    BURGEON = "烈绽放"
    QUICKEN = "原激化"
    AGGRAVATE = "超激化"
    SPREAD = "蔓激化"
    FREEZE = "冻结"
    SHATTER = "碎冰"

@dataclass
class ReactionResult:
    """
    描述一次反应的结果。
    由 NewAuraManager 产出，供 ReactionSystem 消费。
    """
    reaction_type: ElementalReactionType
    category: ReactionCategory
    source_element: Any  # 攻击元素 (Element Enum)
    target_element: Any  # 目标附着元素 (Element Enum)
    
    # 数值负载
    multiplier: float = 1.0      # 针对增幅类的基础倍率 (1.5/2.0)
    gauge_consumed: float = 0.0  # 消耗掉的附着元素量 (GU)
    
    # 扩展数据 (用于剧变反应工厂或特殊效果)
    data: Dict[str, Any] = field(default_factory=dict)

# 反应类别映射表
REACTION_CLASSIFICATION: Dict[ElementalReactionType, ReactionCategory] = {
    ElementalReactionType.VAPORIZE: ReactionCategory.AMPLIFYING,
    ElementalReactionType.MELT: ReactionCategory.AMPLIFYING,
    
    ElementalReactionType.AGGRAVATE: ReactionCategory.ADDITIVE,
    ElementalReactionType.SPREAD: ReactionCategory.ADDITIVE,
    
    ElementalReactionType.OVERLOAD: ReactionCategory.TRANSFORMATIVE,
    ElementalReactionType.ELECTRO_CHARGED: ReactionCategory.TRANSFORMATIVE,
    ElementalReactionType.SUPERCONDUCT: ReactionCategory.TRANSFORMATIVE,
    ElementalReactionType.SWIRL: ReactionCategory.TRANSFORMATIVE,
    ElementalReactionType.SHATTER: ReactionCategory.TRANSFORMATIVE,
    ElementalReactionType.BLOOM: ReactionCategory.TRANSFORMATIVE,
    ElementalReactionType.HYPERBLOOM: ReactionCategory.TRANSFORMATIVE,
    ElementalReactionType.BURGEON: ReactionCategory.TRANSFORMATIVE,
    
    ElementalReactionType.FREEZE: ReactionCategory.STATUS,
    ElementalReactionType.QUICKEN: ReactionCategory.STATUS,
    ElementalReactionType.BURNING: ReactionCategory.STATUS,
    ElementalReactionType.CRYSTALLIZE: ReactionCategory.STATUS,
}

