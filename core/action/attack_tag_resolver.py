from typing import Sequence, Optional

class AttackTagResolver:
    """
    [V2.5] 攻击标签判定器：仅针对普通攻击序列执行语义归约。
    提供剧变反应判定与标准标签判定功能。
    """
    
    # 极简归约映射表：仅处理普通攻击的连段标签
    _STRICT_MAP = {
        "普通攻击1": "普通攻击",
        "普通攻击2": "普通攻击",
        "普通攻击3": "普通攻击",
        "普通攻击4": "普通攻击",
        "普通攻击5": "普通攻击",
        "普通攻击6": "普通攻击",
    }

    # 剧变反应物理标签全集 (基于 V2.5 规范)
    TRANSFORMATIVE_TAGS = {
        "超导伤害",
        "自身扩散火伤害", "自身扩散水伤害", "自身扩散雷伤害", "自身扩散冰伤害",
        "扩散火伤害", "扩散水伤害", "扩散雷伤害", "扩散冰伤害",
        "碎冰伤害",
        "超载伤害",
        "感电伤害",
        "燃烧伤害",
        "撞击伤害",
        "绽放伤害",
        "烈绽放伤害",
        "超绽放伤害",
        "另类绽放伤害"
    }

    @staticmethod
    def check(target_tag: str, main_tag: str, extra_tags: Optional[Sequence[str]] = None) -> bool:
        """
        判断目标标准标签 (target_tag) 是否匹配输入的原始标签集。
        """
        if AttackTagResolver._STRICT_MAP.get(main_tag, main_tag) == target_tag:
            return True
            
        if extra_tags:
            for tag in extra_tags:
                if AttackTagResolver._STRICT_MAP.get(tag, tag) == target_tag:
                    return True
                    
        return False

    @staticmethod
    def is_transformative(main_tag: str, extra_tags: Optional[Sequence[str]] = None) -> bool:
        """
        判断当前伤害是否属于剧变反应路径。
        用于 DamagePipeline Stage 5 的公式路由决策。
        """
        if main_tag in AttackTagResolver.TRANSFORMATIVE_TAGS:
            return True
            
        if extra_tags:
            for tag in extra_tags:
                if tag in AttackTagResolver.TRANSFORMATIVE_TAGS:
                    return True
        return False
