from enum import Enum, auto
from typing import List, Set, Optional, Union

class AttackCategory(Enum):
    """攻击所属的高级分类。"""
    NORMAL = auto()
    CHARGED = auto()
    PLUNGING = auto()
    SKILL = auto()
    BURST = auto()
    REACTION = auto()
    ELEMENTAL = auto()  # 只要带元素都算
    PHYSICAL = auto()   # 纯物理

class AttackTagResolver:
    """
    负责解析攻击标签 (attack_tag) 并将其映射到逻辑分类。
    """
    
    @staticmethod
    def resolve_categories(main_tag: Union[str, AttackCategory], extra_tags: Optional[List[Union[str, AttackCategory]]] = None) -> Set[AttackCategory]:
        """
        根据标签列表解析出所属的分类集合。
        支持传入原生字符串标签或已解析的 AttackCategory 枚举。
        """
        raw_tags = [main_tag]
        if extra_tags:
            raw_tags.extend(extra_tags)
            
        categories: Set[AttackCategory] = set()
        
        for tag in raw_tags:
            if isinstance(tag, AttackCategory):
                categories.add(tag)
                continue
                
            # 字符串解析逻辑
            if not isinstance(tag, str):
                continue
                
            if "普通攻击" in tag: categories.add(AttackCategory.NORMAL)
            if "重击" in tag: categories.add(AttackCategory.CHARGED)
            if "下落攻击" in tag: categories.add(AttackCategory.PLUNGING)
            if "元素战技" in tag: categories.add(AttackCategory.SKILL)
            if "元素爆发" in tag: categories.add(AttackCategory.BURST)
            
        return categories
