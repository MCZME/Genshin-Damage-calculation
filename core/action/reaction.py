from enum import Enum
from typing import Dict, Tuple, Optional, Any

class ElementalReactionType(Enum):
    VAPORIZE = '蒸发'
    MELT = '融化'
    OVERLOAD = '超载'
    ELECTRO_CHARGED = '感电'
    SUPERCONDUCT = '超导'
    SWIRL = '扩散'
    CRYSTALLIZE = '结晶'
    BURNING = '燃烧'
    BLOOM = '绽放'
    HYPERBLOOM = '超绽放'
    BURGEON = '烈绽放'
    QUICKEN = '原激化'
    AGGRAVATE = '超激化'
    SPREAD = '蔓激化'
    FREEZE = '冻结'
    SHATTER = '碎冰'

# 反应倍率映射: (Source, Target) -> (Type, Multiplier)
ReactionMMap: Dict[Tuple[str, str], Tuple[ElementalReactionType, float]] = {
            # 火系反应
            ('火', '水'): (ElementalReactionType.VAPORIZE, 1.5),
            ('水', '火'): (ElementalReactionType.VAPORIZE, 2.0),
            ('火', '冰'): (ElementalReactionType.MELT, 2.0),
            ('冰', '火'): (ElementalReactionType.MELT, 1.5),
            ('火', '雷'): (ElementalReactionType.OVERLOAD, 2.75),
            ('雷', '火'): (ElementalReactionType.OVERLOAD, 2.75),
            
            # 水系反应
            ('水', '雷'): (ElementalReactionType.ELECTRO_CHARGED, 2),
            ('雷', '水'): (ElementalReactionType.ELECTRO_CHARGED, 2),
            ('水', '冰'): (ElementalReactionType.FREEZE, 0),
            ('冰', '水'): (ElementalReactionType.FREEZE, 0),
            
            # 冰系反应
            ('冰', '雷'): (ElementalReactionType.SUPERCONDUCT, 1.5),
            ('雷', '冰'): (ElementalReactionType.SUPERCONDUCT, 1.5),
            
            # 风系扩散
            ('风', '火'): (ElementalReactionType.SWIRL, 0.6),
            ('风', '水'): (ElementalReactionType.SWIRL, 0.6),
            ('风', '雷'): (ElementalReactionType.SWIRL, 0.6),
            ('风', '冰'): (ElementalReactionType.SWIRL, 0.6),
            
            # 岩系结晶
            ('岩', '火'): (ElementalReactionType.CRYSTALLIZE, 0),
            ('岩', '水'): (ElementalReactionType.CRYSTALLIZE, 0),
            ('岩', '雷'): (ElementalReactionType.CRYSTALLIZE, 0),
            ('岩', '冰'): (ElementalReactionType.CRYSTALLIZE, 0),
            
            # 草系反应
            ('草', '火'): (ElementalReactionType.BURNING, 0.25),
            ('火', '草'): (ElementalReactionType.BURNING, 0.25),
            ('草', '水'): (ElementalReactionType.BLOOM, 2.0),
            ('水', '草'): (ElementalReactionType.BLOOM, 2.0),
            ('雷', '原'): (ElementalReactionType.HYPERBLOOM, 3),
            ('火', '原'): (ElementalReactionType.BURGEON, 3),
            ('草', '雷'): (ElementalReactionType.QUICKEN, 0),
            ('雷', '草'): (ElementalReactionType.QUICKEN, 0),
            ('草', '激'): (ElementalReactionType.SPREAD, 1.25),
            ('雷', '激'): (ElementalReactionType.AGGRAVATE, 1.15),
            ('水', '激'): (ElementalReactionType.BLOOM, 2.0),
            ('火', '激'): (ElementalReactionType.BURNING, 0.25),

            # 冻元素反应
            ('火', '冻'): (ElementalReactionType.MELT, 2.0),
            ('雷', '冻'): (ElementalReactionType.SUPERCONDUCT, 1.5),
            ('风', '冻'): (ElementalReactionType.SWIRL, 0.6),
            ('岩', '冻'): (ElementalReactionType.SHATTER, 3),
}

from core.tool import get_reaction_multiplier

class ElementalReaction:
    def __init__(self, damage):
        self.source = damage.source
        self.damage = damage
        self.reaction_type = None
        self.reaction_multiplier = None
        self.lv_multiplier = None
        self.target = damage.target
        self.source_element = None
        self.target_element = None

    def set_reaction_elements(self, source_element, target_element):
        self.source_element = source_element
        self.target_element = target_element
    
    def setReaction(self, reaction_type, reaction_multiplier):
        if reaction_type in [ElementalReactionType.VAPORIZE, ElementalReactionType.MELT]:
            self.reaction_type = ('增幅反应', reaction_type)
        elif reaction_type in [ElementalReactionType.OVERLOAD, ElementalReactionType.ELECTRO_CHARGED,
                                ElementalReactionType.SUPERCONDUCT, ElementalReactionType.SWIRL, ElementalReactionType.CRYSTALLIZE,
                                ElementalReactionType.FREEZE, ElementalReactionType.SHATTER, ElementalReactionType.BURNING,
                                ElementalReactionType.BLOOM, ElementalReactionType.HYPERBLOOM, ElementalReactionType.BURGEON]:
            self.reaction_type = ('剧变反应', reaction_type)
            self.lv_multiplier = get_reaction_multiplier(self.source.level)
        elif reaction_type in [ElementalReactionType.QUICKEN, ElementalReactionType.AGGRAVATE, ElementalReactionType.SPREAD]:
            self.reaction_type = ('激化反应', reaction_type)
            self.lv_multiplier = get_reaction_multiplier(self.source.level)
        self.reaction_multiplier = reaction_multiplier
