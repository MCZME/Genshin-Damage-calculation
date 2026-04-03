"""[V19.0] 审计面板 ViewModel

提供 AuditPanel 组件的数据管理与状态逻辑。

[V19.0] 简化设计：
- 只管理审计面板自己的状态
- 面板切换逻辑由父级 BottomPanelViewModel 管理
- 纯数据类，不使用 @ft.observable
- 交互状态由父级 BottomPanelViewModel 管理

嵌套 ViewModel 设计：
- damage_chain: DamageChainRowViewModel (回调方式，保留域点击状态)
- domain_detail: DomainDetailSectionViewModel (嵌套，派生属性)

更新策略：
- set_event(): 重置状态，清空嵌套 ViewModel
- set_data(): 更新数据并创建嵌套 ViewModel
- update_domain_state(): 从父级接收交互状态，更新嵌套 ViewModel
"""
from __future__ import annotations

from typing import Any, Callable
from dataclasses import dataclass, field

from core.persistence.processors.audit.types import DamageType, DamageTypeContext


@dataclass
class AuditPanelViewModel:
    """审计面板 ViewModel

    管理审计面板的数据状态。
    交互状态（active_bucket, selected_domain）由父级 BottomPanelViewModel 管理，
    通过 update_domain_state() 方法同步。

    [V21.0] 新增多组分月反应支持：
    - is_multi_component_lunar: 是否为多组分月反应
    - component_chains: 组分伤害链 ViewModel 列表
    - lunar_summary: 月反应汇总 ViewModel

    Attributes:
        event: 当前事件数据
        current_event_id: 跟踪当前请求的事件 ID，防止异步竞态
        buckets_data: 乘区数据字典
        damage_type: 伤害类型

        # 交互状态（从父级接收）
        active_bucket: 当前激活的乘区
        selected_domain: 选中的域

        # 嵌套 ViewModel (派生属性)
        damage_chain: 伤害链行 ViewModel
        domain_detail: 域详情区 ViewModel
        component_chains: 月反应组分伤害链列表
        lunar_summary: 月反应汇总 ViewModel
    """

    # 数据状态
    event: dict[str, Any] | None = None
    current_event_id: int | None = None  # 跟踪当前请求的事件 ID，防止异步竞态
    buckets_data: dict[str, Any] = field(default_factory=dict)
    damage_type: DamageType = DamageType.NORMAL

    # 交互状态（从父级接收，不参与初始化）
    active_bucket: str | None = field(default=None, init=False)
    selected_domain: str | None = field(default=None, init=False)

    # 回调（由父级设置，用于域点击）
    on_domain_click: Callable[[str, str], None] | None = field(default=None, init=False, repr=False)

    # 嵌套 ViewModel (派生属性，不参与初始化)
    # 使用 Any 类型避免循环导入问题，实际类型在运行时由 _update_nested_viewmodels 设置
    damage_chain: Any = field(default=None, init=False, repr=False)
    domain_detail: Any = field(default=None, init=False, repr=False)

    # [V21.0] 月反应多组分支持
    is_multi_component_lunar: bool = field(default=False, init=False)
    component_chains: list[Any] = field(default_factory=list, init=False, repr=False)
    lunar_summary: Any = field(default=None, init=False, repr=False)

    # ─────────────────────────────────────────
    # 状态管理方法
    # ─────────────────────────────────────────

    def set_event(self, event: dict[str, Any] | None, active_bucket: str | None = None, selected_domain: str | None = None):
        """设置当前事件并重置状态

        Args:
            event: 事件数据字典
            active_bucket: 当前激活的乘区（从父级传入）
            selected_domain: 选中的域（从父级传入）
        """
        self.event = event
        self.current_event_id = event.get('event_id') if event else None
        self.buckets_data = {}  # 立即清空旧数据，防止重影
        self.damage_type = DamageType.NORMAL
        self.active_bucket = active_bucket
        self.selected_domain = selected_domain

        # 清空嵌套 ViewModel
        self.damage_chain = None
        self.domain_detail = None

        # 如果有事件数据，创建初始的伤害链 ViewModel
        if event:
            self._create_damage_chain_from_event()

    def set_data(self, event_id: int, buckets_data: dict[str, Any]):
        """设置详细数据 (带 ID 校验)

        Args:
            event_id: 事件 ID
            buckets_data: 乘区数据字典
        """
        # 竞态检查：仅接受与当前选中事件匹配的数据
        if self.current_event_id != event_id:
            return

        self.buckets_data = buckets_data

        # 解析伤害类型
        ctx = buckets_data.get("_damage_type_ctx")
        if ctx and isinstance(ctx, DamageTypeContext):
            self.damage_type = ctx.damage_type
        else:
            self.damage_type = DamageType.NORMAL

        # 更新嵌套 ViewModel
        self._update_nested_viewmodels()

    def update_domain_state(self, active_bucket: str | None, selected_domain: str | None):
        """更新域状态并重建嵌套 ViewModel

        由父级 BottomPanelViewModel 调用，同步交互状态。

        Args:
            active_bucket: 当前激活的乘区
            selected_domain: 选中的域
        """
        self.active_bucket = active_bucket
        self.selected_domain = selected_domain
        self._update_nested_viewmodels()

    def clear(self):
        """清空所有状态"""
        self.event = None
        self.current_event_id = None
        self.buckets_data = {}
        self.damage_type = DamageType.NORMAL
        self.active_bucket = None
        self.selected_domain = None
        self.damage_chain = None
        self.domain_detail = None

    # ─────────────────────────────────────────
    # 嵌套 ViewModel 管理
    # ─────────────────────────────────────────

    def _create_damage_chain_from_event(self):
        """从事件数据创建伤害链 ViewModel（仅有伤害值，无详细数据）"""
        from ui.view_models.analysis.bottom_panel.damage_chain_vm import DamageChainRowViewModel

        if not self.event:
            self.damage_chain = None
            return

        self.damage_chain = DamageChainRowViewModel.from_audit_data(
            buckets_data={},  # 暂无详细数据
            damage_value=self.event.get('dmg', 0),
            element=self.event.get('element', 'Neutral'),
            damage_type=self.damage_type,
            active_bucket=self.active_bucket,
            selected_domain=self.selected_domain,
            on_domain_click=self.on_domain_click,
        )

    def _update_nested_viewmodels(self):
        """更新嵌套的子 ViewModel

        [V21.0] 新增多组分月反应处理：
        - 检测 buckets_data 中是否有 _component_buckets
        - 如果有，创建 component_chains 和 lunar_summary
        - 否则使用常规单行展示
        """
        from ui.view_models.analysis.bottom_panel.damage_chain_vm import (
            DamageChainRowViewModel,
            ComponentChainRowViewModel,
            LunarReactionSummaryViewModel,
        )
        from ui.view_models.analysis.bottom_panel.domain_detail_vm import DomainDetailSectionViewModel

        # [V21.0] 检测是否为多组分月反应
        component_buckets = self.buckets_data.get("_component_buckets", [])
        if self.damage_type == DamageType.LUNAR and component_buckets:
            # 多组分月反应路径
            self.is_multi_component_lunar = True

            # 创建组分伤害链 ViewModel 列表
            self.component_chains = [
                ComponentChainRowViewModel.from_component_data(comp)
                for comp in component_buckets
            ]

            # 创建月反应汇总 ViewModel
            contributions = self.buckets_data.get("base_damage", {}).get("contributions", [])
            self.lunar_summary = LunarReactionSummaryViewModel(
                formula_text="最高 + 次高÷2 + 其余÷12",
                final_damage=self.event.get('dmg', 0) if self.event else 0,
                element=self.event.get('element', 'Neutral') if self.event else 'Neutral',
                contributions=contributions,
            )

            # 清空常规伤害链
            self.damage_chain = None

            # 更新域详情 ViewModel（使用共享的擢升区和抗性区）
            self.domain_detail = DomainDetailSectionViewModel.from_audit_data(
                active_bucket=self.active_bucket,
                selected_domain=self.selected_domain,
                buckets_data=self.buckets_data,
            )
        else:
            # 常规单行展示路径
            self.is_multi_component_lunar = False
            self.component_chains = []
            self.lunar_summary = None

            # 更新伤害链 ViewModel
            self.damage_chain = DamageChainRowViewModel.from_audit_data(
                buckets_data=self.buckets_data,
                damage_value=self.event.get('dmg', 0) if self.event else 0,
                element=self.event.get('element', 'Neutral') if self.event else 'Neutral',
                damage_type=self.damage_type,
                active_bucket=self.active_bucket,
                selected_domain=self.selected_domain,
                on_domain_click=self.on_domain_click,
            )

            # 更新域详情 ViewModel
            self.domain_detail = DomainDetailSectionViewModel.from_audit_data(
                active_bucket=self.active_bucket,
                selected_domain=self.selected_domain,
                buckets_data=self.buckets_data,
            )
