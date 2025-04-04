from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCharts import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from PySide6.QtGui import QPainter, QFont
from PySide6.QtCore import Qt, Signal

class VerticalLabelChart(QWidget):
    bar_clicked = Signal(int)

    def __init__(self):
        super().__init__()
        self.frames = []
        self.current_frame = None
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.chart = QChart()
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.layout.addWidget(self.chart_view)
        self.setLayout(self.layout)
        self.set_data({})

    def set_data(self, data):
        self.chart.removeAllSeries()
        for axis in self.chart.axes():
            self.chart.removeAxis(axis)

        if not data:
            self.chart.setTitle("暂无数据")
            self.frames = []
            return

        filtered_data = {frame: int(value) for frame, value in data.items() if value != 0}
        sorted_data = sorted(filtered_data.items())

        if not sorted_data:
            self.chart.setTitle("无有效数据")
            self.frames = []
            return

        frames, values = zip(*sorted_data)
        self.frames = list(frames)

        series = QBarSeries()
        series.setLabelsVisible(True)
        series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)

        bar_set = QBarSet("伤害值")
        bar_set.setLabelColor(Qt.black)
        
        for value in values:
            bar_set.append(value)

        series.append(bar_set)
        series.clicked.connect(self.on_bar_clicked)
        self.chart.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append([str(frame) for frame in frames])
        axis_x.setLabelsAngle(90)
        axis_x.setLabelsFont(QFont("Arial", 8))
        self.chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        max_value = max(values) if values else 1
        axis_y.setRange(0, max_value * 1.1)
        axis_y.setLabelFormat("%d")  # 强制使用十进制整数
        self.chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        self.chart.setTitle("伤害值分布图")
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignBottom)

    def on_bar_clicked(self, index):
        if 0 <= index < len(self.frames):
            self.current_frame = self.frames[index]
            print(f"点击了帧: {self.current_frame}")
            self.bar_clicked.emit(self.current_frame)