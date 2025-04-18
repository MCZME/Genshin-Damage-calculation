from Emulation import Emulation
from core.calculation.DamageCalculation import Damage, DamageType
from core.DataHandler import send_to_handler
from core.effect.BaseEffect import ElectroChargedEffect, ResistanceDebuffEffect
from core.Event import DamageEvent, EnergyChargeEvent, EventBus, EventHandler, EventType, GameEvent
from core.Team import Team
from core.Tool import GetCurrentTime
from core.Logger import get_emulation_logger


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
                        'max_duration':e.max_duration,
                        'msg':e.msg} for e in character.active_effects},
                    'elemental_energy': {'element':character.elemental_energy.elemental_energy[0],
                                        'max_energy':character.elemental_energy.elemental_energy[1],
                                        'energy':character.elemental_energy.current_energy},
                    }
            target_data = {}
            target_data['name'] = Emulation.target.name
            target_data['effect'] = {e.name:{
                        'duration':e.duration,
                        'max_duration':e.max_duration,} for e in Emulation.target.effects}
            target_data['defense'] = Emulation.target.defense
            target_data['elemental_aura'] = [{'element':e['element'],'amount':e['current_amount']} for e in Emulation.target.aura.elementalAura]
            target_data['resistance'] = Emulation.target.current_resistance.copy()

            send_to_handler(event.frame, {'character':character_data, 'target':target_data})

class NightsoulBurstEventHandler(EventHandler):
    '''夜魂迸发事件处理类'''
    def __init__(self):
        super().__init__()
        self.last_nightsoul_burst_time = -9999
        
        EventBus.subscribe(EventType.AFTER_DAMAGE, self)

    def handle_event(self, event):
        if event.event_type == EventType.AFTER_DAMAGE:
            if event.data['character'].association == '纳塔' and event.data['damage'].element[0] != '物理':
                NATLAN_character = 0
                for i in Emulation.team.team:
                        if i.association == '纳塔':
                            NATLAN_character += 1
                self.triggerInterval = [18,12,9][NATLAN_character-1]*60
                if event.frame - self.last_nightsoul_burst_time > self.triggerInterval:
                    self.last_nightsoul_burst_time = event.frame
                    get_emulation_logger().log_effect('触发夜魂迸发')
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

class ReactionsEventHandler(EventHandler):
    def handle_event(self, event):
        self.amplifying(event)
        self.transformative(event)

    def amplifying(self, event):
        if event.event_type == EventType.BEFORE_MELT:
            EventBus.publish(GameEvent(EventType.AFTER_MELT, event.frame,elementalReaction=event.data['elementalReaction']))
        elif event.event_type == EventType.BEFORE_VAPORIZE:
            EventBus.publish(GameEvent(EventType.AFTER_VAPORIZE, event.frame,elementalReaction=event.data['elementalReaction']))

    def transformative(self, event):
        e = event.data['elementalReaction']
        if event.event_type == EventType.BEFORE_OVERLOAD:
            damage = Damage(0,('火',0),DamageType.REACTION, '超载')
            damage.reaction_type = e.damage.reaction_type
            damage.setPanel("等级系数", e.damage.reaction_data['等级系数'])
            damage.setPanel("反应系数", e.damage.reaction_data['反应系数'])
            EventBus.publish(DamageEvent(e.damage.source,e.damage.target,damage,GetCurrentTime()))
            EventBus.publish(GameEvent(EventType.AFTER_OVERLOAD, event.frame,elementalReaction=e))
        elif event.event_type == EventType.BEFORE_SUPERCONDUCT:
            damage = Damage(0,('冰',0),DamageType.REACTION, '超导')
            damage.reaction_type = e.damage.reaction_type
            damage.setPanel("等级系数", e.damage.reaction_data['等级系数'])
            damage.setPanel("反应系数", e.damage.reaction_data['反应系数'])
            EventBus.publish(DamageEvent(e.damage.source,e.damage.target,damage,GetCurrentTime()))
            ResistanceDebuffEffect('超导',e.damage.source,e.damage.target,'物理',40,12*60).apply()
            EventBus.publish(GameEvent(EventType.AFTER_SUPERCONDUCT, event.frame,elementalReaction=e))
        elif event.event_type == EventType.BEFORE_ELECTRO_CHARGED:
            damage = Damage(0,('雷',0),DamageType.REACTION, '感电')
            damage.reaction_type = e.damage.reaction_type
            damage.setPanel("等级系数", e.damage.reaction_data['等级系数'])
            damage.setPanel("反应系数", e.damage.reaction_data['反应系数'])
            ElectroChargedEffect(e.damage.source,e.damage.target,damage).apply()
            EventBus.publish(GameEvent(EventType.AFTER_ELECTRO_CHARGED, event.frame,elementalReaction=e))
        elif event.event_type == EventType.BEFORE_SWIRL:
            damage = Damage(0,(e.target_element,0),DamageType.REACTION, '扩散')
            damage.reaction_type = e.damage.reaction_type
            damage.setPanel("等级系数", e.damage.reaction_data['等级系数'])
            damage.setPanel("反应系数", e.damage.reaction_data['反应系数'])
            EventBus.publish(DamageEvent(e.damage.source,e.damage.target,damage,GetCurrentTime()))
            EventBus.publish(GameEvent(EventType.AFTER_SWIRL, event.frame,elementalReaction=e))

