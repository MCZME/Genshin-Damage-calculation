from core.event import EventHandler, EventType
from core.dataHandler.DataHandler import send_to_handler
from core.context import get_context

class FrameEndEventHandler(EventHandler):
    '''帧结束事件处理类'''
    def handle_event(self, event):
        if event.event_type == EventType.FRAME_END:
            try:
                ctx = get_context()
            except RuntimeError:
                return

            if not ctx.team:
                return

            character_data = {}
            for character in ctx.team.team:
                name = character.name
                character_data[name] = {
                    'weapon': {
                        'name': character.weapon.name if character.weapon else "None",
                        'level': character.weapon.level if character.weapon else 0,
                        'refinement': character.weapon.lv if character.weapon else 0,
                    },
                    'maxHP': character.maxHP,
                    'currentHP': character.currentHP,
                    'level': character.level,
                    'skill_params': [
                        getattr(character.NormalAttack, 'lv', 1), 
                        getattr(character.Skill, 'lv', 1), 
                        getattr(character.Burst, 'lv', 1)
                    ],
                    'constellation': character.constellation,
                    'panel': character.attributePanel.copy(),
                    'effect' : {e.name:{
                        'duration':e.duration,
                        'max_duration':e.max_duration,
                        'msg':getattr(e, 'msg', "")} for e in character.active_effects},
                    'elemental_energy': {
                        'element': character.elemental_energy.elemental_energy[0] if character.elemental_energy else "None",
                        'max_energy': character.elemental_energy.elemental_energy[1] if character.elemental_energy else 0,
                        'energy': character.elemental_energy.current_energy if character.elemental_energy else 0
                    },
                }
            
            # Target 数据收集
            if not ctx.target:
                return
                
            target_data = {}
            target_data['name'] = ctx.target.name
            target_data['effect'] = {e.name:{
                        'duration':e.duration,
                        'max_duration':e.max_duration,} for e in ctx.target.effects}
            target_data['defense'] = ctx.target.defense
            target_data['elemental_aura'] = [{'element':e['element'],'amount':e['current_amount']} for e in ctx.target.aura.elementalAura]
            if ctx.target.aura.burning_elements:
                target_data['elemental_aura'].append({'element':'燃','amount':ctx.target.aura.burning_elements['current_amount']})
            if ctx.target.aura.quicken_elements:
                target_data['elemental_aura'].append({'element':'激','amount':ctx.target.aura.quicken_elements['current_amount']})
            target_data['resistance'] = ctx.target.current_resistance.copy()

            # Object 数据收集
            object_data =  []
            for obj in ctx.team.active_objects:
                object_data.append({'name':obj.name,
                                    'current_frame':obj.current_frame,
                                    'life_frame':obj.life_frame})

            send_to_handler(event.frame, {'character':character_data, 'target':target_data, 'object':object_data})
