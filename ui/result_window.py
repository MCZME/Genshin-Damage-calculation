from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QLabel,
                              QPushButton, QHBoxLayout, QSizePolicy, QScrollArea, QLineEdit)

from ui.widget.character_status_card import CharacterCardManager
from ui.widget.vertical_label_chart import VerticalLabelChart
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QIcon

from setup.DataHandler import send_to_window
class CharacterStatusWidget(QWidget):
    """角色状态显示组件"""
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
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
        # 主布局：左右独立布局
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(10, 0, 10, 10)
        self.main_layout.setSpacing(10)
        
        # 左侧角色头像区域 - 固定宽度和高度
        self.avatar_area = QWidget()
        self.avatar_area.setFixedWidth(80)  # 固定宽度
        self.avatar_area.setFixedHeight(270)  # 固定高度
        self.avatar_area.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.avatar_layout = QVBoxLayout(self.avatar_area)
        self.avatar_layout.setSpacing(10)
        self.avatar_layout.setAlignment(Qt.AlignTop)  # 内容顶部对齐
        self.main_layout.addWidget(self.avatar_area, 0, Qt.AlignTop)  # 固定在顶部
        
        # 右侧状态卡片区域
        self.card_area = QWidget()
        self.card_area.setMinimumHeight(270)  # 设置与左侧相同的高度
        self.card_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 宽度扩展，高度固定
        card_area_layout = QVBoxLayout(self.card_area)
        card_area_layout.setContentsMargins(10, 0, 10, 0)
        card_area_layout.setSpacing(12)  # 卡片间距12px
        card_area_layout.setAlignment(Qt.AlignTop)
        self.main_layout.addWidget(self.card_area, 1)  # 使用伸缩因子1让卡片区域占据剩余空间
        
        # 初始化卡片管理器
        self.card_manager = CharacterCardManager(self.card_area)
        
        # 初始化4个角色头像占位
        self.avatars = []
        self.avatar_click_handlers = []
        for i in range(4):
            avatar = QPushButton()
            avatar.setCursor(Qt.PointingHandCursor)
            avatar.setFixedSize(60, 60)
            avatar.setStyleSheet("""
                QPushButton {
                    border: 2px solid #4a90e2;
                    border-radius: 30px;
                    background-color: #ffffff;
                    padding: 0px;
                }
                QPushButton:hover {
                    border: 2px solid #2a70c2;
                    background-color: #f0f7ff;
                }
            """)
            avatar.setVisible(False)
            self.avatar_layout.addWidget(avatar, stretch=1)
            self.avatars.append(avatar)
        self.set_data()

    def set_data(self):
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
        if not self.data:
            return
            
        # 获取第一帧数据作为初始显示
        first_frame = self.data[1]
        
        # 获取角色名称列表
        character_names = list(first_frame.keys())
        
        # 清除旧的点击处理器
        for handler in self.avatar_click_handlers:
            try:
                handler.disconnect()
            except:
                pass
        self.avatar_click_handlers = []
        
        # 更新角色头像
        for i in range(min(4, len(character_names))):
            char_name = character_names[i]
            char_data = first_frame[char_name]
            # 添加角色名称到数据中
            char_data['name'] = char_name
            
            # 设置头像
            if 'avatar' in char_data:
                pixmap = QPixmap(char_data['avatar'])
                icon = QIcon(pixmap.scaled(50, 50, Qt.KeepAspectRatio))
                self.avatars[i].setIcon(icon)
                self.avatars[i].setIconSize(QSize(50, 50))
            self.avatars[i].setVisible(True)
            
            # 设置点击事件
            handler = lambda checked, name=char_name: \
                self.card_manager.toggle_card(name)
            self.avatars[i].clicked.connect(handler)
            self.avatar_click_handlers.append(handler)
            
        # 初始化所有卡片
        self.card_manager.initialize_cards(first_frame)

    def update_frame(self, frame):
        """更新到指定帧的数据"""
        # 获取完整角色数据
        frame_data = self.data.get(frame, {})
        
        # 更新头像状态
        for char_name in frame_data:
            if 'elemental_energy' in frame_data[char_name]:
                self._update_avatar_border(char_name, frame_data[char_name])
        
        # 更新卡片数据
        self.card_manager.update_cards(frame_data)

    def _update_avatar_border(self, char_name, data):
        """根据元素能量更新头像边框"""
        element = data['elemental_energy'].get('element', '')
        color = self._get_element_color(element)
        for avatar in self.avatars:
            if avatar.property('char_name') == char_name:
                avatar.setStyleSheet(f"""
                    border: 2px solid {color};
                    border-radius: 30px;
                    background-color: #ffffff;
                """)

    def _get_element_color(self, element):
        """获取元素对应颜色"""
        colors = {
            '火': '#FF6666',
            '水': '#66B3FF',
            '雷': '#D966FF',
            # ...其他元素颜色
        }
        return colors.get(element, '#4a90e2')

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
        self.chart.setMinimumSize(400, 300)
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
