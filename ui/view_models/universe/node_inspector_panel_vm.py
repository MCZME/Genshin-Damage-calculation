from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import flet as ft
from core.batch.models import BatchNodeKind, RangeType


@ft.observable
@dataclass
class NodeInspectorPanelViewModel:
    node_id: str = "root"
    node_name: str = "基准配置"
    node_kind: BatchNodeKind = BatchNodeKind.ROOT
    is_generated: bool = False
    rule_path_text: str = ""
    rule_value_text: str = ""
    range_path_text: str = ""
    base_config: dict[str, Any] = field(default_factory=dict)
    range_type: RangeType = RangeType.NUMERIC
    range_start_text: str = "0"
    range_end_text: str = "10"
    range_step_text: str = "1"
    range_values_text: str = ""  # 枚举值，逗号分隔
    range_label_text: str = ""
    range_children_count: int = 0
    can_delete: bool = False
    show_rule_form: bool = False
    show_range_form: bool = False
    help_text: str = ""
