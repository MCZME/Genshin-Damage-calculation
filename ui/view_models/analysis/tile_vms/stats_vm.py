"""
[V9.2] 角色统计 ViewModel

职责：
1. 混合使用缓存和动态查询
2. 提供角色面板数据
3. 计算瞬时属性

重构说明：
- 使用统一签名 state: AnalysisState
- 通过 state.data_service 访问数据服务
- 通过 state.vm 访问 ViewModel
"""
from __future__ import annotations

import flet as ft
from typing import TYPE_CHECKING, Any, Literal

from ui.theme import GenshinTheme
from ui.assets.descriptions import EFFECT_DESCRIPTIONS
from ui.view_models.analysis.tile_vms.types import AuditResult, ZonedModifier, ModifierZone, CUMULATIVE_STATS, PCT_ADDITIVE_STATS

if TYPE_CHECKING:
    from ui.states.analysis_state import AnalysisState


# --- 属性分组常量 ---
# [V9.5 Pro V2] 重构：移除"生存状态"分组
# - 血条/能量条：在顶部显示，可点击选中查看详情
# - 状态效果：在右区效果墙显示，始终可见无需勾选
STAT_GROUPS: dict[str, list[str]] = {
    "基础属性": ["生命值", "攻击力", "防御力", "元素精通"],
    "进阶属性": ["暴击率", "暴击伤害", "元素充能效率", "治疗加成", "受治疗加成", "护盾强效"],
    # [V9.5 Pro Fix] 拆分元素加成为两组，均衡矩阵布局
    "元素加成·上": [
        "火元素伤害加成", "水元素伤害加成", "草元素伤害加成", "雷元素伤害加成"
    ],
    "元素加成·下": [
        "风元素伤害加成", "冰元素伤害加成", "岩元素伤害加成", "物理伤害加成"
    ]
}

DEFAULT_STATS: list[str] = [
    "攻击力", "生命值", "防御力", "元素精通",
    "暴击率", "暴击伤害", "元素充能效率", "伤害加成"
]


def calculate_snapshot_stat(
    base_stats: dict[str, Any],
    mods: list[dict[str, Any]],
    key: str,
    element: str = "Neutral"
) -> AuditResult:
    """
    [V9.1] 核心计算引擎：基于基础快照与动态修饰符还原瞬时数值
    [V9.3] 元素加成自动合并：计算"伤害加成"时自动累加基础属性中的元素伤害加成
    [V9.7] 返回结构化 AuditResult，支持 UI 图形化拆解

    Args:
        base_stats: 角色基础属性
        mods: 活跃修饰符列表
        key: 目标属性名
        element: 角色元素类型

    Returns:
        AuditResult 结构化结果
    """
    base = float(base_stats.get(key, 0.0))
    pct_bonus = float(base_stats.get(f"{key}%", 0.0))
    flat_bonus = float(base_stats.get(f"固定{key}", 0.0))

    # 针对"伤害加成"的特殊逻辑：合并全伤与元素伤
    actual_keys = [key]
    if key == "伤害加成" and element != "Neutral":
        element_dmg_key = f"{element}元素伤害加成"
        actual_keys.append(element_dmg_key)
        # [V9.3] 自动合并基础属性中的元素伤害加成
        element_dmg_base = float(base_stats.get(element_dmg_key, 0.0))
        base += element_dmg_base

    # 判断是否为百分比属性（用于公式格式化）
    is_pct_stat = any(x in key for x in ["率", "伤害", "充能", "加成", "效率"])

    # 识别计算范式
    if key in CUMULATIVE_STATS:
        paradigm: Literal["cumulative", "pct_additive", "additive"] = "cumulative"
    elif key in PCT_ADDITIVE_STATS:
        paradigm = "pct_additive"
    else:
        paradigm = "additive"

    # 叠加修饰符
    for m in mods:
        m_stat = str(m.get("stat", ""))
        m_val = float(m.get("value", 0.0))

        # 匹配属性名或其百分比/固定变体
        if m_stat in actual_keys:
            flat_bonus += m_val
        elif m_stat.replace("%", "") in actual_keys and "%" in m_stat:
            pct_bonus += m_val
        elif m_stat.replace("固定", "") in actual_keys and "固定" in m_stat:
            flat_bonus += m_val

    # 根据范式计算最终值
    if paradigm == "cumulative":
        total = base * (1 + pct_bonus / 100) + flat_bonus
        # 累乘型公式格式化
        formula = _format_cumulative_formula(base, pct_bonus, flat_bonus, is_pct_stat)
    elif paradigm == "pct_additive":
        # 百分比累加型：基础值 + 百分比加成
        total = base + pct_bonus
        formula = _format_pct_additive_formula(base, pct_bonus, is_pct_stat)
    else:
        # 纯累加型：基础值 + 固定值
        total = base + flat_bonus
        pct_bonus = 0.0
        # 累加型公式格式化
        formula = _format_additive_formula(base, flat_bonus, is_pct_stat)

    return AuditResult(
        paradigm=paradigm,
        base=base,
        pct_sum=pct_bonus,
        flat_sum=flat_bonus,
        total=total,
        formula=formula,
        is_pct_stat=is_pct_stat
    )


