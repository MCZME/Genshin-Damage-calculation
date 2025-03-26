from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QLabel, 
                              QPushButton, QHBoxLayout, QFrame, QScrollArea,
                              QSizePolicy)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtCharts import QChart, QChartView,  QLineSeries, QValueAxis
from PySide6.QtGui import QPainter
import numpy as np

from setup.DataHandler import get_next_frame
from test import test_a

        # 角色槽位类
class CharacterSlot(QWidget):
    def __init__(self, char_id):
        super().__init__()
        self.setStyleSheet("""
            border: 1px solid #d1d5db;
            border-radius: 6px;
            padding: 8px;
        """)
        self.info_widgets = []
        
        # 初始化布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # 头像区域
        self.avatar_container = QWidget()
        self.avatar_container.setFixedSize(80, 80)
        avatar_layout = QVBoxLayout(self.avatar_container)
        avatar_layout.setContentsMargins(0, 0, 0, 0)
        
        # 折叠按钮
        self.toggle_btn = QPushButton("▶")
        self.toggle_btn.setFixedSize(20, 20)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: rgba(240, 240, 240, 0.7);
                font-size: 12px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: rgba(224, 224, 224, 0.9);
            }
        """)
        avatar_layout.addWidget(self.toggle_btn, 0, Qt.AlignTop | Qt.AlignRight)
        
        # 头像
        self.avatar = QLabel()
        self.avatar.setFixedSize(80, 80)
        self.avatar.setStyleSheet("""
            background-color: #f0f0f0;
            border-radius: 4px;
        """)
        avatar_layout.addWidget(self.avatar)
        
        layout.addWidget(self.avatar_container)
        
        # 信息区域
        self.info_layout = QVBoxLayout()
        self.info_layout.setSpacing(4)
        
        self.char_name = QLabel(f"角色 {char_id}")
        self.char_name.setStyleSheet("font-weight: bold;")
        self.info_widgets.append(self.char_name)
        
        self.char_level = QLabel("Lv.90")
        self.char_level.setStyleSheet("color: #666;")
        self.info_widgets.append(self.char_level)
        
        self.char_hp = QLabel("HP: 20000/20000")
        self.char_hp.setStyleSheet("color: #666;")
        self.info_widgets.append(self.char_hp)
        
        self.info_layout.addWidget(self.char_name)
        self.info_layout.addWidget(self.char_level)
        self.info_layout.addWidget(self.char_hp)
        self.info_layout.addStretch()
        
        layout.addLayout(self.info_layout, stretch=1)
        
    def toggle_visibility(self, expanded):
        """切换显示状态"""
        for widget in self.info_widgets:
            widget.setVisible(expanded)
        self.toggle_btn.setText("◀" if expanded else "▶")


class ResultWindow(QMainWindow):
    """结果窗口类"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("计算结果")
        self.setMinimumSize(1000, 600)
        
        # 创建中央部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局 - 水平分左右两部分
        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)
        central_widget.setLayout(self.main_layout)
        
        # 可折叠的左侧角色栏
        self.sidebar = QFrame()
        self.sidebar.setFrameShape(QFrame.StyledPanel)
        self.sidebar.setStyleSheet("""
            border: 1px solid #d1d5db;
            border-radius: 6px;
            background-color: white;
        """)
        self.sidebar.setMinimumWidth(300)
        self.sidebar.setMaximumWidth(400)
        
        # 侧边栏布局
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        
        # 角色内容区域
        self.sidebar_content = QWidget()
        self.sidebar_content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        content_layout = QVBoxLayout(self.sidebar_content)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # 角色栏标题
        char_title = QLabel("角色信息")
        char_title.setAlignment(Qt.AlignCenter)
        char_title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 10px;
        """)
        content_layout.addWidget(char_title)
        
        # 角色列表容器
        char_scroll = QScrollArea()
        char_scroll.setWidgetResizable(True)
        char_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        char_scroll.setStyleSheet("border: none;")
        
        char_container = QWidget()
        self.char_container_layout = QVBoxLayout(char_container)
        self.char_container_layout.setSpacing(10)
        self.char_container_layout.setContentsMargins(0, 0, 0, 0)
        self.char_container_layout.setAlignment(Qt.AlignTop)
        

        # 添加4个角色槽位
        for i in range(1, 5):
            char_slot = CharacterSlot(i)
            char_slot.toggle_btn.clicked.connect(self.toggle_sidebar)
            self.char_container_layout.addWidget(char_slot)
        
        char_scroll.setWidget(char_container)
        content_layout.addWidget(char_scroll)
        
        sidebar_layout.addWidget(self.sidebar_content)
        
        # 侧边栏动画
        self.sidebar_animation = QPropertyAnimation(self.sidebar, b"minimumWidth")
        self.sidebar_animation.setDuration(300)
        self.sidebar_animation.setEasingCurve(QEasingCurve.InOutQuad)
        # 确保动画目标属性可动画化
        self.sidebar.setProperty("minimumWidth", 100)
        
        # 初始状态为折叠
        self.sidebar_expanded = False
        self.sidebar.setMinimumWidth(100)
        self.main_layout.addWidget(self.sidebar, stretch=1)  # 初始比例1:4
        
        # 右侧结果区域
        self.result_frame = QFrame()
        self.result_frame.setFrameShape(QFrame.StyledPanel)
        self.result_frame.setStyleSheet("""
            border: 1px solid #d1d5db;
            border-radius: 6px;
            background-color: white;
        """)
        result_layout = QVBoxLayout(self.result_frame)
        result_layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建图表视图
        chart_view = self.create_damage_chart()
        result_layout.addWidget(chart_view, stretch=4)

        # 添加关闭按钮
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.setFixedWidth(120)
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        button_layout.addStretch()
        result_layout.addWidget(button_widget, stretch=0)
        
        # 将结果框架添加到主布局
        self.main_layout.addWidget(self.result_frame, stretch=4)  # 初始比例1:4
        
        # 初始折叠样式
        self.sidebar_content.setStyleSheet("""
            CharacterSlot { min-width: 80px; max-width: 80px; }
        """)
        # 初始隐藏所有角色信息
        for i in range(self.char_container_layout.count()):
            widget = self.char_container_layout.itemAt(i).widget()
            if isinstance(widget, CharacterSlot):
                widget.toggle_visibility(False)

        # 添加定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_chart)
        self.timer.start(100)  # 1秒更新一次
        
        # 初始化数据存储
        self.time_counter = 0
        self.max_points = 800  # 显示最近20个数据点
        
    def create_damage_chart(self):
        """创建实时折线图"""
        chart = QChart()
        chart.setTitle("实时伤害趋势")
        chart.setAnimationOptions(QChart.NoAnimation)  # 禁用动画提升性能
        
        # 创建系列
        self.series_attack = QLineSeries()
        
        self.series_attack.setName("普通攻击")

        
        # 添加到图表
        chart.addSeries(self.series_attack)
        
        # 坐标轴
        self.axisX = QValueAxis()
        self.axisX.setTitleText("时间")
        self.axisX.setRange(0, 600)
        
        self.axisY = QValueAxis()
        self.axisY.setTitleText("伤害值")
        self.axisY.setRange(0, 10000)
        
        chart.addAxis(self.axisX, Qt.AlignBottom)
        chart.addAxis(self.axisY, Qt.AlignLeft)
        
        # 绑定坐标轴
        for series in [self.series_attack]:
            series.attachAxis(self.axisX)
            series.attachAxis(self.axisY)
        
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        test_a()
        return chart_view
    
    def update_chart(self):
        """定时更新图表数据"""
        # 生成随机数据（示例）
        new_attack = get_next_frame()
        
        # 更新X轴范围实现滚动效果
        self.time_counter += 1
        if self.time_counter > self.max_points:
            self.axisX.setRange(self.time_counter - self.max_points, self.time_counter)
        
        # 添加新数据点
        self.series_attack.append(self.time_counter, new_attack)
        
        # 删除旧数据保持性能
        if self.series_attack.count() > self.max_points:
            self.series_attack.remove(0)
        
    def toggle_sidebar(self):
        """切换侧边栏展开/折叠状态"""
        # 先停止当前动画
        self.sidebar_animation.stop()
        # 断开之前的信号
        try:
            self.sidebar_animation.finished.disconnect()
        except:
            pass
            
        self.sidebar_expanded = not self.sidebar_expanded
        
        if self.sidebar_expanded:
            self.sidebar_animation.setStartValue(self.sidebar.width())
            self.sidebar_animation.setEndValue(300)
            # 立即显示内容
            self.sidebar_content.setVisible(True)
            self.sidebar_content.setStyleSheet("")
            # 显示所有角色信息
            for i in range(self.char_container_layout.count()):
                widget = self.char_container_layout.itemAt(i).widget()
                if isinstance(widget, CharacterSlot):
                    widget.toggle_visibility(True)
        else:
            self.sidebar_animation.setStartValue(self.sidebar.width())
            self.sidebar_animation.setEndValue(100)
            # 隐藏所有角色信息（保留头像）
            for i in range(self.char_container_layout.count()):
                widget = self.char_container_layout.itemAt(i).widget()
                if isinstance(widget, CharacterSlot):
                    widget.toggle_visibility(False)
            
        # 连接动画完成信号
        self.sidebar_animation.finished.connect(self.on_animation_finished)
        # 强制更新布局
        self.sidebar.updateGeometry()
        # 启动动画
        self.sidebar_animation.start()
            
    def on_animation_finished(self):
        """动画完成后调整布局比例"""
        if self.sidebar_expanded:
            self.main_layout.setStretch(0, 3)  # 侧边栏
            self.main_layout.setStretch(1, 2)  # 结果区域
        else:
            self.main_layout.setStretch(0, 1)  # 折叠侧边栏
            self.main_layout.setStretch(1, 4)  # 扩展结果区域
            # 折叠状态下只显示角色头像
            self.sidebar_content.setStyleSheet("""

                CharacterSlot { min-width: 80px; max-width: 80px; }
            """)
            # 更新所有角色槽位的显示状态
            for i in range(self.char_container_layout.count()):
                widget = self.char_container_layout.itemAt(i).widget()
                if isinstance(widget, CharacterSlot):
                    widget.toggle_visibility(self.sidebar_expanded)
