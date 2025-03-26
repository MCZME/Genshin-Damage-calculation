from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
                              QLabel, QPushButton, QComboBox, QFrame, QScrollArea)
from PySide6.QtCore import Qt
from .styles import MODERN_STYLE
from .components import ActionCard
from .result_window import ResultWindow

class MainWindow(QMainWindow):
    """主窗口类"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("原神伤害计算器")
        self.setMinimumSize(1000, 600)
        
        # 创建中央部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)  # 取消间距，用stretch控制
        main_layout.setContentsMargins(20, 10, 20, 20)  # 增加底部边距
        central_widget.setLayout(main_layout)
        
        self.setStyleSheet(MODERN_STYLE)
        
        # 标题区域 (1/10)
        title = QLabel("原神伤害计算器")
        title.setAlignment(Qt.AlignCenter)
        title.setProperty("class", "title-area")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            margin: 0;
            padding: 0;
        """)
        main_layout.addWidget(title, stretch=1)  # 标题占1份
        
        spacer1 = QWidget()
        main_layout.addWidget(spacer1, stretch=1)
        
        # 队伍配置区域 (3/10)
        team_frame = QFrame()
        team_frame.setFrameShape(QFrame.StyledPanel)
        team_frame.setStyleSheet("""
            border: 1px solid #d1d5db;
            border-radius: 6px;
            background-color: white;
        """)
        team_layout = QVBoxLayout()
        team_layout.setAlignment(Qt.AlignCenter)
        team_layout.setContentsMargins(10, 10, 10, 10)
        
        team_label = QLabel("队伍配置")
        team_label.setAlignment(Qt.AlignCenter)
        team_label.setStyleSheet("""
            border: 0px;
            border-radius: 6px;
            background-color: white;
        """)
        team_layout.addWidget(team_label)
        
        # 4个角色槽
        char_slots = QHBoxLayout()
        char_slots.setSpacing(20)  # 增加角色间距
        for i in range(4):
            slot = QLabel(f"角色{i+1}")
            slot.setFixedSize(200, 100)  # 进一步扩宽角色方形
            slot.setStyleSheet("border: 2px dashed #aaa;")
            slot.setAlignment(Qt.AlignCenter)
            char_slots.addWidget(slot)
        team_layout.addLayout(char_slots)
        
        team_frame.setLayout(team_layout)
        main_layout.addWidget(team_frame, stretch=3)
        
        # 添加间隙
        spacer = QWidget()
        main_layout.addWidget(spacer, stretch=1)
        
        # 动作序列区域 (5/10)
        action_frame = QFrame()
        action_frame.setFrameShape(QFrame.StyledPanel)
        action_frame.setStyleSheet("""
            border-radius: 6px;
            background-color: white;
        """)
        action_layout = QVBoxLayout()
        action_layout.setContentsMargins(10, 10, 10, 10)
        action_layout.setSpacing(0)
        
        # 动作序列标题区域 (1/5高度)
        title_widget = QWidget()
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        action_label = QLabel("   动作序列")
        action_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_layout.addWidget(action_label)
        title_layout.addStretch()
        
        action_layout.addWidget(title_widget)
        
        # 动作序列内容区域 (4/5高度)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            border: 1px solid #d1d5db;
            border-radius: 6px;
            background-color: white;
        """)
        
        # 动作卡片容器 - 横向布局
        self.action_container = QWidget()
        self.action_container_layout = QHBoxLayout(self.action_container)
        self.action_container_layout.setSpacing(10)  # 减少卡片间距
        self.action_container_layout.setContentsMargins(10, 10, 10, 10)
        self.action_container_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        
        # 初始提示容器 (与卡片大小相同)
        self.hint_container = QWidget()
        self.hint_container.setFixedSize(160, 140)
        hint_layout = QVBoxLayout(self.hint_container)
        hint_label = QLabel("点击添加按钮\n创建动作序列")
        hint_label.setAlignment(Qt.AlignCenter)
        hint_label.setStyleSheet("""
            font-size: 14px; 
            color: #666;
            margin: 0;
            padding: 0;
        """)
        hint_layout.addWidget(hint_label)
        hint_layout.addStretch()
        self.hint_container.setVisible(True)
        
        self.action_container_layout.addWidget(self.hint_container)
        
        # 添加动作按钮 (与卡片大小相同)
        self.add_btn = QPushButton("+")
        self.add_btn.setFixedSize(160, 140)
        self.add_btn.clicked.connect(self._add_action_card)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border-radius: 4px;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        self.action_container_layout.addWidget(self.add_btn)
        
        scroll_area.setWidget(self.action_container)
        action_layout.addWidget(scroll_area)
        
        action_frame.setLayout(action_layout)
        main_layout.addWidget(action_frame, stretch=5)  # 动作序列占5/10
        
        spacer1 = QWidget()
        main_layout.addWidget(spacer1, stretch=1)

        # 按钮区域 (1/10)
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setSpacing(20)
        
        save_btn = QPushButton("保存")
        save_btn.setFixedWidth(60)
        calc_btn = QPushButton("开始计算") 
        calc_btn.setFixedWidth(120)
        calc_btn.clicked.connect(self._start_calculation)
        reset_btn = QPushButton("重置")
        reset_btn.setFixedWidth(60)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(calc_btn)
        button_layout.addWidget(reset_btn)
        
        main_layout.addWidget(button_widget, stretch=1)  # 按钮占1份
        
    def add_widget(self, widget):
        """添加部件到主布局"""
        self.centralWidget().layout().addWidget(widget)
        
    def _start_calculation(self):
        """开始计算按钮点击处理"""
        self.result_window = ResultWindow()
        self.result_window.show()
        self.close()

    def _add_action_card(self):
        """添加动作卡片"""
        print("_add_action_card被调用")  # 调试用
        try:
            # 隐藏初始提示
            if hasattr(self, 'hint_container') and self.hint_container:
                self.hint_container.setVisible(False)
            
            card = ActionCard(self)
            # 在添加按钮之前插入新卡片
            insert_pos = max(0, self.action_container_layout.count()-1)
            self.action_container_layout.insertWidget(insert_pos, card)
            
            # 确保滚动到最右侧
            scroll_area = self.findChild(QScrollArea)
            if scroll_area:
                scroll_bar = scroll_area.horizontalScrollBar()
                # 使用定时器确保在布局更新后执行滚动
                from PySide6.QtCore import QTimer
                QTimer.singleShot(100, lambda: scroll_bar.setValue(scroll_bar.maximum()))
            print("动作卡片添加成功")  # 调试用
        except Exception as e:
            print(f"添加卡片出错: {str(e)}")  # 调试用
