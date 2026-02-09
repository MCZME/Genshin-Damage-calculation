from typing import List, Dict
from core.systems.base_system import GameSystem
from core.context import EventEngine
from core.event import GameEvent, EventType, DamageEvent
from core.action.reaction import ReactionResult, ReactionCategory, ElementalReactionType
from core.action.damage import Damage, DamageType
from core.logger import get_emulation_logger
from core.tool import GetCurrentTime, get_reaction_multiplier
from core.effect.debuff import ResistanceDebuffEffect

class ReactionSystem(GameSystem):
    """
    重构后的元素反应系统 (策略分发引擎)
    负责将物理引擎 (AuraManager) 产出的反应结果转化为实际的游戏效果。
    """
    def __init__(self):
        super().__init__()
        self._target_reaction_cooldowns: Dict[int, Dict[ElementalReactionType, int]] = {}

    def register_events(self, engine: EventEngine):
        # 监听伤害流水线完成后的通知
        engine.subscribe(EventType.BEFORE_DAMAGE, self)

    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.BEFORE_DAMAGE:
            self._process_damage_reactions(event)

    def _process_damage_reactions(self, event: GameEvent):
        dmg: Damage = event.data['damage']
        # 修正点：直接从属性获取反应结果
        results: List[ReactionResult] = getattr(dmg, 'reaction_results', [])
        
        for res in results:
            self._apply_reaction_effect(event, res)

    def _apply_reaction_effect(self, event: GameEvent, res: ReactionResult):
        """核心分发器"""
        category = res.category
        get_emulation_logger().log_reaction(
            source_char=event.data['character'],
            reaction_type=res.reaction_type.value,
            target=event.data['target']
        )

        if category == ReactionCategory.TRANSFORMATIVE:
            self._handle_transformative(event, res)
        elif category == ReactionCategory.STATUS:
            self._handle_status_change(event, res)

    def _handle_transformative(self, event: GameEvent, res: ReactionResult):
        """处理剧变类反应：产生独立伤害"""
        source_char = event.data['character']
        target = event.data['target']
        
        level_mult = get_reaction_multiplier(source_char.level)
        
        reaction_multipliers = {
            ElementalReactionType.OVERLOAD: 2.75,
            ElementalReactionType.ELECTRO_CHARGED: 1.2,
            ElementalReactionType.SUPERCONDUCT: 0.5,
            ElementalReactionType.SWIRL: 0.6,
            ElementalReactionType.SHATTER: 1.5,
            ElementalReactionType.BLOOM: 2.0,
            ElementalReactionType.BURGEON: 3.0,
            ElementalReactionType.HYPERBLOOM: 3.0,
        }
        base_mult = reaction_multipliers.get(res.reaction_type, 1.0)
        
        react_dmg = Damage(
            damage_multiplier=0,
            element=(res.source_element, 0), 
            damage_type=DamageType.REACTION,
            name=res.reaction_type.value
        )
        
        # 修正点：使用 add_data 或直接赋值
        react_dmg.add_data("等级系数", level_mult)
        react_dmg.add_data("反应系数", base_mult)
        
        # 修正点：使用 DamageEvent 工厂方法发布
        self.engine.publish(DamageEvent(
            EventType.BEFORE_DAMAGE,
            GetCurrentTime(),
            source=source_char,
            target=target,
            damage=react_dmg
        ))

        if res.reaction_type == ElementalReactionType.SUPERCONDUCT:
            ResistanceDebuffEffect(target, "超导", ["物理"], 40, 12*60).apply()

    def _handle_status_change(self, event: GameEvent, res: ReactionResult):
        """处理状态类反应"""
        pass
