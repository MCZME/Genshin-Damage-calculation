total_frame_data = {}

def send_to_handler(frame, data:dict):
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


def generate_damage_report():
    d = {}
    from setup.Event import EventType
    for frame in range(1,len(total_frame_data)):
        d[frame] = 0
        for event in total_frame_data[frame]['event']:
            if event['type'] == EventType.AFTER_DAMAGE:
                d[frame] += event['damage'].damage
    return d