def _format_cumulative_formula(
    base: float,
    pct_bonus: float,
    flat_bonus: float,
    is_pct_stat: bool
) -> str:
    """格式化累乘型公式字符串"""
    # 基础值
    base_str = f"{base:.0f}{'%' if is_pct_stat else ''}"

    # 百分比部分：仅在有值时显示
    if abs(pct_bonus) > 0.01:
        pct_str = f" × (1 + {pct_bonus:.1f}%)"
    else:
        pct_str = ""

    # 固定值部分：仅在有值时显示
    if abs(flat_bonus) > 0.01:
        flat_str = f" + {flat_bonus:.0f}"
    else:
        flat_str = ""

    return f"{base_str}{pct_str}{flat_str}"


def _format_pct_additive_formula(
    base: float,
    pct_bonus: float,
    is_pct_stat: bool
) -> str:
    """格式化百分比累加型公式字符串

    Args:
        base: 基础值
        pct_bonus: 百分比加成总和
        is_pct_stat: 是否为百分比属性

    Returns:
        格式化的公式字符串
    """
    if is_pct_stat:
        # 百分比属性（如暴击率、暴击伤害、元素充能效率）
        if abs(pct_bonus) > 0.01:
            return f"{base:.1f}% + {pct_bonus:.1f}%"
        return f"{base:.1f}%"
    else:
        # 非百分比属性（如元素精通）
        if abs(pct_bonus) > 0.01:
            return f"{base:.0f} + {pct_bonus:.0f}"
        return f"{base:.0f}"


def _format_additive_formula(
    base: float,
    flat_bonus: float,
    is_pct_stat: bool
) -> str:
    """格式化累加型公式字符串"""
    if is_pct_stat:
        # 百分比属性格式化
        formula_parts = [f"{base:.1f}%"]
        if abs(flat_bonus) > 0.01:
            sign = "+" if flat_bonus >= 0 else "-"
            formula_parts.append(f"{sign} {abs(flat_bonus):.1f}%")
        return " ".join(formula_parts)
    else:
        # 数值属性格式化
        return f"{base:.1f} + {flat_bonus:.1f}"


# 向后兼容函数
def calculate_snapshot_stat_legacy(
    base_stats: dict[str, Any],
    mods: list[dict[str, Any]],
    key: str,
    element: str = "Neutral"
) -> tuple[float, float, str]:
    """
    [V9.7] 向后兼容包装器 - 返回元组格式

    保持原有签名，供旧代码调用。
    """
    result = calculate_snapshot_stat(base_stats, mods, key, element)
    bonus = result.total - result.base
    return result.total, bonus, result.formula


