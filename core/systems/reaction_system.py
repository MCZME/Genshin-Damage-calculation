from typing import Dict, Any
from core.systems.base_system import GameSystem
from core.context import EventEngine
from core.Event import (GameEvent, EventType, ElementalReactionEvent, DamageEvent)
from core.action.reaction import (ElementalReaction, ElementalReactionType, ReactionMMap)
from core.action.damage import Damage, DamageType
from core.Logger import get_emulation_logger
from core.Tool import GetCurrentTime
from core.effect.BaseEffect import (BurningEffect, ElectroChargedEffect, ResistanceDebuffEffect)
from core.entities.elemental_entities import DendroCoreObject

# 事件类型映射
Reaction_to_EventType = {
    ElementalReactionType.VAPORIZE: EventType.BEFORE_VAPORIZE,
    ElementalReactionType.MELT: EventType.BEFORE_MELT,
    ElementalReactionType.OVERLOAD: EventType.BEFORE_OVERLOAD,
    ElementalReactionType.ELECTRO_CHARGED: EventType.BEFORE_ELECTRO_CHARGED,
    ElementalReactionType.SUPERCONDUCT: EventType.BEFORE_SUPERCONDUCT,
    ElementalReactionType.SWIRL: EventType.BEFORE_SWIRL,
    ElementalReactionType.QUICKEN: EventType.BEFORE_QUICKEN,
    ElementalReactionType.AGGRAVATE: EventType.BEFORE_AGGRAVATE,
    ElementalReactionType.SPREAD: EventType.BEFORE_SPREAD,
    ElementalReactionType.BURNING: EventType.BEFORE_BURNING,
    ElementalReactionType.BLOOM: EventType.BEFORE_BLOOM,
    ElementalReactionType.HYPERBLOOM: EventType.BEFORE_HYPERBLOOM,
    ElementalReactionType.BURGEON: EventType.BEFORE_BURGEON,
    ElementalReactionType.FREEZE: EventType.BEFORE_FREEZE,
    ElementalReactionType.SHATTER: EventType.BEFORE_SHATTER,
    ElementalReactionType.CRYSTALLIZE: EventType.BEFORE_CRYSTALLIZE,
}

