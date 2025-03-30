from PySide6.QtWidgets import (QWidget)
from PySide6.QtCore import (Qt, QRectF)
from PySide6.QtGui import (QColor, QPainter, QFont, QFontMetrics)

class VerticalLabelChart(QWidget):
    def __init__(self):
        super().__init__()
        self.data = []  # [(frame, value), ...]
        # 滑动条相关属性
        self.left_slider_pos = 0
        self.right_slider_pos = 0 
        self.middle_slider_pos = 0
        self.dragging_left = False
        self.dragging_right = False
        self.dragging_middle = False
        self.slider_height = 30
        self.slider_handle_width = 15
        self.slider_handle_height = 20
        self.slider_color = QColor(100, 149, 237)  # 现代化蓝色
        self.slider_handle_color = QColor(70, 130, 180)  # 深蓝色手柄
        self.max_value = 1
        self.bar_color = QColor(255, 0, 0)  # 红色柱子
        self.highlight_color = QColor(255, 165, 0)  # 高亮颜色(橙色)
        self.hover_index = -1  # 当前悬停的柱子索引
        self.found_index = -1  # 找到的非零值索引
        self.mouse_pos = None  # 鼠标当前位置
        self.bar_width = 3
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
        # 根据数据长度设置滑块范围
        self.left_slider_pos = 0
        self.right_slider_pos = len(self.data) - 1
        self.middle_slider_pos = len(self.data) // 2
        self.update()

    def mousePressEvent(self, event):
        """处理鼠标点击事件，检测点击的柱子或滑块"""
        if not self.data or event.button() != Qt.LeftButton:
            return
            
        # 保存鼠标位置
        self.mouse_pos = event.position()
        self.found_index = -1  # 重置找到的索引
        
        # 检查是否点击了滑块
        slider_y = self.height() - self.margin - 10
        slider_width = self.width() - 2 * self.margin
        data_range = max(1, len(self.data) - 1)
        
        # 计算各滑块位置
        left_pos = self.margin + (self.left_slider_pos / data_range) * slider_width
        right_pos = self.margin + (self.right_slider_pos / data_range) * slider_width
        middle_pos = self.margin + (self.middle_slider_pos / data_range) * slider_width
        
        # 检查点击位置是否在滑块手柄上
        mouse_x = event.position().x()
        mouse_y = event.position().y()
        
        # 检查左滑块
        if (abs(mouse_x - left_pos) < self.slider_handle_width and 
            slider_y - 5 <= mouse_y <= slider_y + self.slider_handle_height):
            self.dragging_left = True
            return
            
        # 检查右滑块
        if (abs(mouse_x - right_pos) < self.slider_handle_width and 
            slider_y - 5 <= mouse_y <= slider_y + self.slider_handle_height):
            self.dragging_right = True
            return
            
        # 检查中间滑块
        if (abs(mouse_x - middle_pos) < self.slider_handle_width and 
            slider_y - 10 <= mouse_y <= slider_y + self.slider_handle_height + 5):
            self.dragging_middle = True
            return
            
        # 只在x轴上方区域点击时检测柱子
        chart_bottom = self.height() - self.margin - self.slider_height - 30
        if mouse_y > chart_bottom:
            return
            
        # 计算鼠标位置对应的数据索引(考虑滑块范围)
        visible_points = self.right_slider_pos - self.left_slider_pos + 1
        chart_width = self.width() - 2 * self.margin
        
        # 计算实际显示的柱子宽度
        bar_width = chart_width / visible_points
        
        # 计算鼠标位置对应的全局数据索引(考虑offset)
        global_index = int((mouse_x - self.margin + self.offset) / bar_width) + self.left_slider_pos
        index = max(0, min(len(self.data)-1, global_index))
        
        # 更新点击索引并刷新
        self.hover_index = int(index)
        self.found_index = -1  # 重置找到的索引
        # 更新中间滑块位置到当前高亮柱子
        self.middle_slider_pos = max(self.left_slider_pos, min(self.right_slider_pos, self.hover_index))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), Qt.white)

        if not self.data:
            painter.end()
            return
            
        # 根据滑块范围过滤数据(基于数据索引)
        if not self.data:
            filtered_data = []
        else:
            start_idx = int(self.left_slider_pos)
            end_idx = int(self.right_slider_pos)
            filtered_data = self.data[start_idx:end_idx+1]

        # 计算布局参数
        chart_width = self.width()-2*self.margin
        chart_height = self.height() - 2*self.margin - self.slider_height - 20  # 为滑动条留出空间
        total_points = len(filtered_data)
        bar_width = chart_width / total_points
        self.bar_width = bar_width
        
        # 绘制Y轴
        painter.setPen(Qt.black)
        painter.drawLine(self.margin, self.margin, self.margin, self.height()-self.margin-self.slider_height-20)

        # 绘制X轴基线 (确保不超出Y轴)
        x_start = max(self.margin, self.margin - self.offset)
        x_end = self.width() - self.margin  # 窗口最右边-100
        painter.drawLine(
            x_start, 
            self.height()-self.margin-self.slider_height-20,
            x_end,
            self.height()-self.margin-self.slider_height-20
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
            y = self.height() - self.margin - self.slider_height - 20 - bar_height
            if x<x_start or x>x_end:
                continue
            # 绘制柱子(高亮或普通)
            if int(index + self.left_slider_pos) == self.hover_index or int(index + self.left_slider_pos) == self.found_index:
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
                self.height() - self.margin - self.slider_height - 20 + 5,
                text_width + 10,
                fm.height()
            )
            painter.drawText(text_rect, Qt.AlignCenter, text)

        # 绘制Y轴刻度
        for i in range(0, 11):
            y_pos = self.height() - self.margin - self.slider_height - 20 - (i/10)*chart_height
            label = f"{self.max_value * i/10:.1f}"
            painter.drawText(QRectF(10, y_pos-10, self.margin-15, 20),
                            Qt.AlignRight|Qt.AlignVCenter, label)

        # 在点击位置显示数值(不显示0值)
        if self.hover_index >= 0 and self.mouse_pos and self.hover_index < len(self.data):
            # 计算5%数据范围作为搜索半径
            search_radius = max(1, int(len(self.data) * 0.05))
            
            # 查找最近的非零值(前后5%范围内)
            display_index = self.hover_index
            frame, value = self.data[display_index]
            if value == 0:
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
            
            frame, value = self.data[display_index]
            if value != 0:
                self.found_index = display_index
                value_text = f"{value:.1f}"
                text_width = fm.horizontalAdvance(value_text)
                self.update()
                # 计算柱子高度
                bar_height = (value / self.max_value) * chart_height
                bar_top = self.height() - self.margin - self.slider_height - 20 - bar_height
                
                # 确定显示位置
                if bar_top > self.mouse_pos.y():
                    # 柱子高于鼠标位置，在鼠标高度显示
                    y_pos = self.mouse_pos.y()
                else:
                    # 柱子低于鼠标位置，在柱子位置显示
                    y_pos = bar_top + bar_height/2
                
                # 在右侧显示数值(考虑滑块范围和offset)
                local_index = self.found_index - self.left_slider_pos
                text_rect = QRectF(
                    self.margin + local_index * bar_width - self.offset + bar_width/2,
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

        # 绘制滑动条 (放在x轴下方)
        slider_y = self.height() - self.margin - 10
        slider_width = self.width() - 2 * self.margin
        
        # 绘制滑动条背景
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(220, 220, 220))  # 浅灰色背景
        painter.drawRoundedRect(
            self.margin, slider_y, 
            slider_width, self.slider_height, 
            5, 5
        )
        
        # 绘制滑动条轨道(基于数据索引)
        painter.setBrush(self.slider_color)
        data_range = max(1, len(self.data) - 1)
        left_pos = self.margin + (self.left_slider_pos / data_range) * slider_width
        right_pos = self.margin + (self.right_slider_pos / data_range) * slider_width
        painter.drawRoundedRect(
            left_pos, slider_y,
            right_pos - left_pos, self.slider_height,
            5, 5
        )
        
        # 绘制滑块手柄(基于数据索引)
        middle_pos = self.margin + (self.middle_slider_pos / data_range) * slider_width
        painter.setBrush(self.slider_handle_color)
        
        # 左滑块
        painter.drawRoundedRect(
            left_pos - self.slider_handle_width/2, slider_y - 5,
            self.slider_handle_width, self.slider_handle_height,
            3, 3
        )
        
        # 右滑块
        painter.drawRoundedRect(
            right_pos - self.slider_handle_width/2, slider_y - 5,
            self.slider_handle_width, self.slider_handle_height,
            3, 3
        )
        
        # 中间滑块
        painter.drawRoundedRect(
            middle_pos - self.slider_handle_width/2, slider_y - 10,
            self.slider_handle_width, self.slider_handle_height + 5,
            3, 3
        )

        painter.end()

    def wheelEvent(self, event):
        """基于鼠标位置的滚轮缩放"""
        if not self.data:
            return
            
        # 获取鼠标位置和滚轮角度
        mouse_x = event.position().x()
        angle = event.angleDelta().y()
        
        # 计算鼠标位置对应的数据索引(0-1范围)
        slider_width = self.width() - 2 * self.margin
        mouse_pos_ratio = (mouse_x - self.margin) / slider_width
        
        # 计算当前范围宽度和中心位置
        current_range = self.right_slider_pos - self.left_slider_pos
        center_pos = (self.left_slider_pos + self.right_slider_pos) / 2
        
        # 计算缩放因子(正向滚轮缩小范围，负向放大)
        zoom_factor = 1.1 if angle > 0 else 0.9
        
        # 计算新的范围宽度(限制最小/最大范围)
        new_range = max(10, min(len(self.data)-1, current_range * zoom_factor))
        
        # 计算新的左右滑块位置(基于鼠标位置为中心)
        new_left = center_pos - new_range * mouse_pos_ratio
        new_right = center_pos + new_range * (1 - mouse_pos_ratio)
        
        # 确保不超出数据范围
        if new_left < 0:
            new_right += -new_left
            new_left = 0
        if new_right > len(self.data)-1:
            new_left -= (new_right - (len(self.data)-1))
            new_right = len(self.data)-1
            
        # 更新滑块位置
        self.left_slider_pos = max(0, min(len(self.data)-1, new_left))
        self.right_slider_pos = max(0, min(len(self.data)-1, new_right))
        self.middle_slider_pos = (self.left_slider_pos + self.right_slider_pos) / 2
        
        # 更新水平滚动偏移，保持鼠标位置的数据点位置不变
        if current_range > 0:
            # 计算鼠标位置对应的数据索引
            mouse_data_pos = self.left_slider_pos + mouse_pos_ratio * current_range
            # 计算新的偏移量
            new_offset = (mouse_data_pos - new_left) * (self.width() - 2*self.margin) / new_range - (mouse_x - self.margin)
            self.offset = max(0, min(self.width() - 2*self.margin, new_offset))
        
        self.update()

    def mouseMoveEvent(self, event):
        """处理滑块拖动"""
        if not self.data:
            return
            
        slider_width = self.width() - 2 * self.margin
        data_range = max(1, len(self.data) - 1)
        
        # 处理左滑块拖动
        if self.dragging_left:
            new_pos = (event.position().x() - self.margin) / slider_width * data_range
            self.left_slider_pos = max(0, min(self.middle_slider_pos, new_pos))
            self.update()
            
        # 处理右滑块拖动
        elif self.dragging_right:
            new_pos = (event.position().x() - self.margin) / slider_width * data_range
            self.right_slider_pos = min(len(self.data)-1, max(self.middle_slider_pos, new_pos))
            self.update()
            
        # 处理中间滑块拖动
        elif self.dragging_middle:
            new_pos = (event.position().x() - self.margin) / slider_width * data_range
            self.middle_slider_pos = max(self.left_slider_pos, min(self.right_slider_pos, new_pos))
            self.update()

    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件"""
        self.dragging_left = False
        self.dragging_right = False
        self.dragging_middle = False
        self.update()
