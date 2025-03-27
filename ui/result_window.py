from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QLabel,
                              QPushButton, QHBoxLayout, QFrame, QScrollArea,
                              QSizePolicy)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer,QMargins
from PySide6.QtCharts import (QChart, QChartView, QLineSeries, QValueAxis,
                             QBarSeries, QBarSet, QBarCategoryAxis)
from PySide6.QtGui import QPainter, QColor,QFont

from setup.DataHandler import send_to_window

class ResultWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.chart = None
        self.chart_view = None
        self.setup_chart()  # 初始化图表

    def setup_chart(self):
        """初始化折线图"""
        self.chart = QChart()
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.chart_view.setMinimumSize(800, 500)  # 增大显示区域
        self.setCentralWidget(self.chart_view)
        self.update_damage_chart()  # 初始化数据

    def update_damage_chart(self):
        damage_data = send_to_window('damage')
        if not damage_data:
            return

        # 过滤非零数据
        non_zero_data = {time: dmg for time, dmg in damage_data.items() if dmg > 0}
        if not non_zero_data:
            return

        # 清除旧数据
        self.chart.removeAllSeries()

        # 创建折线系列
        series = QLineSeries()
        series.setName("伤害值")
        series.setColor(QColor(255, 0, 0))  # 红色线条
        series.setPointsVisible(True)       # 显示数据点
        series.setPointLabelsVisible(True)  # 启用标签
        series.setPointLabelsFormat("@yPoint")  # 关键修改：仅显示Y值

        # 填充数据
        sorted_times = sorted(non_zero_data.keys())
        for time in sorted_times:
            series.append(time, non_zero_data[time])

        self.chart.addSeries(series)

        # 设置坐标轴（X轴仍保留帧号，但点标签不显示）
        axis_x = QValueAxis()
        axis_x.setTitleText("帧号")
        axis_x.setRange(min(sorted_times) - 10, max(sorted_times) + 10)
        axis_x.setLabelFormat("%d")

        axis_y = QValueAxis()
        axis_y.setTitleText("伤害值")
        axis_y.setRange(0, max(non_zero_data.values()) * 1.2)

        self.chart.addAxis(axis_x, Qt.AlignBottom)
        self.chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

        # 图表样式
        self.chart.setTitle("伤害值分布（仅显示数值）")
        self.chart.legend().setVisible(True)
        series.setPointLabelsFont(QFont("Arial", 8))  # 设置标签字体
        series.setPointLabelsColor(QColor(0, 0, 0))   # 黑色标签
        self.chart.setAnimationOptions(QChart.NoAnimation)