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

    紧凑型设计，适用于网格布局。
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

        # 根据启用状态设置样式
        self.bgcolor = (
            ft.Colors.with_opacity(0.03, ft.Colors.WHITE)
            if instance.enabled
            else ft.Colors.with_opacity(0.015, ft.Colors.WHITE)
        )
        self.border_radius = 12
        self.padding = 12
        self.border = ft.Border.all(
            1,
            ft.Colors.with_opacity(0.1 if instance.enabled else 0.05, ft.Colors.WHITE)
        )

        self.content = self._build_content()

    def _build_content(self) -> ft.Control:
        rule_type_id = self.instance.rule_type_id
        params = self.instance.params

        # 获取规则类型
        rule_type = self.instance.get_rule_type()
        display_name = rule_type.display_name if rule_type else rule_type_id
        schema = rule_type.get_schema() if rule_type else {}

        # 获取应用模式标签
        apply_mode = self._get_apply_mode(rule_type)

        # 标题行：规则名称 + 应用模式标签 + 删除按钮
        header = ft.Row([
            ft.Icon(
                ft.Icons.TUNE,
                size=14,
                color=GenshinTheme.PRIMARY if self.instance.enabled else GenshinTheme.TEXT_SECONDARY
            ),
            ft.Text(
                display_name,
                size=13,
                weight=ft.FontWeight.W_600,
                color=GenshinTheme.ON_SURFACE if self.instance.enabled else GenshinTheme.TEXT_SECONDARY,
                overflow=ft.TextOverflow.ELLIPSIS,
                expand=True,
            ),
            ft.Container(
                content=ft.Text(
                    apply_mode,
                    size=9,
                    color=GenshinTheme.PRIMARY if self.instance.enabled else GenshinTheme.TEXT_SECONDARY,
                ),
                bgcolor=ft.Colors.with_opacity(0.1, GenshinTheme.PRIMARY if self.instance.enabled else ft.Colors.WHITE),
                border_radius=4,
                padding=ft.Padding(4, 1, 4, 1),
            ),
            ft.IconButton(
                ft.Icons.DELETE_OUTLINE,
                icon_size=16,
                icon_color=GenshinTheme.TEXT_SECONDARY,
                on_click=lambda _: self.vm.remove_rule(self.instance.instance_id),
                tooltip="删除规则",
                style=ft.ButtonStyle(padding=4),
            ),
        ], alignment=ft.MainAxisAlignment.START, spacing=6)

        # 参数控件（紧凑型）
        param_controls = self._build_param_controls(schema, params)

        # 构建内容
        content_controls: list[ft.Control] = [header]
        if param_controls:
            content_controls.append(
                ft.Container(
                    content=ft.Column(param_controls, spacing=6),
                    padding=ft.Padding(0, 6, 0, 0),
                )
            )

        return ft.Column(content_controls, spacing=8)

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
        """根据 schema 动态构建参数控件（紧凑型）。"""
        controls: list[ft.Control] = []

        for param in schema.get("params", []):
            param_key = param["key"]
            param_label = param["label"]
            param_type = param.get("type", "number")
            current_value = current_params.get(param_key, param.get("default"))

            if param_type == "number":
                # 数值显示（用于 Slider 旁边）
                value_text = ft.Text(
                    f"{current_value}{param.get('unit', '')}",
                    size=11,
                    color=GenshinTheme.TEXT_SECONDARY,
                    width=50,
                    text_align=ft.TextAlign.RIGHT,
                    key=f"value_{param_key}",  # 用于后续更新
                )

                control: ft.Control = ft.Column([
                    ft.Row([
                        ft.Text(
                            param_label,
                            size=11,
                            color=GenshinTheme.TEXT_SECONDARY,
                        ),
                        ft.Container(expand=True),
                        value_text,
                    ], spacing=0),
                    ft.Slider(
                        min=param.get("min", 0),
                        max=param.get("max", 100),
                        divisions=param.get("divisions"),
                        value=float(current_value) if current_value is not None else param.get("default", 0),
                        on_change=lambda e, k=param_key, vt=value_text, u=param.get('unit', ''): self._on_slider_change(e, k, vt, u),
                        expand=True,
                        active_color=GenshinTheme.PRIMARY,
                        height=20,
                    ),
                ], spacing=2, tight=True)

            elif param_type == "select":
                options = param.get("options", [])
                if isinstance(options, list):
                    dropdown_options = [ft.dropdown.Option(str(opt)) for opt in options]
                else:
                    dropdown_options = [ft.dropdown.Option(k, v) for k, v in options.items()]

                control = ft.Row([
                    ft.Text(
                        param_label,
                        size=11,
                        color=GenshinTheme.TEXT_SECONDARY,
                    ),
                    ft.Dropdown(
                        value=str(current_value),
                        options=dropdown_options,
                        dense=True,
                        text_size=11,
                        expand=True,
                        border_color=ft.Colors.WHITE_24,
                        content_padding=ft.Padding(8, 4, 8, 4),
                        on_select=lambda e, k=param_key: self.vm.update_rule_param(
                            self.instance.instance_id, k, e.control.value
                        ),
                    ),
                ], alignment=ft.MainAxisAlignment.START, spacing=8)

            else:
                control = ft.TextField(
                    label=param_label,
                    value=str(current_value) if current_value is not None else "",
                    dense=True,
                    text_size=11,
                    border_color=ft.Colors.WHITE_24,
                    content_padding=ft.Padding(8, 4, 8, 4),
                    on_change=lambda e, k=param_key: self.vm.update_rule_param(
                        self.instance.instance_id, k, e.control.value
                    ),
                )

            controls.append(control)

        return controls

    def _on_slider_change(
        self,
        e: ft.ControlEvent,
        param_key: str,
        value_text: ft.Text,
        unit: str
    ) -> None:
        """Slider 值变化时更新参数和显示文本。"""
        slider = e.control
        if slider is None:
            return
        new_value = float(getattr(slider, "value", 0) or 0)
        self.vm.update_rule_param(self.instance.instance_id, param_key, new_value)
        value_text.value = f"{new_value:.0f}{unit}"
        value_text.update()
