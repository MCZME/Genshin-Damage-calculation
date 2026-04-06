"""工作台核心状态管理器。"""

import json
import os

import flet as ft
from typing import Any, cast

from core.data.repository import MySQLDataRepository
from core.data_models.team_data_model import CharacterDataModel
from core.logger import get_ui_logger
from ui.services.metadata_service import MetadataService
from ui.services.simulation_service import SimulationService
from ui.view_models.library_vm import LibraryViewModel
from ui.view_models.layout_vm import LayoutViewModel
from ui.states.strategic_state import StrategicState
from ui.states.scene_state import SceneState
from ui.states.tactical_state import TacticalState


@ft.observable
class AppState:
    """
    工作台核心状态管理器 (MVVM V5.0)。

    作为各领域状态与服务的协调中枢。
    """

    def __init__(self) -> None:
        self.page: ft.Page | None = None
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
        self.scene_state = SceneState()
        self.tactical_state = TacticalState()
        self.tactical_state.clear_sequence()

        # 4. 视图模型层
        self.library_vm = LibraryViewModel(self.repo)
        self.library_vm.initialize()
        self.layout_vm = LayoutViewModel()

        # 5. 仿真运行状态
        self.sim_status = "IDLE"
        self.sim_progress = 0.0
        self.is_simulating = False

    def register_page(self, page: ft.Page) -> None:
        self.page = page

    # --- 代理属性 ---

    @property
    def char_map(self) -> dict:
        return self.metadata.char_map

    @property
    def weapon_map(self) -> dict:
        return self.metadata.weapon_map

    @property
    def target_map(self) -> dict:
        return self.metadata.target_map

    @property
    def implemented_chars(self) -> set[str]:
        return self.metadata.implemented_chars

    @property
    def implemented_weapons(self) -> set[str]:
        return self.metadata.implemented_weapons

    @property
    def artifact_sets(self) -> list[str]:
        return self.metadata.artifact_sets

    # --- 配置流 ---

    async def apply_external_config(self, config: dict) -> None:
        """导入外部全量配置。"""
        ctx = config.get("context_config", {})

        # 1. 恢复编队
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

        # 2. 恢复场景（使用 SceneState）
        self.scene_state.load_from_context_config(ctx)

        # 3. 恢复战术
        self.tactical_state.load_from_dict(config.get("sequence_config", []))

        # 4. 恢复规则配置
        rules_data = config.get("rules_config", {})
        self.scene_state.rules_vm.load_from_dict(rules_data)

        # 5. 触发 VM 重建与全局刷新
        self.strategic_state.rebind_all_vms()
        self.notify_update()
        get_ui_logger().log_info("AppState: Configuration normalized and applied.")

    def export_config(self) -> dict[str, Any]:
        """导出全量配置。"""
        team_cfg = [
            CharacterDataModel(m).to_simulator_format()
            for m in self.strategic_state.team_data if m.get("id")
        ]

        simulation_sequence = []
        for act in self.tactical_state.page_vm.sequence_vms:
            if act.model is not None:
                simulation_sequence.append(act.model.to_simulator_format())

        return {
            "context_config": {
                "team": team_cfg,
                **self.scene_state.to_context_config()
            },
            "sequence_config": simulation_sequence,
            "rules_config": self.scene_state.rules_vm.to_dict()
        }

    # --- 仿真控制代理 ---

    async def run_simulation(self) -> None:
        if self.is_simulating:
            return

        def update_progress(status: str, progress: float) -> None:
            self.sim_status = status
            self.sim_progress = progress
            self.layout_vm.update_simulation(status, progress, True)
            self.notify_update()

        self.is_simulating = True
        try:
            config = self.export_config()
            await self.simulation.run_single(config, on_progress=update_progress)
        finally:
            self.is_simulating = False
            self.layout_vm.update_simulation(self.sim_status, self.sim_progress, False)
            self.notify_update()

    def notify_update(self) -> None:
        """触发 UI 刷新。"""
        cast(Any, self).notify()

    def save_config(self, filename: str, data: dict | None = None) -> None:
        if not filename.endswith(".json"):
            filename += ".json"
        save_path = os.path.join("data/configs", filename) if not os.path.isabs(filename) else filename
        config_data = data if data is not None else self.export_config()
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
        get_ui_logger().log_info(f"Config saved: {save_path}")

    async def load_config(self, filename: str) -> None:
        path = os.path.join("data/configs", filename)
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        await self.apply_external_config(data)

    # --- 模板导入导出 ---

    def export_character_template(self, index: int) -> dict[str, Any]:
        """导出单个角色配置模板。"""
        from core.data_models.team_data_model import CharacterDataModel

        member = self.strategic_state.team_data[index]
        model = CharacterDataModel(member)

        if not model.id:
            return {}

        return {
            "character": {
                "id": model.id,
                "name": model.name,
                "element": model.element,
                "level": model.level,
                "constellation": model.constellation,
                "talents": model.talent_levels,
                "type": member.get("type", "Unknown")
            },
            "weapon": {
                "name": model.weapon.name,
                "level": model.weapon.level,
                "refinement": model.weapon.refinement
            },
            "artifacts": model.artifacts.raw_data
        }

    def apply_character_template(self, index: int, template: dict) -> None:
        """导入角色配置模板。"""
        from core.data_models.team_data_model import CharacterDataModel

        if not template:
            return

        char_cfg = template.get("character", {})
        weapon_cfg = template.get("weapon", {})
        artifacts_cfg = template.get("artifacts", {})

        model = CharacterDataModel.create_empty()
        model.id = char_cfg.get("id")
        model.name = char_cfg.get("name", "Unknown")
        model.element = char_cfg.get("element", "Neutral")
        model.level = char_cfg.get("level", 90)
        model.constellation = char_cfg.get("constellation", 0)

        talents = char_cfg.get("talents", {})
        if isinstance(talents, dict):
            for k, v in talents.items():
                model.set_talent(k, int(v) if isinstance(v, str) else v)
        elif isinstance(talents, list) and len(talents) >= 3:
            model.set_talent("na", talents[0])
            model.set_talent("e", talents[1])
            model.set_talent("q", talents[2])

        model.weapon.name = weapon_cfg.get("name", "")
        model.weapon.level = weapon_cfg.get("level", 90)
        model.weapon.refinement = weapon_cfg.get("refinement", 1)

        model.raw_data["artifacts"] = artifacts_cfg
        model.raw_data["type"] = char_cfg.get("type", "Unknown")

        self.strategic_state.team_data[index] = model.raw_data
        from ui.view_models.strategic.character_vm import CharacterViewModel
        self.strategic_state.team_vms[index] = CharacterViewModel(model)
        if self.strategic_state.current_index == index:
            self.strategic_state.active_character_proxy.bind_to(self.strategic_state.team_vms[index])

        self.notify_update()

    def export_artifact_set(self, index: int) -> dict[str, Any]:
        """导出圣遗物五件套配置。"""
        from core.data_models.team_data_model import CharacterDataModel

        member = self.strategic_state.team_data[index]
        model = CharacterDataModel(member)

        return model.artifacts.raw_data.copy()

    def apply_artifact_set(self, index: int, template: dict) -> None:
        """导入圣遗物五件套配置。"""
        from core.data_models.team_data_model import CharacterDataModel

        if not template:
            return

        member = self.strategic_state.team_data[index]
        member["artifacts"] = template

        # 重新绑定 VM
        model = CharacterDataModel(member)
        from ui.view_models.strategic.character_vm import CharacterViewModel
        self.strategic_state.team_vms[index] = CharacterViewModel(model)
        if self.strategic_state.current_index == index:
            self.strategic_state.active_character_proxy.bind_to(self.strategic_state.team_vms[index])

        self.notify_update()
