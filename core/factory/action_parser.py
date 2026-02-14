from typing import List, Dict, Any
from core.action.action_data import ActionCommand


class ActionParser:
    """
    动作解析器，负责将用户定义的动作序列 JSON 转换为可执行的指令。
    """

    ACTION_NAME_MAP = {
        "普通攻击": "normal_attack",
        "重击": "charged_attack",
        "下落攻击": "plunging_attack",
        "元素战技": "elemental_skill",
        "元素爆发": "elemental_burst",
        "跳过": "skip",
        "冲刺": "dash",
        "跳跃": "jump",
    }

    def parse_sequence(
        self, sequence_config: List[Dict[str, Any]]
    ) -> List[ActionCommand]:
        """
        解析动作序列配置。
        返回格式: List[ActionCommand]
        支持指令展开：如 normal_attack 带 count 参数会展开为多条。
        """
        parsed_actions = []
        for action_entry in sequence_config:
            char_name = action_entry["character_name"]
            raw_action = action_entry["action_key"]

            # 兼容逻辑
            method_name = self.ACTION_NAME_MAP.get(raw_action, raw_action)
            params = action_entry.get("params", {})

            # 指令展开逻辑：仅针对普通攻击处理 count 参数
            if method_name == "normal_attack" and "count" in params:
                try:
                    count = int(params["count"])
                    # 将一条 count 指令拆分为多条单段指令
                    for _ in range(count):
                        # 构造单段指令，移除 count 防止子层混淆
                        single_params = params.copy()
                        single_params.pop("count", None)

                        cmd = ActionCommand(
                            character_name=char_name,
                            action_type=method_name,
                            params=single_params,
                        )
                        parsed_actions.append(cmd)
                    continue  # 已处理展开，跳过原始追加
                except (ValueError, TypeError):
                    pass  # 非法 count 退回到普通处理

            # 普通处理
            cmd = ActionCommand(
                character_name=char_name, action_type=method_name, params=params
            )
            parsed_actions.append(cmd)

        return parsed_actions
