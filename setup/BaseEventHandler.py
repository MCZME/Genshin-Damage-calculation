from Emulation import Emulation
from setup.Event import EnergyChargeEvent, EventBus, EventHandler, EventType, GameEvent
from setup.Team import Team
from setup.Tool import GetCurrentTime


class NightsoulBurstEventHandler(EventHandler):
    '''夜魂迸发事件处理类'''
    def __init__(self):
        super().__init__()
        self.last_nightsoul_burst_time = -9999
        self.NATLAN_character = 0
        self.triggerInterval = [9,12,18][self.NATLAN_character-1]*60
        
        EventBus.subscribe(EventType.AFTER_DAMAGE, self)

    def handle_event(self, event):
        if event.event_type == EventType.AFTER_DAMAGE:
            if event.data['character'].association == '纳塔' and event.data['damage'].element[0] != '物理':
                if event.frame - self.last_nightsoul_burst_time > self.triggerInterval:
                    for i in Emulation.team.team:
                        if i.association == '纳塔':
                            self.NATLAN_character += 1
                    self.last_nightsoul_burst_time = event.frame
                    NightsoulBurstEvent = GameEvent(EventType.NightsoulBurst, event.frame,character=event.data['character'])
                    EventBus.publish(NightsoulBurstEvent)

class ElementalEnergyEventHandler(EventHandler):
    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_ENERGY_CHANGE:
            amount = event.data['amount']
            l = len(Team.team)
            for character in Team.team:
                ee = character.elemental_energy
                if character.on_field:
                    team_rate = 1.0
                elif l == 2:
                    team_rate = 0.8
                elif l == 3:
                    team_rate = 0.7
                else:
                    team_rate = 0.6

                if ee.elemental_energy[0] == amount[0]:
                    element_rate = 1.5
                elif amount[0] == '无':
                    element_rate = 1.0
                else:
                    element_rate = 0.5
                emergy_rate = character.attributePanel['元素充能效率']/100
                emergy_value = amount[1] * team_rate * element_rate * emergy_rate
                emergy_value = min(emergy_value, ee.elemental_energy[1])
                ee.current_energy += emergy_value
                print(f'🔋 {character.name}恢复{emergy_value:.2f}点元素能量')
                e_event = EnergyChargeEvent(character, (amount[0],emergy_value), GetCurrentTime(),before=False)
                EventBus.publish(e_event)
                
