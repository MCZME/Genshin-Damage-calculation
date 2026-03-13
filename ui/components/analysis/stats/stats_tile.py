"""
[V9.5 Pro V2] 角色实时面板磁贴组件

重构说明：
- 数据转换逻辑已迁移至 StatsViewModel
- 组件仅负责 UI 渲染
- 混合使用缓存和动态查询
- 引入状态胶囊系统 (Status Capsule System)
- [V9.5 Pro V2] 引入自适应状态集群 (AdaptiveStatusCluster)
- [V9.2] 使用统一签名 state: AnalysisState
- StatsDashboard 和 StatsDetailAudit 已拆分至独立文件
- [V9.6] ViewModel 提升至 CharacterStatsTileRenderer，统一生命周期管理
"""
import flet as ft
from typing import TYPE_CHECKING, Any, cast

from ui.components.analysis.base_widget import AnalysisTile
from ui.view_models.analysis.tile_vms.stats_vm import StatsViewModel
from ui.components.analysis.stats.stats_dashboard import StatsDashboard
from ui.components.analysis.stats.stats_detail_audit import StatsDetailAudit
from ui.theme import GenshinTheme

if TYPE_CHECKING:
    from ui.states.analysis_state import AnalysisState


@ft.component
def CharacterStatsTileRenderer(
    state: 'AnalysisState',
    instance_id: str,
    is_maximized: bool
):
    """[V9.6] 统一的渲染入口，管理 VM 生命周期

    职责：
    1. 创建单一 ViewModel 实例
    2. 同步 char_id
    3. 统一数据获取触发
    4. 分发渲染
    """

    # 1. 获取关键状态
    char_id = state.vm.get_tile_char(instance_id)
    frame_id = state.vm.current_frame
    session_id = state.vm.current_session_id

    # 2. 创建 ViewModel (单一实例)
    vm = ft.use_memo(
        lambda: StatsViewModel(state, instance_id, initial_char_id=char_id),
        [frame_id]
    )

    # 3. 同步 char_id
    if vm.target_char_id != char_id:
        vm.target_char_id = char_id

    # 4. 统一数据获取
    def fetch_data():
        state.vm.run_task(vm.fetch_snapshot)

    ft.use_effect(fetch_data, [frame_id, char_id, session_id])

    # 5. 获取基础数据
    base_slot = state.data_service.get_slot("char_base")
    if not base_slot or not base_slot.data or char_id not in base_slot.data:
        return ft.Container(
            content=ft.Text("请先选择角色", color=ft.Colors.WHITE_38),
            alignment=ft.Alignment.CENTER
        )

    # 6. 分发渲染
    if is_maximized:
        return StatsDetailAudit(vm=vm)
    return StatsDashboard(vm=vm)


class CharacterStatsTile(AnalysisTile):
    """
    [V9.2] 磁贴：角色实时面板 (瞬时快照审计版)
    规格: 2x2

    重构说明：
    - 数据转换逻辑已迁移至 StatsViewModel
    - 组件仅负责 UI 渲染
    - 使用统一签名 state: AnalysisState
    """

    def __init__(
        self,
        state: 'AnalysisState',
        instance_id: str
    ):
        super().__init__(
            "角色实时面板",
            ft.Icons.PERSON_SEARCH_ROUNDED,
            "stats",
            state
        )
        self.instance_id = instance_id
        self.theme_color = GenshinTheme.ELEMENT_COLORS["Neutral"]
        self.is_maximized = False
        self.has_settings = True

    def get_settings_items(self) -> list[ft.PopupMenuItem]:
        """[V9.1] 构造角色切换菜单项列表"""
        base_slot = self.state.data_service.get_slot("char_base")
        if not base_slot or not base_slot.data:
            return []

        menu_items: list[ft.PopupMenuItem] = []
        char_data = cast(dict[int, Any], base_slot.data)
        iid = cast(str, self.instance_id)

        for cid, stats in char_data.items():
            name = str(stats.get("名称", f"ID:{cid}"))

            def make_handler(_cid, _iid=iid):
                return lambda e: self.state.vm.set_tile_char(_iid, _cid)

            menu_items.append(ft.PopupMenuItem(content=ft.Text(name), on_click=make_handler(cid)))
        return menu_items

    def render(self) -> ft.Control:
        """
        [V9.6] 渲染入口分发。
        委托给 CharacterStatsTileRenderer，由其管理 ViewModel 生命周期。
        """
        return CharacterStatsTileRenderer(
            state=self.state,
            instance_id=cast(str, self.instance_id),
            is_maximized=getattr(self, "is_maximized", False)
        )
