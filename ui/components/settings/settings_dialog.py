"""设置对话框主组件。"""
from __future__ import annotations

import flet as ft
from typing import TYPE_CHECKING, cast, Callable, Any

from ui.theme import GenshinTheme
from ui.states.settings_state import SettingsState
from ui.view_models.settings_vm import SettingsViewModel
from ui.components.settings.config_switch_item import ConfigSwitchItem
from ui.components.settings.config_text_item import ConfigTextItem
from ui.components.settings.config_path_item import ConfigPathItem
from core.logger import get_ui_logger

if TYPE_CHECKING:
    from flet import Page

_logger = get_ui_logger()


def _show_toast(page: "Page", message: str) -> None:
    """显示提示消息"""
    snack = ft.SnackBar(
        content=ft.Text(message, color=ft.Colors.WHITE),
        bgcolor=GenshinTheme.SURFACE_VARIANT,
        duration=2000,
    )
    page.show_dialog(snack)


def _build_emulation_section(state: SettingsState) -> ft.Control:
    """构建仿真设置分组"""
    return ft.Column(
        [
            ConfigSwitchItem(
                label="启用暴击",
                description="是否启用暴击计算",
                value=bool(state.get_value("emulation.open_critical", True)),
                on_change=lambda v: state.set_value("emulation.open_critical", v),
            ),
        ],
        spacing=8,
    )


def _build_database_section(state: SettingsState) -> ft.Control:
    """构建数据库连接分组"""
    return ft.Column(
        [
            ConfigTextItem(
                label="主机地址",
                value=str(state.get_value("database.host", "")),
                on_change=lambda v: state.set_value("database.host", v),
            ),
            ft.Row(
                [
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    "用户名",
                                    size=12,
                                    weight=ft.FontWeight.W_500,
                                    color=GenshinTheme.TEXT_SECONDARY,
                                ),
                                ft.TextField(
                                    value=str(state.get_value("database.username", "")),
                                    on_change=lambda e: state.set_value(
                                        "database.username", e.control.value or ""
                                    ),
                                    dense=True,
                                    text_size=13,
                                    border_color=ft.Colors.WHITE_24,
                                    bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                                    cursor_color=GenshinTheme.PRIMARY,
                                    expand=True,
                                ),
                            ],
                            spacing=4,
                        ),
                        padding=ft.Padding(12, 8, 12, 8),
                        bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.WHITE),
                        border_radius=8,
                        expand=True,
                    ),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    "密码",
                                    size=12,
                                    weight=ft.FontWeight.W_500,
                                    color=GenshinTheme.TEXT_SECONDARY,
                                ),
                                ft.TextField(
                                    value=str(state.get_value("database.password", "")),
                                    on_change=lambda e: state.set_value(
                                        "database.password", e.control.value or ""
                                    ),
                                    password=True,
                                    can_reveal_password=True,
                                    dense=True,
                                    text_size=13,
                                    border_color=ft.Colors.WHITE_24,
                                    bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                                    cursor_color=GenshinTheme.PRIMARY,
                                    expand=True,
                                ),
                            ],
                            spacing=4,
                        ),
                        padding=ft.Padding(12, 8, 12, 8),
                        bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.WHITE),
                        border_radius=8,
                        expand=True,
                    ),
                ],
                spacing=10,
            ),
            ft.Row(
                [
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    "数据库",
                                    size=12,
                                    weight=ft.FontWeight.W_500,
                                    color=GenshinTheme.TEXT_SECONDARY,
                                ),
                                ft.TextField(
                                    value=str(state.get_value("database.database", "")),
                                    on_change=lambda e: state.set_value(
                                        "database.database", e.control.value or ""
                                    ),
                                    dense=True,
                                    text_size=13,
                                    border_color=ft.Colors.WHITE_24,
                                    bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                                    cursor_color=GenshinTheme.PRIMARY,
                                    expand=True,
                                ),
                            ],
                            spacing=4,
                        ),
                        padding=ft.Padding(12, 8, 12, 8),
                        bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.WHITE),
                        border_radius=8,
                        expand=True,
                    ),
                    ft.Container(
                        content=ft.Column(
                            [
                            ft.Text(
                                "端口",
                                size=12,
                                weight=ft.FontWeight.W_500,
                                color=GenshinTheme.TEXT_SECONDARY,
                            ),
                            ft.TextField(
                                value=str(state.get_value("database.port", 3306)),
                                on_change=lambda e: state.set_value(
                                    "database.port",
                                    int(e.control.value or 3306),
                                ),
                                dense=True,
                                text_size=13,
                                keyboard_type=ft.KeyboardType.NUMBER,
                                border_color=ft.Colors.WHITE_24,
                                bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                                cursor_color=GenshinTheme.PRIMARY,
                                expand=True,
                            ),
                            ],
                            spacing=4,
                        ),
                        padding=ft.Padding(12, 8, 12, 8),
                        bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.WHITE),
                        border_radius=8,
                        expand=True,
                    ),
                ],
                spacing=10,
            ),
        ],
        spacing=10,
    )


