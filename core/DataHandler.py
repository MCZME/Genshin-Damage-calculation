import json


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
        'shield': event['shield'].shield
    }

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

def handel_event(frame, event):
    from core.Event import EventType
    
    if event['type'] == EventType.AFTER_DAMAGE:
        handle_damage_event(frame, event['damage'])
    
    handler_key = event['type'].name
    if handler_key in _event_handlers:
        event_data = _event_handlers[handler_key](frame, event)
        total_frame_data[frame]['event'].append(event_data)

def handle_damage_event(frame,data):
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
        json.dump(OptimizedData(), f)

# 键名缩短映射表(扩展更多常用字段)
_KEY_MAPPING = {
    'character': 'c',
    'target': 't', 
    'object': 'o',
    'event': 'e',
    'frame': 'f',
    'name': 'n',
    'value': 'v',
    'source': 's',
    'type': 'tp',
    'data': 'dt',
    'maxHP': 'mh',
    'currentHP': 'ch',
    'level': 'l',
    'skill_params': 'sp',
    'constellation': 'cn',
    'panel': 'p',
    'effect': 'ef',
    'elemental_energy': 'ee',
    'duration': 'd',
    'max_duration': 'md',
    'msg': 'm',
    'element': 'el',
    'max_energy': 'me',
    'energy': 'en',
    'damage': 'dmg',
    'reaction': 'rct'
}

def _round_floats(value):
    """对浮点数保留2位小数"""
    if isinstance(value, float):
        return round(value, 2)
    return value

def _shorten_keys(data):
    """优化后的键名缩短函数，同时处理数值精度"""
    if not isinstance(data, (dict, list)):
        return _round_floats(data)
        
    if isinstance(data, dict):
        # 只处理实际需要缩短的键，避免不必要的递归
        return {
            _KEY_MAPPING.get(k, k): _shorten_keys(_round_floats(v))
            for k, v in data.items()
        }
    
    # 列表处理保持简单
    return [
        _shorten_keys(_round_floats(item))
        for item in data
    ]

def _compare_character(current, previous):
    """比较角色数据增量变化，按角色名分别比较"""
    diff = {}
    # 检查新增或删除的角色
    all_chars = set(current.keys()) | set(previous.keys())
    
    for char_name in all_chars:
        curr_char = current.get(char_name, {})
        prev_char = previous.get(char_name, {})
        char_diff = {}
        
        # 比较基础属性
        for attr in ['mh', 'ch', 'l', 'sp', 'cn']:
            if curr_char.get(attr) != prev_char.get(attr):
                char_diff[attr] = curr_char.get(attr)
        
        # 比较面板属性
        if curr_char.get('p') != prev_char.get('p'):
            char_diff['p'] = curr_char.get('p')
            
        # 比较效果
        if curr_char.get('ef') != prev_char.get('ef'):
            char_diff['ef'] = curr_char.get('ef')
            
        # 比较元素能量
        if curr_char.get('ee') != prev_char.get('ee'):
            char_diff['ee'] = curr_char.get('ee')
            
        if char_diff:
            diff[char_name] = char_diff
            
    return diff if diff else None

def _compare_target(current, previous):
    """比较目标数据增量变化"""
    diff = {}
    # 基础属性
    for attr in ['n', 'ef', 'defense', 'resistance']:
        if current.get(attr) != previous.get(attr):
            diff[attr] = current.get(attr)
    
    # 比较元素附着
    curr_aura = current.get('el_aura', [])
    prev_aura = previous.get('el_aura', [])
    if len(curr_aura) != len(prev_aura) or any(
        c['el'] != p['el'] or c['amount'] != p['amount']
        for c, p in zip(curr_aura, prev_aura)
    ):
        diff['el_aura'] = curr_aura
        
    return diff if diff else None

def _compare_object(current, previous):
    """比较对象数据增量变化"""
    if len(current) != len(previous):
        return current
        
    diff = []
    for curr_obj, prev_obj in zip(current, previous):
        obj_diff = {}
        if curr_obj.get('n') != prev_obj.get('n'):
            obj_diff['n'] = curr_obj['n']
        if curr_obj.get('current_frame') != prev_obj.get('current_frame'):
            obj_diff['current_frame'] = curr_obj['current_frame']
        if curr_obj.get('life_frame') != prev_obj.get('life_frame'):
            obj_diff['life_frame'] = curr_obj['life_frame']
            
        if obj_diff:
            diff.append(obj_diff)
        else:
            diff.append(prev_obj)
            
    return diff if any(obj != prev for obj, prev in zip(diff, previous)) else None

def _compare_event(current, previous):
    """比较event数据的增量变化"""
    if len(current) != len(previous):
        return current
    for i, evt in enumerate(current):
        if evt != previous[i]:
            return current
    return None

def _incremental_update(current_data, previous_data):
    """增量更新逻辑，深入比较各部分数据的变化"""
    incremental_data = {_KEY_MAPPING['frame']: current_data[_KEY_MAPPING['frame']]}
    has_changes = False
    
    # 比较character数据
    char_diff = _compare_character(
        current_data.get(_KEY_MAPPING['character'], {}),
        previous_data.get(_KEY_MAPPING['character'], {})
    )
    if char_diff:
        incremental_data[_KEY_MAPPING['character']] = char_diff
        has_changes = True
    
    # 比较target数据
    target_diff = _compare_target(
        current_data.get(_KEY_MAPPING['target'], {}),
        previous_data.get(_KEY_MAPPING['target'], {})
    )
    if target_diff:
        incremental_data[_KEY_MAPPING['target']] = target_diff
        has_changes = True
    
    # 比较object数据
    obj_diff = _compare_object(
        current_data.get(_KEY_MAPPING['object'], []),
        previous_data.get(_KEY_MAPPING['object'], [])
    )
    if obj_diff:
        incremental_data[_KEY_MAPPING['object']] = obj_diff
        has_changes = True
    
    # 比较event数据
    event_diff = _compare_event(
        current_data.get(_KEY_MAPPING['event'], []),
        previous_data.get(_KEY_MAPPING['event'], [])
    )
    if event_diff:
        incremental_data[_KEY_MAPPING['event']] = event_diff
        has_changes = True
    
    return incremental_data if has_changes else {_KEY_MAPPING['frame']: current_data[_KEY_MAPPING['frame']]}

def OptimizedData():
    """优化数据存储，先缩短键名再进行增量存储"""
    data = []
    previous_frame_data = None
    
    frames = sorted(total_frame_data.keys())
    for frame in frames:
        # 先对当前帧数据进行键名缩短
        shortened_data = _shorten_keys({
            'frame': frame,
            'character': total_frame_data[frame]['character'],
            'target': total_frame_data[frame]['target'],
            'object': total_frame_data[frame]['object'],
            'event': total_frame_data[frame]['event']
        })
        
        if previous_frame_data is None:
            # 第一帧存储完整缩短后的数据
            data.append(shortened_data)
        else:
            # 后续帧存储增量数据
            incremental_data = _incremental_update(shortened_data, previous_frame_data)
            if incremental_data:
                data.append(incremental_data)
        
        previous_frame_data = shortened_data
    
    return data
