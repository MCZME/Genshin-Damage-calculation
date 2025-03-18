from Emulation import Emulation
from setup.Event import EventBus, EventHandler, EventType, GameEvent


class NightsoulBurstEventHandler(EventHandler):
    def __init__(self):
        super().__init__()
        self.last_nightsoul_burst_time = -9999
        self.NATLAN_character = 0
        self.triggerInterval = [18,12,9][self.NATLAN_character-1]*60
        
        EventBus.subscribe(EventType.BEFORE_DAMAGE, self)

    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_DAMAGE:
            if event.data['character'].association == '纳塔' and event.data['damage'].element[0] != '物理':
                if event.frame - self.last_nightsoul_burst_time > self.triggerInterval:
                    for i in Emulation.team.team:
                        if i.association == '纳塔':
                            self.NATLAN_character += 1
                    self.last_nightsoul_burst_time = event.frame
                    NightsoulBurstEvent = GameEvent(EventType.NightsoulBurst, event.frame,character=event.data['character'])
                    EventBus.publish(NightsoulBurstEvent)