def _build_logging_section(state: SettingsState) -> ft.Control:
    """构建日志设置分组"""
    emulation_items = [
        ("console", "控制台输出"),
        ("damage", "伤害日志"),
        ("heal", "治疗日志"),
        ("energy", "能量日志"),
        ("effect", "效果日志"),
        ("reaction", "反应日志"),
        ("object", "对象日志"),
        ("debug", "调试日志"),
    ]

    ui_items = [
        ("console", "控制台输出"),
        ("button_click", "按钮点击"),
        ("window_open", "窗口打开"),
        ("debug", "调试日志"),
    ]

    emulation_switches = [
        ConfigSwitchItem(
            label=label,
            description=f"Emulation.{key}",
            value=bool(state.get_value(f"logging.Emulation.{key}", False)),
            on_change=cast(Callable[[bool], Any], lambda v, k=key: state.set_value(f"logging.Emulation.{k}", v)),
        )
        for key, label in emulation_items
    ]

    ui_switches = [
        ConfigSwitchItem(
            label=label,
            description=f"UI.{key}",
            value=bool(state.get_value(f"logging.UI.{key}", False)),
            on_change=cast(Callable[[bool], Any], lambda v, k=key: state.set_value(f"logging.UI.{k}", v)),
        )
        for key, label in ui_items
    ]

    return ft.Column(
        [
            ConfigSwitchItem(
                label="保存日志文件",
                description="全局日志保存开关",
                value=bool(state.get_value("logging.save_file", True)),
                on_change=lambda v: state.set_value("logging.save_file", v),
            ),
            ft.Divider(height=1, color=GenshinTheme.GLASS_BORDER),
            ft.Text(
                "仿真日志",
                size=11,
                weight=ft.FontWeight.BOLD,
                color=GenshinTheme.TEXT_SECONDARY,
            ),
            *emulation_switches,
            ft.Divider(height=1, color=GenshinTheme.GLASS_BORDER),
            ft.Text(
                "UI 日志",
                size=11,
                weight=ft.FontWeight.BOLD,
                color=GenshinTheme.TEXT_SECONDARY,
            ),
            *ui_switches,
        ],
        spacing=6,
    )


def _build_ui_section(state: SettingsState, page: "Page") -> ft.Control:
    """构建界面路径分组"""
    return ft.Column(
        [
            ConfigPathItem(
                label="角色文件路径",
                value=str(state.get_value("ui.character_file_path", "./data/character/")),
                on_change=lambda v: state.set_value("ui.character_file_path", v),
                page=page,
                browse_type="folder",
            ),
            ConfigPathItem(
                label="圣遗物文件路径",
                value=str(state.get_value("ui.artifact_file_path", "./data/artifact/")),
                on_change=lambda v: state.set_value("ui.artifact_file_path", v),
                page=page,
                browse_type="folder",
            ),
        ],
        spacing=10,
    )


def _build_section_content(section_id: str, state: SettingsState, page: "Page") -> ft.Control:
    """构建分组内容"""
    if section_id == "emulation":
        return _build_emulation_section(state)
    elif section_id == "database":
        return _build_database_section(state)
    elif section_id == "logging":
        return _build_logging_section(state)
    elif section_id == "ui":
        return _build_ui_section(state, page)
    return ft.Container()


