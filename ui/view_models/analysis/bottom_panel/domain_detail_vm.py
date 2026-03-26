"""[V17.0] 域详情 ViewModel 数据类

提供域详情区和修饰符卡片的声明式数据绑定。

创建策略：
- ModifierCardViewModel: 独立创建（无状态，仅展示修饰符数据）
- DomainDetailSectionViewModel: 独立创建（数据完全从 buckets_data 派生）
"""

from dataclasses import dataclass, field

import flet as ft


@dataclass
class ModifierCardViewModel:
    """修饰符卡片 ViewModel

    无状态，仅展示修饰符数据。
    每次渲染时独立创建。

    Attributes:
        stat: 属性名称
        value: 数值
        source: 来源
        bucket_color: 乘区颜色
        is_percentage: 是否为百分比属性（派生属性）
        display_text: 显示文本（派生属性）
    """
    stat: str
    value: float
    source: str
    bucket_color: str
    is_percentage: bool = field(default=False, init=False)
    display_text: str = field(default="", init=False)

    def __post_init__(self):
        """初始化派生属性"""
        # 判断是否为百分比属性
        # 1. stat 包含 '%' 字符
        # 2. stat 包含百分比属性关键词
        pct_keywords = ('加成', '暴击', '率', '减抗', '减防', '穿透', '无视')
        self.is_percentage = '%' in self.stat or self.stat.endswith(pct_keywords)

        # 生成显示文本
        # 使用 + 格式说明符自动处理正负号：正数显示 +，负数显示 -
        if self.is_percentage:
            self.display_text = f"{self.value:+.1f}%"
        else:
            self.display_text = f"{self.value:+.0f}"

    @classmethod
    def from_dict(cls, modifier: dict, bucket_color: str) -> 'ModifierCardViewModel':
        """从修饰符字典创建 ViewModel

        Args:
            modifier: 修饰符数据，包含 stat, value, source 字段
            bucket_color: 乘区颜色

        Returns:
            ModifierCardViewModel 实例
        """
        return cls(
            stat=modifier.get('stat', ''),
            value=modifier.get('value', 0),
            source=modifier.get('source', ''),
            bucket_color=bucket_color,
        )