class ReactionSystem(GameSystem):
    def __init__(self):
        super().__init__()
        # 将静态状态转为实例状态
        self.last_bloom_time = 0
        self.bloom_count = -30

    def register_events(self, engine: EventEngine):
        # 基础反应处理
        engine.subscribe(EventType.BEFORE_ELEMENTAL_REACTION, self)
        
        # 订阅所有具体反应的前置事件
        for event_type in Reaction_to_EventType.values():
            engine.subscribe(event_type, self)
            
        # 结晶后置处理
        engine.subscribe(EventType.AFTER_CRYSTALLIZE, self)

    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.BEFORE_ELEMENTAL_REACTION:
            self._process_reaction_init(event)
        elif event.event_type == EventType.AFTER_CRYSTALLIZE:
            # 结晶特殊处理
            self.engine.publish(GameEvent(EventType.AFTER_CRYSTALLIZE, event.frame, elementalReaction=event.data['elementalReaction']))
        else:
            # 处理具体反应逻辑 (分发到 amplifying, transformative, catalyze)
            reaction = event.data.get('elementalReaction')
            if not reaction:
                return
                
            rtype_group = reaction.reaction_type[0]
            if rtype_group == '增幅反应':
                self.amplifying(event)
            elif rtype_group == '剧变反应':
                self.transformative(event)
            elif rtype_group == '激化反应':
                self.catalyze(event)

    def _process_reaction_init(self, event: ElementalReactionEvent):
        r = event.data['elementalReaction']
        reaction_info = ReactionMMap.get((r.source_element, r.target_element))
        if not reaction_info:
            return

        r.setReaction(*reaction_info)
        r.damage.setReaction(r.reaction_type, {
                '等级系数': r.lv_multiplier,
                '反应系数': r.reaction_multiplier
            })
        
        if r.reaction_type[1] in [ElementalReactionType.SWIRL, ElementalReactionType.CRYSTALLIZE]:
            r.damage.reaction_data['目标元素'] = r.target_element

        # 发布具体的反应前置事件 (如 BEFORE_VAPORIZE)
        next_event_type = Reaction_to_EventType.get(r.reaction_type[1])
        if next_event_type:
            self.engine.publish(GameEvent(next_event_type, GetCurrentTime(), elementalReaction=r))
            
        # 记录日志并发布反应后事件 (原有逻辑)
        elemental_event = ElementalReactionEvent(r, GetCurrentTime(), before=False)
        self.engine.publish(elemental_event)
        get_emulation_logger().log_reaction(f"🔁{r.source.name}触发了 {r.reaction_type[1].value} 反应")

    def amplifying(self, event):
        if event.event_type == EventType.BEFORE_MELT:
            self.engine.publish(GameEvent(EventType.AFTER_MELT, event.frame, elementalReaction=event.data['elementalReaction']))
        elif event.event_type == EventType.BEFORE_VAPORIZE:
            self.engine.publish(GameEvent(EventType.AFTER_VAPORIZE, event.frame, elementalReaction=event.data['elementalReaction']))

    def transformative(self, event):
        e = event.data['elementalReaction']
        damage_args = None
        
        # 构造剧变反应伤害对象
        if event.event_type == EventType.BEFORE_OVERLOAD:
            damage_args = (0, ('火', 0), DamageType.REACTION, '超载')
            after_type = EventType.AFTER_OVERLOAD
        elif event.event_type == EventType.BEFORE_SUPERCONDUCT:
            damage_args = (0, ('冰', 0), DamageType.REACTION, '超导')
            after_type = EventType.AFTER_SUPERCONDUCT
            ResistanceDebuffEffect('超导', e.damage.source, e.damage.target, ['物理'], 40, 12*60).apply()
        elif event.event_type == EventType.BEFORE_ELECTRO_CHARGED:
            damage_args = (0, ('雷', 0), DamageType.REACTION, '感电')
            after_type = EventType.AFTER_ELECTRO_CHARGED
            ElectroChargedEffect(e.damage.source, e.damage.target, Damage(*damage_args)).apply()
            # 感电比较特殊，伤害由 Effect 触发，这里可能不需要直接 publish damage
            damage_args = None 
        elif event.event_type == EventType.BEFORE_SWIRL:
            damage_args = (0, (e.target_element, 0), DamageType.REACTION, '扩散')
            after_type = EventType.AFTER_SWIRL
        elif event.event_type == EventType.BEFORE_FREEZE:
            after_type = EventType.AFTER_FREEZE
        elif event.event_type == EventType.BEFORE_SHATTER:
            damage_args = (0, ('冰', 0), DamageType.REACTION, '碎冰')
            after_type = EventType.AFTER_SHATTER
        elif event.event_type == EventType.BEFORE_BURNING:
            damage_args = (0, ('火', 1), DamageType.REACTION, '燃烧')
            after_type = EventType.AFTER_BURNING
            BurningEffect(e.source, e.target, Damage(*damage_args)).apply()
            damage_args = None
        elif event.event_type == EventType.BEFORE_BLOOM:
            damage_args = (0, ('草', 0), DamageType.REACTION, '绽放')
            after_type = EventType.AFTER_BLOOM
            DendroCoreObject(e.source, e.target, Damage(*damage_args)).apply()
            damage_args = None
        elif event.event_type == EventType.BEFORE_HYPERBLOOM:
            if GetCurrentTime() - self.last_bloom_time > 0.5*60:
                self.bloom_count = 0
            if self.bloom_count < 2:
                self.bloom_count += 1
                damage_args = (0, ('草', 0), DamageType.REACTION, '超绽放')
                self.last_bloom_time = GetCurrentTime()
            else:
                damage_args = None
            after_type = EventType.AFTER_HYPERBLOOM
        elif event.event_type == EventType.BEFORE_BURGEON:
            if GetCurrentTime() - self.last_bloom_time > 0.5*60:
                self.bloom_count = 0
            if self.bloom_count < 2:
                self.bloom_count += 1
                damage_args = (0, ('草', 0), DamageType.REACTION, '烈绽放')
                self.last_bloom_time = GetCurrentTime()
            else:
                damage_args = None
            after_type = EventType.AFTER_BURGEON
        else:
            return

        # 统一处理伤害发布
        if damage_args:
            damage = Damage(*damage_args)
            damage.reaction_type = e.damage.reaction_type
            damage.setPanel("等级系数", e.damage.reaction_data['等级系数'])
            damage.setPanel("反应系数", e.damage.reaction_data['反应系数'])
            self.engine.publish(DamageEvent(e.damage.source, e.damage.target, damage, GetCurrentTime()))

        self.engine.publish(GameEvent(after_type, event.frame, elementalReaction=e))

    def catalyze(self, event):
        e = event.data['elementalReaction']
        if event.event_type == EventType.BEFORE_QUICKEN:
            self.engine.publish(GameEvent(EventType.AFTER_QUICKEN, event.frame, elementalReaction=event.data['elementalReaction']))
        elif event.event_type == EventType.BEFORE_AGGRAVATE:
            e.damage.setPanel("等级系数", e.damage.reaction_data['等级系数'])
            e.damage.setPanel("反应系数", e.damage.reaction_data['反应系数'])
            self.engine.publish(GameEvent(EventType.AFTER_AGGRAVATE, event.frame, elementalReaction=event.data['elementalReaction']))
        elif event.event_type == EventType.BEFORE_SPREAD:
            e.damage.setPanel("等级系数", e.damage.reaction_data['等级系数'])
            e.damage.setPanel("反应系数", e.damage.reaction_data['反应系数'])
            self.engine.publish(GameEvent(EventType.AFTER_SPREAD, event.frame, elementalReaction=event.data['elementalReaction']))
