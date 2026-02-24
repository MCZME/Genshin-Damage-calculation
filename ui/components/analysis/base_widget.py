import flet as ft
from abc import ABC, abstractmethod
from typing import Optional
from core.persistence.adapter import ReviewDataAdapter

class AnalysisTile(ft.Container, ABC):
    """
    分析磁贴基类。
    定义了模块化分析组件的标准接口：数据加载与帧同步。
    """
    def __init__(self, title: str, icon: str):
        super().__init__()
        self.title = title
        self.icon = icon
        # 移除默认的 self.expand = True，由具体的磁贴控制
        self.clip_behavior = ft.ClipBehavior.ANTI_ALIAS

    @abstractmethod
    def load_data(self, adapter: ReviewDataAdapter):
        """
        初始化加载：从数据库适配器预取并索引数据。
        """
        pass

    @abstractmethod
    def sync_to_frame(self, frame_id: int):
        """
        时间同步：全局标尺变动时，仅修改现有控件属性，严禁重建 UI。
        """
        pass

    def get_optimal_size(self) -> tuple[int, int]:
        """
        返回磁贴推荐的网格尺寸 (col_span, row_span)。
        默认 1x1。
        """
        return (1, 1)

    def on_config_toggle(self):
        """
        可选：磁贴内部设置面板切换回调。
        """
        pass
