"""设置视图模型。"""
from __future__ import annotations

import flet as ft
from dataclasses import dataclass, field
from typing import Any, cast


@ft.observable
@dataclass
class SettingsViewModel:
    """
    设置视图模型。

    管理界面交互状态和配置分组元数据。
    """

    # 对话框可见性
    is_open: bool = False

    # 配置分组定义
    sections: list[dict] = field(
        default_factory=lambda: [
            {
                "id": "emulation",
                "title": "仿真设置",
                "icon": ft.Icons.SCIENCE,
                "description": "核心仿真参数配置",
            },
            {
                "id": "database",
                "title": "数据库连接",
                "icon": ft.Icons.STORAGE,
                "description": "MySQL 数据库连接配置",
            },
            {
                "id": "logging",
                "title": "日志设置",
                "icon": ft.Icons.ARTICLE,
                "description": "仿真日志与 UI 日志配置",
            },
            {
                "id": "ui",
                "title": "界面路径",
                "icon": ft.Icons.FOLDER,
                "description": "文件存储路径配置",
            },
        ]
    )

    def notify_update(self) -> None:
        """触发 UI 更新"""
        cast(Any, self).notify()

    def open(self) -> None:
        """打开对话框"""
        self.is_open = True
        self.notify_update()

    def close(self) -> None:
        """关闭对话框"""
        self.is_open = False
        self.notify_update()

    def toggle(self) -> None:
        """切换对话框状态"""
        self.is_open = not self.is_open
        self.notify_update()
