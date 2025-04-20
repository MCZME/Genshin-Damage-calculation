from enum import Enum
from core.Event import EventBus, EventHandler, EventType, ElementalReactionEvent, GameEvent
from core.Logger import get_emulation_logger
from core.Tool import GetCurrentTime, get_reaction_multiplier

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
    CATALYZE = '激化'
    FREEZE = '冻结'
    SHATTER = '碎冰'

ReactionMMap = {
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
            ('草', '水'): (ElementalReactionType.BLOOM, 2.0),

            # 冻元素反应
            ('火', '冻'): (ElementalReactionType.MELT, 2.0),
            ('雷', '冻'): (ElementalReactionType.SUPERCONDUCT, 1.5),
            ('风', '冻'): (ElementalReactionType.SWIRL, 0.6),
            ('岩', '冻'): (ElementalReactionType.SHATTER, 3),
            
        }

Reaction_to_EventType = {
    ElementalReactionType.VAPORIZE: EventType.BEFORE_VAPORIZE,
    ElementalReactionType.MELT: EventType.BEFORE_MELT,
    ElementalReactionType.OVERLOAD: EventType.BEFORE_OVERLOAD,
    ElementalReactionType.ELECTRO_CHARGED: EventType.BEFORE_ELECTRO_CHARGED,
    ElementalReactionType.SUPERCONDUCT: EventType.BEFORE_SUPERCONDUCT,
    ElementalReactionType.SWIRL: EventType.BEFORE_SWIRL,
    # ElementalReactionType.CRYSTALLIZE: EventType.BEFORE_CRYSTALLIZE,
    ElementalReactionType.BURNING: EventType.BEFORE_BURNING,
    # ElementalReactionType.BLOOM: EventType.BEFORE_BLOOM,
    # ElementalReactionType.HYPERBLOOM: EventType.BEFORE_HYPERBLOOM,
    # ElementalReactionType.BURGEON: EventType.BEFORE_BURGEON,
    ElementalReactionType.FREEZE: EventType.BEFORE_FREEZE,
    ElementalReactionType.SHATTER: EventType.BEFORE_SHATTER,
}

class ElementalReaction:
    def __init__(self,damage):
        self.source = damage.source
        self.damage = damage
        self.reaction_type = None
        self.reaction_multiplier = None
        self.lv_multiplier = None
        self.target = damage.target

    def set_reaction_elements(self, source_element, target_element):
        self.source_element = source_element
        self.target_element = target_element
    
    def setReaction(self, reaction_type, reaction_multiplier):
        if reaction_type in [ElementalReactionType.VAPORIZE,ElementalReactionType.MELT]:
            self.reaction_type = ('增幅反应', reaction_type)
        elif reaction_type in [ElementalReactionType.OVERLOAD,ElementalReactionType.ELECTRO_CHARGED,
                                ElementalReactionType.SUPERCONDUCT,ElementalReactionType.SWIRL,ElementalReactionType.BURGEON,
                                ElementalReactionType.CRYSTALLIZE,ElementalReactionType.FREEZE,ElementalReactionType.SHATTER]:
            self.reaction_type = ('剧变反应', reaction_type)
            self.lv_multiplier = get_reaction_multiplier(self.source.level)
        self.reaction_multiplier = reaction_multiplier

class ElementalReactionHandler(EventHandler):
    def handle_event(self, event: ElementalReactionEvent):
        if event.event_type == EventType.BEFORE_ELEMENTAL_REACTION:
            self._process_reaction(event)
            elemental_event = ElementalReactionEvent(event.data['elementalReaction'],GetCurrentTime(),before=False)
            EventBus.publish(elemental_event)
            get_emulation_logger().log_reaction(f"🔁{elemental_event.data['elementalReaction'].source.name}触发了 {elemental_event.data['elementalReaction'].reaction_type[1].value} 反应")

    def _process_reaction(self, event):
        '''处理元素反应的类型'''
        r = event.data['elementalReaction']
        r.setReaction(*ReactionMMap[(r.source_element, r.target_element)])
        r.damage.setReaction(r.reaction_type,{
                '等级系数': r.lv_multiplier,
                '反应系数': r.reaction_multiplier
            })
        if r.reaction_type[1] == ElementalReactionType.SWIRL:
            r.damage.reaction_data['目标元素'] = r.target_element

        eventType =  Reaction_to_EventType.get(r.reaction_type[1],None)
        if eventType:
            EventBus.publish(GameEvent(eventType,
                                    GetCurrentTime(),
                                    elementalReaction=r))
