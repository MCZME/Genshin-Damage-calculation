from typing import List, Set


class AttackCategory:
    """逻辑增伤分类标签。"""

    NORMAL = "普通攻击"
    CHARGED = "重击"
    PLUNGING = "下落攻击"
    SKILL = "元素战技"
    BURST = "元素爆发"
    REACTION = "剧变反应"


class AttackTagResolver:
    """
    攻击标签解析器。
    负责根据 attack_tag 和 extra_tags 判定其所属的逻辑加成类别。
    """

    @staticmethod
    def is_normal_attack(tag: str) -> bool:
        # 匹配: 普通攻击1, 普通攻击2 ...
        return tag.startswith("普通攻击")

    @staticmethod
    def is_charged_attack(tag: str) -> bool:
        return tag.startswith("重击")

    @staticmethod
    def is_plunging_attack(tag: str) -> bool:
        return tag.startswith("下落攻击")

    @staticmethod
    def resolve_categories(tag: str, extra_tags: List[str] = None) -> Set[str]:
        """
        解析出该攻击所属的所有逻辑分类。
        """
        categories = set()
        extra = extra_tags or []

        # 1. 基础逻辑映射
        if tag.startswith("普通攻击") or "普通攻击" in extra:
            categories.add(AttackCategory.NORMAL)

        if tag.startswith("重击") or "重击" in extra:
            categories.add(AttackCategory.CHARGED)

        if tag.startswith("下落攻击") or "下落攻击" in extra:
            categories.add(AttackCategory.PLUNGING)

        if tag.startswith("元素战技") or "元素战技" in extra:
            categories.add(AttackCategory.SKILL)

        if tag.startswith("元素爆发") or "元素爆发" in extra:
            categories.add(AttackCategory.BURST)

        if tag == "剧变反应" or "剧变反应" in extra:
            categories.add(AttackCategory.REACTION)

        # 2. 特殊标签映射 (可根据需求扩展)
        # 某些召唤物可能被归类为战技
        summons_as_skill = ["乌瑟勋爵", "海薇玛夫人", "谢贝蕾妲小姐"]
        if any(s in tag for s in summons_as_skill):
            categories.add(AttackCategory.SKILL)

        return categories
