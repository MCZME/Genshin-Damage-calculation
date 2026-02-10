import copy
from typing import List, Dict, Any, Generator
import itertools
from core.batch.models import ModifierRule, SimulationNode

class ConfigGenerator:
    """
    仿真配置生成器 (Base Modifier 实现)。
    支持 1. 笛卡尔积组合 (线性扫描)
    支持 2. 树形路径派生 (分支宇宙)
    """

    @staticmethod
    def generate_from_tree(base_config: Dict[str, Any], root_node: SimulationNode) -> Generator[Dict[str, Any], None, None]:
        """
        从“分支宇宙树”生成配置变体。
        每个叶子节点产出一个配置，该配置应用了从根到叶路径上的所有规则。
        """
        def dfs(node: SimulationNode, current_rules: List[ModifierRule]):
            # 1. 累加当前节点的规则
            new_rules = current_rules.copy()
            if node.rule:
                new_rules.append(node.rule)
            
            # 2. 如果是叶子节点，产出配置
            if node.is_leaf():
                variant = copy.deepcopy(base_config)
                param_snapshot = {}
                
                # 依次应用路径上的所有规则
                for rule in new_rules:
                    # 注意：如果规则包含多个 values (SWEEP)，在树结构中我们假设
                    # 每个节点只代表一个具体的值。如果有多个值，应在前端拆分为多个子节点。
                    # 或者这里取 rule.values[0]
                    val = rule.values[0] if rule.values else None
                    ConfigGenerator._set_nested_value(variant, tuple(rule.target_path), val)
                    
                    key = rule.label or ".".join(map(str, rule.target_path))
                    param_snapshot[key] = val
                
                variant["_batch_metadata"] = {
                    "params": param_snapshot,
                    "node_id": node.id,
                    "node_name": node.name
                }
                yield variant
            else:
                # 3. 否则继续向下遍历
                for child in node.children:
                    yield from dfs(child, new_rules)

        yield from dfs(root_node, [])

    @staticmethod
    def generate_variants(base_config: Dict[str, Any], rules: List[ModifierRule]) -> Generator[Dict[str, Any], None, None]:
        """
        基于规则集生成变体配置。
        
        Args:
            base_config: 基准 SimulationBundle。
            rules: 修改规则列表。
            
        Yields:
            Dict[str, Any]: 派生出的具体仿真配置。
        """
        if not rules:
            yield base_config
            return

        # 1. 准备各个变量的取值空间
        rule_paths = [tuple(r.target_path) for r in rules]
        rule_values = [r.values for r in rules]
        rule_labels = [r.label for r in rules]

        # 2. 生成笛卡尔积组合
        for combination in itertools.product(*rule_values):
            variant = copy.deepcopy(base_config)
            param_snapshot = {}
            
            # 3. 按路径注入值并记录快照
            for i, path in enumerate(rule_paths):
                ConfigGenerator._set_nested_value(variant, path, combination[i])
                
                # 记录快照名：优先使用规则标签，否则使用路径字符串
                key = rule_labels[i] or ".".join(map(str, path))
                param_snapshot[key] = combination[i]
            
            # 4. 注入批处理元数据
            variant["_batch_metadata"] = {"params": param_snapshot}
            yield variant

    @staticmethod
    def _set_nested_value(dic: Dict[str, Any], path: tuple, value: Any):
        """
        设置嵌套字典/列表中的值或对象。
        支持全路径覆盖，包括字典键替换和列表索引替换。
        """
        current = dic
        try:
            for i, key in enumerate(path[:-1]):
                if isinstance(current, list):
                    key = int(key)
                current = current[key]
            
            last_key = path[-1]
            if isinstance(current, list):
                last_key = int(last_key)
            
            # 执行覆盖
            # 如果是复杂对象，使用 deepcopy 确保变体间的完全隔离
            if isinstance(value, (dict, list)):
                current[last_key] = copy.deepcopy(value)
            else:
                current[last_key] = value
                
        except (KeyError, IndexError, ValueError, TypeError):
            # 路径无效时跳过
            pass
