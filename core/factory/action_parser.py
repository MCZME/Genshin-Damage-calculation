from typing import List, Dict, Any, Tuple

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

    def parse_sequence(self, sequence_config: List[Dict[str, Any]]) -> List[Tuple[str, str, Any]]:
        """
        解析动作序列配置。
        返回格式: [(角色名, 方法名, 解析后的参数), ...]
        """
        parsed_actions = []
        for action_entry in sequence_config:
            char_name = action_entry['character']
            raw_action = action_entry['action']
            
            method_name = self.ACTION_NAME_MAP.get(raw_action)
            if not method_name:
                continue
                
            params = action_entry.get('params', {})
            method_params = self._parse_params(params) if params else None
            
            parsed_actions.append((char_name, method_name, method_params))
            
        return parsed_actions

    def _parse_params(self, params: Dict[str, Any]) -> Any:
        """
        处理动作参数映射逻辑。
        """
        # 兼容旧逻辑的特殊参数处理
        for k, v in params.items():
            if k == '攻击次数':
                return int(v)
            elif k == '攻击距离':
                return True if v == '高空' else False
            elif k == '释放时间':
                return True if v == '长按' else False
            elif k == '时间':
                return int(v)
            elif k == '释放时长':
                mapping = {'点按': 0, '一段蓄力': 1, '二段蓄力': 2}
                return mapping.get(v, 0)
        return None
