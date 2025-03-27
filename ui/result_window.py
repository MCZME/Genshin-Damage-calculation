from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QLabel,
                              QPushButton, QHBoxLayout, QFrame, QScrollArea,
                              QSizePolicy)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QMargins, QRectF
from PySide6.QtGui import QPainter, QColor, QFont, QFontMetrics
from PySide6.QtCharts import (QChart, QChartView, QLineSeries, QValueAxis,
                             QBarSeries, QBarSet, QBarCategoryAxis)

from setup.DataHandler import send_to_window

class VerticalLabelChart(QWidget):
    def __init__(self):
        super().__init__()
        self.data = []  # [(frame, value), ...]
        self.max_value = 1
        self.bar_color = QColor(255, 0, 0)  # 红色柱子
        self.highlight_color = QColor(255, 165, 0)  # 高亮颜色(橙色)
        self.hover_index = -1  # 当前悬停的柱子索引
        self.found_index = -1  # 找到的非零值索引
        self.mouse_pos = None  # 鼠标当前位置
        self.min_bar_width = 3  # 最小柱宽
        self.setMinimumSize(1200, 600)  # 增大最小尺寸
        self.label_spacing = 100  # 增大标签间隔
        self.margin = 100  # 增大边距到100
        self.offset = 0  # 水平滚动偏移

    def set_data(self, data):
        """设置图表数据"""
        if not data:
            self.data = []
            self.max_value = 1
            self.update()
            return            
            
        self.data = sorted(data.items())  # 转换为[(frame, value), ...]并排序
        self.max_value = max((v for _, v in self.data), default=1)
        self.update()

    def mousePressEvent(self, event):
        """处理鼠标点击事件，检测点击的柱子"""
        if not self.data or event.button() != Qt.LeftButton:
            return
            
        # 保存鼠标位置
        self.mouse_pos = event.position()
        self.found_index = -1  # 重置找到的索引
        
        # 计算鼠标位置对应的柱子索引
        mouse_x = event.position().x()
        total_points = len(self.data)
        chart_width = max(self.width(), len(self.data)*self.min_bar_width)
        bar_width = max(self.min_bar_width, chart_width / total_points)
        
        # 计算鼠标位置对应的数据索引
        index = int((mouse_x - self.margin + self.offset) / bar_width)
        index = max(0, min(len(self.data)-1, index))
        
        # 更新点击索引并刷新
        self.hover_index = index
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), Qt.white)

        if not self.data:
            return
            
        # 根据绘制范围过滤数据
        filtered_data = self.data

        # 计算布局参数
        chart_width = max(self.width()-2*self.margin, len(filtered_data)*self.min_bar_width)
        chart_height = self.height() - 2*self.margin
        total_points = len(filtered_data)
        bar_width = max(self.min_bar_width, chart_width / total_points)
        
        # 绘制Y轴
        painter.setPen(Qt.black)
        painter.drawLine(self.margin, self.margin, self.margin, self.height()-self.margin)

        # 绘制X轴基线 (确保不超出Y轴)
        x_start = max(self.margin, self.margin - self.offset)
        x_end = self.width() - self.margin  # 窗口最右边-100
        painter.drawLine(
            x_start, 
            self.height()-self.margin,
            x_end,
            self.height()-self.margin
        )

        # 预计算标签位置
        font = QFont("Arial", 8)
        painter.setFont(font)
        fm = QFontMetrics(font)
        last_label_x = -float('inf')
        visible_labels = []

        # 绘制所有柱子
        for index, (frame, value) in enumerate(filtered_data):
            x = self.margin + index * bar_width - self.offset
            bar_height = (value / self.max_value) * chart_height
            y = self.height() - self.margin - bar_height
            if x<x_start or x>x_end:
                continue
            # 绘制柱子(高亮或普通)
            if index == self.hover_index or index == self.found_index:
                painter.setBrush(self.highlight_color)
                # 绘制高亮柱子
                painter.drawRect(x, y, bar_width, bar_height)
            else:
                painter.setBrush(self.bar_color)
                painter.drawRect(x, y, bar_width, bar_height)

            # 计算标签位置
            text = f"帧:{frame}"
            text_width = fm.horizontalAdvance(text)
            
            # 标签碰撞检测
            if x - last_label_x >= self.label_spacing:
                visible_labels.append((x, text))
                last_label_x = x + text_width

        # 绘制可见标签
        for x, text in visible_labels:
            text_rect = QRectF(
                x - bar_width/2, 
                self.height() - self.margin + 5,
                text_width + 10,
                fm.height()
            )
            painter.drawText(text_rect, Qt.AlignCenter, text)

        # 绘制Y轴刻度
        for i in range(0, 11):
            y_pos = self.height() - self.margin - (i/10)*chart_height
            label = f"{self.max_value * i/10:.1f}"
            painter.drawText(QRectF(10, y_pos-10, self.margin-15, 20),
                            Qt.AlignRight|Qt.AlignVCenter, label)

        # 在点击位置显示数值(不显示0值)
        if self.hover_index >= 0 and self.mouse_pos and self.hover_index < len(self.data):
            # 计算5%数据范围作为搜索半径
            search_radius = max(1, int(len(self.data) * 0.05))
            
            # 查找最近的非零值(前后5%范围内)
            display_index = self.hover_index
            if self.data[display_index][1] == 0:
                # 向前查找最近的
                prev_found = None
                prev_dist = float('inf')
                for i in range(1, search_radius + 1):
                    prev_index = display_index - i
                    if prev_index >= 0 and self.data[prev_index][1] != 0:
                        if i < prev_dist:
                            prev_found = prev_index
                            prev_dist = i
                
                # 向后查找最近的
                next_found = None
                next_dist = float('inf')
                for i in range(1, search_radius + 1):
                    next_index = display_index + i
                    if next_index < len(self.data) and self.data[next_index][1] != 0:
                        if i < next_dist:
                            next_found = next_index
                            next_dist = i
                
                # 选择距离更近的
                if prev_found is not None and next_found is not None:
                    display_index = prev_found if prev_dist <= next_dist else next_found
                elif prev_found is not None:
                    display_index = prev_found
                elif next_found is not None:
                    display_index = next_found
            
            if self.data[display_index][1] != 0:
                self.found_index = display_index
                self.update()  # 立即刷新高亮
                frame, value = self.data[display_index]
                value_text = f"{value:.1f}"
                text_width = fm.horizontalAdvance(value_text)
                
            # 计算柱子高度
            chart_height = self.height() - 2*self.margin
            bar_height = (value / self.max_value) * chart_height
            bar_top = self.height() - self.margin - bar_height
            
            # 确定显示位置
            if bar_top > self.mouse_pos.y():
                # 柱子高于鼠标位置，在鼠标高度显示
                y_pos = self.mouse_pos.y()
            else:
                # 柱子低于鼠标位置，在柱子位置显示
                y_pos = bar_top + bar_height/2
            
            # 在右侧显示数值
            text_rect = QRectF(
                self.margin + self.found_index * bar_width - self.offset + bar_width/2,
                y_pos - fm.height()/2,
                text_width + 20,
                fm.height()
            )
            # 绘制背景框
            painter.setBrush(QColor(255, 255, 255, 200))  # 半透明白色背景
            painter.setPen(Qt.NoPen)
            painter.drawRect(text_rect)
            # 绘制文本
            painter.setPen(Qt.black)
            painter.drawText(text_rect, Qt.AlignCenter, value_text)

    def wheelEvent(self, event):
        """基于鼠标位置的滚轮缩放"""
        if not self.data:
            return
            
        # 获取鼠标位置
        mouse_x = event.position().x()
        
        # 计算当前鼠标位置对应的数据索引
        visible_width = self.width() - 2 * self.margin
        
        # 计算鼠标位置对应的数据点
        data_pos = (mouse_x - self.margin + self.offset) / self.min_bar_width
        data_pos = max(0, min(len(self.data)-1, int(data_pos)))
        
        # 计算缩放因子
        zoom_factor = 1.25 if event.angleDelta().y() > 0 else 0.8
        new_min_width = max(1, min(50, self.min_bar_width * zoom_factor))
        
        # 计算缩放后保持鼠标位置不变所需的偏移量
        new_width = len(self.data) * new_min_width
        mouse_data_pos = (mouse_x - self.margin + self.offset) / self.min_bar_width
        
        # 计算新的offset使鼠标位置保持在同一数据点
        self.offset = mouse_data_pos * new_min_width - (mouse_x - self.margin)
        
        # 限制offset范围，优先保证鼠标中心缩放
        max_offset = max(0, new_width - visible_width)
        self.offset = max(0, min(max_offset, self.offset))
        
        # 仅在绝对必要时才修正边界
        if self.offset > 0 and (mouse_x - self.margin + self.offset) < self.margin:
            self.offset = max(0, mouse_x - self.margin)
        
        # 应用缩放
        self.min_bar_width = new_min_width
        self.update()

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
