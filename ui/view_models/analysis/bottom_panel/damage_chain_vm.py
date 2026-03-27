"""[V20.0] 伤害链 ViewModel 数据类

提供伤害链行、乘区卡片和伤害结果卡片的声明式数据绑定。

[V20.0] 纯数据设计：
- MultiplierCardViewModel 只存储数据，不存储组件
- formula_parts 存储 FormulaPartData（TextPart | DomainValuePart）
- 组件在渲染时根据数据创建
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.persistence.processors.audit.types import DamageType


@dataclass
class MultiplierCardViewModel:
    """乘区卡片 ViewModel

    [V20.0] 纯数据设计：
    - formula_parts 存储数据结构，不存储 Flet 组件
    - 组件在渲染时根据数据创建

    Attributes:
        bucket_key: 乘区键（如 CORE, BONUS, CRIT 等）
        bucket_label: 乘区标签（如 "核心伤害", "增伤乘区" 等）
        bucket_color: 乘区颜色
        bucket_data: 乘区数据字典
        is_selected: 是否选中（当前激活的乘区）
        selected_domain: 选中的域
        active_bucket: 当前激活的乘区（用于域选中判断）
        damage_type: 伤害类型
        on_domain_click: 域点击回调（用于跳转到域详情）

        # 派生属性（纯数据）
        formula_parts: 公式部分数据列表（TextPart | DomainValuePart）
        total_text: 总计文本
        total_color: 总计颜色
    """
    bucket_key: str
    bucket_label: str
    bucket_color: str
    bucket_data: dict = field(default_factory=dict)
    is_selected: bool = False
    selected_domain: str | None = None
    active_bucket: str | None = None
    damage_type: 'DamageType | None' = field(default=None, repr=False)
    on_domain_click: Callable | None = field(default=None, repr=False)

    # 派生属性（纯数据，不存储组件）
    formula_parts: list = field(default_factory=list, init=False, repr=False)
    formula_parts_line2: list = field(default_factory=list, init=False, repr=False)  # 第二行公式
    total_text: str = field(default="", init=False)
    total_color: str = field(default="", init=False)

    def __post_init__(self):
        """初始化派生属性 - 构建公式数据"""
        from ui.components.analysis.bottom_panel.formulas import (
            build_formula, build_transformative_formula, build_lunar_formula
        )
        from core.persistence.processors.audit.types import DamageType

        # 处理 damage_type 默认值
        actual_damage_type = self.damage_type if self.damage_type is not None else DamageType.NORMAL

        # 根据伤害类型选择公式构建器
        if actual_damage_type == DamageType.LUNAR:
            result = build_lunar_formula(
                bucket_key=self.bucket_key,
                bucket_data=self.bucket_data,
                bucket_color=self.bucket_color,
            )
        elif actual_damage_type == DamageType.TRANSFORMATIVE:
            result = build_transformative_formula(
                bucket_key=self.bucket_key,
                bucket_data=self.bucket_data,
                bucket_color=self.bucket_color,
            )
        else:
            result = build_formula(
                bucket_key=self.bucket_key,
                bucket_data=self.bucket_data,
                bucket_color=self.bucket_color,
            )

        # 存储数据，不存储组件
        self.formula_parts = result.parts
        self.formula_parts_line2 = result.parts_line2
        self.total_text = result.total_text
        self.total_color = result.total_color or self.bucket_color


@dataclass
class DamageResultCardViewModel:
    """伤害结果卡片 ViewModel

    无状态，仅展示最终伤害值。
    每次渲染时独立创建。

    Attributes:
        damage_value: 伤害值
        element: 元素类型
        element_color: 元素颜色（派生属性）
    """
    damage_value: float
    element: str = "Neutral"
    element_color: str = field(default="", init=False)

    def __post_init__(self):
        """初始化派生属性"""
        from ui.theme import GenshinTheme
        self.element_color = GenshinTheme.get_element_color(self.element)


@dataclass
class DamageChainRowViewModel:
    """伤害链行 ViewModel

    保留域点击状态，需要回调父级（AuditPanelViewModel）。
    multiplier_cards 列表在每次更新时重新创建（派生属性）。

    Attributes:
        active_bucket: 当前激活的乘区
        selected_domain: 选中的域
        buckets_data: 乘区数据字典
        damage_type: 伤害类型
        damage_result: 伤害结果卡片 ViewModel（派生属性）
        multiplier_cards: 乘区卡片 ViewModel 列表（派生属性）
        _on_domain_click: 域点击回调（不参与序列化）
    """
    active_bucket: str | None = None
    selected_domain: str | None = None
    buckets_data: dict = field(default_factory=dict)
    damage_type: 'DamageType | None' = field(default=None, repr=False)
    damage_result: DamageResultCardViewModel | None = field(default=None, init=False)
    multiplier_cards: list[MultiplierCardViewModel] = field(default_factory=list, init=False)
    _on_domain_click: Callable | None = field(default=None, repr=False)

    # 伤害值和元素（从外部传入）
    damage_value: float = 0
    element: str = "Neutral"

    def __post_init__(self):
        """初始化派生属性"""
        from core.persistence.processors.audit.types import DamageType
        from ui.components.analysis.bottom_panel.constants import (
            BUCKET_COLORS, NORMAL_BUCKET_CONFIGS, TRANSFORMATIVE_BUCKET_CONFIGS
        )

        # 处理 damage_type 默认值
        actual_damage_type = self.damage_type if self.damage_type is not None else DamageType.NORMAL

        # 创建伤害结果卡片 ViewModel
        self.damage_result = DamageResultCardViewModel(
            damage_value=self.damage_value,
            element=self.element,
        )

        # 根据伤害类型选择桶配置
        if actual_damage_type == DamageType.TRANSFORMATIVE:
            bucket_configs = TRANSFORMATIVE_BUCKET_CONFIGS
        else:
            bucket_configs = NORMAL_BUCKET_CONFIGS

        # 创建乘区卡片 ViewModel 列表
        self.multiplier_cards = []
        for bucket_key, bucket_label, data_key in bucket_configs:
            bucket_data = self.buckets_data.get(data_key, {})
            bucket_color = BUCKET_COLORS.get(bucket_key, "#FFFFFF")

            card_vm = MultiplierCardViewModel(
                bucket_key=bucket_key,
                bucket_label=bucket_label,
                bucket_data=bucket_data,
                bucket_color=bucket_color,
                is_selected=self.active_bucket == bucket_key,
                selected_domain=self.selected_domain,
                active_bucket=self.active_bucket,
                damage_type=actual_damage_type,
                on_domain_click=self._on_domain_click,
            )
            self.multiplier_cards.append(card_vm)

    @classmethod
    def from_audit_data(
        cls,
        buckets_data: dict,
        damage_value: float = 0,
        element: str = "Neutral",
        damage_type: 'DamageType | None' = None,
        active_bucket: str | None = None,
        selected_domain: str | None = None,
        on_domain_click: Callable | None = None
    ) -> 'DamageChainRowViewModel':
        """从审计数据创建 ViewModel

        Args:
            buckets_data: 乘区数据字典
            damage_value: 最终伤害值
            element: 元素类型
            damage_type: 伤害类型
            active_bucket: 当前激活的乘区
            selected_domain: 选中的域
            on_domain_click: 域点击回调

        Returns:
            DamageChainRowViewModel 实例
        """
        return cls(
            active_bucket=active_bucket,
            selected_domain=selected_domain,
            buckets_data=buckets_data,
            damage_type=damage_type,
            damage_value=damage_value,
            element=element,
            _on_domain_click=on_domain_click,
        )

    def handle_domain_click(self, bucket_key: str, domain_key: str):
        """处理域点击

        Args:
            bucket_key: 乘区键
            domain_key: 域键
        """
        if self._on_domain_click:
            self._on_domain_click(bucket_key, domain_key)
