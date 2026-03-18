"""[V17.0] 选择面板 ViewModel 数据类

提供选择面板和事件卡片的声明式数据绑定。

创建策略：独立创建（每次渲染时生成）
- EventCardViewModel: 仅展示数据，选中状态由父级管理
- SelectionPanelViewModel: 数据从 frame_range_selection 派生
"""

from dataclasses import dataclass, field
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ui.view_models.analysis.tile_vms.types import FrameRangeSelection


@dataclass
class EventCardViewModel:
    """事件卡片 ViewModel

    仅展示数据，选中状态由父级管理。
    每次渲染时独立创建，无需保留状态。

    Attributes:
        event_id: 事件 ID
        frame: 帧数
        source: 角色名称
        name: 伤害名称
        element: 元素类型
        damage: 伤害值
        is_selected: 是否选中（由父级传入）
        element_color: 元素颜色（派生属性）
        raw_event: 原始事件数据（用于回调）
    """
    event_id: int
    frame: int
    source: str
    name: str
    element: str
    damage: float
    is_selected: bool = False
    element_color: str = field(default="", init=False)
    raw_event: dict = field(default_factory=dict, repr=False)

    def __post_init__(self):
        """初始化派生属性"""
        # 延迟导入避免循环依赖
        from ui.theme import GenshinTheme
        self.element_color = GenshinTheme.get_element_color(self.element)

    @classmethod
    def from_event(
        cls,
        event: dict,
        selected_event_id: int | None = None
    ) -> 'EventCardViewModel':
        """从事件字典创建 ViewModel

        Args:
            event: 事件数据字典
            selected_event_id: 当前选中的事件 ID（用于计算 is_selected）

        Returns:
            EventCardViewModel 实例
        """
        return cls(
            event_id=event.get('event_id', 0),
            frame=event.get('frame', 0),
            source=event.get('source', '未知'),
            name=event.get('name', '未知伤害'),
            element=event.get('element', 'Neutral'),
            damage=event.get('dmg', 0),
            is_selected=(selected_event_id is not None
                         and event.get('event_id') == selected_event_id),
            raw_event=event,
        )


@dataclass
class SelectionPanelViewModel:
    """选择面板 ViewModel

    数据从 frame_range_selection 派生，每次渲染时独立创建。
    不保留交互状态（如选中的事件），这些状态由 AnalysisViewModel 管理。

    Attributes:
        center_frame: 点击中心帧
        start_frame: 范围起始帧
        end_frame: 范围结束帧
        total_damage: 范围总伤害
        time_range_seconds: 时间范围
        event_count: 事件数量
        event_cards: 事件卡片 ViewModel 列表（派生属性）
        has_selection: 是否有选择数据
        selected_event_id: 当前选中的事件 ID
        _on_event_click: 事件点击回调（不参与序列化）
    """
    center_frame: int = 0
    start_frame: int = 0
    end_frame: int = 0
    total_damage: float = 0.0
    time_range_seconds: float = 0.5
    event_count: int = 0
    event_cards: list[EventCardViewModel] = field(default_factory=list)
    has_selection: bool = False
    selected_event_id: int | None = None
    _on_event_click: Callable[[dict], None] | None = field(default=None, repr=False)

    def __post_init__(self):
        """初始化派生属性"""
        self.event_count = len(self.event_cards)

    @classmethod
    def from_selection(
        cls,
        selection: 'FrameRangeSelection | None',
        selected_event: dict | None = None,
        on_event_click: Callable[[dict], None] | None = None
    ) -> 'SelectionPanelViewModel':
        """从帧范围选择创建 ViewModel

        Args:
            selection: 帧范围选择数据，包含事件列表
            selected_event: 当前选中的事件（用于计算事件卡片的选中状态）
            on_event_click: 事件点击回调

        Returns:
            SelectionPanelViewModel 实例
        """
        if not selection:
            return cls(
                has_selection=False,
                selected_event_id=selected_event.get('event_id') if selected_event else None,
                _on_event_click=on_event_click,
            )

        selected_event_id = selected_event.get('event_id') if selected_event else None

        # 创建事件卡片 ViewModel 列表
        event_cards = [
            EventCardViewModel.from_event(event, selected_event_id)
            for event in selection.events
        ]

        return cls(
            center_frame=selection.center_frame,
            start_frame=selection.start_frame,
            end_frame=selection.end_frame,
            total_damage=selection.total_damage,
            time_range_seconds=selection.time_range_seconds,
            has_selection=True,
            selected_event_id=selected_event_id,
            _on_event_click=on_event_click,
            event_cards=event_cards,
        )

    def get_event_count(self) -> int:
        """获取事件数量"""
        return len(self.event_cards) if self.event_cards else 0

    def handle_event_click(self, event_card: EventCardViewModel):
        """处理事件卡片点击

        Args:
            event_card: 被点击的事件卡片 ViewModel
        """
        if self._on_event_click:
            self._on_event_click(event_card.raw_event)
