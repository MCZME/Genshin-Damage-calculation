"""规则编辑器组件。"""

from __future__ import annotations

import flet as ft
from typing import TYPE_CHECKING, cast

from ui.theme import GenshinTheme
from ui.components.scene.rule_card import RuleCard

if TYPE_CHECKING:
    from ui.view_models.scene.rules_vm import RulesViewModel
    from ui.services.persistence_manager import PersistenceManager


@ft.component
def RulesEditor(vm: "RulesViewModel", persistence: "PersistenceManager") -> ft.Control:
    """
    规则编辑器组件。

    包含规则列表、添加规则按钮、加载/保存按钮。
    """

    # 规则卡片列表（直接绑定 VM 实例）
    rule_cards = [
        RuleCard(instance, vm)
        for instance in vm.instances
    ]

    # 添加规则按钮的菜单项
    add_menu_items: list[ft.PopupMenuItem] = []
    for rule_type_id, schema in vm.rule_type_schemas.items():
        display_name = schema.get("display_name", rule_type_id)
        description = schema.get("description", "")
        menu_content: list[ft.Control] = [
            ft.Text(display_name, size=13),
        ]
        if description:
            menu_content.append(
                ft.Text(description, size=10, color=GenshinTheme.TEXT_SECONDARY)
            )
        add_menu_items.append(
            ft.PopupMenuItem(
                content=ft.Column(menu_content, spacing=2, tight=True),
                icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                on_click=lambda _, rt=rule_type_id: vm.add_rule(rt),
            )
        )

    # 标题行（包含操作按钮）
    header_row = ft.Row([
        ft.Icon(ft.Icons.SETTINGS_SUGGEST, color=GenshinTheme.PRIMARY, size=18),
        ft.Text("规则配置", size=16, weight=ft.FontWeight.BOLD, color=GenshinTheme.ON_SURFACE),
        ft.Container(expand=True),
        # 添加规则按钮
        ft.PopupMenuButton(
            icon=ft.Icons.ADD,
            icon_color=GenshinTheme.PRIMARY,
            tooltip="添加规则",
            items=add_menu_items,
        ),
        # 加载按钮
        ft.IconButton(
            ft.Icons.FOLDER_OPEN,
            icon_color=GenshinTheme.TEXT_SECONDARY,
            tooltip="加载",
            on_click=lambda _: persistence.page.run_task(persistence.load_rules_config),
        ),
        # 保存按钮
        ft.IconButton(
            ft.Icons.SAVE,
            icon_color=GenshinTheme.TEXT_SECONDARY,
            tooltip="保存",
            on_click=lambda _: persistence.page.run_task(persistence.save_rules_config),
        ),
        # 清空按钮
        ft.IconButton(
            ft.Icons.DELETE_SWEEP,
            icon_color=GenshinTheme.TEXT_SECONDARY,
            tooltip="清空",
            on_click=lambda _: vm.clear_rules(),
        ),
    ], spacing=8)

    # 规则列表面板
    rules_panel = ft.Column(
        controls=cast(list[ft.Control], rule_cards) if rule_cards else [
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.RULE, size=32, color=ft.Colors.WHITE_24),
                    ft.Text("暂无规则配置", size=12, color=GenshinTheme.TEXT_SECONDARY),
                    ft.Text("点击上方添加按钮创建规则", size=11, color=ft.Colors.WHITE_38),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                alignment=ft.Alignment.CENTER,
                expand=True,
            )
        ],
        spacing=10,
        scroll=ft.ScrollMode.ADAPTIVE,
        expand=True,
    )

    # 主容器
    main_content = ft.Column([
        header_row,
        ft.Divider(height=1, color=GenshinTheme.GLASS_BORDER),
        rules_panel,
    ], spacing=12)

    return ft.Container(
        content=main_content,
        padding=15,
        bgcolor=ft.Colors.with_opacity(0.02, ft.Colors.WHITE),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.05, ft.Colors.WHITE)),
        border_radius=15,
        expand=True,
    )
