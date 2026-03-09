import json
import os
import flet as ft
from typing import Any
from core.data.repository import MySQLDataRepository
from core.data_models.team_data_model import CharacterDataModel
from core.logger import get_ui_logger
from core.batch.models import SimulationNode, ModifierRule
from ui.services.metadata_service import MetadataService
from ui.services.simulation_service import SimulationService
from ui.view_models.library_vm import LibraryViewModel
from ui.view_models.layout_vm import LayoutViewModel
from ui.states.strategic_state import StrategicState
from ui.states.tactical_state import TacticalState
from ui.states.universe_state import UniverseState

@ft.observable
class AppState:
    """
    工作台核心状态管理器 (MVVM V5.0 - 职责瘦身版)。
    作为各领域状态与服务的协调中枢。
    已移除旧版 UIEventBus，完全转向声明式状态驱动。
    """
    def __init__(self):
        self.page = None
        self.main_to_branch = None
        self.branch_to_main = None
        
        # 1. 基础设施层
        self.repo = MySQLDataRepository()
        
        # 2. 业务服务层
        self.metadata = MetadataService(self.repo)
        self.metadata.load_all()
        self.simulation = SimulationService(self.repo)
        
        # 3. 领域状态层
        self.strategic_state = StrategicState()
        self.tactical_state = TacticalState()
        self.tactical_state.clear_sequence()
        
        # 分支宇宙状态不再接收 events 引用
        self.universe_state = UniverseState()

        # 4. 视图模型层
        self.library_vm = LibraryViewModel(self.repo)
        self.library_vm.initialize() # 同步 Metadata 状态
        self.layout_vm = LayoutViewModel()

        # 5. 仿真运行状态
        self.sim_status = "IDLE"
        self.sim_progress = 0.0
        self.is_simulating = False

    def register_page(self, page: ft.Page):
        self.page = page

    # --- 代理属性 ---
    @property
    def char_map(self):
        return self.metadata.char_map

    @property
    def weapon_map(self):
        return self.metadata.weapon_map

    @property
    def target_map(self):
        return self.metadata.target_map

    @property
    def implemented_chars(self):
        return self.metadata.implemented_chars

    @property
    def implemented_weapons(self):
        return self.metadata.implemented_weapons

    @property
    def artifact_sets(self):
        return self.metadata.artifact_sets

    # --- 配置流重构 ---

    async def apply_external_config(self, config: dict):
        """导入外部全量配置"""
        from core.data_models.team_data_model import CharacterDataModel

        ctx = config.get("context_config", {})

        # 1. 恢复编队 (从仿真格式转回内部格式)
        loaded_team = ctx.get("team", [])
        for i in range(4):
            if i < len(loaded_team) and loaded_team[i]:
                item = loaded_team[i]
                char_cfg = item.get("character", {})
                weapon_cfg = item.get("weapon", {})

                internal_dict = {
                    "id": char_cfg.get("id"),
                    "name": char_cfg.get("name"),
                    "element": char_cfg.get("element"),
                    "level": str(char_cfg.get("level", 90)),
                    "constellation": str(char_cfg.get("constellation", 0)),
                    "type": char_cfg.get("type", "Unknown"),
                    "talents": {
                        "na": str(char_cfg.get("talents", [1, 1, 1])[0]),
                        "e": str(char_cfg.get("talents", [1, 1, 1])[1]),
                        "q": str(char_cfg.get("talents", [1, 1, 1])[2]),
                    },
                    "weapon": {
                        "id": weapon_cfg.get("name"),
                        "level": str(weapon_cfg.get("level", 90)),
                        "refinement": str(weapon_cfg.get("refinement", 1))
                    },
                    "artifacts": item.get("artifacts", [])
                }
                self.strategic_state.team_data[i] = internal_dict
            else:
                self.strategic_state.team_data[i] = CharacterDataModel.create_empty().raw_data

        # 2. 恢复场景
        self.strategic_state.targets_data.clear()
        self.strategic_state.spatial_data["target_positions"].clear()
        for t_item in ctx.get("targets", []):
            target_id = t_item.get("id", "target_unknown")
            self.strategic_data_target_pos = self.strategic_state.spatial_data["target_positions"]
            self.strategic_data_target_pos[target_id] = t_item.get("position", {"x": 0, "z": 5})

            internal_target = {
                "id": target_id,
                "name": t_item.get("name"),
                "level": str(t_item.get("level", 90)),
                "resists": {k: str(v) for k, v in t_item.get("resists", {}).items()}
            }
            self.strategic_state.targets_data.append(internal_target)

        self.strategic_state.scene_data = ctx.get("environment", {})

        # 3. 恢复战术
        self.tactical_state.load_from_dict(config.get("sequence_config", []))

        # 4. 触发 VM 重建与全局刷新
        self.strategic_state.rebind_all_vms()
        self.notify()  # 代替 events.notify
        get_ui_logger().log_info("AppState: Configuration normalized and applied.")

    def export_config(self) -> dict[str, Any]:
        """导出全量配置"""
        team_cfg = [
            CharacterDataModel(m).to_simulator_format()
            for m in self.strategic_state.team_data if m.get("id")
        ]

        # 核心修复：手动解析 char_id 到 character_name 的映射，确保动作序列符合仿真引擎格式
        char_id_to_name: dict[str, str] = {
            m.get("id", ""): m.get("name", "Unknown")
            for m in self.strategic_state.team_data
            if m.get("id")
        }

        simulation_sequence = []
        for act in self.tactical_state.page_vm.sequence_vms:
            raw_name = char_id_to_name.get(act.char_id, "Unknown")
            char_name = str(raw_name) if raw_name is not None else "Unknown"
            
            if act.model is not None:
                simulation_sequence.append(act.model.to_simulator_format(char_name))

        return {
            "context_config": {
                "team": team_cfg,
                "targets": [t.to_simulator_format() for t in self.strategic_state.target_vms],
                "environment": self.strategic_state.scene_data
            },
            "sequence_config": simulation_sequence
        }

    # --- 仿真控制代理 ---

    async def run_simulation(self):
        if self.is_simulating:
            return

        def update_progress(status, progress):
            self.sim_status = status
            self.sim_progress = progress
            self.layout_vm.update_simulation(status, progress, True)
            self.notify()

        self.is_simulating = True
        try:
            config = self.export_config()
            await self.simulation.run_single(config, on_progress=update_progress)
        finally:
            self.is_simulating = False
            self.layout_vm.update_simulation(self.sim_status, self.sim_progress, False)
            self.notify()

    # --- 其它代理方法 ---
    @property
    def universe_root(self):
        return self.universe_state.universe_root

    def save_config(self, filename: str, data: dict | None = None):
        if not filename.endswith(".json"):
            filename += ".json"
        save_path = os.path.join("data/configs", filename) if not os.path.isabs(filename) else filename
        config_data = data if data is not None else self.export_config()
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
        get_ui_logger().log_info(f"Config saved: {save_path}")

    async def load_config(self, filename: str):
        path = os.path.join("data/configs", filename)
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        await self.apply_external_config(data)

    # --- 变异树操作 (通过 UniverseState 代理) ---
    @property
    def selected_node(self) -> SimulationNode | None:
        return self.universe_state.selected_node

    def select_node(self, node: SimulationNode | None):
        self.universe_state.select_node(node)

    def add_branch(self, parent: SimulationNode, name: str = "新分支"):
        self.universe_state.add_branch(parent, name)

    def apply_range_to_node(self, node: SimulationNode, path: list, s: float, e: float, step: float, label: str):
        self.universe_state.apply_range_to_node(node, path, s, e, step, label)

    def remove_node(self, nid: str):
        self.universe_state.remove_node(nid)

    def update_node(self, nid: str, name: str | None = None, rule: ModifierRule | None = None):
        self.universe_state.update_node(nid, name, rule)

    def get_selected_node_config(self) -> dict | None:
        return self.universe_state.get_selected_node_config()

    def save_universe(self, filename):
        self.universe_state.save_universe(filename)

    def load_universe(self, filename):
        self.universe_state.load_universe(filename)

    def list_universes(self):
        return self.universe_state.list_universes()
