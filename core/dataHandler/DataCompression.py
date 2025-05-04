# 键名缩短映射表
import copy


_KEY_MAPPING = {
    'character': 'c',
    'target': 't', 
    'object': 'o',
    'event': 'e',
    'frame': 'f',
    'name': 'n',
    'value': 'v',
    'max_value': 'mv',
    'min_value': 'mnv',
    'current_frame': 'cf',
    'life_frame': 'lf',
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
    'reaction': 'rct',
    'elemental_aura': 'el_aura'
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

def _compare_dict_subset(current, previous, keys):
    """比较字典中指定键的子集"""
    diff = {}
    for key in keys:
        if current.get(key) != previous.get(key):
            diff[key] = current.get(key)
    return diff if diff else None

def _compare_panel(current, previous):
    """比较角色面板属性的增量变化"""
    panel_diff = {}
    panel_keys = [
        '生命值', '固定生命值', '攻击力', '固定攻击力', '防御力', '固定防御力',
        '元素精通', '暴击率', '暴击伤害', '元素充能效率', '治疗加成', '受治疗加成',
        '火元素伤害加成', '水元素伤害加成', '雷元素伤害加成', '冰元素伤害加成',
        '岩元素伤害加成', '风元素伤害加成', '草元素伤害加成', '物理伤害加成',
        '生命值%', '攻击力%', '防御力%', '伤害加成'
    ]
    for key in panel_keys:
        if current.get(key) != previous.get(key):
            panel_diff[key] = current.get(key)
    return panel_diff if panel_diff else None

def _compare_character(current, previous):
    """比较角色数据增量变化，按角色名分别比较"""
    diff = {}
    # 只比较现有角色(角色不会新增和删除)
    for char_name in current.keys():
        curr_char = current[char_name]
        prev_char = previous.get(char_name, {})
        char_diff = {}
            
        # 比较基础属性
        base_diff = _compare_dict_subset(curr_char, prev_char, ['mh', 'ch', 'l', 'sp', 'cn'])
        if base_diff:
            char_diff.update(base_diff)
        
        # 比较面板属性(更细粒度)
        if 'p' in curr_char or 'p' in prev_char:
            panel_diff = _compare_panel(curr_char.get('p', {}), prev_char.get('p', {}))
            if panel_diff:
                char_diff['p'] = panel_diff
            
            # 比较角色效果(按效果名分别比较duration/max_duration/msg)
            if 'ef' in curr_char or 'ef' in prev_char:
                effect_diff = {}
                all_effects = set(curr_char.get('ef', {}).keys()) | set(prev_char.get('ef', {}).keys())
                for eff_name in all_effects:
                    curr_eff = curr_char.get('ef', {}).get(eff_name, {})
                    prev_eff = prev_char.get('ef', {}).get(eff_name, {})
                    if eff_name not in prev_char.get('ef', {}):
                        # 新增效果
                        effect_diff[eff_name] = {'__op__': 'add', **curr_eff}
                    elif eff_name not in curr_char.get('ef', {}):
                        # 删除效果
                        effect_diff[eff_name] = {'__op__': 'remove'}
                    else:
                        # 更新效果
                        eff_diff = _compare_dict_subset(curr_eff, prev_eff, ['d', 'md', 'm'])
                        if eff_diff:
                            effect_diff[eff_name] = {'__op__': 'update', **eff_diff}
                
                if effect_diff:
                    char_diff['ef'] = effect_diff
            
        # 比较元素能量
        if 'ee' in curr_char or 'ee' in prev_char:
            energy_diff = _compare_dict_subset(
                curr_char.get('ee', {}),
                prev_char.get('ee', {}),
                ['element', 'max_energy', 'energy']
            )
            if energy_diff:
                char_diff['ee'] = energy_diff
            
        if char_diff:
            diff[char_name] = {'__op__': 'update', **char_diff}
            
    return diff if diff else None

def _compare_resistance(current, previous):
    """比较目标抗性数据的增量变化"""
    resistance_diff = {}
    resistance_keys = ['火', '水', '雷', '草', '冰', '岩', '风', '物理']
    for key in resistance_keys:
        if current.get(key) != previous.get(key):
            resistance_diff[key] = current.get(key)
    return resistance_diff if resistance_diff else None

def _compare_elemental_aura(current, previous):
    """比较元素附着数据的增量变化"""
    if len(current) != len(previous):
        return current
    
    diff = []
    for curr, prev in zip(current, previous):
        if curr['el'] != prev['el'] or curr['amount'] != prev['amount']:
            diff.append(curr)
        else:
            diff.append(prev)
    
    return diff if any(c != p for c, p in zip(diff, previous)) else None

def _compare_target(current, previous):
    """比较目标数据增量变化"""
    diff = {}
    
    # 初始目标数据
    if not previous:
        return None
        
    # 基础属性
    base_diff = _compare_dict_subset(current, previous, ['n', 'defense'])
    if base_diff:
        diff.update(base_diff)
    
    # 比较目标效果(按效果名分别比较duration/max_duration)
    if 'ef' in current or 'ef' in previous:
        effect_diff = {}
        all_effects = set(current.get('ef', {}).keys()) | set(previous.get('ef', {}).keys())
        for eff_name in all_effects:
            curr_eff = current.get('ef', {}).get(eff_name, {})
            prev_eff = previous.get('ef', {}).get(eff_name, {})
            if eff_name not in previous.get('ef', {}):
                # 新增效果
                effect_diff[eff_name] = {'__op__': 'add', **curr_eff}
            elif eff_name not in current.get('ef', {}):
                # 删除效果
                effect_diff[eff_name] = {'__op__': 'remove'}
            else:
                # 更新效果
                eff_diff = _compare_dict_subset(curr_eff, prev_eff, ['d', 'md'])
                if eff_diff:
                    effect_diff[eff_name] = {'__op__': 'update', **eff_diff}
        
        if effect_diff:
            diff['ef'] = effect_diff
    
    # 比较抗性
    if 'resistance' in current or 'resistance' in previous:
        resistance_diff = _compare_resistance(
            current.get('resistance', {}),
            previous.get('resistance', {})
        )
        if resistance_diff:
            diff['resistance'] = resistance_diff
    
    # 比较元素附着(更精确的比较)
    if 'el_aura' in current or 'el_aura' in previous:
        aura_diff = _compare_elemental_aura(
            current.get('el_aura', []),
            previous.get('el_aura', [])
        )
        if aura_diff:
            diff['el_aura'] = aura_diff
        
    return {'__op__': 'update', **diff} if diff else None

def _compare_object(current, previous):
    """比较对象数据增量变化"""
    if len(current) != len(previous):
        return {'__op__': 'replace', 'value': current}
        
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
            diff.append({'__op__': 'update', **obj_diff})
        else:
            diff.append(prev_obj)
            
    return {'__op__': 'update', 'value': diff} if any(
        isinstance(obj, dict) and obj.get('__op__') == 'update' 
        for obj in diff
    ) else None

def _compare_event(current, previous):
    """比较event数据的增量变化"""
    if len(current) != len(previous):
        return {'__op__': 'replace', 'value': current}
    for i, evt in enumerate(current):
        if evt != previous[i]:
            return {'__op__': 'replace', 'value': current}
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

def OptimizedData(total_frame_data):
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

def _revert_keys(data):
    """将缩短的键名还原为原始键名，并确保frame为int类型"""
    if not isinstance(data, (dict, list)):
        return data
        
    if isinstance(data, dict):
        # 创建反向映射字典
        reverse_mapping = {v: k for k, v in _KEY_MAPPING.items()}
        result = {}
        for k, v in data.items():
            new_key = reverse_mapping.get(k, k)
            # 特殊处理frame字段
            if new_key == 'frame':
                result[new_key] = int(v) if isinstance(v, str) else v
            else:
                result[new_key] = _revert_keys(v)
        return result
    
    return [_revert_keys(item) for item in data]

def _merge_character_data(merged_frame, char_name, char_data):
    """合并角色数据"""
    op = char_data.get('__op__', 'update')
    if op == 'update':
        # 更新角色属性
        if char_name in merged_frame['character']:
            for k, v in char_data.items():
                if k != '__op__':
                    if k == 'effect' and isinstance(v, dict):
                        # 处理角色效果数据，根据每个效果的__op__进行操作
                        existing_effects = copy.deepcopy(merged_frame['character'][char_name].get('effect', {}))
                        for eff_name, eff_data in v.items():
                            eff_op = eff_data.get('__op__', 'update')
                            if eff_op == 'add':
                                # 新增效果
                                existing_effects[eff_name] = {k:v for k,v in eff_data.items() if k != '__op__'}
                            elif eff_op == 'remove':
                                # 删除效果
                                if eff_name in existing_effects:
                                    del existing_effects[eff_name]
                            elif eff_op == 'update':
                                # 更新效果
                                if eff_name in existing_effects:
                                    for field, value in eff_data.items():
                                        if field != '__op__':
                                            existing_effects[eff_name][field] = value
                        merged_frame['character'][char_name]['effect'] = existing_effects
                    elif isinstance(v, dict):
                        # 深拷贝字典值并更新
                        existing = copy.deepcopy(merged_frame['character'][char_name].get(k, {}))
                        existing.update(copy.deepcopy(v))
                        merged_frame['character'][char_name][k] = existing
                    else:
                        # 直接赋值基本类型
                        merged_frame['character'][char_name][k] = v

def _merge_target_data(merged_frame, target_data):
    """合并目标数据"""
    op = target_data.get('__op__', 'update')
    if op == 'update':
        # 增量更新目标数据
        for k, v in target_data.items():
            if k != '__op__':
                if k == 'effect' and isinstance(v, dict):
                    # 处理目标效果数据，根据每个效果的__op__进行操作
                    existing_effects = copy.deepcopy(merged_frame['target'].get('effect', {}))
                    for eff_name, eff_data in v.items():
                        eff_op = eff_data.get('__op__', 'update')
                        if eff_op == 'add':
                            # 新增效果
                            existing_effects[eff_name] = {k:v for k,v in eff_data.items() if k != '__op__'}
                        elif eff_op == 'remove':
                            # 删除效果
                            if eff_name in existing_effects:
                                del existing_effects[eff_name]
                        elif eff_op == 'update':
                            # 更新效果
                            if eff_name in existing_effects:
                                for field, value in eff_data.items():
                                    if field != '__op__':
                                        existing_effects[eff_name][field] = value
                    merged_frame['target']['effect'] = existing_effects
                elif isinstance(v, dict):
                    # 深拷贝字典值并更新
                    existing = copy.deepcopy(merged_frame['target'].get(k, {}))
                    existing.update(copy.deepcopy(v))
                    merged_frame['target'][k] = existing
                else:
                    # 直接赋值基本类型
                    merged_frame['target'][k] = v

def _merge_object_data(merged_frame, object_data):
    """合并对象数据"""
    op = object_data.get('__op__', 'update')
    if op == 'replace':
        # 完全替换对象列表
        merged_frame['object'] = object_data['value'].copy()
    elif op == 'update':
        # 增量更新对象数据
        for i, obj_diff in enumerate(object_data['value']):
            if isinstance(obj_diff, dict) and '__op__' in obj_diff:
                obj_op = obj_diff['__op__']
                if obj_op == 'update' and i < len(merged_frame['object']):
                    # 更新现有对象
                    for k, v in obj_diff.items():
                        if k != '__op__':
                            if isinstance(v, dict):
                                # 深拷贝字典值并更新
                                existing = copy.deepcopy(merged_frame['object'][i].get(k, {}))
                                existing.update(copy.deepcopy(v))
                                merged_frame['object'][i][k] = existing
                            else:
                                # 直接赋值基本类型
                                merged_frame['object'][i][k] = v

def _merge_event_data(merged_frame, event_data):
    """合并事件数据"""
    op = event_data.get('__op__', 'update')
    if op == 'replace':
        # 完全替换事件列表
        merged_frame['event'] = event_data['value'].copy()
    elif op == 'update':
        # 事件数据不支持部分更新，保持不变
        pass

def _reconstruct_full_data(optimized_data):
    """从优化数据重建完整数据(字典格式)"""
    restored_data = {}
    previous_frame = None
    
    for frame_data in optimized_data:
        reverted_data = _revert_keys(frame_data)
        frame_num = reverted_data['frame']
        
        if previous_frame is None:
            # 第一帧是完整数据
            restored_data[frame_num] = {
                'character': copy.deepcopy(reverted_data.get('character', {})),
                'target': copy.deepcopy(reverted_data.get('target', {})),
                'object': copy.deepcopy(reverted_data.get('object', [])),
                'event': copy.deepcopy(reverted_data.get('event', []))
            }
        else:
            # 后续帧是增量数据，需要根据操作类型合并
            merged_frame = {
                'character': copy.deepcopy(previous_frame['character']),
                'target': copy.deepcopy(previous_frame['target']),
                'object': copy.deepcopy(previous_frame['object']),
                'event': copy.deepcopy(previous_frame['event'])
            }
            
            # 处理角色数据
            if 'character' in reverted_data:
                for char_name, char_data in reverted_data['character'].items():
                    _merge_character_data(merged_frame, char_name, char_data)
            
            # 处理目标数据
            if 'target' in reverted_data:
                _merge_target_data(merged_frame, reverted_data['target'])
            
            # 处理对象数据
            if 'object' in reverted_data:
                _merge_object_data(merged_frame, reverted_data['object'])
            
            # 处理事件数据
            if 'event' in reverted_data:
                _merge_event_data(merged_frame, reverted_data['event'])
            
            restored_data[frame_num] = merged_frame
        
        previous_frame = restored_data[frame_num]
    
    return restored_data

def RestoreData(optimized_data):
    """将优化后的数据还原为原始字典格式"""
    return _reconstruct_full_data(optimized_data)