@ft.observable
class StatsViewModel:
    """
    角色统计 ViewModel - 演示缓存与动态查询混合
    [V9.3] 异步抓取下沉至 ViewModel，带竞态保护
    [V9.4] 字符快照查找缓存 + 计算缓存
    [V9.2] 使用统一签名 state: AnalysisState
    """

    def __init__(
        self,
        state: 'AnalysisState',
        instance_id: str,
        initial_char_id: int = 0
    ):
        self.state = state
        self.instance_id = instance_id
        self.target_char_id: int = initial_char_id
        self.snapshot: dict[str, Any] | None = None
        self.loading_snapshot: bool = False
        # [V9.3] 竞态保护：请求版本控制
        self._request_version: int = 0
        # [V9.4] 字符快照查找缓存
        self._char_snapshot_cache: dict[str, Any] | None = None
        self._char_snapshot_frame: int = -1
        # [V9.4] 计算缓存
        self._stat_cache: dict[str, tuple[float, float, str]] = {}
        # [V9.7] 分解缓存
        self._breakdown_cache: dict[str, tuple[AuditResult, list[ZonedModifier]]] = {}
        self._cache_frame_id: int = -1

    # ============================================================
    # 状态属性
    # ============================================================

    @property
    def frame_id(self) -> int:
        """当前帧 ID"""
        return self.state.vm.current_frame

    @property
    def char_base_slot(self) -> dict[int, dict[str, Any]] | None:
        """从缓存获取角色基础属性槽位"""
        slot = self.state.data_service.get_cached("char_base")
        return slot.data if slot and slot.data else None

    @property
    def char_base(self) -> dict[str, Any]:
        """获取当前目标角色的基础属性"""
        if self.char_base_slot and self.target_char_id in self.char_base_slot:
            return self.char_base_slot[self.target_char_id]
        return {}

    @property
    def char_name(self) -> str:
        """角色名称"""
        return str(self.char_base.get("名称", "Unknown"))

    @property
    def element(self) -> str:
        """角色元素"""
        char_name = self.char_name
        if self.state.vm.app_state:
            char_map = self.state.vm.app_state.char_map
            if char_name in char_map:
                return str(char_map[char_name].get("element", "无"))
        return "无"

    @property
    def theme_color(self) -> str:
        """主题色（基于元素）"""
        return GenshinTheme.get_element_color(self.element)

    # ============================================================
    # 字符快照缓存 [V9.4]
    # ============================================================

    @property
    def _char_snapshot(self) -> dict[str, Any] | None:
        """缓存当前角色快照引用，避免重复遍历 team 列表"""
        if self._char_snapshot_frame != self.frame_id or self._char_snapshot_cache is None:
            if self.snapshot and "team" in self.snapshot:
                self._char_snapshot_cache = next(
                    (c for c in self.snapshot["team"] if c["entity_id"] == self.target_char_id),
                    None
                )
            else:
                self._char_snapshot_cache = None
            self._char_snapshot_frame = self.frame_id
        return self._char_snapshot_cache

    # ============================================================
    # 动态数据
    # ============================================================

    @property
    def active_mods(self) -> list[dict[str, Any]]:
        """活跃修饰符（完整数据，用于计算）"""
        char_snap = self._char_snapshot
        return char_snap.get("active_modifiers", []) if char_snap else []

    @property
    def active_mods_for_display(self) -> list[dict[str, Any]]:
        """[V9.4] 活跃修饰符（精简数据，仅用于 UI 展示）"""
        mods = self.active_mods
        # 只返回 UI 需要的字段
        return [
            {
                "name": m.get("name", "Unknown"),
                "stat": m.get("stat", ""),
                "value": m.get("value", 0.0),
                "op": m.get("op", "unknown")
            }
            for m in mods
        ]

    @property
    def active_effects(self) -> list[dict[str, Any]]:
        """活跃效果"""
        char_snap = self._char_snapshot
        return char_snap.get("active_effects", []) if char_snap else []

    @property
    def active_effects_with_frames(self) -> list[dict[str, Any]]:
        """
        [V9.5] 返回带帧数信息的活跃效果列表
        [V9.6] 添加描述信息，支持动态数据注入

        每个效果包含:
        - name: 效果名称
        - start_frame: 开始帧
        - end_frame: 结束帧（可能为 None）
        - remaining_frames: 剩余帧数
        - total_duration_frames: 总持续时间（帧数）
        - description: 效果描述（可能为 None）
        """
        effects = self.active_effects
        current_frame = self.frame_id
        result: list[dict[str, Any]] = []

        # 获取当前角色的 metrics（用于描述模板格式化）
        char_snap = self._char_snapshot
        metrics = char_snap.get("metrics", {}) if char_snap else {}

        for eff in effects:
            start_f = eff.get("start_frame", 0)
            end_f = eff.get("end_frame")
            duration = eff.get("duration")

            # 计算剩余帧数
            if end_f is not None:
                remaining = end_f - current_frame
            else:
                remaining = None  # 无限持续时间

            # 计算总持续时间
            if end_f is not None and start_f is not None:
                total_duration = end_f - start_f
            elif duration is not None:
                total_duration = duration
            else:
                total_duration = None  # 未知总时间

            # 构建描述 [V9.6]
            description: str | None = None
            effect_name = eff.get("name", "Unknown")
            if effect_name in EFFECT_DESCRIPTIONS:
                template = EFFECT_DESCRIPTIONS[effect_name]
                try:
                    description = template.format(**metrics)
                except KeyError:
                    # 缺少必要的 metric key，使用原始模板
                    description = template

            result.append({
                "name": effect_name,
                "instance_id": eff.get("instance_id"),
                "start_frame": start_f,
                "end_frame": end_f,
                "remaining_frames": max(0, remaining) if remaining is not None else None,
                "total_duration_frames": total_duration,
                "description": description
            })

        return result

    @property
    def shields(self) -> list[dict[str, Any]]:
        """护盾列表"""
        char_snap = self._char_snapshot
        return char_snap.get("shields", []) if char_snap else []

    @property
    def current_hp(self) -> float:
        """当前 HP"""
        base_hp = float(self.char_base.get("生命值", 0))
        char_snap = self._char_snapshot
        if char_snap:
            final_hp, _, _ = calculate_snapshot_stat_legacy(
                self.char_base, self.active_mods, "生命值", self.element
            )
            return float(char_snap.get("current_hp", final_hp))
        return base_hp

    @property
    def max_hp(self) -> float:
        """最大 HP"""
        base_hp = float(self.char_base.get("生命值", 0))
        char_snap = self._char_snapshot
        if char_snap:
            final_hp, _, _ = calculate_snapshot_stat_legacy(
                self.char_base, self.active_mods, "生命值", self.element
            )
            return final_hp
        return base_hp

    @property
    def current_energy(self) -> float:
        """当前能量"""
        char_snap = self._char_snapshot
        if char_snap:
            return float(char_snap.get("current_energy", 0.0))
        return 0.0

    @property
    def max_energy(self) -> float:
        """最大能量"""
        return float(self.char_base.get("元素爆发能量", 40.0))

    # ============================================================
    # 异步操作
    # ============================================================

    async def load_frame_snapshot(self, frame_id: int) -> None:
        """动态查询帧快照（绕过缓存）"""
        self.loading_snapshot = True
        try:
            self.snapshot = await self.state.data_service.query_frame_snapshot(frame_id)
        finally:
            self.loading_snapshot = False

    async def fetch_snapshot(self) -> None:
        """
        [V9.3] 异步获取当前帧快照（带版本控制防止竞态）
        用于从 View 层调用的主要入口
        [V9.5] 添加帧缓存保护，避免重复请求同一帧
        """
        if not self.state.data_service.adapter:
            return

        current_frame = self.frame_id
        # 如果已经有当前帧的数据，跳过
        if self.snapshot and self._cache_frame_id == current_frame:
            return

        # 递增版本号
        current_version = self._request_version + 1
        self._request_version = current_version

        self.loading_snapshot = True
        try:
            data = await self.state.data_service.adapter.get_frame(current_frame)

            # 仅当版本匹配时更新（防止旧数据覆盖新数据）
            if self._request_version == current_version:
                self.snapshot = data
                self._cache_frame_id = current_frame
        finally:
            self.loading_snapshot = False

    # ============================================================
    # 计算方法
    # ============================================================

    def calculate_stat(self, key: str) -> tuple[float, float, str]:
        """
        [V9.4] 计算指定属性的瞬时值（带缓存）
        [V9.7] 内部使用 AuditResult，外部返回元组格式（向后兼容）
        [V9.10] 修复：在 snapshot 未获取或正在加载时不缓存空结果

        Returns:
            (最终值, 加成值, 公式字符串)
        """
        # 如果正在加载或 snapshot 未获取，返回空结果（不缓存）
        if self.loading_snapshot or self.snapshot is None:
            result = calculate_snapshot_stat(
                self.char_base, [], key, self.element
            )
            bonus = result.total - result.base
            return (result.total, bonus, result.formula)

        # 缓存失效检测：帧 ID 变化时清空缓存
        if self._cache_frame_id != self.frame_id:
            self._stat_cache.clear()
            self._cache_frame_id = self.frame_id

        # 检查缓存
        if key in self._stat_cache:
            return self._stat_cache[key]

        # 计算并缓存（转换为元组格式）
        result = calculate_snapshot_stat(
            self.char_base, self.active_mods, key, self.element
        )
        bonus = result.total - result.base
        tuple_result = (result.total, bonus, result.formula)
        self._stat_cache[key] = tuple_result
        return tuple_result

    def get_display_stats(self) -> list[str]:
        """获取用户偏好的展示属性列表"""
        char_id = self.target_char_id
        prefs = self.state.vm.get_stat_preferences(char_id)
        return prefs if prefs else DEFAULT_STATS

    def get_relevant_mods(self, stat_key: str) -> list[dict[str, Any]]:
        """[V9.4] 获取与指定属性相关的修饰符（精简数据，用于 UI 展示）"""
        search_keys = [stat_key, f"{stat_key}%", f"固定{stat_key}"]
        if stat_key == "伤害加成":
            search_keys.append(f"{self.element}元素伤害加成")

        relevant: list[dict[str, Any]] = []
        for m in self.active_mods:
            if m.get("stat") in search_keys:
                # 只返回 UI 需要的字段
                relevant.append({
                    "name": m.get("name", "Unknown"),
                    "stat": m.get("stat", ""),
                    "value": m.get("value", 0.0),
                    "op": m.get("op", "unknown")
                })
        return relevant

    def get_stat_breakdown(self, stat_key: str) -> tuple[AuditResult, list[ZonedModifier]]:
        """
        [V9.7] 获取属性计算的完整分解
        [V9.10] 修复：在 snapshot 未获取或正在加载时不缓存空结果

        Args:
            stat_key: 属性名称

        Returns:
            (AuditResult 计算结果, ZonedModifier 带乘区标记的修饰符列表)
        """
        # 如果正在加载或 snapshot 未获取，返回空结果（不缓存）
        if self.loading_snapshot or self.snapshot is None:
            result = calculate_snapshot_stat(
                self.char_base, [], stat_key, self.element
            )
            return result, []

        # 缓存失效检测：帧 ID 变化时清空缓存
        if self._cache_frame_id != self.frame_id:
            self._stat_cache.clear()
            self._breakdown_cache.clear()
            self._cache_frame_id = self.frame_id

        # 检查缓存
        if stat_key in self._breakdown_cache:
            return self._breakdown_cache[stat_key]

        # 计算结构化结果
        result = calculate_snapshot_stat(
            self.char_base, self.active_mods, stat_key, self.element
        )

        # 过滤修饰符并标记乘区
        zoned_mods: list[ZonedModifier] = []
        search_keys = [stat_key, f"{stat_key}%", f"固定{stat_key}"]
        if stat_key == "伤害加成":
            search_keys.append(f"{self.element}元素伤害加成")

        for m in self.active_mods:
            m_stat = m.get("stat", "")
            if m_stat in search_keys:
                # 判断所属乘区
                if "%" in m_stat:
                    zone = ModifierZone.PERCENT
                elif "固定" in m_stat:
                    zone = ModifierZone.FLAT
                else:
                    # 直接匹配属性名的修饰符
                    # - 累乘型属性（攻击力/生命值/防御力）：归入 BASE 区（作为基础加成）
                    # - 其他属性（元素精通等）：归入 FLAT 区（作为固定值加成）
                    if result.paradigm == "cumulative":
                        zone = ModifierZone.BASE
                    else:
                        zone = ModifierZone.FLAT

                # [V9.9] 识别来源类型
                m_name = str(m.get("name", "Unknown"))
                source_type = "Other"
                
                # 简单的名称启发式识别 (实际项目中可根据 m 中的元数据判断)
                if any(x in m_name for x in ["之", "刃", "弓", "剑", "枪", "棒", "典"]):
                    source_type = "Weapon"
                elif any(x in m_name for x in ["2P", "4P", "件套", "花", "羽", "沙", "杯", "冠", "套"]):
                    source_type = "Artifact"
                elif any(x in m_name for x in ["天赋", "命之座", "技能"]):
                    source_type = "Talent"
                elif "共鸣" in m_name:
                    source_type = "Resonance"

                zoned_mods.append(ZonedModifier(
                    name=m_name,
                    stat=str(m_stat),
                    value=float(m.get("value", 0.0)),
                    op=str(m.get("op", "unknown")),
                    zone=zone,
                    source_type=source_type
                ))

        # 缓存结果
        self._breakdown_cache[stat_key] = (result, zoned_mods)
        return result, zoned_mods

    def get_total_shield_hp(self) -> float:
        """计算总护盾量"""
        return sum(s.get('current_hp', 0) for s in self.shields)

    # ============================================================
    # 角色同步方法
    # ============================================================

    def update_char_id(self, char_id: int) -> bool:
        """更新角色 ID，返回是否发生变化"""
        if self.target_char_id != char_id:
            self.target_char_id = char_id
            return True
        return False

    # ============================================================
    # 状态条代理方法
    # ============================================================

    def get_status_bar_selection(self) -> list[str] | None:
        """获取状态条选中状态"""
        return self.state.vm.get_status_bar_selection(self.instance_id)

    def toggle_status_bar_selection(self, selection: str) -> None:
        """切换状态条选中状态"""
        self.state.vm.toggle_status_bar_selection(self.instance_id, selection)

    # ============================================================
    # 设置菜单
    # ============================================================

    def get_settings_menu_items(self) -> list[tuple[int, str]]:
        """
        获取设置菜单项
        Returns: [(char_id, char_name), ...]
        """
        items: list[tuple[int, str]] = []
        if not self.char_base_slot:
            return items

        for cid, stats in self.char_base_slot.items():
            name = str(stats.get("名称", f"ID:{cid}"))
            items.append((cid, name))
        return items

    # ============================================================
    # [V9.5 Pro V2] 自适应状态集群数据
    # ============================================================

    def get_status_indicators(
        self, 
        selection: list[str] | None = None,
        focus_name: str | None = None,
        always_show: bool = False
    ) -> list[dict[str, Any]]:
        """
        [V9.5 Pro V2] 为 AdaptiveStatusCluster 提供配置数据

        Args:
            selection: 当前选中状态列表（如 ["血条", "能量条"]）
            focus_name: 当前获得焦点的状态项（供审计面板使用，带高亮反馈）
            always_show: 是否始终显示所有指标（展开模式用）

        Returns:
            指示器配置列表
        """
        indicators: list[dict[str, Any]] = []
        
        # 如果 selection 为 None，视为“未初始化的默认状态”，此时全显（show_all = True）
        # 一旦用户进行了勾选操作（哪怕勾选后又全部取消，导致 selection 为空列表），则进入“仅显示选中项”模式，不再全显
        show_all = selection is None
        actual_selection = selection or []

        # HP 指示器
        hp_checked = "血条" in actual_selection
        indicators.append({
            "name": "HP",
            "current": self.current_hp,
            "maximum": self.max_hp,
            "color": ft.Colors.GREEN_400,
            "visible": always_show or show_all or hp_checked,
            "checked": hp_checked,
            "selected": focus_name == "血条"
        })

        # 能量指示器
        energy_checked = "能量条" in actual_selection
        indicators.append({
            "name": "Energy",
            "current": self.current_energy,
            "maximum": self.max_energy,
            "color": self.theme_color,
            "visible": always_show or show_all or energy_checked,
            "checked": energy_checked,
            "selected": focus_name == "能量条"
        })

        return indicators
