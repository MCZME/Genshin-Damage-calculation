import json
import os
from typing import List, Dict, Any, Optional
from core.logger import get_ui_logger
from core.batch.models import SimulationNode, SimulationMetrics, ModifierRule
from core.batch.generator import ConfigGenerator
from ui.services.event_bus import UIEventBus

class UniverseState:
    """
    分支宇宙 (Universe/Batch) 状态管理器。
    负责管理仿真树结构、规则派生以及持久化。
    """
    def __init__(self, events: UIEventBus):
        self.events = events
        
        # 1. 核心数据
        self.root_config: Optional[Dict] = None  # 存储从工作台传入的基准配置
        self.universe_root = SimulationNode(id="root", name="基准宇宙")
        self.selected_node = self.universe_root

    # --- 变异树操作 (规则驱动版) ---

    def select_node(self, node: Optional[SimulationNode]):
        self.selected_node = node
        self.events.notify("global")

    def add_branch(self, parent_node: SimulationNode, name: str = "新分支"):
        new_node = SimulationNode(id=f"node_{os.urandom(4).hex()}", name=name, rule=None)
        parent_node.children.append(new_node)
        self.selected_node = new_node
        self.events.notify("global")

    def apply_range_to_node(
        self, target_node: SimulationNode, target_path: list, start: float, end: float, step: float, label: str
    ):
        """
        将指定节点转化为区间锚点：清空其子节点并根据区间生成受控子节点。
        """
        import numpy as np

        # 1. 净化目标节点：它变身为锚点，不直接持有 rule，名称改为区间描述
        target_node.name = f"区间: {label}"
        target_node.rule = None
        target_node.children.clear()  # 重新生成受控子项

        # 2. 生成数值并创建受控子节点
        try:
            # 保证终止值包含在内
            values = np.arange(start, end + (step * 0.1), step).tolist()
            for val in values:
                # 处理浮点数精度显示的显示问题
                display_val = round(val, 2) if isinstance(val, float) else val
                child_node = SimulationNode(
                    id=f"val_{os.urandom(4).hex()}",
                    name=f"{display_val}",
                    rule=ModifierRule(target_path=target_path, value=val, label=f"{label}={display_val}"),
                    is_managed=True,
                    managed_by=target_node.id,
                )
                target_node.children.append(child_node)
        except Exception as e:
            get_ui_logger().log_error(f"Range Generation Error: {e}")

        self.selected_node = target_node
        self.events.notify("global")

    def remove_node(self, node_id: str):
        def _remove(current):
            for child in current.children:
                if child.id == node_id:
                    # 如果删除的是普通节点，直接删
                    # 如果删除的是锚点，其 children 会被一并销毁 (Python GC)
                    current.children.remove(child)
                    return True
                if _remove(child):
                    return True
            return False

        # 检查是否为受控节点，受控节点不允许直接删除
        def _is_managed(node_id):
            def _search(n):
                if n.id == node_id:
                    return n.is_managed
                for c in n.children:
                    res = _search(c)
                    if res is not None:
                        return res
                return None

            return _search(self.universe_root)

        if node_id != "root" and not _is_managed(node_id):
            if _remove(self.universe_root):
                self.selected_node = self.universe_root
                self.events.notify("global")

    def update_node(self, node_id: str, name: str = None, rule: ModifierRule = None):
        def _find(current):
            if current.id == node_id:
                return current
            for child in current.children:
                res = _find(child)
                if res:
                    return res
            return None

        node = _find(self.universe_root)
        if node:
            if name is not None:
                node.name = name
            if rule is not None:
                node.rule = rule
            self.events.notify("global")

    def get_selected_node_config(self) -> Optional[Dict]:
        """按需实时解析当前选中节点的配置"""
        if not self.root_config or not self.selected_node:
            return None
        return ConfigGenerator.resolve_node_config(self.root_config, self.universe_root, self.selected_node.id)

    # --- 批处理 tree 持久化 ---

    def save_universe(self, filename: str):
        if not filename.endswith(".json"):
            filename += ".json"
        os.makedirs("data/universes", exist_ok=True)

        def node_to_dict(node):
            return {
                "id": node.id,
                "name": node.name,
                "is_managed": node.is_managed,
                "managed_by": node.managed_by,
                "rule": {
                    "target_path": node.rule.target_path,
                    "value": node.rule.value,
                    "label": node.rule.label,
                }
                if node.rule
                else None,
                "children": [node_to_dict(c) for c in node.children],
            }

        # 仅保存树结构，不再包含 root_config
        data = {"tree": node_to_dict(self.universe_root)}

        with open(os.path.join("data/universes", filename), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        get_ui_logger().log_info(f"Universe tree saved to {filename}")

    def load_universe(self, filename: str):
        path = os.path.join("data/universes", filename)
        if not os.path.exists(path):
            return

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 加载逻辑不再修改 root_config，保留当前环境
        def dict_to_node(d):
            rule_data = d.get("rule")
            rule = ModifierRule(**rule_data) if rule_data else None
            node = SimulationNode(
                id=d["id"],
                name=d["name"],
                rule=rule,
                is_managed=d.get("is_managed", False),
                managed_by=d.get("managed_by"),
            )
            node.children = [dict_to_node(c) for c in d.get("children", [])]
            return node

        self.universe_root = dict_to_node(data["tree"])
        self.selected_node = self.universe_root
        self.events.notify("global")
        get_ui_logger().log_info(f"Universe tree loaded from {filename}")

    def list_universes(self) -> List[str]:
        os.makedirs("data/universes", exist_ok=True)
        return [f for f in os.listdir("data/universes") if f.endswith(".json")]
