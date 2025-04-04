from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QLabel,
                              QPushButton, QHBoxLayout, QSizePolicy, QScrollArea, QLineEdit)

from ui.widget.character_status_widget import CharacterStatusWidget
from ui.widget.vertical_label_chart import VerticalLabelChart

from setup.DataHandler import send_to_window

class ResultWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("战斗数据分析")
        self.resize(900, 700)  # 设置初始窗口大小
        
        # 主滚动区域
        self.main_widget = QScrollArea()
        self.main_widget.setWidgetResizable(True)
        self.main_widget.setStyleSheet("""
            QScrollArea {
                border: none;
                background: #f5f7fa;
            }
        """)
        
        # 主容器
        self.container = QWidget()
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        self.main_widget.setWidget(self.container)
        
        # 标题区域
        self.title_label = QLabel("战斗数据分析报告")
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #333333;
                padding-bottom: 10px;
                border-bottom: 2px solid #4a90e2;
            }
        """)
        self.main_layout.addWidget(self.title_label)
        
        # 图表区域
        self.chart_section = QWidget()
        self.chart_section.setStyleSheet("""
            QWidget {
                background: white;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        chart_layout = QVBoxLayout(self.chart_section)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        
        self.chart_title = QLabel("伤害数据统计")
        self.chart_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #333333;
                margin-bottom: 5px;
            }
        """)
        chart_layout.addWidget(self.chart_title)
        
        self.chart = VerticalLabelChart()
        self.chart.setMinimumSize(400, 400)
        self.chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.chart.set_data(send_to_window('damage'))
        self.chart.bar_clicked.connect(self.on_chart_bar_clicked)
        chart_layout.addWidget(self.chart)
        
        self.main_layout.addWidget(self.chart_section)
        
        # 角色状态区域
        self.character_section = QWidget()
        self.character_section.setStyleSheet("""
            QWidget {
                background: white;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        character_layout = QVBoxLayout(self.character_section)
        character_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建标题行布局
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 10)
        
        self.character_title = QLabel("角色状态分析")
        self.character_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #333333;
            }
        """)
        title_row.addWidget(self.character_title)
        
        # 添加输入框和按钮
        self.frame_input = QLineEdit()
        self.frame_input.setPlaceholderText("输入帧数")
        self.frame_input.setFixedWidth(100)
        self.frame_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 4px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #4a90e2;
            }
        """)
        title_row.addWidget(self.frame_input)
        
        self.frame_button = QPushButton("确定")
        self.frame_button.setFixedWidth(60)
        self.frame_button.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #3a80d2;
            }
            QPushButton:pressed {
                background-color: #2a70c2;
            }
        """)
        title_row.addWidget(self.frame_button)
        
        title_row.addStretch()
        character_layout.addLayout(title_row)
        
        self.character_status = CharacterStatusWidget(send_to_window('character'))
        self.character_status.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        character_layout.addWidget(self.character_status)
        
        self.main_layout.addWidget(self.character_section)
        self.main_layout.addStretch(1)
        
        # 连接按钮信号
        self.frame_button.clicked.connect(self.on_frame_button_clicked)
        
        self.setCentralWidget(self.main_widget)
        self.update_damage_chart()
    
    def on_frame_button_clicked(self):
        """处理帧数输入按钮点击事件"""
        try:
            frame = int(self.frame_input.text())
            self.update_character_frame(frame)
        except ValueError:
            print("请输入有效的帧数")
    

    def update_damage_chart(self):
        damage_data = send_to_window('damage')
        if not damage_data:
            return
        self.chart.set_data(damage_data)
            
    def on_chart_bar_clicked(self, frame):
        """处理图表柱子点击事件"""
        self.frame_input.setText(str(frame))
        self.update_character_frame(frame)

    def update_character_frame(self, frame):
        """更新当前帧的角色状态显示"""
        self.character_status.update_frame(frame)
