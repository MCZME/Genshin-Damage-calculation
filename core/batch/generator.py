import copy
from typing import List, Dict, Any, Generator
import itertools

class ConfigGenerator:
    """
    仿真配置生成器。
    支持通过参数区间扫描 (Sweep) 产生多个具体的仿真配置。
    """

    @staticmethod
    def generate_sweep_configs(base_config: Dict[str, Any], variables: List[Dict[str, Any]]) -> Generator[Dict[str, Any], None, None]:
        """
        基于参数扫描生成配置。
        
        Args:
            base_config: 基础 SimulationBundle。
            variables: 变量列表，格式如 [{"path": ["context_config", "team", 0, "character", "level"], "values": [80, 90]}]
            
        Yields:
            Dict[str, Any]: 一个具体的仿真配置。
        """
        # 1. 提取所有变量的值列表
        var_keys = [tuple(v["path"]) for v in variables]
        var_values = [v["values"] for v in variables]

        # 2. 生成笛卡尔积 (Cartesian Product)
        for combination in itertools.product(*var_values):
            new_cfg = copy.deepcopy(base_config)
            param_snapshot = {}
            
            # 3. 注入当前组合的值
            for i, path in enumerate(var_keys):
                ConfigGenerator._set_nested_value(new_cfg, path, combination[i])
                param_snapshot[".".join(map(str, path))] = combination[i]
            
            # 4. 记录参数快照到 metadata 中以便溯源
            new_cfg["_batch_metadata"] = {"params": param_snapshot}
            yield new_cfg

    @staticmethod
    def _set_nested_value(dic: Dict[str, Any], path: tuple, value: Any):
        """设置嵌套字典中的值"""
        current = dic
        for i, key in enumerate(path[:-1]):
            if isinstance(current, list):
                key = int(key)
            current = current[key]
        
        last_key = path[-1]
        if isinstance(current, list):
            last_key = int(last_key)
        current[last_key] = value
