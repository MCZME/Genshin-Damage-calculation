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
