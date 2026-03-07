import flet as ft
import asyncio
from typing import Dict, Any, List, Optional
from ui.theme import GenshinTheme
from ui.states.analysis_state import AnalysisState
from ui.components.analysis.base_widget import AnalysisTile
from core.logger import get_ui_logger

@ft.component
def StatsContent(state: AnalysisState):
    """
    角色面板核心渲染组件 (响应式 V1.0)。
    监听 frame_id 与 focus_char_id。
    """
    frame_id = state.model.current_frame
    focus_id = state.model.focus_char_id
    
    # 1. 局部状态：存储抓取到的快照
    snapshot, set_snapshot = ft.use_state(None)
    loading, set_loading = ft.use_state(False)

    # 2. 数据抓取逻辑
    def fetch_data():
        if not state.adapter: return
        
        async def _fetch():
            set_loading(True)
            try:
                # 使用 Adapter 的 get_frame 接口直接获取特定帧快照
                data = await state.adapter.get_frame(frame_id)
                set_snapshot(data)
            except Exception as e:
                get_ui_logger().log_error(f"StatsTile Fetch Error: {e}")
            finally:
                set_loading(False)
        
        asyncio.create_task(_fetch())

    # 监听帧变动与 Session 变动
    ft.use_effect(fetch_data, [frame_id, state.model.current_session_id])

    # 3. 渲染逻辑
    if loading and not snapshot:
        return ft.Container(
            content=ft.ProgressRing(width=20, height=20, color=ft.Colors.WHITE_24),
            alignment=ft.Alignment.CENTER,
            expand=True
        )

    if not snapshot or not snapshot.get("team"):
        return ft.Container(
            content=ft.Text("无有效数据快照", size=12, color=ft.Colors.WHITE_38),
            alignment=ft.Alignment.CENTER,
            expand=True
        )

    # 4. 提取目标角色
    team = snapshot["team"]
    char_data = None
    if focus_id:
        char_data = next((c for c in team if c["entity_id"] == focus_id), team[0])
    else:
        char_data = team[0]
        # 顺便同步到全局状态，确保后续组件一致性
        if not state.model.focus_char_id:
            state.model.focus_char_id = char_data["entity_id"]

    # 5. 属性提取
    base_stats = char_data.get("stats", {})
    mods = char_data.get("active_modifiers", [])
    
    # 定义展示指标
    metrics = [
        ("攻击力", "攻击力", ft.Icons.TARGET),
        ("生命值", "生命值", ft.Icons.FAVORITE_ROUNDED),
        ("防御力", "防御力", ft.Icons.SHIELD_ROUNDED),
        ("元素精通", "元素精通", ft.Icons.AUTO_AWESOME_ROUNDED),
        ("暴击率", "暴击率", ft.Icons.TRACK_CHANGES_ROUNDED),
        ("暴击伤害", "暴击伤害", ft.Icons.FLASH_ON_ROUNDED),
        ("充能效率", "元素充能效率", ft.Icons.REPLAY_CIRCLE_FILLED_ROUNDED),
        ("伤害加成", "伤害加成", ft.Icons.ADD_CHART_ROUNDED),
    ]

    def create_stat_item(label, key, icon):
        # 从 stats 中提取最终值
        total = base_stats.get(key, 0.0)
        # TODO: 未来版本可以从快照中提取更精细的 Base/Bonus 区分
        # 目前版本先展示总值
        
        is_pct = "%" in label or "暴击" in label or "充能" in label or "加成" in label
        fmt = ".1f" if is_pct else ".0f"
        suffix = "%" if is_pct else ""
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(icon, size=12, color=ft.Colors.WHITE_38),
                    ft.Text(label, size=10, color=ft.Colors.WHITE_54),
                ], spacing=4),
                ft.Row([
                    ft.Text(f"{total:{fmt}}{suffix}", size=15, weight="w900", color=ft.Colors.WHITE),
                ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.BASELINE, spacing=4)
            ], spacing=2),
            expand=True
        )

    # 6. 构造最终 UI
    element = char_data.get("element", "Neutral")
    theme_color = GenshinTheme.get_element_color(element)

    return ft.Column([
        # 角色头信息
        ft.Row([
            ft.Container(
                content=ft.Text(element, size=9, weight="bold", color=ft.Colors.BLACK),
                bgcolor=theme_color,
                padding=ft.Padding(4, 2, 4, 2),
                border_radius=4
            ),
            ft.Text(char_data.get("name", "Unknown"), size=14, weight="bold"),
            ft.Spacer(),
            ft.Text(f"FRAME {frame_id}", size=10, font_family="Consolas", color=ft.Colors.WHITE_24)
        ], alignment=ft.MainAxisAlignment.START),
        
        ft.Divider(height=1, color="rgba(255,255,255,0.05)"),
        
        # 属性网格 (2x4)
        ft.Column([
            ft.Row([create_stat_item(metrics[i][0], metrics[i][1], metrics[i][2]) for i in range(0, 2)], spacing=10),
            ft.Row([create_stat_item(metrics[i][0], metrics[i][1], metrics[i][2]) for i in range(2, 4)], spacing=10),
            ft.Row([create_stat_item(metrics[i][0], metrics[i][1], metrics[i][2]) for i in range(4, 6)], spacing=10),
            ft.Row([create_stat_item(metrics[i][0], metrics[i][1], metrics[i][2]) for i in range(6, 8)], spacing=10),
        ], spacing=12, expand=True),
        
        ft.Divider(height=1, color="rgba(255,255,255,0.05)"),
        
        # 底部元数据
        ft.Row([
            ft.Row([
                ft.Icon(ft.Icons.BOLT_ROUNDED, size=12, color=theme_color),
                ft.Text(f"{len(mods)} ACTIVE BUFFS", size=9, color=theme_color, weight="bold"),
            ], spacing=4),
            ft.Text(f"ID: {char_data['entity_id']}", size=9, color=ft.Colors.WHITE_10)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    ], spacing=10, expand=True)

class CharacterStatsTile(AnalysisTile):
    """
    磁贴：角色实时面板 (V1.0)
    规格: 2x2
    """
    def __init__(self, state: AnalysisState, instance_id: str):
        super().__init__("角色实时面板", ft.Icons.PERSON_SEARCH_ROUNDED, "stats", state)
        self.instance_id = instance_id
        # 初始主题色，实际颜色由内部组件根据角色元素动态计算
        self.theme_color = GenshinTheme.ELEMENT_COLORS["Neutral"]
        self.gradient_top = "#2A2634"

    def render(self):
        # 委托给函数组件处理响应式逻辑
        return StatsContent(state=self.state)
