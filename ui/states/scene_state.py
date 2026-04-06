"""场景视图状态管理器。"""

from __future__ import annotations

import flet as ft
from typing import Any, cast

from core.data_models.scene_data_model import TargetDataModel
from ui.view_models.scene.target_vm import TargetViewModel
from ui.view_models.scene.rules_vm import RulesViewModel


@ft.observable
class SceneState:
    """
    场景视图状态管理器 (MVVM V5.0)。

    负责维护目标实体、战场空间及规则配置。
    """

    def __init__(self) -> None:
        # 1. 目标实体列表
        self.targets_data: list[dict[str, Any]] = [
            TargetDataModel.create_default("target_0", "遗迹守卫")
        ]
        self.selected_target_index: int = 0

        # 2. 战场空间
        self.spatial_data: dict[str, Any] = {
            "player_pos": {"x": 0.0, "z": 0.0},
            "target_positions": {
                "target_0": {"x": 0.0, "z": 5.0}
            }
        }

        # 3. 目标 ViewModel
        self.target_vms: list[TargetViewModel] = [
            TargetViewModel(TargetDataModel(d, self.spatial_data["target_positions"]))
            for d in self.targets_data
        ]

        # 4. 规则配置
        self.rules_vm = RulesViewModel()

    def notify_update(self) -> None:
        """触发状态更新通知。"""
        cast(Any, self).notify()

    def rebind_target_vms(self) -> None:
        """重建目标 VM 树。"""
        self.target_vms = [
            TargetViewModel(TargetDataModel(d, self.spatial_data["target_positions"]))
            for d in self.targets_data
        ]
        self.notify_update()

    # === 目标管理 ===

    @property
    def current_target_vm(self) -> TargetViewModel:
        """获取当前选中的目标 ViewModel。"""
        return self.target_vms[self.selected_target_index]

    def add_target(self, name: str = "遗迹守卫") -> None:
        """添加新目标。"""
        new_id = f"target_{len(self.targets_data)}"
        new_raw = TargetDataModel.create_default(new_id, name)
        self.targets_data.append(new_raw)
        self.spatial_data["target_positions"][new_id] = {"x": 0.0, "z": 5.0}

        new_vm = TargetViewModel(TargetDataModel(new_raw, self.spatial_data["target_positions"]))
        self.target_vms.append(new_vm)
        self.selected_target_index = len(self.target_vms) - 1
        self.notify_update()

    def remove_target(self, index: int) -> None:
        """移除目标。"""
        if len(self.target_vms) > 1:
            target_id = self.target_vms[index].id
            self.targets_data.pop(index)
            self.target_vms.pop(index)
            if target_id in self.spatial_data["target_positions"]:
                del self.spatial_data["target_positions"][target_id]
            self.selected_target_index = min(self.selected_target_index, len(self.target_vms) - 1)
            self.notify_update()

    def select_target(self, index: int) -> None:
        """选中目标。"""
        self.selected_target_index = index
        self.notify_update()

    # === 兼容性属性 ===

    @property
    def targets(self) -> list[dict[str, Any]]:
        """兼容性属性：返回目标数据列表。"""
        return self.targets_data

    @property
    def current_target(self) -> dict[str, Any]:
        """兼容性属性：返回当前目标数据。"""
        return self.targets_data[self.selected_target_index]

    # === 配置导出 ===

    def to_context_config(self) -> dict[str, Any]:
        """导出为仿真上下文配置格式。"""
        return {
            "targets": [t.to_simulator_format() for t in self.target_vms]
        }

    def load_from_context_config(self, ctx: dict[str, Any]) -> None:
        """从仿真上下文配置加载。"""
        # 恢复目标
        self.targets_data.clear()
        self.spatial_data["target_positions"].clear()
        for t_item in ctx.get("targets", []):
            target_id = t_item.get("id", "target_unknown")
            position = t_item.get("position", {"x": 0.0, "z": 5.0})
            self.spatial_data["target_positions"][target_id] = {
                "x": float(position.get("x", 0.0)),
                "z": float(position.get("z", 5.0))
            }
            internal_target = {
                "id": target_id,
                "name": t_item.get("name"),
                "level": str(t_item.get("level", 90)),
                "resists": {k: str(v) for k, v in t_item.get("resists", {}).items()}
            }
            self.targets_data.append(internal_target)

        # 重建 VM
        self.rebind_target_vms()