@dataclass
class DomainDetailSectionViewModel:
    """域详情区 ViewModel

    数据完全从 buckets_data 派生。
    每次渲染时独立创建，不保留状态。

    Attributes:
        active_bucket: 当前激活的乘区
        selected_domain: 选中的域
        buckets_data: 乘区数据字典
        domain_label: 域标签（派生属性）
        modifier_cards: 修饰符卡片 ViewModel 列表（派生属性）
        bucket_color: 乘区颜色（派生属性）
    """
    active_bucket: str | None = None
    selected_domain: str | None = None
    buckets_data: dict = field(default_factory=dict)
    domain_label: str = field(default="全部来源", init=False)
    modifier_cards: list[ModifierCardViewModel] = field(default_factory=list, init=False)
    bucket_color: str = field(default=ft.Colors.WHITE, init=False)

    def __post_init__(self):
        """初始化派生属性"""
        from ui.components.analysis.bottom_panel.constants import (
            BUCKET_COLORS, NORMAL_BUCKET_CONFIGS, TRANSFORMATIVE_BUCKET_CONFIGS
        )

        if not self.active_bucket:
            return

        # 合并常规伤害和剧变反应的桶配置映射
        bucket_data_map = {key: data_key for key, _, data_key in NORMAL_BUCKET_CONFIGS}
        bucket_data_map.update({key: data_key for key, _, data_key in TRANSFORMATIVE_BUCKET_CONFIGS})

        data_key = bucket_data_map.get(self.active_bucket, "core_dmg")
        self.bucket_color = BUCKET_COLORS.get(self.active_bucket, ft.Colors.WHITE)

        # 获取步骤列表
        steps = self.buckets_data.get(data_key, {}).get('steps', [])

        # 解析修饰符列表
        modifiers = self._resolve_modifiers(steps, data_key)

        # 创建修饰符卡片 ViewModel 列表
        self.modifier_cards = [
            ModifierCardViewModel.from_dict(mod, self.bucket_color)
            for mod in modifiers[:10]  # 限制最多 10 个
        ]

    def _resolve_modifiers(self, steps: list[dict], data_key: str) -> list[dict]:
        """解析选中域的修饰符列表

        Args:
            steps: 步骤列表
            data_key: 数据键

        Returns:
            修饰符列表
        """
        modifiers = []

        # CORE 区处理
        if self.active_bucket == "CORE":
            modifiers = self._resolve_core_modifiers(steps, data_key)
        # BONUS 区处理
        elif self.active_bucket == "BONUS":
            modifiers = self._resolve_bonus_modifiers(steps, data_key)
        # CRIT 区处理
        elif self.active_bucket == "CRIT":
            modifiers = self._resolve_crit_modifiers(steps, data_key)
        # REACT 区处理
        elif self.active_bucket == "REACT":
            modifiers = self._resolve_react_modifiers(steps, data_key)
        # RES 区处理
        elif self.active_bucket == "RES":
            modifiers = self._resolve_res_modifiers(steps, data_key)
        # DEF 区处理
        elif self.active_bucket == "DEF":
            modifiers = self._resolve_def_modifiers(steps, data_key)
        # 其他乘区
        else:
            from core.persistence.processors.audit import AuditProcessor
            domain_values = AuditProcessor.calculate_domains(steps)
            if self.selected_domain == "domain1":
                modifiers = domain_values.domain1_modifiers or []
                self.domain_label = "固定值加成"
            elif self.selected_domain == "domain2":
                modifiers = domain_values.domain2_modifiers or []
                self.domain_label = "百分比加成"
            else:
                modifiers = steps
                self.domain_label = "全部来源"

        return modifiers

    def _resolve_core_modifiers(self, steps: list[dict], data_key: str) -> list[dict]:
        """解析 CORE 区修饰符"""
        scaling_info = self.buckets_data.get(data_key, {}).get('scaling_info', [])

        # 处理属性特定域（如 "pct:攻击力", "flat:防御力"）
        if self.selected_domain and ":" in self.selected_domain:
            domain_type, attr_name = self.selected_domain.split(":", 1)

            if domain_type == "pct":
                attr_info = next((i for i in scaling_info if i.get('attr_name') == attr_name), None)
                if attr_info:
                    modifiers = [
                        {"stat": f"{attr_name}%", "value": m.get("value", 0.0), "source": m.get("name", "未知来源")}
                        for m in attr_info.get('pct_modifiers', [])
                    ]
                else:
                    modifiers = []
                self.domain_label = f"{attr_name}百分比加成"

            elif domain_type == "flat":
                attr_info = next((i for i in scaling_info if i.get('attr_name') == attr_name), None)
                if attr_info:
                    modifiers = [
                        {"stat": f"固定{attr_name}", "value": m.get("value", 0.0), "source": m.get("name", "未知来源")}
                        for m in attr_info.get('flat_modifiers', [])
                    ]
                else:
                    modifiers = []
                self.domain_label = f"{attr_name}固定值加成"

            elif domain_type == "skill_mult":
                modifiers = [
                    s for s in steps
                    if s.get("stat", "").endswith("技能倍率%") and attr_name in s.get("stat", "")
                ]
                self.domain_label = f"{attr_name}倍率"

            else:
                modifiers = steps
                self.domain_label = "全部来源"

        elif self.selected_domain == "skill_mult":
            modifiers = [s for s in steps if s.get("stat", "").endswith("技能倍率%") or s.get("stat") == "技能倍率%"]
            self.domain_label = "技能倍率"

        elif self.selected_domain == "independent":
            modifiers = [s for s in steps if s.get("stat") == "独立乘区%"]
            self.domain_label = "独立乘区"

        elif self.selected_domain == "bonus_pct":
            modifiers = [s for s in steps if s.get("stat") == "倍率加值%"]
            self.domain_label = "倍率加值"

        elif self.selected_domain == "flat":
            modifiers = [s for s in steps if s.get("stat") == "固定伤害值加成"]
            self.domain_label = "固定值加成"

        elif self.selected_domain == "pct":
            modifiers = [s for s in steps if s.get('op') == 'PCT']
            self.domain_label = "百分比加成"

        else:
            modifiers = steps
            self.domain_label = "全部来源"

        return modifiers

    def _resolve_bonus_modifiers(self, steps: list[dict], data_key: str) -> list[dict]:
        """解析 BONUS 区修饰符"""
        if self.selected_domain == "bonus_pct":
            modifiers = self.buckets_data.get(data_key, {}).get('modifiers', [])
            if not modifiers:
                modifiers = [s for s in steps if "伤害加成" in s.get("stat", "")]
            if not modifiers:
                modifiers = [{"stat": "伤害加成", "value": 0.0, "source": "面板聚合值（含基础+装备+天赋）"}]
            self.domain_label = "增伤来源"
        else:
            modifiers = steps
            self.domain_label = "全部来源"

        return modifiers

    def _resolve_crit_modifiers(self, steps: list[dict], data_key: str) -> list[dict]:
        """解析 CRIT 区修饰符"""
        if self.selected_domain == "crit_rate":
            modifiers = self.buckets_data.get(data_key, {}).get('crit_rate_modifiers', [])
            if not modifiers:
                modifiers = [s for s in steps if "暴击率" in s.get("stat", "")]
            if not modifiers:
                modifiers = [{"stat": "暴击率", "value": 0.0, "source": "面板聚合值（含基础+装备+天赋）"}]
            self.domain_label = "暴击率来源"
        else:
            modifiers = self.buckets_data.get(data_key, {}).get('modifiers', [])
            if not modifiers:
                modifiers = [s for s in steps if "暴击伤害" in s.get("stat", "")]
            if not modifiers:
                modifiers = [{"stat": "暴击伤害", "value": 0.0, "source": "面板聚合值（含基础+装备+天赋）"}]
            self.domain_label = "暴击伤害来源"

        return modifiers

    def _resolve_react_modifiers(self, steps: list[dict], data_key: str) -> list[dict]:
        """解析 REACT 区修饰符"""
        if self.selected_domain == "em_bonus":
            modifiers = [s for s in steps if s.get("stat") == "精通转化"]
            if not modifiers:
                modifiers = [s for s in steps if "精通" in s.get("source", "")]
            if not modifiers:
                modifiers = [{"stat": "精通转化", "value": 0.0, "source": "无精通加成"}]
            self.domain_label = "精通转化加成"

        elif self.selected_domain == "special":
            modifiers = [s for s in steps if s.get("stat") == "特殊加成"]
            if not modifiers:
                modifiers = [{"stat": "特殊加成", "value": 0.0, "source": "无特殊加成"}]
            self.domain_label = "特殊加成来源"

        elif self.selected_domain == "other_bonus":
            modifiers = [s for s in steps if s["stat"] == "反应加成系数" and s.get("source") != "[精通转化]"]
            self.domain_label = "反应加成来源"

        elif self.selected_domain == "reaction_base":
            modifiers = [s for s in steps if s["stat"] in ("反应基础倍率", "反应系数")]
            self.domain_label = "反应系数"

        else:
            modifiers = steps
            self.domain_label = "全部来源"

        return modifiers

    def _resolve_res_modifiers(self, steps: list[dict], data_key: str) -> list[dict]:
        """解析 RES 区修饰符

        将基础抗性（来自目标面板）转化为修饰符格式显示，
        同时合并 steps 中的减抗修饰符。
        """
        modifiers = []

        # 从 buckets_data 获取抗性原始数据
        res_data = self.buckets_data.get(data_key, {})
        raw_data = res_data.get("raw_data", {})

        # 1. 添加基础抗性（作为第一条修饰符）
        base_res = raw_data.get("base_resistance", 0.0)
        element_name = raw_data.get("element_name", "")
        if base_res != 0 or element_name:  # 有值或元素信息时显示
            modifiers.append({
                "stat": f"{element_name}元素抗性",
                "value": base_res,
                "source": "[目标面板]"
            })

        # 2. 添加减抗修饰符（来自 steps）
        modifiers.extend(steps)

        # 3. 设置域标签
        self.domain_label = "抗性来源"

        return modifiers

    def _resolve_def_modifiers(self, steps: list[dict], data_key: str) -> list[dict]:
        """解析 DEF 区修饰符

        根据 selected_domain 显示不同的修饰符：
        - target_def: 显示目标面板防御力
        - def_reduce: 显示减防修饰符
        - 其他: 显示全部
        """
        modifiers = []

        # 从 buckets_data 获取防御区原始数据
        def_data = self.buckets_data.get(data_key, {})
        raw_data = def_data.get("raw_data", {})

        target_def = raw_data.get("target_defense", 0.0)

        if self.selected_domain == "target_def":
            # 只显示目标面板防御力
            if target_def > 0:
                modifiers.append({
                    "stat": "防御力",
                    "value": target_def,
                    "source": "[目标面板]"
                })
            self.domain_label = "目标防御力"

        elif self.selected_domain == "def_reduce":
            # 只显示减防修饰符
            modifiers.extend(steps)
            self.domain_label = "减防来源"

        else:
            # 显示全部
            if target_def > 0:
                modifiers.append({
                    "stat": "防御力",
                    "value": target_def,
                    "source": "[目标面板]"
                })
            modifiers.extend(steps)
            self.domain_label = "防御来源"

        return modifiers

    @classmethod
    def from_audit_data(
        cls,
        active_bucket: str | None,
        selected_domain: str | None,
        buckets_data: dict
    ) -> 'DomainDetailSectionViewModel':
        """从审计数据创建 ViewModel

        Args:
            active_bucket: 当前激活的乘区
            selected_domain: 选中的域
            buckets_data: 乘区数据字典

        Returns:
            DomainDetailSectionViewModel 实例
        """
        return cls(
            active_bucket=active_bucket,
            selected_domain=selected_domain,
            buckets_data=buckets_data,
        )

    @property
    def has_content(self) -> bool:
        """是否有内容可显示"""
        return self.active_bucket is not None and len(self.modifier_cards) > 0

    @property
    def modifier_count(self) -> int:
        """修饰符数量"""
        return len(self.modifier_cards)