@ft.component
def SettingsDialog(
    vm: SettingsViewModel,
    state: SettingsState,
    page: "Page",
) -> ft.Control:
    """
    设置对话框主组件。

    Args:
        vm: 设置视图模型
        state: 设置状态
        page: Flet Page 对象
    """

    def close_dialog() -> None:
        _logger.log_info("关闭设置对话框")
        vm.close()

    def handle_save() -> None:
        _logger.log_info("保存配置到文件")
        state.save_to_config()
        _show_toast(page, "配置已保存")
        vm.close()

    def handle_reset() -> None:
        _logger.log_info("撤销配置修改")
        state.reset_to_config()
        _show_toast(page, "已撤销所有修改")

    def build_section_header(section: dict) -> ft.Control:
        is_expanded = state.expanded_section == section["id"]

        def on_header_click(_) -> None:
            _logger.log_debug(f"切换配置分组: {section['id']}")
            state.toggle_section(section["id"])

        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(section["icon"], color=GenshinTheme.PRIMARY, size=20),
                    ft.Column(
                        [
                            ft.Text(
                                section["title"],
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=GenshinTheme.ON_SURFACE,
                            ),
                            ft.Text(
                                section["description"],
                                size=10,
                                color=GenshinTheme.TEXT_SECONDARY,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Icon(
                        ft.Icons.EXPAND_MORE if is_expanded else ft.Icons.CHEVRON_RIGHT,
                        color=GenshinTheme.TEXT_SECONDARY,
                        size=20,
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=ft.Padding(16, 12, 16, 12),
            bgcolor=ft.Colors.with_opacity(0.08 if is_expanded else 0.02, ft.Colors.WHITE),
            border_radius=12,
            on_click=on_header_click,
            animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
        )

    def build_section(section: dict) -> ft.Control:
        is_expanded = state.expanded_section == section["id"]
        content = _build_section_content(section["id"], state, page) if is_expanded else ft.Container()

        return ft.Column(
            [
                build_section_header(section),
                ft.Container(
                    content=content,
                    visible=is_expanded,
                    padding=ft.Padding(16, 8, 16, 8),
                    animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
                ),
            ],
            spacing=0,
        )

    dialog_content = ft.Container(
        content=ft.Column(
            [
                # 标题栏
                ft.Row(
                    [
                        ft.Icon(ft.Icons.SETTINGS, color=GenshinTheme.PRIMARY, size=24),
                        ft.Text(
                            "系统设置",
                            size=18,
                            weight=ft.FontWeight.W_900,
                            color=GenshinTheme.ON_SURFACE,
                        ),
                        ft.Container(expand=True),
                        ft.IconButton(
                            ft.Icons.CLOSE,
                            icon_color=GenshinTheme.TEXT_SECONDARY,
                            on_click=lambda _: close_dialog(),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                ft.Divider(height=1, color=GenshinTheme.GLASS_BORDER),
                # 配置分组列表
                ft.Column(
                    [build_section(s) for s in vm.sections],
                    spacing=8,
                    expand=True,
                    scroll=ft.ScrollMode.ADAPTIVE,
                ),
                ft.Divider(height=1, color=GenshinTheme.GLASS_BORDER),
                # 底部操作栏
                ft.Row(
                    [
                        ft.TextButton(
                            "撤销修改",
                            icon=ft.Icons.RESTORE,
                            on_click=lambda _: handle_reset(),
                        ),
                        ft.Container(expand=True),
                        ft.Button(
                            "保存配置",
                            icon=ft.Icons.SAVE,
                            bgcolor=GenshinTheme.PRIMARY,
                            color=GenshinTheme.ON_PRIMARY,
                            on_click=lambda _: handle_save(),
                            disabled=not state.is_dirty,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            spacing=12,
        ),
        width=520,
        height=600,
        bgcolor=GenshinTheme.SURFACE,
        border_radius=16,
        border=ft.Border.all(1, GenshinTheme.GLASS_BORDER),
        shadow=[
            ft.BoxShadow(
                blur_radius=40,
                color=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
                offset=ft.Offset(0, 10),
            )
        ],
        padding=20,
    )

    # 全屏遮罩 + 对话框
    return ft.Stack(
        [
        # 遮罩层
        ft.Container(
            bgcolor=ft.Colors.with_opacity(0.6, ft.Colors.BLACK),
            visible=vm.is_open,
            on_click=lambda _: close_dialog(),
            expand=True,
        ),
        # 对话框
        ft.Container(
            content=dialog_content,
            visible=vm.is_open,
            alignment=ft.Alignment.CENTER,
            expand=True,
            animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
        ),
        ],
        expand=True,
    )
