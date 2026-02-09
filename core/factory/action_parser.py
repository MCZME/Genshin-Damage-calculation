from typing import List, Dict, Any, Tuple
from core.action.action_data import ActionCommand

class ActionParser:
    """
    动作解析器，负责将用户定义的动作序列 JSON 转换为可执行的指令。
    """
    
    ACTION_NAME_MAP = {
        '普通攻击': 'normal_attack',
        '重击': 'charged_attack',
        '下落攻击': 'plunging_attack',
        '元素战技': 'elemental_skill',
        '元素爆发': 'elemental_burst',
        '跳过': 'skip',
        '冲刺': 'dash',
        '跳跃': 'jump',
    }

    def parse_sequence(self, sequence_config: List[Dict[str, Any]]) -> List[ActionCommand]:
        """
        解析动作序列配置。
        返回格式: List[ActionCommand]
        """
        parsed_actions = []
        for action_entry in sequence_config:
            char_name = action_entry['character_name'] # V2 UI 导出的 key
            raw_action = action_entry['action_key']    # V2 UI 导出的 key (已经是英文 key，或者需要映射)
            
            # 兼容旧逻辑：如果传的是中文，尝试映射；如果是英文，直接使用
            method_name = self.ACTION_NAME_MAP.get(raw_action, raw_action)
            
            # 获取原始参数字典，不做任何降维处理
            params = action_entry.get('params', {})
            
            cmd = ActionCommand(
                character_name=char_name,
                action_type=method_name,
                params=params
            )
            parsed_actions.append(cmd)
            
        return parsed_actions
