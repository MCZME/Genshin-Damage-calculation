from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QLabel,
                              QPushButton, QHBoxLayout, QStackedWidget, QStyle)
from .widget.character_status_dialog import CharacterStatusDialog
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from setup.DataHandler import generate_character_report, send_to_window

class CharacterStatusCard(QWidget):
    """单个角色状态卡片组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            background-color: #ffffff;
            border-radius: 0px;
            padding: 8px;
            border-top: 1px solid #e0e0e0;
            border-bottom: 1px solid #e0e0e0;
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(3, 8, 3, 8)
        self.layout.setSpacing(6)
        
        self.data = None
        self.settings_btn = QPushButton()
        self.settings_btn.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_FileDialogDetailedView')))
        self.settings_btn.setFixedSize(24, 24)
        self.settings_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
            }
            QPushButton:hover {
                background: rgba(0, 0, 0, 0.05);
            }
        """)

    def set_data(self, data):
        """设置角色数据"""
        self.data = data
        
        # 清空现有内容
        for i in reversed(range(self.layout.count())): 
            self.layout.itemAt(i).widget().setParent(None)
        
        # 第一行：角色信息 + 设置按钮
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(10)
        
        # 角色基本信息
        info_layout = QHBoxLayout()
        info_layout.setSpacing(10)
        
        if 'name' in data:
            name_label = QLabel(data['name'])
            name_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #333333;")
            info_layout.addWidget(name_label)
            
        if 'constellation' in data:
            const_label = QLabel(f"命座: {data['constellation']}")
            const_label.setStyleSheet("color: #4a90e2;")
            info_layout.addWidget(const_label)
            
        if 'level' in data:
            level_label = QLabel(f"等级: {data['level']}")
            level_label.setStyleSheet("color: #4a90e2;")
            info_layout.addWidget(level_label)
            
        if 'skill_params' in data:
            skills_label = QLabel(f"技能: {', '.join(map(str, data['skill_params']))}")
            skills_label.setStyleSheet("color: #4a90e2;")
            info_layout.addWidget(skills_label)
            
        top_row.addLayout(info_layout)
        top_row.addStretch()
        top_row.addWidget(self.settings_btn)
        
        self.layout.addLayout(top_row)
        
        # 设置按钮点击事件 - 显示详情弹窗
        def show_detail_dialog():
            dialog = CharacterStatusDialog(self)
            dialog.set_data(data)
            dialog.exec()
            
        self.settings_btn.clicked.connect(show_detail_dialog)

    def update_data(self, new_data):
        """更新角色数据"""
        if self.data:
            for i in range(self.layout.count()):
                widget = self.layout.itemAt(i).widget()
                if isinstance(widget, QLabel) and i % 2 == 1:
                    key = self.layout.itemAt(i-1).widget().text()[:-1]
                    widget.setText(str(new_data.get(key, '')))

class CharacterStatusWidget(QWidget):
    """角色状态显示组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f7fa;
                color: #333333;
                border-radius: 8px;
            }
            QLabel {
                font-size: 13px;
                padding: 4px;
                font-family: "Microsoft YaHei";
            }
        """)
        
        # 主布局：左右1:4比例
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(10)
        
        # 左侧角色头像区域 (1/5宽度)
        self.avatar_area = QWidget()
        self.avatar_layout = QVBoxLayout(self.avatar_area)
        self.avatar_layout.setSpacing(10)
        self.main_layout.addWidget(self.avatar_area, stretch=1)
        
        # 右侧状态卡片区域 (4/5宽度)
        self.card_stack = QStackedWidget()
        self.main_layout.addWidget(self.card_stack, stretch=4)
        
        # 初始化4个角色头像占位
        self.avatars = []
        for i in range(4):
            avatar = QLabel()
            avatar.setAlignment(Qt.AlignCenter)
            avatar.setFixedSize(60, 60)
            avatar.setStyleSheet("""
                border: 2px solid #4a90e2;
                border-radius: 30px;
                background-color: #ffffff;
            """)
            self.avatar_layout.addWidget(avatar)
            self.avatars.append(avatar)
        
        # 初始化4个状态卡片
        self.cards = []
        for i in range(4):
            card = CharacterStatusCard()
            self.card_stack.addWidget(card)
            self.cards.append(card)
        
        self.character_data = None

    def set_data(self, data):
        """设置角色状态数据
        data结构: {frame: {角色名称: 角色数据}}
        角色数据: {
            "level": int,
            "skill_params": list,
            "constellation": int,
            "panel": dict,
            "effect": dict,
            "elemental_energy": dict
        }
        """
        if not data:
            return
            
        # 获取第一帧数据作为初始显示
        first_frame = next(iter(data.values()))
        self.character_data = data
        
        # 获取角色名称列表
        character_names = list(first_frame.keys())
        
        # 更新角色头像和卡片
        for i in range(min(4, len(character_names))):
            char_name = character_names[i]
            char_data = first_frame[char_name]
            # 添加角色名称到数据中
            char_data['name'] = char_name
            # 设置头像
            if 'avatar' in char_data:
                pixmap = QPixmap(char_data['avatar'])
                self.avatars[i].setPixmap(pixmap.scaled(50, 50, Qt.KeepAspectRatio))
            
            # 设置卡片数据
            self.cards[i].set_data(char_data)
            
    def update_frame(self, frame):
        """更新当前帧的角色状态显示
        frame: 要显示的帧标识符
        """
        if self.character_data and frame in self.character_data:
            frame_data = self.character_data[frame]
            character_names = list(frame_data.keys())
            for i in range(min(4, len(character_names))):
                char_name = character_names[i]
                self.cards[i].update_data(frame_data[char_name])

class ResultWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 主布局
        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout(self.main_widget)
        
        # 角色状态显示区域
        self.character_status = CharacterStatusWidget()
        self.main_layout.addWidget(self.character_status)
        self.set_character_data()
        
        # 图表区域
        # self.chart = VerticalLabelChart()
        # self.main_layout.addWidget(self.chart)
        
        self.setCentralWidget(self.main_widget)
        # self.update_damage_chart()

    def update_damage_chart(self):
        damage_data = send_to_window('damage')
        if not damage_data:
            return
        self.chart.set_data(damage_data)
        
    def set_character_data(self):
        """设置角色状态数据"""
        data = generate_character_report()
        self.character_status.set_data(data)
            
    def update_character_frame(self, frame):
        """更新当前帧的角色状态显示"""
