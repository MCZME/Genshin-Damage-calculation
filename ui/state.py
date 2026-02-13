import json
import os
import asyncio
import flet as ft
from typing import List, Dict, Any, Optional
from core.data.repository import MySQLDataRepository
from core.logger import get_emulation_logger, get_ui_logger
from core.batch.models import SimulationNode, SimulationMetrics, ModifierRule
from core.factory.assembler import create_simulator_from_config
from core.batch.generator import ConfigGenerator

class AppState:
    """
    工作台全量状态管理器 (V3.1 - 规则派生架构)。
    """
    def __init__(self):
        self.page = None
        self.main_to_branch = None 
        self.branch_to_main = None 
        self.repo = MySQLDataRepository()
        
        # 1. 基础元数据
        self.char_map = {}
        self.target_map = {} 
        self.artifact_sets = []
        self._load_metadata()
        
        # 2. UI 流程状态
        self.sidebar_collapsed = False 
        self.visual_collapsed = False  
        self.selection: Optional[Dict] = None 
        
        # 3. 核心配置数据 (工作台当前状态)
        self.team: List[Optional[Dict]] = [None] * 4
        self.targets: List[Dict] = [self._create_default_target()]
        self.environment: Dict = {"weather": "Clear", "field": "Neutral"}
        self.action_sequence: List[Dict] = []
        self.selected_action_index: Optional[int] = None
        
        # 4. 分支宇宙状态
        self.root_config: Optional[Dict] = None # 存储从工作台传入的基准配置
        self.universe_root = SimulationNode(id="root", name="基准宇宙")
        self.selected_node = self.universe_root
        
        # 5. 仿真运行状态
        self.is_simulating = False
        self.sim_progress = 0.0
        self.sim_status = "IDLE"
        self.last_metrics: Optional[SimulationMetrics] = None

    def register_page(self, page: ft.Page):
        self.page = page

    def _load_metadata(self):
        try:
            char_list = self.repo.get_all_characters()
            self.char_map = {c["name"]: {"id": c["id"], "element": c["element"], "type": c["type"]} for c in char_list}
            self.artifact_sets = self.repo.get_all_artifact_sets()
            self.target_map = {
                "遗迹守卫": {"level": 90, "resists": {k: 10 for k in ["火", "水", "雷", "草", "冰", "岩", "风", "物理"]}},
                "丘丘人": {"level": 90, "resists": {k: 10 for k in ["火", "水", "雷", "草", "冰", "岩", "风", "物理"]}},
                "古岩龙蜥": {"level": 90, "resists": {k: 10 for k in ["火", "水", "雷", "草", "冰", "岩", "风", "物理"]}},
            }
        except Exception as e:
            get_ui_logger().log_error(f"AppState: Metadata load failed: {e}")

    def refresh(self):
        if self.page:
            try: self.page.update()
            except: pass

    # --- 变异树操作 (规则驱动版) ---

    def select_node(self, node: Optional[SimulationNode]):
        self.selected_node = node
        self.refresh()

    def add_branch(self, parent_node: SimulationNode, name: str = "新分支"):
        new_node = SimulationNode(id=f"node_{os.urandom(4).hex()}", name=name, rule=None)
        parent_node.children.append(new_node)
        self.selected_node = new_node
        self.refresh()

    def apply_range_to_node(self, target_node: SimulationNode, target_path: list, start: float, end: float, step: float, label: str):
        """
        将指定节点转化为区间锚点：清空其子节点并根据区间生成受控子节点。
        """
        import numpy as np
        import os
        
        # 1. 净化目标节点：它变身为锚点，不直接持有 rule，名称改为区间描述
        target_node.name = f"区间: {label}"
        target_node.rule = None 
        target_node.children.clear() # 重新生成受控子项
        
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
                    managed_by=target_node.id
                )
                target_node.children.append(child_node)
        except Exception as e:
            get_ui_logger().log_error(f"Range Generation Error: {e}")
            
        self.selected_node = target_node
        self.refresh()

    def remove_node(self, node_id: str):
        def _remove(current):
            for child in current.children:
                if child.id == node_id:
                    # 如果删除的是普通节点，直接删
                    # 如果删除的是锚点，其 children 会被一并销毁 (Python GC)
                    current.children.remove(child)
                    return True
                if _remove(child): return True
            return False
        
        # 检查是否为受控节点，受控节点不允许直接删除
        def _is_managed(node_id):
            def _search(n):
                if n.id == node_id: return n.is_managed
                for c in n.children:
                    res = _search(c)
                    if res is not None: return res
                return None
            return _search(self.universe_root)

        if node_id != "root" and not _is_managed(node_id):
            if _remove(self.universe_root):
                self.selected_node = self.universe_root
                self.refresh()

    def update_node(self, node_id: str, name: str = None, rule: ModifierRule = None):
        def _find(current):
            if current.id == node_id: return current
            for child in current.children:
                res = _find(child)
                if res: return res
            return None
        node = _find(self.universe_root)
        if node:
            if name is not None: node.name = name
            if rule is not None: node.rule = rule
            self.refresh()

    def get_selected_node_config(self) -> Optional[Dict]:
        """按需实时解析当前选中节点的配置"""
        if not self.root_config or not self.selected_node:
            return None
        return ConfigGenerator.resolve_node_config(
            self.root_config, 
            self.universe_root, 
            self.selected_node.id
        )

    # --- 跨进程通信 ---

    def launch_commander(self):
        if self.main_to_branch:
            config = self.export_config()
            config["action_sequence_raw"] = self.action_sequence
            # 将初始化配置存为子进程的 root_config
            msg = {"type": "INIT_UNIVERSE", "config": config}
            self.main_to_branch.put(msg)

    async def apply_external_config(self, config: Dict):
        ctx = config.get("context_config", {})
        self.team = ctx.get("team", [None] * 4)
        while len(self.team) < 4: self.team.append(None)
        for member in self.team:
            if member and isinstance(member.get("artifacts"), list):
                art_dict = {}
                for art in member["artifacts"]: art_dict[art["slot"]] = art
                member["artifacts"] = art_dict
        self.targets = ctx.get("targets", [self._create_default_target()])
        self.environment = ctx.get("environment", {"weather": "Clear", "field": "Neutral"})
        self.action_sequence = config.get("action_sequence_raw", [])
        self.selection = None
        self.refresh()
        get_ui_logger().log_info("External configuration applied to Workbench.")

    # --- 运行逻辑 ---

    def export_config(self) -> Dict[str, Any]:
        team_cfg = []
        for member in self.team:
            if member is None: continue
            arts_list = []
            for slot, data in member["artifacts"].items():
                if data["set"] != "未装备":
                    arts_list.append({"slot": slot, "set": data["set"], "main": data["main"], "value": data["value"], "subs": data["subs"]})
            team_cfg.append({"character": member["character"], "weapon": member["weapon"], "artifacts": arts_list, "position": member["position"]})
        mapping = {"skill": "elemental_skill", "burst": "elemental_burst", "normal": "normal_attack", "charged": "charged_attack", "plunging": "plunging_attack", "dash": "dash", "jump": "jump"}
        seq_cfg = []
        for act in self.action_sequence:
            seq_cfg.append({"character_name": act["char_name"], "action_key": mapping.get(act["action_id"], act["action_id"]), "params": act.get("params", {})})
        return {"context_config": {"team": team_cfg, "targets": self.targets, "environment": self.environment}, "sequence_config": seq_cfg}

    async def run_simulation(self):
        if self.is_simulating: return
        self.is_simulating = True; self.sim_status = "RUNNING..."; self.refresh()
        try:
            config = self.export_config()
            simulator = create_simulator_from_config(config, self.repo)
            await simulator.run()
            total_dmg = getattr(simulator.ctx, "total_damage", 0.0)
            duration = simulator.ctx.current_frame
            dps = (total_dmg / duration * 60) if duration > 0 else 0.0
            self.last_metrics = SimulationMetrics(total_damage=total_dmg, dps=dps, simulation_duration=duration)
            self.sim_status = f"FINISHED | DPS: {int(dps)}"; self.sim_progress = 1.0
        except Exception as e:
            self.sim_status = f"FAILED: {str(e)[:25]}"
            get_ui_logger().log_error(f"Single Simulation Error: {e}")
        finally:
            self.is_simulating = False; self.refresh()

    async def run_batch_simulation(self):
        if self.is_simulating: return
        if not self.root_config: return

        self.is_simulating = True; self.sim_status = "BATCH PREPARING..."; self.refresh()
        try:
            from core.batch.runner import BatchRunner
            configs = list(ConfigGenerator.generate_from_tree(self.root_config, self.universe_root))
            if not configs: return
            runner = BatchRunner()
            def update_progress(c, t):
                self.sim_progress = c / t; self.sim_status = f"BATCH RUNNING ({c}/{t})..."; self.refresh()
            summary = await runner.run_batch(configs, on_progress=update_progress)
            self.sim_status = f"BATCH FINISHED | AVG: {int(summary.avg_dps)}"; self.sim_progress = 1.0
            return summary
        except Exception as e:
            self.sim_status = f"BATCH FAILED: {str(e)[:20]}"
            get_ui_logger().log_error(f"Batch Simulation Error: {e}")
        finally:
            self.is_simulating = False; self.refresh()

    def save_config(self, filename: str):
        if not filename.endswith(".json"): filename += ".json"
        os.makedirs("data/configs", exist_ok=True)
        config_data = self.export_config(); config_data["action_sequence_raw"] = self.action_sequence
        with open(os.path.join("data/configs", filename), "w", encoding="utf-8") as f: json.dump(config_data, f, ensure_ascii=False, indent=4)
        get_ui_logger().log_info(f"Config saved to {filename}")

    async def load_config(self, filename: str):
        path = os.path.join("data/configs", filename)
        if not os.path.exists(path): return
        with open(path, "r", encoding="utf-8") as f: data = json.load(f)
        await self.apply_external_config(data)
        get_ui_logger().log_info(f"Config loaded from {filename}")

    # --- 批处理 tree 持久化 ---

    def save_universe(self, filename: str):
        if not filename.endswith(".json"): filename += ".json"
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
                    "label": node.rule.label
                } if node.rule else None,
                "children": [node_to_dict(c) for c in node.children]
            }

        # 仅保存树结构，不再包含 root_config
        data = {
            "tree": node_to_dict(self.universe_root)
        }
        
        with open(os.path.join("data/universes", filename), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        get_ui_logger().log_info(f"Universe tree saved to {filename}")

    def load_universe(self, filename: str):
        path = os.path.join("data/universes", filename)
        if not os.path.exists(path): return
        
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
                managed_by=d.get("managed_by")
            )
            node.children = [dict_to_node(c) for c in d.get("children", [])]
            return node

        self.universe_root = dict_to_node(data["tree"])
        self.selected_node = self.universe_root
        self.refresh()
        get_ui_logger().log_info(f"Universe tree loaded from {filename}")

    def list_universes(self) -> List[str]:
        os.makedirs("data/universes", exist_ok=True)
        return [f for f in os.listdir("data/universes") if f.endswith(".json")]

    def list_configs(self): return [f for f in os.listdir("data/configs") if f.endswith(".json")] if os.path.exists("data/configs") else []
    def select_overview(self): self.selection = None; self.refresh()
    def select_character(self, index: int):
        char_data = self.team[index]
        self.selection = {"type": "character", "index": index, "data": char_data} if char_data else {"type": "empty", "index": index}
        self.refresh()
    def select_target(self, index: int):
        if 0 <= index < len(self.targets): self.selection = {"type": "target", "index": index, "data": self.targets[index]}
        self.refresh()
    def select_environment(self): self.selection = {"type": "env", "data": self.environment}; self.refresh()
    def _create_default_target(self): return {"id": "target_A", "name": "遗迹守卫", "level": 90, "position": {"x": 0, "z": 5}, "resists": {"火": 10, "水": 10, "雷": 10, "草": 10, "冰": 10, "岩": 10, "风": 10, "物理": 10}}
    def _create_placeholder_char(self): return {"position": {"x": 0, "z": -2}, "character": {"id": 0, "name": "待选择", "element": "物理", "level": 90, "constellation": 0, "talents": [1, 1, 1], "type": "单手剑"}, "weapon": {"name": "无锋剑", "level": 1, "refinement": 1}, "artifacts": {"flower": {"set": "未装备", "main": "生命值", "value": 0.0, "subs": []}, "feather": {"set": "未装备", "main": "攻击力", "value": 0.0, "subs": []}, "sands": {"set": "未装备", "main": "攻击力%", "value": 0.0, "subs": []}, "goblet": {"set": "未装备", "main": "属性伤害%", "value": 0.0, "subs": []}, "circlet": {"set": "未装备", "main": "暴击率%", "value": 0.0, "subs": []}}}
    def add_character(self, name: str):
        if self.selection and self.selection["type"] == "empty":
            idx = self.selection["index"]; char_info = self.char_map.get(name)
            if char_info:
                new_m = self._create_placeholder_char(); new_m["character"].update({"id": char_info["id"], "name": name, "element": char_info["element"], "type": char_info["type"]})
                self.team[idx] = new_m; self.select_character(idx)
    def remove_character(self, index: int): self.team[index] = None; self.select_overview()
    def add_target(self):
        new_t = self._create_default_target(); new_t["id"] = f"target_{len(self.targets)}"; self.targets.append(new_t); self.select_target(len(self.targets) - 1)
    def remove_target(self, index: int):
        if 0 <= index < len(self.targets): self.targets.pop(index); self.select_overview()
    def get_weapons(self, t): return self.repo.get_weapons_by_type(t)
    def save_character_template(self, d, n): pass
    def save_artifact_set_template(self, d, n): pass
    def list_templates(self, t): return []
