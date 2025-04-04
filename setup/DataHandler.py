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
            'event':[]
        }
        
    for k in data.keys():
        if k == 'event':
            total_frame_data[frame][k].append(data[k])
        else:
            total_frame_data[frame][k] = data[k] 

def send_to_window(type):
    if type == 'damage':
        return generate_damage_report()
    elif type == 'character':
        return generate_character_report()

def generate_damage_report():
    d = {}
    from setup.Event import EventType
    for frame in range(1,len(total_frame_data)+1):
        d[frame] = {'value':0, 'damage':[]}
        for event in total_frame_data[frame]['event']:
            if event['type'] == EventType.AFTER_DAMAGE:
                d[frame]['value'] += event['damage'].damage
                d[frame]['damage'].append({
                    'name':event['damage'].name,
                    'value':event['damage'].damage,
                    'source':event['damage'].source.name,
                    'target':event['damage'].target.name,
                    'element':event['damage'].element[0],
                    'type':event['damage'].damageType.value,
                    'data':event['damage'].data,
                    'panel':event['damage'].panel,
                    'reaction': event['damage'].reaction.reaction_type.value if event['damage'].reaction else "",
                })
    return d

def generate_character_report():
    c = {}
    for frame,value in total_frame_data.items():
        cc = {}
        for k in value['character'].keys():
            cc[k] = value['character'][k]
            cc[k]['effect'] = value['character'][k]['effect']
            cc[k]['elemental_energy'] = value['character'][k]['elemental_energy']
        c[frame] = cc
    return c
