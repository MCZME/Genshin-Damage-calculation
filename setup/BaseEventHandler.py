from Emulation import Emulation
from setup.DataHandler import send_to_handler
from setup.Event import EnergyChargeEvent, EventBus, EventHandler, EventType, GameEvent
from setup.Team import Team
from setup.Tool import GetCurrentTime
from setup.Logger import get_emulation_logger


class FrameEndEventHandler(EventHandler):
    '''帧结束事件处理类'''
    def handle_event(self, event):
        if event.event_type == EventType.FRAME_END:
            character_data = {}
            for character in Emulation.team.team:
                name = character.name
                character_data[name] = {
                    'maxHP': character.maxHP,
                    'currentHP': character.currentHP,
                    'level': character.level,
                    'skill_params': character.skill_params,
                    'constellation': character.constellation,
                    'panel': character.attributePanel.copy(),
                    'effect' : {e.name:{
                        'duration':e.duration,
                        'max_duration':e.max_duration,} for e in character.active_effects},
                    'elemental_energy': {'element':character.elemental_energy.elemental_energy[0],
                                        'max_energy':character.elemental_energy.elemental_energy[1],
                                        'energy':character.elemental_energy.current_energy},
                    }
            target_data = {}
            target_data['name'] = Emulation.target.name
            target_data['effect'] = Emulation.target.effects
            target_data['defense'] = Emulation.target.defense
            target_data['elemental_aura'] = Emulation.target.elementalAura
            target_data['resistance'] = Emulation.target.current_resistance

            send_to_handler(event.frame, {'character':character_data, 'target':target_data})

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
            
            if event.data['is_alone']:
                character = event.data['character']
                if event.data['is_fixed']:
                    emergy_value = min(amount[1], 
                                           character.elemental_energy.elemental_energy[1] -
                                           character.elemental_energy.current_energy)
                    character.elemental_energy.current_energy += emergy_value
                else:
                    rate = self.get_rate(character,amount[0])
                    emergy_value = amount[1] * rate[0] * rate[1] * rate[2]
                    emergy_value = min(emergy_value, 
                                           character.elemental_energy.elemental_energy[1] -
                                           character.elemental_energy.current_energy)
                    character.elemental_energy.current_energy += emergy_value
                get_emulation_logger().log_energy(character, emergy_value)
                e_event = EnergyChargeEvent(character, (amount[0],emergy_value),
                                            GetCurrentTime(),
                                            before=False,
                                            is_fixed=event.data['is_fixed'],
                                            is_alone=event.data['is_alone'])
                EventBus.publish(e_event) 
            else:
                for character in Team.team:
                    if event.data['is_fixed']:
                        character.elemental_energy.current_energy += amount[1]
                    else:
                        rate = self.get_rate(character,amount[0])
                        emergy_value = amount[1] * rate[0] * rate[1] * rate[2]
                        emergy_value = min(emergy_value, 
                                           character.elemental_energy.elemental_energy[1] -
                                           character.elemental_energy.current_energy)
                        character.elemental_energy.current_energy += emergy_value
                        get_emulation_logger().log_energy(character, emergy_value)
                    e_event = EnergyChargeEvent(character, (amount[0],emergy_value),
                                            GetCurrentTime(),
                                            before=False,
                                            is_fixed=event.data['is_fixed'],
                                            is_alone=event.data['is_alone'])
                    EventBus.publish(e_event) 
                
    def get_rate(self,character,element):
        l = len(Team.team)
        if character.on_field:
            team_rate = 1.0
        elif l == 2:
            team_rate = 0.8
        elif l == 3:
            team_rate = 0.7
        else:
            team_rate = 0.6

        if character.elemental_energy.elemental_energy[0] == element:
            element_rate = 1.5
        elif element == '无':
            element_rate = 1.0
        else:
            element_rate = 0.5
        emergy_rate = character.attributePanel['元素充能效率']/100
        
        return (team_rate,element_rate,emergy_rate)
