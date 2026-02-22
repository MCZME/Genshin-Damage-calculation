import flet as ft
import json
import os
from typing import Optional, Dict, Any
from core.logger import get_ui_logger

class PersistenceManager:
    """
    持久化管理器：解耦 UI 视图与文件系统操作。
    采用 Flet V3 推荐的异步返回模式 (Async Return Path)。
    """
    def __init__(self, page: ft.Page, app_state):
        self.page = page
        self.app_state = app_state
        # 获取项目根目录下的 data 路径
        self.base_data_dir = os.path.abspath(os.path.join(os.getcwd(), "data"))
        os.makedirs(self.base_data_dir, exist_ok=True)



    def _show_toast(self, text: str):
        self.page.snack_bar = ft.SnackBar(ft.Text(text))
        self.page.snack_bar.open = True
        self.page.update()

    # --- 全量配置操作 ---
    async def load_config(self):
        # 按照用户示例：直接瞬间实例化并调用
        target_dir = os.path.join(self.base_data_dir, "configs")
        os.makedirs(target_dir, exist_ok=True)
        
        files = await ft.FilePicker().pick_files(
            dialog_title="读取仿真配置",
            initial_directory=target_dir,
            allowed_extensions=["json"]
        )


        if files:
            path = files[0].path
            await self.app_state.load_config(path)
            self._show_toast(f"已加载配置: {os.path.basename(path)}")
            return True
        return False

    async def save_config(self):
        target_dir = os.path.join(self.base_data_dir, "configs")
        os.makedirs(target_dir, exist_ok=True)

        path = await ft.FilePicker().save_file(
            dialog_title="保存当前配置",
            initial_directory=target_dir,
            file_name="sim_config.json"
        )


        if path:
            self.app_state.save_config(path)
            self._show_toast(f"配置已保存: {os.path.basename(path)}")
            return True
        return False

    # --- 角色模版操作 ---
    async def save_character_template(self, index: int):
        member = self.app_state.strategic_state.team_data[index]
        name = member.get("name", "character")
        target_dir = os.path.join(self.base_data_dir, "character")
        os.makedirs(target_dir, exist_ok=True)

        path = await ft.FilePicker().save_file(
            dialog_title=f"导出角色模解: {name}",
            initial_directory=target_dir,
            file_name=f"{name}_template.json"
        )


        if path:
            data = self.app_state.export_character_template(index)
            self.app_state.save_config(path, data=data)
            self._show_toast(f"角色模版已保存: {os.path.basename(path)}")
            return True
        return False

    async def load_character_template(self, index: int):
        target_dir = os.path.join(self.base_data_dir, "character")
        os.makedirs(target_dir, exist_ok=True)

        files = await ft.FilePicker().pick_files(
            dialog_title="读取角色模版",
            initial_directory=target_dir,
            allowed_extensions=["json"]
        )


        if files:
            path = files[0].path
            with open(path, "r", encoding="utf-8") as f:
                template = json.load(f)
            self.app_state.apply_character_template(index, template)
            self._show_toast(f"已加载角色模版: {os.path.basename(path)}")
            return True
        return False

    # --- 圣遗物套装操作 ---
    async def save_artifact_set(self, index: int):
        target_dir = os.path.join(self.base_data_dir, "artifact")
        os.makedirs(target_dir, exist_ok=True)

        path = await ft.FilePicker().save_file(
            dialog_title="导出圣遗物五件套",
            initial_directory=target_dir,
            file_name="artifact_set.json"
        )


        if path:
            data = self.app_state.export_artifact_set(index)
            self.app_state.save_config(path, data=data)
            self._show_toast(f"圣遗物套装已保存")
            return True
        return False

    async def load_artifact_set(self, index: int):
        target_dir = os.path.join(self.base_data_dir, "artifact")
        os.makedirs(target_dir, exist_ok=True)

        files = await ft.FilePicker().pick_files(
            dialog_title="读取圣遗物套装",
            initial_directory=target_dir,
            allowed_extensions=["json"]
        )


        if files:
            path = files[0].path
            with open(path, "r", encoding="utf-8") as f:
                template = json.load(f)
            self.app_state.apply_artifact_set(index, template)
            self._show_toast(f"圣遗物套装已加载")
            return True
        return False
