"""[V19.0] 底部面板 ViewModel 数据类

提供声明式的 ViewModel 数据类，支持 Flet 组件的数据绑定。

[V19.0] 父子持有设计：
- BottomPanelViewModel: 容器，持有子 VM，管理面板切换
- SelectionPanelViewModel: 选择面板状态（每次渲染时重建）
- AuditPanelViewModel: 审计面板状态（@ft.observable，持久）
"""

from .bottom_panel_vm import BottomPanelViewModel
from .selection_vm import EventCardViewModel, SelectionPanelViewModel
from .audit_panel_vm import AuditPanelViewModel
from .damage_chain_vm import (
    MultiplierCardViewModel,
    DamageResultCardViewModel,
    DamageChainRowViewModel,
)
from .domain_detail_vm import ModifierCardViewModel, DomainDetailSectionViewModel

__all__ = [
    # Container
    "BottomPanelViewModel",
    # Selection
    "EventCardViewModel",
    "SelectionPanelViewModel",
    # Audit
    "AuditPanelViewModel",
    # Damage Chain
    "MultiplierCardViewModel",
    "DamageResultCardViewModel",
    "DamageChainRowViewModel",
    # Domain Detail
    "ModifierCardViewModel",
    "DomainDetailSectionViewModel",
]
