import copy
from typing import List, Dict, Any, Generator, Optional
from core.batch.models import ModifierRule, SimulationNode

class ConfigGenerator:
    """
    仿真配置生成器 (V3.1 - 递归派生实现)。
    """

    @staticmethod
    def generate_from_tree(base_config: Dict[str, Any], root_node: SimulationNode) -> Generator[Dict[str, Any], None, None]:
        """
        遍历整棵变异树，仅为物理叶子节点（即没有子节点的节点）生成最终配置。
        每个产出的配置都应用了从根到该叶子节点路径上的所有规则。
        """
        def dfs(node: SimulationNode, config_so_far: Dict[str, Any]):
            # 1. 派生当前节点的配置快照
            current_config = copy.deepcopy(config_so_far)
            param_snapshot = current_config.get("_batch_metadata", {}).get("params", {}).copy()
            
            # 2. 如果当前节点有规则，应用它
            if node.rule:
                val = node.rule.value
                ConfigGenerator._set_nested_value(current_config, tuple(node.rule.target_path), val)
                
                # 记录变异参数快照
                key = node.rule.label or ".".join(map(str, node.rule.target_path))
                param_snapshot[key] = val
            
            # 3. 注入/更新元数据
            current_config["_batch_metadata"] = {
                "params": param_snapshot,
                "node_id": node.id,
                "node_name": node.name
            }

            # 4. 判断递归逻辑
            if not node.children:
                # 物理叶子节点：产出最终配置
                # 注意：根节点如果是孤家寡人，也会产出一个(即基准配置)
                yield current_config
            else:
                # 非叶子节点：继续向下游递归
                for child in node.children:
                    yield from dfs(child, current_config)

        yield from dfs(root_node, base_config)

    @staticmethod
    def resolve_node_config(root_config: Dict[str, Any], root_node: SimulationNode, target_node_id: str) -> Optional[Dict[str, Any]]:
        """
        根据节点 ID，解析并返回该节点应用了全路径变异后的完整配置。
        """
        def dfs(current_node: SimulationNode, config_so_far: Dict[str, Any]):
            # 应用当前规则
            new_config = copy.deepcopy(config_so_far)
            if current_node.rule:
                ConfigGenerator._set_nested_value(new_config, tuple(current_node.rule.target_path), current_node.rule.value)
            
            if current_node.id == target_node_id:
                return new_config
            
            for child in current_node.children:
                res = dfs(child, new_config)
                if res: return res
            return None

        return dfs(root_node, root_config)

    @staticmethod
    def _set_nested_value(dic: Dict[str, Any], path: tuple, value: Any):
        """
        工具：设置嵌套字典/列表中的值。
        """
        current = dic
        try:
            for i, key in enumerate(path[:-1]):
                # 处理列表索引
                if isinstance(current, list):
                    key = int(key)
                current = current[key]
            
            last_key = path[-1]
            if isinstance(current, list):
                last_key = int(last_key)
            
            # 执行覆盖
            if isinstance(value, (dict, list)):
                current[last_key] = copy.deepcopy(value)
            else:
                current[last_key] = value
        except (KeyError, IndexError, ValueError, TypeError):
            pass
