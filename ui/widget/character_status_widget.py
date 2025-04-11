from PySide6.QtWidgets import (QVBoxLayout, QWidget, QHBoxLayout, QSizePolicy)

from ui.widget.character_status_card import CharacterCardManager
from PySide6.QtCore import Qt

from ui.widget.image_loader_widget import ImageAvatarButton

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
            avatar = ImageAvatarButton()
            avatar.setCursor(Qt.PointingHandCursor)
            avatar.setFixedSize(60, 60)
            avatar.setStyleSheet("""
                QPushButton {
                    border: 2px solid #4a90e2;
                    border-radius: 30px;
                    background-color: #ffffff;
                    padding: 0px;
                    margin: 0px;
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
            self.avatars[i].load_image(char_data['name'])
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
