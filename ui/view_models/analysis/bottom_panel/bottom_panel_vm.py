"""[V19.0] 底部面板 ViewModel

作为弹出面板的父容器，管理面板切换和子 ViewModel。

设计说明：
- 父 VM 持有子 VM，级联 notify
- 面板切换逻辑集中在这里
- 子 VM 各自独立管理自己的状态

UI 层级对应：
    DamageAuditBottomPanel  →  BottomPanelViewModel (容器)
    ├── SelectionPanel      →  SelectionPanelViewModel (子)
    └── AuditPanel          →  AuditPanelViewModel (子)
"""
from __future__ import annotations

from typing import Any, Callable
from dataclasses import dataclass, field
import flet as ft

from ui.view_models.analysis.bottom_panel.selection_vm import SelectionPanelViewModel
from ui.view_models.analysis.bottom_panel.audit_panel_vm import AuditPanelViewModel


@ft.observable
@dataclass
class BottomPanelViewModel:
    """底部面板容器 ViewModel

    管理面板显示状态和模式切换。

    Attributes:
        visible: 面板是否可见
        panel_mode: 当前面板模式 ("selection" | "audit")

        # 交互状态（由 @ft.observable 管理）
        active_bucket: 当前激活的乘区
        selected_domain: 选中的域

        # 子 ViewModel
        selection: 选择面板 ViewModel
        audit: 审计面板 ViewModel

        # 外部依赖
        data_service: 数据服务（用于加载审计详情）
    """

    # 面板状态
    visible: bool = False
    panel_mode: str = "selection"  # selection | audit

    # 交互状态（由 @ft.observable 管理，直接修改可触发 UI 更新）
    active_bucket: str | None = None
    selected_domain: str | None = None

    # 子 ViewModel（延迟初始化，设为 None 避免创建时的问题）
    selection: SelectionPanelViewModel | None = field(default=None, init=False)
    audit: AuditPanelViewModel | None = field(default=None, init=False)

    # 外部依赖
    data_service: Any = field(default=None, repr=False)

    # ─────────────────────────────────────────
    # 面板切换方法
    # ─────────────────────────────────────────

    def show(self):
        """显示面板"""
        self.visible = True

    def hide(self):
        """隐藏面板"""
        self.visible = False

    def toggle(self):
        """切换显示/隐藏"""
        self.visible = not self.visible

    # ─────────────────────────────────────────
    # 面板模式切换
    # ─────────────────────────────────────────

    def switch_to_selection(self):
        """切换到选择面板"""
        self.panel_mode = "selection"
        # 重置交互状态
        self.active_bucket = None
        self.selected_domain = None
        if self.audit:
            self.audit.clear()

    def switch_to_audit(self, event: dict):
        """切换到审计面板

        Args:
            event: 选中的事件数据
        """
        self.panel_mode = "audit"

        # 重置交互状态
        self.active_bucket = None
        self.selected_domain = None

        # 确保 audit 已初始化
        if not self.audit:
            self.audit = AuditPanelViewModel()

        # 设置域点击回调（指向父级的 toggle_domain 方法）
        self.audit.on_domain_click = self.toggle_domain

        # 设置事件数据（交互状态通过参数传入）
        self.audit.set_event(event, self.active_bucket, self.selected_domain)

        # 异步加载详情
        event_id = event.get('event_id')
        if event_id is not None and self.data_service:
            import asyncio

            async def _load():
                data = await self.data_service.load_audit_detail(int(event_id))
                if self.audit:
                    self.audit.set_data(int(event_id), data)
                    # 同步交互状态到子 ViewModel
                    self.audit.update_domain_state(self.active_bucket, self.selected_domain)

            asyncio.create_task(_load())

    def toggle_domain(self, bucket_key: str, domain_key: str):
        """切换域选中状态 - 直接修改 observable 属性触发 UI 更新

        Args:
            bucket_key: 乘区键
            domain_key: 域键
        """
        if self.active_bucket == bucket_key and self.selected_domain == domain_key:
            # 取消选中
            self.active_bucket = None
            self.selected_domain = None
        else:
            # 选中新域
            self.active_bucket = bucket_key
            self.selected_domain = domain_key

        # 同步交互状态到子 ViewModel（不触发父级更新，因为上面已修改 observable 属性）
        if self.audit:
            self.audit.update_domain_state(self.active_bucket, self.selected_domain)

    # ─────────────────────────────────────────
    # 选择面板数据更新
    # ─────────────────────────────────────────

    def update_selection(
        self,
        selection_data: Any,
        selected_event: dict | None = None,
        on_event_click: Callable[[dict], None] | None = None
    ):
        """更新选择面板数据

        Args:
            selection_data: 帧范围选择数据
            selected_event: 当前选中的事件
            on_event_click: 事件点击回调
        """
        # 创建新的 SelectionPanelViewModel（每次渲染时重新创建）
        self.selection = SelectionPanelViewModel.from_selection(
            selection=selection_data,
            selected_event=selected_event,
            on_event_click=on_event_click,
        )

    # ─────────────────────────────────────────
    # 初始化方法
    # ─────────────────────────────────────────

    def ensure_initialized(self):
        """确保子 ViewModel 已初始化"""
        if self.selection is None:
            self.selection = SelectionPanelViewModel()
        if self.audit is None:
            self.audit = AuditPanelViewModel()
