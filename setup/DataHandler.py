total_frame_data = {}

def clear_data():
    total_frame_data.clear()

def send_to_handler(frame, data:dict):
    if frame not in total_frame_data and frame > 0:
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
    for frame in range(1,len(total_frame_data)):
        d[frame] = 0
        for event in total_frame_data[frame]['event']:
            if event['type'] == EventType.AFTER_DAMAGE:
                d[frame] += event['damage'].damage
    return d

def generate_character_report():
    c = {}
    for frame,value in total_frame_data.items():
        cc = {}
        for k in value['character'].keys():
            cc[k] = value['character'][k]
            effects = {}
            for effect in value['character'][k]['effect']:
                effects[effect.name] = {
                    'duration':effect.duration,
                    'max_duration':effect.max_duration,
                }
            e = value['character'][k]['elemental_energy']
            elemental_energy = {'element':e.elemental_energy[0],
                                'max_energy':e.elemental_energy[1],
                                'energy':e.current_energy}
            cc[k]['effect'] = effects
            cc[k]['elemental_energy'] = elemental_energy
        c[frame] = cc
    return c
