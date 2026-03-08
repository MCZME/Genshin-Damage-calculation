from __future__ import annotations
import flet as ft
import json
import os
from typing import Any, cast

class PersistenceManager:
    """
    持久化管理器：解耦 UI 视图与文件系统操作。
    采用 Flet V3 推荐的异步返回模式 (Async Return Path)。
    """
    def __init__(self, page: ft.Page, app_state: Any):
        self.page = page
        self.app_state = app_state
        # 获取项目根目录下的 data 路径
        self.base_data_dir = os.path.abspath(os.path.join(os.getcwd(), "data"))
        os.makedirs(self.base_data_dir, exist_ok=True)

    def _show_toast(self, text: str):
        # [FIX] 修复 SnackBar 显示逻辑，适配 Flet 0.80+ 
        sb = ft.SnackBar(ft.Text(text))
        self.page.overlay.append(sb)
        sb.open = True
        self.page.update()

    # --- 全量配置操作 ---
    async def load_config(self):
        target_dir = os.path.join(self.base_data_dir, "configs")
        os.makedirs(target_dir, exist_ok=True)
        
        picker = ft.FilePicker()
        self.page.overlay.append(picker)
        self.page.update()
        
        result = await picker.pick_files(
            dialog_title="读取仿真配置",
            initial_directory=target_dir,
            allowed_extensions=["json"]
        )

        if result:
            # 根据 Flet 版本不同，result 可能是 FilePickerResult 对象或 list
            files = getattr(result, "files", result)
            if files and isinstance(files, list) and len(files) > 0:
                path = files[0].path
                if path:
                    await self.app_state.load_config(path)
                    self._show_toast(f"已加载配置: {os.path.basename(cast(str, path))}")
                    return True
        return False

    async def save_config(self):
        target_dir = os.path.join(self.base_data_dir, "configs")
        os.makedirs(target_dir, exist_ok=True)

        picker = ft.FilePicker()
        self.page.overlay.append(picker)
        self.page.update()

        path = await picker.save_file(
            dialog_title="保存当前配置",
            initial_directory=target_dir,
            file_name="sim_config.json"
        )

        if path:
            self.app_state.save_config(path)
            self._show_toast(f"配置已保存: {os.path.basename(cast(str, path))}")
            return True
        return False

    # --- 角色模版操作 ---
    async def save_character_template(self, index: int):
        member = self.app_state.strategic_state.team_data[index]
        name = member.get("name", "character")
        target_dir = os.path.join(self.base_data_dir, "character")
        os.makedirs(target_dir, exist_ok=True)

        picker = ft.FilePicker()
        self.page.overlay.append(picker)
        self.page.update()

        path = await picker.save_file(
            dialog_title=f"导出角色模版: {name}",
            initial_directory=target_dir,
            file_name=f"{name}_template.json"
        )

        if path:
            data = self.app_state.export_character_template(index)
            self.app_state.save_config(path, data=data)
            self._show_toast(f"角色模版已保存: {os.path.basename(cast(str, path))}")
            return True
        return False

    async def load_character_template(self, index: int):
        target_dir = os.path.join(self.base_data_dir, "character")
        os.makedirs(target_dir, exist_ok=True)

        picker = ft.FilePicker()
        self.page.overlay.append(picker)
        self.page.update()

        result = await picker.pick_files(
            dialog_title="读取角色模版",
            initial_directory=target_dir,
            allowed_extensions=["json"]
        )

        if result:
            files = getattr(result, "files", result)
            if files and isinstance(files, list) and len(files) > 0:
                path = files[0].path
                if path:
                    with open(cast(str, path), "r", encoding="utf-8") as f:
                        template = json.load(f)
                    self.app_state.apply_character_template(index, template)
                    self._show_toast(f"已加载角色模版: {os.path.basename(cast(str, path))}")
                    return True
        return False

    # --- 圣遗物套装操作 ---
    async def save_artifact_set(self, index: int):
        target_dir = os.path.join(self.base_data_dir, "artifact")
        os.makedirs(target_dir, exist_ok=True)

        picker = ft.FilePicker()
        self.page.overlay.append(picker)
        self.page.update()

        path = await picker.save_file(
            dialog_title="导出圣遗物五件套",
            initial_directory=target_dir,
            file_name="artifact_set.json"
        )

        if path:
            data = self.app_state.export_artifact_set(index)
            self.app_state.save_config(path, data=data)
            self._show_toast("圣遗物套装已保存")
            return True
        return False

    async def load_artifact_set(self, index: int):
        target_dir = os.path.join(self.base_data_dir, "artifact")
        os.makedirs(target_dir, exist_ok=True)

        picker = ft.FilePicker()
        self.page.overlay.append(picker)
        self.page.update()

        result = await picker.pick_files(
            dialog_title="读取圣遗物套装",
            initial_directory=target_dir,
            allowed_extensions=["json"]
        )

        if result:
            files = getattr(result, "files", result)
            if files and isinstance(files, list) and len(files) > 0:
                path = files[0].path
                if path:
                    with open(cast(str, path), "r", encoding="utf-8") as f:
                        template = json.load(f)
                    self.app_state.apply_artifact_set(index, template)
                    self._show_toast("圣遗物套装已加载")
                    return True
        return False
