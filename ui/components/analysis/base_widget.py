import flet as ft
from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ui.states.analysis_state import AnalysisState, DataSlot

class AnalysisTile(ABC):
    """
    分析磁贴基类 (V4.7 订阅制版)
    所有业务磁贴必须继承此类，通过引用计数机制按需获取数据。
    """
    def __init__(self, title: str, icon: str, tile_type: str, state: 'AnalysisState'):
        self.title = title
        self.icon = icon
        self.tile_type = tile_type
        self.state = state
        self.instance_id: Optional[str] = None # 由 View 在创建时分配
        self.expand = False


    async def subscribe_data(self) -> Optional['DataSlot']:
        """
        向 DataManager 订阅本磁贴所需的数据切片。
        """
        if not self.instance_id:
            return None
        return await self.state.data_manager.subscribe(self.tile_type, self.instance_id)

    async def unsubscribe_data(self):
        """
        释放订阅，允许 DataManager 在无引用时清理内存。
        """
        if self.instance_id:
            await self.state.data_manager.unsubscribe(self.tile_type, self.instance_id)
