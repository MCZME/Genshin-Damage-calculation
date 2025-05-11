import random
from PySide6.QtWidgets import (QVBoxLayout, QWidget, QLabel,
                              QPushButton, QHBoxLayout, QProgressBar, QStyle,
                              QGridLayout, QApplication)

from ui.widget.character_status_dialog import CharacterStatusDialog, EffectDisplayWidget, EnergyDisplayWidget
from PySide6.QtCore import Qt, QObject
from PySide6.QtGui import QPixmap

class CharacterStatusCard(QWidget):
    """单个角色状态卡片组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dialog = CharacterStatusDialog()
        color_hash = random.randint(0, 3)
        colors = [
            '#FFE4E1',  # 淡粉色
            '#E0F7E0',  # 淡薄荷绿
            '#E0F2F8',  # 淡蓝色
            '#FFE5CC'   # 淡橙色
        ]
        bg_color = colors[color_hash]
        self.border_color = [
            '#FFA07A',  # 粉色边框
            '#98D8A0',  # 绿色边框
            '#87CEEB',  # 蓝色边框
            '#FFB347'   # 橙色边框
        ][color_hash]
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("CharacterCard")
        self.setStyleSheet(f"""
            QWidget#CharacterCard {{
                background-color: {bg_color};
                border-radius: 8px;
                border: 2px solid {self.border_color};
                padding: 12px;
                margin: 4px;
            }}
            QWidget#CharacterCard > QWidget {{
                background: transparent;
            }}
            
            QWidget#CharacterCard QLabel {{
                color: white;
                font: 13px "Microsoft YaHei";
            }}
        """)
        self.card_layout = QVBoxLayout(self)
        self.card_layout.setContentsMargins(10,10,10,10)
        self.card_layout.setSpacing(8)
        
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
        
        # 存储卡片中的各个部件
        self.name_label = None
        self.hp_bar = None
        self.prop_widgets = {}
        self.effect_widgets = {}
        self.energy_widget = None

    def set_data(self, data):
        """设置角色数据"""   
        self.dialog.set_data(data)
        
        # 清除现有内容
        self._clear_content()
        
        # 第一行：角色信息 + 设置按钮
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(10)
        
        # 角色基本信息
        info_layout = QHBoxLayout()
        info_layout.setSpacing(10)
        
        if 'name' in data:
            self.name_label = QLabel(data['name'])
            self.name_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #333333;")
            info_layout.addWidget(self.name_label)
            
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

        if 'weapon' in data:
            weapon_name = QLabel(f"武器: {data['weapon']['name']}")
            weapon_name.setStyleSheet("color: #4a90e2;")
            info_layout.addWidget(weapon_name)

            weapon_level = QLabel(f"等级: {data['weapon']['level']}")
            weapon_level.setStyleSheet("color: #4a90e2;")
            info_layout.addWidget(weapon_level)

            weapon_refinement = QLabel(f"精炼: {data['weapon']['refinement']}")
            weapon_refinement.setStyleSheet("color: #4a90e2;")
            info_layout.addWidget(weapon_refinement)
            
        top_row.addLayout(info_layout)
        top_row.addStretch()
        top_row.addWidget(self.settings_btn)
        
        self.card_layout.addLayout(top_row)
        
        # 根据对话框中的单选按钮状态显示内容
        self._update_card_display()
        
        self.settings_btn.clicked.connect(self.show_detail_dialog)

    def _update_card_display(self):
        """根据对话框中的单选按钮状态更新卡片显示"""
        selected_data = self.dialog.get_selected_data()
        self._clear_content()
        
        # 清除旧的布局引用
        if hasattr(self, 'props_container'):
            self.props_container.deleteLater()
            del self.props_container
        if hasattr(self, 'effects_container'):
            self.effects_container.deleteLater()
            del self.effects_container
        
        # 用于跟踪是否需要添加分隔线
        has_previous_content = False
        
        # 处理选中的数据
        for item in selected_data:
            if item.get("type") == "HP":
                # 显示血条
                if has_previous_content:
                    self._add_separator()
                has_previous_content = True
                
                hp_container = QWidget()
                hp_container.setStyleSheet('''
                    border: none;
                    background: transparent;''')
                hp_layout = QHBoxLayout(hp_container)
                hp_layout.setContentsMargins(0, 0, 0, 0)
                hp_layout.setSpacing(0)
                
                self.hp_bar = QProgressBar()
                self.hp_bar.setRange(0, item["max"])
                self.hp_bar.setValue(item["current"])
                self.hp_bar.setTextVisible(True)
                self.hp_bar.setFormat(f"生命值：{int(item['current'])}/{int(item['max'])}")
                self.hp_bar.setStyleSheet("""
                    QProgressBar {
                        height: 24px;
                        text-align: center;
                        font-size: 14px;
                        font-weight: bold;
                    }
                    QProgressBar::chunk {
                        background-color: #4ae051;
                        border-radius: 3px;
                    }
                """)
                
                hp_layout.addWidget(self.hp_bar)
                self.card_layout.addWidget(hp_container)
                
            elif "prop" in item:
                # 显示属性 - 第一次显示属性时添加容器
                if not hasattr(self, 'props_container'):
                    if has_previous_content:
                        self._add_separator()
                    has_previous_content = True
                    
                    self.props_container = QWidget()
                    self.props_container.setStyleSheet("""
                        border: none;
                        margin-bottom: 10px;
                    """)
                    self.props_layout = QGridLayout(self.props_container)
                    self.props_layout.setHorizontalSpacing(15)
                    self.props_layout.setVerticalSpacing(5)
                    self.card_layout.addWidget(self.props_container)
                    self.current_prop_row = 0
                    self.current_prop_col = 0
                
                # 添加单个属性
                prop = item["prop"]
                value = item["value"]
                
                if prop == '反应系数提高':
                    display_text = f"<b>{prop}:</b> {list(value.keys())[0]}-{list(value.values())[0]}"
                else:
                    display_text = f"<b>{prop}:</b> {value:.1f}"
                
                prop_container = QWidget()
                prop_container.setStyleSheet("""
                    border: none;
                    border-bottom: 1px solid #e0e0e0;
                    margin-bottom: 10px;
                    background-color: rgba(74, 144, 226, 0.1);
                    border-radius: 4px;
                """)
                prop_layout = QHBoxLayout(prop_container)
                prop_layout.setContentsMargins(0, 0, 0, 0)
                prop_layout.setSpacing(5)
                
                combined_label = QLabel(display_text)
                combined_label.setStyleSheet("""
                    color: #4a90e2; 
                    min-width: 140px;
                    padding: 2px;
                    background-color: none;
                    border: none
                """)
                prop_layout.addWidget(combined_label)
                
                self.props_layout.addWidget(prop_container, self.current_prop_row, self.current_prop_col)
                self.prop_widgets[prop] = prop_container
                
                self.current_prop_col += 1
                if self.current_prop_col >= 3:
                    self.current_prop_col = 0
                    self.current_prop_row += 1
                    
            elif item.get("type") == "Effect":
                # 显示效果 - 第一次显示效果时添加容器
                if not hasattr(self, 'effects_container'):
                    if has_previous_content:
                        self._add_separator()
                    has_previous_content = True
                    
                    self.effects_container = QWidget()
                    self.effects_container.setStyleSheet("""
                        background-color: rgba(74, 144, 226, 0.1);
                        border-radius: 8px;
                        padding: 2px;
                    """)
                    self.effects_layout = QGridLayout(self.effects_container)
                    self.effects_layout.setHorizontalSpacing(10)
                    self.effects_layout.setVerticalSpacing(5)
                    self.card_layout.addWidget(self.effects_container)
                    self.current_effect_row = 0
                    self.current_effect_col = 0
                
                # 添加单个效果
                effect_widget = EffectDisplayWidget(
                    name=item["name"],
                    duration=item["duration"],
                    max_duration=item["max_duration"],
                    msg=item["msg"]
                )
                effect_widget.setStyleSheet("""
                    border: none;
                    margin: 2px;
                """)
                
                self.effects_layout.addWidget(effect_widget, self.current_effect_row, self.current_effect_col)
                self.effect_widgets[item["name"]] = effect_widget
                
                self.current_effect_col += 1
                if self.current_effect_col >= 4:
                    self.current_effect_col = 0
                    self.current_effect_row += 1
                    
            elif item.get("type") == "Energy":
                # 显示元素能量
                if has_previous_content:
                    self._add_separator()
                has_previous_content = True
                
                energy_container = QWidget()
                energy_container.setStyleSheet("""
                    border: none;
                    margin-bottom: 5px;
                """)
                energy_layout = QVBoxLayout(energy_container)
                energy_layout.setContentsMargins(0, 0, 0, 0)
                
                self.energy_widget = EnergyDisplayWidget(
                    element=item["element"],
                    energy=item["current"],
                    max_energy=item["max"]
                )
                
                energy_layout.addWidget(self.energy_widget)
                self.card_layout.addWidget(energy_container)

    def _clear_content(self):
        """清除卡片内容，保留第一行（角色信息）"""
        # 移除除第一行外的所有内容
        while self.card_layout.count() > 1:
            item = self.card_layout.takeAt(1)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
        
        # 清空部件引用
        self.hp_bar = None
        self.prop_widgets.clear()
        self.effect_widgets.clear()
        self.energy_widget = None
        
        # 清除可能的布局容器引用
        if hasattr(self, 'props_container'):
            del self.props_container
        if hasattr(self, 'effects_container'):
            del self.effects_container

    def _clear_layout(self, layout):
        """递归清除布局中的所有部件"""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
    
    def _add_separator(self):
        """添加分隔线"""
        separator = QWidget()
        separator.setFixedHeight(2)
        separator.setStyleSheet(f"background-color: {self.border_color};")
        self.card_layout.addWidget(separator)
    
    def update_data(self, new_data):
        """更新角色数据"""
        self.dialog.update_data(new_data)
        self._update_card_display()
    
    def show_detail_dialog(self):
        """显示详细对话框"""
        self.dialog.exec()
        # 对话框关闭后，根据新的选择状态更新卡片显示
        self._update_card_display()

class CharacterCardManager(QObject):
    """角色卡片管理器，处理卡片添加/移除和动画效果"""
    def __init__(self, card_area):
        super().__init__()
        self.card_area = card_area
        self.all_cards = {}  # {角色名: 卡片实例}
        
    def initialize_cards(self, character_data):
        """初始化所有角色卡片但不添加到布局"""
        for char_name, char_data in character_data.items():
            card = CharacterStatusCard()
            card.set_data(char_data)
            card.setVisible(False)
            self.all_cards[char_name] = card
        
    def toggle_card(self, char_name):
        """切换卡片显示状态"""
        if char_name in self.all_cards:
            card = self.all_cards[char_name]
            if card.isVisible():
                # 隐藏时从布局移除
                self.card_area.layout().removeWidget(card)
                card.setVisible(False)
            else:
                # 显示时添加到布局末尾
                self.card_area.layout().addWidget(card)
                card.setVisible(True)
                # 确保新添加的卡片在布局中可见
                self.card_area.layout().update()

    def update_cards(self, frame_data):
        """更新卡片数据"""
        for char_name, card in self.all_cards.items():
            if char_name in frame_data:
                try:
                    card.update_data(frame_data[char_name])
                except Exception as e:
                    print(f"更新卡片 {char_name} 失败: {str(e)}")

    def _validate_data(self, data):
        """基础数据校验"""
        required_fields = ['level', 'currentHP', 'maxHP']
        return all(field in data for field in required_fields)
