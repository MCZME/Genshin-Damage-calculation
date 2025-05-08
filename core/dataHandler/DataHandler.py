import json

from core.dataHandler.DataCompression import OptimizedData

total_frame_data = {}

def clear_data():
    total_frame_data.clear()

def send_to_handler(frame, data:dict):
    if frame == 0:
        return
    if frame not in total_frame_data:
        total_frame_data[frame] = {
            'character':{},
            'target':{},
            'object':[],
            'event':[]
        }
        
    for k in data.keys():
        if k == 'event':
            handel_event(frame,data[k])
        else:
            total_frame_data[frame][k] = data[k]

def send_to_window(data_type):
    if data_type == 'damage':
        return generate_damage_report()
    elif data_type == 'character':
        return generate_character_report()
    elif data_type == 'target':
        return generate_target_report()
    elif data_type == 'object':
        return generate_object_report()

def handel_event(frame, event):
    from core.Event import EventType
    
    if event['type'] == EventType.AFTER_DAMAGE:
        _handle_damage_event(frame, event['damage'])
    
    handler_key = event['type'].name
    if handler_key in _event_handlers:
        event_data = _event_handlers[handler_key](frame, event)
        total_frame_data[frame]['event'].append(event_data)

def _handle_character_switch(frame, event):
    return {
        'type': 'character_switch',
        'old_character': event['old_character'].name,
        'new_character': event['new_character'].name
    }

def _handle_nightsoul_blessing(frame, event):
    return {
        'type': 'nightsoul_blessing',
        'character': event['character'].name
    }

def _handle_normal_attack(frame, event):
    return {
        'type': 'normal_attack',
        'character': event['character'].name,
        'segment': event['segment']
    }

def _handle_plunging_attack(frame, event):
    return {
        'type': 'plunging_attack',
        'character': event['character'].name,
        'is_plunging_impact': event['is_plunging_impact']
    }

def _handle_elemental_reaction(frame, event):
    return {
        'type': 'elemental_reaction',
        'character': event['elementalReaction'].source.name,
        'target': event['elementalReaction'].target.name,
        'reaction': event['elementalReaction'].reaction_type[1].value
    }

def _handle_heal(frame, event):
    return {
        'type': 'heal',
        'character': event['healing'].source.name,
        'target': event['healing'].target.name,
        'amount': event['healing'].final_value
    }

def _handle_shield(frame, event):
    return {
        'type': 'shield',
        'character': event['character'].name,
        'shield': event['shield'].shield_value
    }

def _handle_damage_event(frame,data):
    damage_event = next((x for x in total_frame_data[frame]['event'] if x['type'] == 'damage_event'), None)
    if not damage_event:
        total_frame_data[frame]['event'].append({'type':'damage_event',
                                            'value':0,
                                            'damage':[]
                                            })
    d = next((x for x in total_frame_data[frame]['event'] if x['type'] == 'damage_event'), None)
    d['value'] += data.damage
    d['damage'].append({
        'name':data.name,
        'value':data.damage,
        'source':data.source.name,
        'target':data.target.name,
        'element':data.element[0],
        'type':data.damageType.value,
        'data':data.data,
        'panel':data.panel,
        'reaction': data.reaction_type[1].value if data.reaction_type else "",
    })

# 事件处理器映射表
_event_handlers = {
    'AFTER_CHARACTER_SWITCH': _handle_character_switch,
    'AFTER_NIGHTSOUL_BLESSING': _handle_nightsoul_blessing,
    'AFTER_NORMAL_ATTACK': _handle_normal_attack,
    'AFTER_CHARGED_ATTACK': lambda f,e: {'type':'charged_attack','character':e['character'].name},
    'AFTER_PLUNGING_ATTACK': _handle_plunging_attack,
    'AFTER_NIGHT_SOUL_CHANGE': lambda f,e: {'type':'nightsoul_change','character':e['character'].name,'amount':e['amount']},
    'AFTER_BURST': lambda f,e: {'type':'burst','character':e['character'].name},
    'AFTER_SKILL': lambda f,e: {'type':'skill','character':e['character'].name},
    'AFTER_HEALTH_CHANGE': lambda f,e: {'type':'health_change','character':e['character'].name,'amount':e['amount']},
    'AFTER_ELEMENTAL_REACTION': _handle_elemental_reaction,
    'AFTER_HEAL': _handle_heal,
    'AFTER_HURT': lambda f,e: {'type':'hurt','character':e['character'].name,'target':e['target'].name,'amount':e['amount']},
    'BEFORE_SHIELD_CREATION': _handle_shield,
    'AFTER_ENERGY_CHANGE': lambda f,e: {'type':'energy_change','character':e['character'].name,'amount':e['amount'],'is_fixed':e['is_fixed'],'is_alone':e['is_alone']},
    'OBJECT_CREATE': lambda f,e: {'type':'object_create','object':e['object'].name},
    'OBJECT_DESTROY': lambda f,e: {'type':'object_destroy','object':e['object'].name}
}

def generate_damage_report():
    d = {}
    for frame, value in total_frame_data.items():
        damage = {'type':'damage_event',
                  'value':0,
                  'damage':[]}
        event = next((x for x in value['event'] if x['type'] == 'damage_event'), None)
        if event:
            d[frame] = event
        else:
            d[frame] = damage

    return d

def generate_character_report():
    return {frame: value['character'] for frame, value in total_frame_data.items()}

def generate_target_report():
    return {frame: value['target'] for frame, value in total_frame_data.items()}

def generate_object_report():
    return {frame: value['object'] for frame, value in total_frame_data.items()}

def save_report(file_path, file_name):
    with open(file_path + file_name + '.json', 'w', encoding='utf-8') as f:
        json.dump(OptimizedData(total_frame_data), f)

