import json
import os
import asyncio
import flet as ft
from typing import List, Dict, Any, Optional
from core.data.repository import MySQLDataRepository
from core.logger import get_emulation_logger
from core.batch.models import SimulationNode, BatchSummary, SimulationMetrics
from core.factory.assembler import create_simulator_from_config

class AppState:
    """
    Flet 全量状态管理器。
    """
    def __init__(self, page: ft.Page):
        self.page = page
        self.repo = MySQLDataRepository()
        
        # 基础数据
        self.char_map = {}
        self.target_map = {} 
        self.artifact_sets = []
        self._load_metadata()
        
        # 流程状态
        self.active_view = "strategic"
        self.sidebar_collapsed = False 
        self.visual_collapsed = False  
        self.selection: Optional[Dict] = None 
        
        # 仿真输入数据
        self.team: List[Optional[Dict]] = [None] * 4
        self.targets: List[Dict] = [self._create_default_target()]
        self.environment: Dict = {"weather": "Clear", "field": "Neutral"}
        
        self.universe_root = SimulationNode(id="root", name="基准宇宙")
        self.selected_node = self.universe_root
        self.action_sequence: List[Dict] = []
        self.selected_action_index: Optional[int] = None
        
        # 运行状态
        self.is_simulating = False
        self.sim_progress = 0.0
        self.sim_status = "IDLE"
        self.last_metrics: Optional[SimulationMetrics] = None

    def _load_metadata(self):
        try:
            char_list = self.repo.get_all_characters()
            self.char_map = {
                c["name"]: {"id": c["id"], "element": c["element"], "type": c["type"]}
                for c in char_list
            }
            self.artifact_sets = self.repo.get_all_artifact_sets()
            self.target_map = {
                "遗迹守卫": {"level": 90, "resists": {k: 10 for k in ["火", "水", "雷", "草", "冰", "岩", "风", "物理"]}},
                "丘丘人": {"level": 90, "resists": {k: 10 for k in ["火", "水", "雷", "草", "冰", "岩", "风", "物理"]}},
                "古岩龙蜥": {"level": 90, "resists": {k: 10 for k in ["火", "水", "雷", "草", "冰", "岩", "风", "物理"]}},
            }
        except Exception as e:
            print(f"AppState: Metadata load failed: {e}")

    # --- 仿真运行逻辑 (单次模式) ---

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

        return {
            "context_config": {"team": team_cfg, "targets": self.targets, "environment": self.environment},
            "sequence_config": seq_cfg
        }

    async def run_simulation(self):
        """核心业务：单次仿真运行"""
        if self.is_simulating: return
        
        self.is_simulating = True
        self.sim_status = "INITIALIZING..."
        self.sim_progress = 0.0
        self.refresh()

        try:
            # 1. 组装模拟器
            config = self.export_config()
            simulator = create_simulator_from_config(config, self.repo)
            
            # 2. 执行仿真 (直接在当前环境运行)
            self.sim_status = "RUNNING..."
            self.sim_progress = 0.5 # 单次运行中途设为 50%
            self.refresh()
            
            # 注意：Simulator.run 是协程
            await simulator.run()
            
            # 3. 提取结果
            total_dmg = getattr(simulator.ctx, "total_damage", 0.0)
            duration = simulator.ctx.current_frame
            dps = (total_dmg / duration * 60) if duration > 0 else 0.0
            
            self.last_metrics = SimulationMetrics(
                total_damage=total_dmg,
                dps=dps,
                simulation_duration=duration,
                param_snapshot={}
            )
            
            self.sim_status = f"FINISHED | DPS: {int(dps)}"
            self.sim_progress = 1.0
            
        except Exception as e:
            self.sim_status = f"FAILED: {str(e)[:25]}"
            print(f"Single Simulation Error: {e}")
        finally:
            self.is_simulating = False
            self.refresh()

    # --- 数据持久化 ---

    def save_config(self, filename: str):
        if not filename.endswith(".json"): filename += ".json"
        os.makedirs("data/configs", exist_ok=True)
        config_data = self.export_config()
        config_data["action_sequence_raw"] = self.action_sequence
        with open(os.path.join("data/configs", filename), "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)

    def load_config(self, filename: str):
        path = os.path.join("data/configs", filename)
        if not os.path.exists(path): return
        with open(path, "r", encoding="utf-8") as f: data = json.load(f)
        ctx = data.get("context_config", {})
        self.team = ctx.get("team", [None] * 4)
        while len(self.team) < 4: self.team.append(None)
        for member in self.team:
            if member and isinstance(member.get("artifacts"), list):
                art_dict = {}
                for art in member["artifacts"]: art_dict[art["slot"]] = art
                member["artifacts"] = art_dict
        self.targets = ctx.get("targets", [])
        self.environment = ctx.get("environment", {"weather": "Clear", "field": "Neutral"})
        self.action_sequence = data.get("action_sequence_raw", [])
        self.selection = None
        self.refresh()

    def list_configs(self) -> List[str]:
        os.makedirs("data/configs", exist_ok=True)
        return [f for f in os.listdir("data/configs") if f.endswith(".json")]

    def save_character_template(self, char_data: Dict, name: str):
        os.makedirs("data/templates/characters", exist_ok=True)
        path = os.path.join("data/templates/characters", f"{name}.json")
        with open(path, "w", encoding="utf-8") as f: json.dump(char_data, f, ensure_ascii=False, indent=4)

    def save_artifact_set_template(self, artifact_data: Dict, name: str):
        os.makedirs("data/templates/artifacts", exist_ok=True)
        path = os.path.join("data/templates/artifacts", f"{name}.json")
        with open(path, "w", encoding="utf-8") as f: json.dump(artifact_data, f, ensure_ascii=False, indent=4)

    def list_templates(self, type: str) -> List[str]:
        dir = f"data/templates/{type}"
        os.makedirs(dir, exist_ok=True)
        return [f for f in os.listdir(dir) if f.endswith(".json")]

    # --- 状态与数据操作 ---
    def select_overview(self): self.selection = None; self.refresh()
    def select_character(self, index: int):
        if 0 <= index < 4:
            char_data = self.team[index]
            if char_data: self.selection = {"type": "character", "index": index, "data": char_data}
            else: self.selection = {"type": "empty", "index": index}
        self.refresh()
    def select_target(self, index: int):
        if 0 <= index < len(self.targets): self.selection = {"type": "target", "index": index, "data": self.targets[index]}
        self.refresh()
    def select_environment(self): self.selection = {"type": "env", "data": self.environment}; self.refresh()

    def _create_default_target(self):
        return {"id": "target_A", "name": "遗迹守卫", "level": 90, "position": {"x": 0, "z": 5}, "resists": {"火": 10, "水": 10, "雷": 10, "草": 10, "冰": 10, "岩": 10, "风": 10, "物理": 10}}

    def _create_placeholder_char(self):
        return {"position": {"x": 0, "z": -2}, "character": {"id": 0, "name": "待选择", "element": "物理", "level": 90, "constellation": 0, "talents": [1, 1, 1], "type": "单手剑"}, "weapon": {"name": "无锋剑", "level": 1, "refinement": 1}, "artifacts": {"flower": {"set": "未装备", "main": "生命值", "value": 0.0, "subs": []}, "feather": {"set": "未装备", "main": "攻击力", "value": 0.0, "subs": []}, "sands": {"set": "未装备", "main": "攻击力%", "value": 0.0, "subs": []}, "goblet": {"set": "未装备", "main": "属性伤害%", "value": 0.0, "subs": []}, "circlet": {"set": "未装备", "main": "暴击率%", "value": 0.0, "subs": []}}}

    def add_character(self, name: str):
        if self.selection and self.selection["type"] == "empty":
            idx = self.selection["index"]; char_info = self.char_map.get(name)
            if char_info:
                new_member = self._create_placeholder_char(); new_member["character"].update({"id": char_info["id"], "name": name, "element": char_info["element"], "type": char_info["type"]})
                self.team[idx] = new_member; self.select_character(idx)
        
    def remove_character(self, index: int):
        if 0 <= index < 4: self.team[index] = None; self.select_overview()

    def add_target(self):
        new_target = self._create_default_target(); new_target["id"] = f"target_{len(self.targets)}"; self.targets.append(new_target); self.select_target(len(self.targets) - 1)

    def remove_target(self, index: int):
        if 0 <= index < len(self.targets): self.targets.pop(index); self.select_overview()

    def refresh(self):
        try: self.page.update()
        except: pass

    def get_weapons(self, weapon_type: str) -> List[str]:
        try: return self.repo.get_weapons_by_type(weapon_type)
        except: return []
