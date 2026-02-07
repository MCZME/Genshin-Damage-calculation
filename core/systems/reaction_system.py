from typing import List, Dict, Any
from core.systems.base_system import GameSystem
from core.context import EventEngine
from core.event import GameEvent, EventType, DamageEvent
from core.action.reaction import ReactionResult, ReactionCategory, ElementalReactionType
from core.action.damage import Damage, DamageType
from core.logger import get_emulation_logger
from core.tool import GetCurrentTime, get_reaction_multiplier
from core.effect.elemental import BurningEffect, ElectroChargedEffect
from core.effect.debuff import ResistanceDebuffEffect

class ReactionSystem(GameSystem):
    """
    重构后的元素反应系统 (策略分发引擎)
    负责将物理引擎 (AuraManager) 产出的反应结果转化为实际的游戏效果。
    """
    def __init__(self):
        super().__init__()
        # 用于剧变反应的内置冷却 (ICD) 限制 (针对同一目标的同一反应)
        self._target_reaction_cooldowns: Dict[int, Dict[ElementalReactionType, int]] = {}

    def register_events(self, engine: EventEngine):
        # 监听伤害流水线完成后的通知
        engine.subscribe(EventType.BEFORE_DAMAGE, self)

    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.BEFORE_DAMAGE:
            self._process_damage_reactions(event)

    def _process_damage_reactions(self, event: GameEvent):
        dmg: Damage = event.data['damage']
        # 从 Damage DTO 中提取 Pipeline 存入的反应结果列表
        results: List[ReactionResult] = dmg.data.get('reaction_results', [])
        
        for res in results:
            self._apply_reaction_effect(event, res)

    def _apply_reaction_effect(self, event: GameEvent, res: ReactionResult):
        """核心分发器"""
        category = res.category
        
        # 1. 记录日志 (统一处理)
        get_emulation_logger().log_reaction(f"🔁 {event.data['character'].name} 触发了 {res.reaction_type.value} 反应")

        # 2. 根据类别执行应用逻辑
        if category == ReactionCategory.TRANSFORMATIVE:
            self._handle_transformative(event, res)
        elif category == ReactionCategory.STATUS:
            self._handle_status_change(event, res)
        
        # 注：AMPLIFYING 和 ADDITIVE 的数值加成已经在 DamagePipeline 中完成
        # 此处仅作为分发点，如需触发特定圣遗物效果可在此发布 AFTER_REACTION 事件

    def _handle_transformative(self, event: GameEvent, res: ReactionResult):
        """处理剧变类反应：产生独立伤害"""
        source_char = event.data['character']
        target = event.data['target']
        
        # 1. 计算剧变基础伤害
        # 公式: 等级系数 * 反应倍率 * (1 + 精通加成 + 反应特定加成)
        level_mult = get_reaction_multiplier(source_char.level)
        
        # 反应特定倍率表 (高等元素论)
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
        
        # 2. 构造剧变伤害 DTO
        # 剧变伤害固定为 REACTION 类型，且不继承原攻击的倍率
        src_el_val = res.source_element.value if hasattr(res.source_element, 'value') else str(res.source_element)
        react_dmg = Damage(
            damage_multiplier=0, # 剧变反应不直接使用此倍率，由 Pipeline 内部结算
            element=(src_el_val, 0), 
            damage_type=DamageType.REACTION,
            name=res.reaction_type.value
        )
        
        # 注入计算参数
        react_dmg.set_damage_data("等级系数", level_mult)
        react_dmg.set_damage_data("反应系数", base_mult)
        
        # 3. 发布剧变伤害事件
        # 修正传参顺序: (event_type, frame, source, target, damage)
        self.engine.publish(DamageEvent(
            EventType.BEFORE_DAMAGE,
            GetCurrentTime(),
            source=source_char,
            target=target,
            damage=react_dmg
        ))

        # 4. 触发特定副作用
        if res.reaction_type == ElementalReactionType.SUPERCONDUCT:
            # 超导：减物抗 40%，持续 12s (Target 是 Effect 的持有者)
            ResistanceDebuffEffect(target, "超导", ["物理"], 40, 12*60).apply()

    def _handle_status_change(self, event: GameEvent, res: ReactionResult):
        """处理状态类反应：冻结、结晶、燃烧、激化"""
        source_char = event.data['character']
        target = event.data['target']
        
        if res.reaction_type == ElementalReactionType.BURNING:
            # 启动燃烧跳字 Effect (TODO: 需要 Damage 对象支撑)
            pass
        elif res.reaction_type == ElementalReactionType.CRYSTALLIZE:
            # 生成结晶掉落物或直接给盾 (根据项目具体实现决定)
            pass
        elif res.reaction_type == ElementalReactionType.FREEZE:
            # 发布冻结事件
            pass