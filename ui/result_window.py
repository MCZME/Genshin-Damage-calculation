from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QLabel,
                              QPushButton, QHBoxLayout, QFrame, QScrollArea,
                              QSizePolicy)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QMargins, QRectF
from PySide6.QtGui import QPainter, QColor, QFont, QFontMetrics
from PySide6.QtCharts import (QChart, QChartView, QLineSeries, QValueAxis,
                             QBarSeries, QBarSet, QBarCategoryAxis)

from setup.DataHandler import send_to_window
from ui.components import VerticalLabelChart

class ResultWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.chart = VerticalLabelChart()
        self.setCentralWidget(self.chart)
        self.update_damage_chart()

    def update_damage_chart(self):
        damage_data = send_to_window('damage')
        if not damage_data:
            return

        self.chart.set_data(damage_data)
