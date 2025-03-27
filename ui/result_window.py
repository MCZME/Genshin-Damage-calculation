from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QLabel,
                              QPushButton, QHBoxLayout, QFrame, QScrollArea,
                              QSizePolicy)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtCharts import (QChart, QChartView, QLineSeries, QValueAxis,
                             QBarSeries, QBarSet, QBarCategoryAxis)
from PySide6.QtGui import QPainter

from setup.DataHandler import send_to_window

class ResultWindow(QMainWindow):
    """结果窗口类"""
    def __init__(self):
        super().__init__()
        self.damage_chart = None
        self.damage_chart_view = None
        
        # 主窗口布局
        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout()
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)
        
        # 初始化图表
        self.init_damage_chart()
        self.main_layout.addWidget(self.damage_chart_view)
        
    def init_damage_chart(self):
        """初始化伤害柱状图"""
        self.damage_chart = QChart()
        self.damage_chart.setAnimationOptions(QChart.SeriesAnimations)
        self.damage_chart_view = QChartView(self.damage_chart)
        self.damage_chart_view.setRenderHint(QPainter.Antialiasing)
        self.damage_chart_view.setMinimumSize(600, 400)
        self.update_damage_chart()

    def update_damage_chart(self):
        """更新伤害柱状图数据
        Args:
            damage_data (dict): {时间: 伤害}格式的伤害数据
        """
        damage_data=send_to_window('damage')
        if not self.damage_chart:
            self.init_damage_chart()
            
        # 清除旧数据
        self.damage_chart.removeAllSeries()
        
        # 创建柱状图系列
        series = QBarSeries()
        bar_set = QBarSet("伤害值")
        
        # 提取并排序数据
        sorted_times = sorted(damage_data.keys())
        damages = [damage_data[time] for time in sorted_times]
        
        # 添加数据
        bar_set.append(damages)
        series.append(bar_set)
        self.damage_chart.addSeries(series)
        
        # 设置X轴(时间)
        axis_x = QBarCategoryAxis()
        axis_x.append([str(time) for time in sorted_times])
        self.damage_chart.createDefaultAxes()
        self.damage_chart.setAxisX(axis_x, series)
        
        # 设置Y轴(伤害值)
        axis_y = QValueAxis()
        axis_y.setTitleText("伤害值")
        self.damage_chart.setAxisY(axis_y, series)
        
        # 设置图表标题
        self.damage_chart.setTitle("伤害随时间变化")
