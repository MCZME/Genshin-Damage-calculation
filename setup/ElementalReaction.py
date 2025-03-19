from enum import Enum, auto
from setup.Event import EventBus, EventHandler, EventType, ElementalReactionEvent
from setup.Tool import GetCurrentTime

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
        }

class ElementalReaction:
    def __init__(self,source, target_element, damage):
        self.source = source
        self.target_element = target_element
        self.damage = damage
        self.reaction_type = None
        self.reaction_ratio = None
        self.reaction_Type = None
    
    def setReaction(self, reaction_type, reaction_ratio):
        self.reaction_type = reaction_type
        self.reaction_ratio = reaction_ratio

class ElementalReactionHandler(EventHandler):
    def handle_event(self, event: ElementalReactionEvent):
        if event.event_type == EventType.BEFORE_ELEMENTAL_REACTION:
            self._process_reaction(event)
            elemental_event = ElementalReactionEvent(event.data['elementalReaction'],GetCurrentTime(),before=False)
            EventBus.publish(elemental_event)
            print(f"🔁{elemental_event.data['elementalReaction'].source.name}触发了{elemental_event.data['elementalReaction'].reaction_Type}反应")

    def _process_reaction(self, event):
        r = event.data['elementalReaction']
        r.setReaction(*ReactionMMap[(r.damage.element[0], r.target_element)])
        if r.reaction_type in [ElementalReactionType.VAPORIZE,ElementalReactionType.MELT]:
            r.reaction_Type = '增幅反应'

