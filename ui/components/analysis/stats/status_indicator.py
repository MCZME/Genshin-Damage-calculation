"""
[V9.5 Pro V2] 状态指示器组件

提供自适应状态条组件：
- StatusIndicator: 原子化状态指示器（HP条、能量条等）
- AdaptiveStatusCluster: 自适应状态集群，支持动态宽度分配
"""
import flet as ft
from typing import Any


@ft.component
def StatusIndicator(
    name: str,
    current: float,
    maximum: float,
    color: str,
    bar_height: int = 6,
    show_label: bool = False,
    selected: bool = False,
    checked: bool = False
) -> ft.Control:
    """
    [V9.5 Pro V2] 原子化状态指示器

    Args:
        name: 资源名称 (HP, Energy)
        current: 当前值
        maximum: 最大值
        color: 进度条颜色
        bar_height: 条高度 (默认 6)
        show_label: 是否显示标签
        selected: 是否处于选中状态（审计中）
        checked: 是否处于勾选状态（仪表盘可见）

    Returns:
        状态指示器组件
    """
    ratio = max(0.0, min(1.0, current / maximum)) if maximum > 0 else 0.0

    controls: list[ft.Control] = []

    # 可选标签
    if show_label:
        controls.append(
            ft.Text(
                name,
                size=9,
                color=ft.Colors.WHITE_54,
                weight=ft.FontWeight.W_500
            )
        )

    # 进度条
    controls.append(
        ft.ProgressBar(
            value=ratio,
            bar_height=bar_height,
            color=color,
            bgcolor=ft.Colors.WHITE_10,
            expand=True
        )
    )

    # 指示器主体
    indicator_body = ft.Column(
        controls=controls,
        spacing=2,
        expand=True
    )

    # 布局整合：左侧带勾选框，右侧指示器条
    main_content = ft.Row([
        ft.Checkbox(
            value=checked,
            fill_color=ft.Colors.AMBER_400,
            scale=0.8,
            disabled=True # 禁用交互，统一由外部 Container 处理点击
        ),
        indicator_body
    ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER, expand=True)

    return ft.Container(
        content=main_content,
        padding=ft.Padding(left=2, right=8, top=4, bottom=4),
        bgcolor=ft.Colors.WHITE_10,
        border=ft.Border.all(1, ft.Colors.AMBER_400) if selected else None,
        border_radius=4,
        expand=True
    )


@ft.component
def AdaptiveStatusCluster(
    indicators: list[dict[str, Any]],
    expand: bool = True,
    min_width: float = 60.0,
    spacing: int = 4,
    bar_height: int = 6,
    on_indicator_click: Any = None
) -> ft.Control:
    """
    自适应状态集群 - 横向均分空间

    Args:
        indicators: 指示器配置列表，每个元素包含:
            - name: 资源名称
            - current: 当前值
            - maximum: 最大值
            - color: 进度条颜色
            - visible: 是否可见
        expand: 是否自适应扩展填充可用空间
        min_width: 单个指示器最小宽度
        spacing: 指示器间距
        bar_height: 进度条高度
        on_indicator_click: 状态条点击的回调函数，接收指示器名称参数

    Returns:
        自适应状态集群组件
    """
    # 过滤可见指示器
    visible_indicators = [ind for ind in indicators if ind.get("visible", True)]

    if not visible_indicators:
        return ft.Container()

    # 渲染指示器
    indicator_controls: list[ft.Control] = []

    for ind in visible_indicators:
        ind_name = ind.get("name", "")
        current = float(ind.get("current", 0))
        maximum = float(ind.get("maximum", 1))

        # 计算数值显示
        ratio = max(0.0, min(1.0, current / maximum)) if maximum > 0 else 0.0
        current_str = f"{current:.0f}" if ind_name == "HP" else f"{current:.1f}"
        max_str = f"{maximum:.0f}"
        pct_str = f"{ratio * 100:.1f}%"
        tooltip_text = f"{ind_name}: {current_str} / {max_str} ({pct_str})"

        def create_toggle_handler():
            """点击切换展示状态（勾选/取消勾选）"""
            if on_indicator_click:
                param_name = "血条" if ind_name == "HP" else "能量条"
                return lambda _: on_indicator_click(param_name)
            return None

        indicator_container = ft.Container(
            content=StatusIndicator(
                name=ind_name,
                current=current,
                maximum=maximum,
                color=ind.get("color", ft.Colors.GREEN_400),
                bar_height=bar_height,
                show_label=False,
                selected=ind.get("selected", False),
                checked=ind.get("checked", False)
            ),
            expand=True,
            on_click=create_toggle_handler(),
            tooltip=tooltip_text
        )

        indicator_controls.append(indicator_container)

    return ft.Row(
        controls=indicator_controls,
        spacing=spacing,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True
    )


@ft.component
def CompactStatusBar(
    indicators: list[dict[str, Any]],
    compact: bool = True
) -> ft.Control:
    """
    [V9.5 Pro V2] 紧凑型状态条（垂直堆叠模式）

    用于仪表盘模式，将 HP 和能量条垂直堆叠显示

    Args:
        indicators: 指示器配置列表
        compact: 紧凑模式（更细的条）

    Returns:
        紧凑型状态条组件
    """
    visible_indicators = [ind for ind in indicators if ind.get("visible", True)]

    if not visible_indicators:
        return ft.Container()

    bar_heights = (4, 2) if compact else (6, 4)

    bars: list[ft.Control] = []

    for i, ind in enumerate(visible_indicators):
        current = float(ind.get("current", 0))
        maximum = float(ind.get("maximum", 1))
        ratio = max(0.0, min(1.0, current / maximum)) if maximum > 0 else 0.0

        # 根据 index 选择条高度，循环使用
        h = bar_heights[i % len(bar_heights)]

        bars.append(
            ft.ProgressBar(
                value=ratio,
                bar_height=h,
                color=ind.get("color", ft.Colors.GREEN_400),
                bgcolor=ft.Colors.WHITE_10,
                expand=True
            )
        )

    return ft.Column(
        controls=bars,
        spacing=2,
        expand=True
    )
