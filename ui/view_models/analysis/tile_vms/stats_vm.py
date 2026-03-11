"""
[V9.1] 角色统计 ViewModel

职责：
1. 混合使用缓存和动态查询
2. 提供角色面板数据
3. 计算瞬时属性
"""
from __future__ import annotations

import flet as ft
from typing import TYPE_CHECKING, Any

from ui.theme import GenshinTheme

if TYPE_CHECKING:
    from ui.services.analysis_data_service import AnalysisDataService


# --- 属性分组常量 ---
# [V9.5] 重构：区分"生存状态"（组件项）和"面板属性"（数值项）
# - 血条/能量条 = 实时状态组件，控制顶部及仪表盘状态条显示
# - 生命值/元素能量 = 面板数值项，参与计算
STAT_GROUPS: dict[str, list[str]] = {
    "生存状态": ["血条", "能量条"],  # 组件项：控制顶部状态条显示
    "基础属性": ["生命值", "攻击力", "防御力", "元素精通"],  # 数值项
    "进阶属性": ["暴击率", "暴击伤害", "元素充能效率", "治疗加成", "受治疗加成"],
    "元素加成": [
        "火元素伤害加成", "水元素伤害加成", "草元素伤害加成",
        "雷元素伤害加成", "风元素伤害加成", "冰元素伤害加成",
        "岩元素伤害加成", "物理伤害加成"
    ],
    "其他": ["抗打断", "护盾强效"]
}

DEFAULT_STATS: list[str] = [
    # [V9.5] 新增默认显示血条和能量条
    "血条", "能量条",
    "攻击力", "生命值", "防御力", "元素精通",
    "暴击率", "暴击伤害", "元素充能效率", "伤害加成"
]


def calculate_snapshot_stat(
    base_stats: dict[str, Any],
    mods: list[dict[str, Any]],
    key: str,
    element: str = "Neutral"
) -> tuple[float, float, str]:
    """
    [V9.1] 核心计算引擎：基于基础快照与动态修饰符还原瞬时数值
    [V9.3] 元素加成自动合并：计算"伤害加成"时自动累加基础属性中的元素伤害加成

    Args:
        base_stats: 角色基础属性
        mods: 活跃修饰符列表
        key: 目标属性名
        element: 角色元素类型

    Returns:
        (最终值, 加成值, 公式字符串)
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

    # 计算公式追踪
    formula = f"{base:.1f}{'%' if is_pct_stat else ''}"

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

    if key in ["攻击力", "生命值", "防御力"]:
        total = base * (1 + pct_bonus / 100) + flat_bonus
        bonus = total - base
        formula = f"{base:.0f} × (1 + {pct_bonus:.1f}%) + {flat_bonus:.0f}"
        return total, bonus, formula

    # 其他属性（如精通、双暴、充能）通常是平铺加法
    total = base + flat_bonus
    bonus = total - base

    # [V9.4] 优化百分比属性格式化
    if is_pct_stat:
        # 基础值显示为百分比
        formula_parts = [f"{base:.1f}%"]
        # 加成也显示为百分比
        if abs(flat_bonus) > 0.01:
            formula_parts.append(f"+ {flat_bonus:.1f}%")
        formula = " ".join(formula_parts)
    else:
        formula = f"{base:.1f} + {flat_bonus:.1f}"

    return total, bonus, formula


@ft.observable
class StatsViewModel:
    """
    角色统计 ViewModel - 演示缓存与动态查询混合
    [V9.3] 异步抓取下沉至 ViewModel，带竞态保护
    [V9.4] 字符快照查找缓存 + 计算缓存
    """

    def __init__(self, data_service: 'AnalysisDataService', instance_id: str):
        self.data_service = data_service
        self.instance_id = instance_id
        self.target_char_id: int = 0
        self.snapshot: dict[str, Any] | None = None
        self.loading_snapshot: bool = False
        # [V9.3] 竞态保护：请求版本控制
        self._request_version: int = 0
        # [V9.4] 字符快照查找缓存
        self._char_snapshot_cache: dict[str, Any] | None = None
        self._char_snapshot_frame: int = -1
        # [V9.4] 计算缓存
        self._stat_cache: dict[str, tuple[float, float, str]] = {}
        self._cache_frame_id: int = -1

    # ============================================================
    # 状态属性
    # ============================================================

    @property
    def frame_id(self) -> int:
        """当前帧 ID"""
        return self.data_service.state.current_frame

    @property
    def char_base_slot(self) -> dict[int, dict[str, Any]] | None:
        """从缓存获取角色基础属性槽位"""
        slot = self.data_service.get_cached("char_base")
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
        if self.data_service.state.app_state:
            char_map = self.data_service.state.app_state.char_map
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
            final_hp, _, _ = calculate_snapshot_stat(
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
            final_hp, _, _ = calculate_snapshot_stat(
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
            self.snapshot = await self.data_service.query_frame_snapshot(frame_id)
        finally:
            self.loading_snapshot = False

    async def fetch_snapshot(self) -> None:
        """
        [V9.3] 异步获取当前帧快照（带版本控制防止竞态）
        用于从 View 层调用的主要入口
        [V9.5] 添加帧缓存保护，避免重复请求同一帧
        """
        if not self.data_service.adapter:
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
            data = await self.data_service.adapter.get_frame(current_frame)

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

        Returns:
            (最终值, 加成值, 公式字符串)
        """
        # 缓存失效检测：帧 ID 变化时清空缓存
        if self._cache_frame_id != self.frame_id:
            self._stat_cache.clear()
            self._cache_frame_id = self.frame_id

        # 检查缓存
        if key in self._stat_cache:
            return self._stat_cache[key]

        # 计算并缓存
        result = calculate_snapshot_stat(
            self.char_base, self.active_mods, key, self.element
        )
        self._stat_cache[key] = result
        return result

    def get_display_stats(self) -> list[str]:
        """获取用户偏好的展示属性列表"""
        char_id = self.target_char_id
        prefs = self.data_service.state.get_stat_preferences(char_id)
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

    def get_total_shield_hp(self) -> float:
        """计算总护盾量"""
        return sum(s.get('current_hp', 0) for s in self.shields)

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
