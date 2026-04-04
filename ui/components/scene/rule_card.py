"""规则卡片组件。"""

from __future__ import annotations

import flet as ft
from typing import Any, TYPE_CHECKING

from ui.theme import GenshinTheme
from core.rules import ApplyMode

if TYPE_CHECKING:
    from ui.view_models.scene.rules_vm import RuleInstanceVM, RulesViewModel


class RuleCard(ft.Container):
    """
    单条规则实例配置卡片。

    直接绑定 RuleInstanceVM，显示规则类型、目标和参数。
    """

    def __init__(
        self,
        instance: "RuleInstanceVM",
        view_model: "RulesViewModel",
        **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        self.instance = instance
        self.vm = view_model

        self.bgcolor = ft.Colors.with_opacity(0.03, ft.Colors.WHITE)
        self.border_radius = 12
        self.padding = 15
        self.border = ft.Border.all(1, ft.Colors.with_opacity(0.08, ft.Colors.WHITE))

        self.content = self._build_content()

    def _build_content(self) -> ft.Control:
        rule_type_id = self.instance.rule_type_id
        target = self.instance.target
        params = self.instance.params

        # 获取规则类型
        rule_type = self.instance.get_rule_type()
        display_name = rule_type.display_name if rule_type else rule_type_id
        description = rule_type.description if rule_type else ""
        schema = rule_type.get_schema() if rule_type else {}

        # 获取应用模式标签
        apply_mode = self._get_apply_mode(rule_type)

        # 标题行：规则类型 + 应用模式标签 + 删除按钮
        header = ft.Row([
            ft.Icon(ft.Icons.TUNE, size=16, color=GenshinTheme.PRIMARY),
            ft.Text(
                display_name,
                size=14,
                weight=ft.FontWeight.W_600,
                color=GenshinTheme.ON_SURFACE,
            ),
            ft.Container(
                content=ft.Text(
                    apply_mode,
                    size=10,
                    color=GenshinTheme.PRIMARY,
                ),
                bgcolor=ft.Colors.with_opacity(0.1, GenshinTheme.PRIMARY),
                border_radius=4,
                padding=ft.Padding(4, 2, 4, 2),
            ),
            ft.Container(expand=True),
            ft.IconButton(
                ft.Icons.DELETE_OUTLINE,
                icon_size=18,
                icon_color=GenshinTheme.TEXT_SECONDARY,
                on_click=lambda _: self.vm.remove_rule(self.instance.instance_id),
                tooltip="删除规则"
            ),
        ], alignment=ft.MainAxisAlignment.START, spacing=8)

        # 描述文本（如果有）
        description_text = None
        if description:
            description_text = ft.Text(
                description,
                size=11,
                color=GenshinTheme.TEXT_SECONDARY,
            )

        # 目标选择
        target_dropdown = ft.Dropdown(
            label="目标",
            value=target,
            options=[
                ft.dropdown.Option(k, v)
                for k, v in self.vm.target_display_names.items()
            ],
            dense=True,
            text_size=12,
            width=150,
            border_color=ft.Colors.WHITE_24,
            on_select=lambda e: self.vm.update_rule_target(
                self.instance.instance_id, e.control.value
            ),
        )

        # 参数控件（根据 schema 动态生成）
        param_controls = self._build_param_controls(schema, params)

        # 构建内容列
        content_controls: list[ft.Control] = [header]
        if description_text:
            content_controls.append(description_text)
        content_controls.append(ft.Row([target_dropdown], spacing=10))
        content_controls.append(
            ft.Container(
                content=ft.Column(param_controls, spacing=8),
                padding=ft.Padding(10, 5, 0, 0),
            )
        )

        return ft.Column(content_controls, spacing=10)

    def _get_apply_mode(self, rule_type: Any) -> str:
        """获取应用模式的显示文本。"""
        if rule_type is None:
            return "未知"
        if rule_type.apply_mode == ApplyMode.ONCE:
            return "一次性"
        elif rule_type.apply_mode == ApplyMode.SUBSCRIBE:
            return "订阅"
        return "未知"

    def _build_param_controls(
        self, schema: dict, current_params: dict
    ) -> list[ft.Control]:
        """根据 schema 动态构建参数控件。"""
        controls: list[ft.Control] = []

        for param in schema.get("params", []):
            param_key = param["key"]
            param_label = param["label"]
            param_type = param.get("type", "number")
            current_value = current_params.get(param_key, param.get("default"))

            if param_type == "number":
                control: ft.Control = ft.Row([
                    ft.Text(
                        param_label,
                        size=12,
                        color=GenshinTheme.TEXT_SECONDARY,
                        width=80
                    ),
                    ft.Slider(
                        min=param.get("min", 0),
                        max=param.get("max", 100),
                        divisions=param.get("divisions"),
                        value=float(current_value) if current_value is not None else param.get("default", 0),
                        on_change=lambda e, k=param_key: self.vm.update_rule_param(
                            self.instance.instance_id, k, float(e.control.value)
                        ),
                        expand=True,
                        active_color=GenshinTheme.PRIMARY,
                    ),
                    ft.Text(
                        f"{current_value}{param.get('unit', '')}",
                        size=12,
                        width=60,
                        text_align=ft.TextAlign.RIGHT
                    ),
                ], alignment=ft.MainAxisAlignment.START)

            elif param_type == "select":
                options = param.get("options", [])
                if isinstance(options, list):
                    dropdown_options = [ft.dropdown.Option(str(opt)) for opt in options]
                else:
                    dropdown_options = [ft.dropdown.Option(k, v) for k, v in options.items()]

                control = ft.Row([
                    ft.Text(
                        param_label,
                        size=12,
                        color=GenshinTheme.TEXT_SECONDARY,
                        width=80
                    ),
                    ft.Dropdown(
                        value=str(current_value),
                        options=dropdown_options,
                        dense=True,
                        text_size=12,
                        expand=True,
                        border_color=ft.Colors.WHITE_24,
                        on_select=lambda e, k=param_key: self.vm.update_rule_param(
                            self.instance.instance_id, k, e.control.value
                        ),
                    ),
                ], alignment=ft.MainAxisAlignment.START)

            else:
                control = ft.TextField(
                    label=param_label,
                    value=str(current_value) if current_value is not None else "",
                    dense=True,
                    text_size=12,
                    border_color=ft.Colors.WHITE_24,
                    on_change=lambda e, k=param_key: self.vm.update_rule_param(
                        self.instance.instance_id, k, e.control.value
                    ),
                )

            controls.append(control)

        return controls
