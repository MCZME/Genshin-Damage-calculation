"""月曜反应转换器模块。"""

from typing import Any

from core.systems.contract.reaction import (
    ElementalReactionType,
    ReactionCategory,
    ReactionResult,
)


class LunarConverter:
    """
    月曜反应转换器。

    负责判断是否可以将普通反应转换为月曜反应，
    并执行转换逻辑。
    """

    def __init__(self):
        self._lunar_system: Any = None

    def _get_lunar_system(self, context: Any) -> Any:
        """获取月曜系统实例。"""
        if self._lunar_system is None and context:
            from core.systems.lunar_system import LunarReactionSystem
            self._lunar_system = context.get_system(LunarReactionSystem)
        return self._lunar_system

    def try_convert(
        self,
        context: Any,
        source: Any,
        res: ReactionResult
    ) -> ReactionResult:
        """
        尝试将原反应转换为月曜反应。

        条件：
        1. 队伍中有对应触发角色
        2. 反应由角色触发（非敌人/环境）
        3. 元素组合匹配

        Args:
            context: 仿真上下文
            source: 反应触发源
            res: 原始反应结果

        Returns:
            转换后的反应结果（如果满足条件）或原始结果
        """
        # 检查是否为角色触发
        if not self._is_character_source(source):
            return res

        # 获取队伍成员
        team_members = self._get_team_members(context)

        # 绽放 → 月绽放
        if res.reaction_type == ElementalReactionType.BLOOM:
            if self._can_trigger_lunar_bloom(context, team_members):
                return self._convert_to_lunar_bloom(res, source)

        # 感电 → 月感电
        elif res.reaction_type == ElementalReactionType.ELECTRO_CHARGED:
            if self._can_trigger_lunar_charged(context, team_members):
                return self._convert_to_lunar_charged(res, source)

        # 结晶（水） → 月结晶
        elif res.reaction_type == ElementalReactionType.CRYSTALLIZE:
            from core.mechanics.aura import Element
            # 仅水元素结晶可转换
            if res.target_element == Element.HYDRO:
                if self._can_trigger_lunar_crystallize(context, team_members):
                    # 月结晶无冷却：即使普通结晶在冷却中，仍可触发月结晶
                    converted = self._convert_to_lunar_crystallize(res, source)
                    converted.is_cooldown_skipped = False
                    return converted

        return res

    def _is_character_source(self, source: Any) -> bool:
        """判定反应源是否为角色。"""
        from character.character import Character
        return isinstance(source, Character)

    def _get_team_members(self, context: Any) -> list[Any]:
        """获取当前队伍成员。"""
        if context and context.space and context.space.team:
            return context.space.team.get_members()
        return []

    def _can_trigger_lunar_bloom(self, context: Any, members: list[Any]) -> bool:
        """判定是否可触发月绽放。"""
        lunar_system = self._get_lunar_system(context)
        if lunar_system:
            return lunar_system.can_trigger_lunar_bloom(members)
        return False

    def _can_trigger_lunar_charged(self, context: Any, members: list[Any]) -> bool:
        """判定是否可触发月感电。"""
        lunar_system = self._get_lunar_system(context)
        if lunar_system:
            return lunar_system.can_trigger_lunar_charged(members)
        return False

    def _can_trigger_lunar_crystallize(self, context: Any, members: list[Any]) -> bool:
        """判定是否可触发月结晶。"""
        lunar_system = self._get_lunar_system(context)
        if lunar_system:
            return lunar_system.can_trigger_lunar_crystallize(members)
        return False

    def _convert_to_lunar_bloom(
        self,
        res: ReactionResult,
        source_char: Any
    ) -> ReactionResult:
        """将绽放转换为月绽放。"""
        return ReactionResult(
            reaction_type=ElementalReactionType.LUNAR_BLOOM,
            category=ReactionCategory.LUNAR,
            source_element=res.source_element,
            target_element=res.target_element,
            multiplier=res.multiplier,
            gauge_consumed=res.gauge_consumed,
            data={
                **res.data,
                "original_reaction": ElementalReactionType.BLOOM,
            }
        )

    def _convert_to_lunar_charged(
        self,
        res: ReactionResult,
        source_char: Any
    ) -> ReactionResult:
        """将感电转换为月感电。"""
        return ReactionResult(
            reaction_type=ElementalReactionType.LUNAR_CHARGED,
            category=ReactionCategory.LUNAR,
            source_element=res.source_element,
            target_element=res.target_element,
            multiplier=res.multiplier,
            gauge_consumed=res.gauge_consumed,
            data={
                **res.data,
                "original_reaction": ElementalReactionType.ELECTRO_CHARGED,
                "source_characters": [source_char],
            }
        )

    def _convert_to_lunar_crystallize(
        self,
        res: ReactionResult,
        source_char: Any
    ) -> ReactionResult:
        """将水结晶转换为月结晶。"""
        return ReactionResult(
            reaction_type=ElementalReactionType.LUNAR_CRYSTALLIZE,
            category=ReactionCategory.LUNAR,
            source_element=res.source_element,
            target_element=res.target_element,
            multiplier=res.multiplier,
            gauge_consumed=res.gauge_consumed,
            data={
                **res.data,
                "original_reaction": ElementalReactionType.CRYSTALLIZE,
                "source_characters": [source_char],
            }
        )
