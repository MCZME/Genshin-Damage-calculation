"""
[V9.5] 状态胶囊组件

提供标准化的状态效果展示组件，支持两种模式：
- Mini 模式：仪表盘使用，微型胶囊显示效果名前2字
- Expanded 模式：审计详情区使用，显示全名和剩余帧数进度条
"""
import flet as ft
from typing import Any


@ft.component
def StatusCapsule(
    name: str,
    remaining_frames: int | None,
    total_duration_frames: int | None,
    mode: str = "mini",
    bgcolor: str = ft.Colors.BLACK_26
):
    """
    [V9.5] 状态胶囊组件

    Args:
        name: 效果名称
        remaining_frames: 剩余帧数（None 表示无限持续时间）
        total_duration_frames: 总持续时间（帧数）
        mode: "mini" | "expanded"
            - mini: 微型胶囊，用于仪表盘
            - expanded: 展开药丸状，用于审计详情区
        bgcolor: 背景颜色

    Mini 模式特性：
    - 微型胶囊，显示效果名前2字
    - tooltip 显示完整名称

    Expanded 模式特性：
    - 标准药丸状：图标 + 全名 + 剩余帧数 (如 "45F")
    - 内底部嵌入细长进度条（剩余帧/总帧，由右向左变短）
    """
    if mode == "mini":
        return _render_mini_capsule(name, remaining_frames, bgcolor)
    else:
        return _render_expanded_capsule(name, remaining_frames, total_duration_frames, bgcolor)


def _render_mini_capsule(
    name: str,
    remaining_frames: int | None,
    bgcolor: str
) -> ft.Control:
    """渲染 Mini 模式胶囊（仪表盘使用）"""
    display_name = name[:2] if len(name) > 2 else name

    # 构建 tooltip 内容
    tooltip_parts = [name]
    if remaining_frames is not None:
        tooltip_parts.append(f"剩余 {remaining_frames} 帧")
    else:
        tooltip_parts.append("无限持续时间")
    tooltip_text = "\n".join(tooltip_parts)

    return ft.Container(
        content=ft.Text(
            display_name,
            size=8,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE
        ),
        bgcolor=bgcolor,
        padding=ft.Padding(left=4, right=4, top=1, bottom=1),
        border_radius=3,
        tooltip=tooltip_text
    )


def _render_expanded_capsule(
    name: str,
    remaining_frames: int | None,
    total_duration_frames: int | None,
    bgcolor: str
) -> ft.Control:
    """
    渲染 Expanded 模式胶囊（审计详情区使用）

    布局结构：
    ┌─────────────────────────────────┐
    │ ⚡ 效果名称              45F    │
    │ ▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░ │ <- 进度条（由右向左变短）
    └─────────────────────────────────┘
    """
    # 剩余帧数显示
    if remaining_frames is not None:
        frame_text = f"{remaining_frames}F"
    else:
        frame_text = "∞"

    # 计算进度条值（由右向左变短，所以用 1 - ratio）
    progress_value = 0.0
    if remaining_frames is not None and total_duration_frames is not None and total_duration_frames > 0:
        progress_value = remaining_frames / total_duration_frames
        progress_value = max(0.0, min(1.0, progress_value))

    # 主内容行
    main_row = ft.Row([
        ft.Icon(
            ft.Icons.BOLT_ROUNDED,
            size=12,
            color=ft.Colors.AMBER_400
        ),
        ft.Text(
            name,
            size=10,
            weight=ft.FontWeight.W_600,
            color=ft.Colors.WHITE,
            expand=True,
            no_wrap=True,
            overflow=ft.TextOverflow.ELLIPSIS
        ),
        ft.Text(
            frame_text,
            size=10,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.AMBER_200,
            font_family="Consolas"
        )
    ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    # 底部进度条
    progress_bar = ft.Container(
        content=ft.ProgressBar(
            value=progress_value,
            bar_height=2,
            color=ft.Colors.AMBER_400,
            bgcolor=ft.Colors.WHITE_10,
            expand=True
        ),
        padding=ft.Padding(top=2, bottom=0, left=0, right=0)
    )

    return ft.Container(
        content=ft.Column([
            main_row,
            progress_bar
        ], spacing=0),
        bgcolor=bgcolor,
        padding=ft.Padding(left=8, right=8, top=6, bottom=4),
        border_radius=6,
        width=140  # 固定宽度便于流式布局
    )


@ft.component
def StatusCapsuleWall(
    effects: list[dict[str, Any]],
    max_visible: int = 6,
    bgcolor: str = ft.Colors.BLACK_26
):
    """
    [V9.5] 仪表盘模式的状态胶囊墙（单行截断 + +N 显示）

    Args:
        effects: 效果列表，每个元素需包含 name, remaining_frames, total_duration_frames
        max_visible: 最多显示的胶囊数量，超出显示 +N
        bgcolor: 背景颜色
    """
    if not effects:
        return ft.Container()

    visible_effects = effects[:max_visible]
    hidden_count = len(effects) - max_visible

    capsules: list[ft.Control] = [
        StatusCapsule(
            name=eff["name"],
            remaining_frames=eff.get("remaining_frames"),
            total_duration_frames=eff.get("total_duration_frames"),
            mode="mini",
            bgcolor=bgcolor
        )
        for eff in visible_effects
    ]

    # 如果有隐藏的胶囊，显示 +N
    if hidden_count > 0:
        capsules.append(ft.Container(
            content=ft.Text(
                f"+{hidden_count}",
                size=8,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.WHITE_54
            ),
            bgcolor=ft.Colors.WHITE_12,
            padding=ft.Padding(left=4, right=4, top=1, bottom=1),
            border_radius=3
        ))

    return ft.Row(
        controls=capsules,
        spacing=4,
        wrap=False
    )


@ft.component
def StatusCapsuleGrid(
    effects: list[dict[str, Any]],
    bgcolor: str = ft.Colors.BLACK_26
):
    """
    [V9.5] 审计模式的 Expanded 状态胶囊网格（流式布局）

    Args:
        effects: 效果列表，每个元素需包含 name, remaining_frames, total_duration_frames
        bgcolor: 背景颜色
    """
    if not effects:
        return ft.Container(
            content=ft.Text(
                "当前帧无活跃状态效果",
                size=10,
                color=ft.Colors.WHITE_24,
                italic=True
            ),
            padding=ft.Padding.all(10)
        )

    capsules: list[ft.Control] = [
        StatusCapsule(
            name=eff["name"],
            remaining_frames=eff.get("remaining_frames"),
            total_duration_frames=eff.get("total_duration_frames"),
            mode="expanded",
            bgcolor=bgcolor
        )
        for eff in effects
    ]

    return ft.Column([
        ft.Text(
            f"活跃状态效果 ({len(effects)})",
            size=10,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE_54
        ),
        ft.Row(
            controls=capsules,
            spacing=8,
            wrap=True,
            run_spacing=8
        )
    ], spacing=6)
