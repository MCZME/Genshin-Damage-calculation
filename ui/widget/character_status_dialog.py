from PySide6.QtWidgets import (QDialog, QVBoxLayout, QWidget, QLabel, 
                             QHBoxLayout, QGridLayout, QProgressBar,
                             QRadioButton, QScrollArea, QSizePolicy,QPushButton,QStyle)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

class CharacterStatusDialog(QDialog):
    """角色状态详情弹窗"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("角色详情")
        self.setMinimumSize(800, 800)
        
        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_layout.setSpacing(10)
        
        scroll.setWidget(self.content_widget)
        self.main_layout.addWidget(scroll)
        
        # 样式设置
        self.setStyleSheet("""
            background-color: #ffffff;
            border-radius: 0px;
            padding: 8px;
            border-top: 1px solid #e0e0e0;
            border-bottom: 1px solid #e0e0e0;
        """)
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
        # 清空现有内容
        for i in reversed(range(self.content_layout.count())): 
            self.content_layout.itemAt(i).widget().setParent(None)
        
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
        
        self.content_layout.addLayout(top_row)
        
        # 显示血条
        if 'currentHP' in data and 'maxHP' in data:
            hp_container = QWidget()
            hp_container.setStyleSheet('''border: none;
                    border-top: 1px solid #e0e0e0;
                    border-bottom: 1px solid #e0e0e0;
                    border-left: none;
                    border-right: none;''')
            hp_layout = QHBoxLayout(hp_container)
            hp_layout.setContentsMargins(0, 0, 0, 0)
            hp_layout.setSpacing(0)
            
            hp_bar = QProgressBar()
            hp_bar.setRange(0, data['maxHP'])
            hp_bar.setValue(data['currentHP'])
            hp_bar.setTextVisible(True)
            hp_bar.setFormat(f"生命值：{int(data['currentHP'])}/{int(data['maxHP'])}")
            hp_bar.setStyleSheet("""
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
            
            hp_layout.addWidget(hp_bar)
            self.link_to_radio_btn(hp_container, hp_layout)
            self.content_layout.addWidget(hp_container)

        # 显示面板属性
        if 'panel' in data and isinstance(data['panel'], dict):
            categories = {
                "基础属性": ['生命值', '攻击力', '防御力', '元素精通'],
                "进阶属性": ['暴击率', '暴击伤害', '元素充能效率', '治疗加成', '受治疗加成'],
                "元素属性": ['火元素伤害加成', '水元素伤害加成', '雷元素伤害加成', 
                          '冰元素伤害加成', '岩元素伤害加成', '风元素伤害加成', 
                          '草元素伤害加成', '物理伤害加成'],
                "额外属性": ['生命值%', '攻击力%', '防御力%', '伤害加成']
            }
                
            for category, props in categories.items():
                has_props = any(p in data['panel'] for p in props)
                if not has_props:
                    continue
                    
                category_container = QWidget()
                category_container.setStyleSheet("border: none;")
                category_layout = QHBoxLayout(category_container)
                category_layout.setContentsMargins(0, 0, 0, 0)
                category_layout.setSpacing(0)
                category_label = QLabel(category)
                category_label.setStyleSheet("""
                    font-weight: bold; 
                    margin-top: 5px; 
                    color: #333333;
                    border-bottom: 1px solid #e0e0e0;
                    padding-bottom: 3px;
                """)
                category_layout.addWidget(category_label)
                self.link_to_radio_btn(category_container, category_layout)
                self.content_layout.addWidget(category_container)
                
                panel_grid = QGridLayout()
                panel_grid.setHorizontalSpacing(15)
                panel_grid.setVerticalSpacing(5)
                
                row = 0
                col = 0
                for prop in props:
                    if prop not in data['panel']:
                        continue
                        
                    value = data['panel'][prop]
                    
                    if prop in ['生命值','攻击力','防御力']:
                        display_text = f"<b>{prop}:</b> {int(value)} + {(data['panel']['固定'+prop]+value*data['panel'][prop+'%']/100):.0f}"
                    else:
                        display_text = f"<b>{prop}:</b> {value}"
                    
                    prop_container = QWidget()
                    prop_container.setStyleSheet(" border:none;")
                    prop_layout = QHBoxLayout(prop_container)
                    prop_layout.setContentsMargins(0, 0, 0, 0)
                    prop_layout.setSpacing(5)
                    
                    combined_label = QLabel(display_text)
                    combined_label.setStyleSheet("color: #4a90e2; min-width: 140px;padding: 2px;")
                    prop_layout.addWidget(combined_label)
                    
                    self.link_to_radio_btn(prop_container, prop_layout)
                    
                    panel_grid.addWidget(prop_container, row, col)
                    
                    col += 1
                    if col >= 3:
                        col = 0
                        row += 1
                
                self.content_layout.addLayout(panel_grid)
        
        # 显示效果属性
        if 'effect' in data and isinstance(data['effect'], dict):
            effects_container = QWidget()
            effects_container.setStyleSheet("border: none;")
            effects_layout = QHBoxLayout(effects_container)
            effects_layout.setContentsMargins(0, 0, 0, 0)
            effects_layout.setSpacing(5)
            effect_group = QLabel("效果加成")
            effect_group.setStyleSheet("""
                font-weight: bold; 
                margin-top: 5px; 
                color: #333333;
                border-bottom: 1px solid #e0e0e0;
                padding-bottom: 3px;
            """)
            effects_layout.addWidget(effect_group)
            self.link_to_radio_btn(effects_container, effects_layout)
            self.content_layout.addWidget(effects_container)
            
            effect_container = QWidget()
            effect_container.setStyleSheet("""
                background-color: rgba(74, 144, 226, 0.1);
                border-radius: 8px;
                padding: 2px;
            """)
            effect_layout = QGridLayout(effect_container)
            effect_layout.setContentsMargins(0, 0, 0, 0)
            effect_layout.setHorizontalSpacing(5)
            effect_layout.setVerticalSpacing(5)
            
            row = 0
            col = 0
            for key, value in data['effect'].items():
                duration = value.get('duration', 0)
                max_duration = value.get('max_duration', 0)
                effect_widget = EffectDisplayWidget(
                    name=key,
                    duration=duration,
                    max_duration=max_duration)
                effect_layout.addWidget(effect_widget, row, col)
                
                col += 1
                if col >= 4:
                    col = 0
                    row += 1
            
            self.content_layout.addWidget(effect_container)
        
        # 显示元素能量
        if 'elemental_energy' in data and isinstance(data['elemental_energy'], dict):
            category_container = QWidget()
            category_container.setStyleSheet("border: none;")
            category_layout = QHBoxLayout(category_container)
            category_layout.setContentsMargins(0, 0, 0, 0)
            category_layout.setSpacing(5)
            energy_group = QLabel("元素能量")
            energy_group.setStyleSheet("""
                font-weight: bold; 
                margin-top: 5px; 
                color: #333333;
                border-bottom: 1px solid #e0e0e0;
                padding-bottom: 3px;
            """)
            category_layout.addWidget(energy_group)
            self.link_to_radio_btn(category_container, category_layout)
            self.content_layout.addWidget(category_container)
            
            energy_container = QWidget()
            energy_container.setStyleSheet("""
                background-color: rgba(74, 144, 226, 0.1);
                border-radius: 8px;
                padding: 3px;
            """)
            energy_layout = QVBoxLayout(energy_container)
            energy_layout.setContentsMargins(0, 0, 0, 0)
            energy_layout.setSpacing(5)
            
            element = data['elemental_energy'].get('element')
            energy = data['elemental_energy'].get('energy')
            max_energy = data['elemental_energy'].get('max_energy')
            energy_widget = EnergyDisplayWidget(
                element=element,
                energy=energy,
                max_energy=max_energy)
            energy_layout.addWidget(energy_widget)
            
            self.content_layout.addWidget(energy_container)

    def link_to_radio_btn(self, widget, layout):
        """添加单选按钮并设置点击事件"""
        radio_btn = QRadioButton()
        radio_btn.setStyleSheet("color: #4a90e2;border: none;")
        layout.addWidget(radio_btn)
        layout.setAlignment(radio_btn, Qt.AlignRight)

        widget.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        widget.setCursor(Qt.PointingHandCursor)

        def toggle_radio(event, btn=radio_btn):
            btn.setChecked(not btn.isChecked())
        widget.mousePressEvent = toggle_radio

class EnergyDisplayWidget(QWidget):
    """元素能量显示组件"""
    def __init__(self, element="", energy=0, max_energy=0, parent=None):
        super().__init__(parent)
        self.element = element
        self.setFixedHeight(24)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)
        
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        
        element_colors = {
            "火": "#ff5e56",
            "水": "#59b0ff",
            "雷": "#d15aff",
            "冰": "#90e0ff",
            "岩": "#ffd700",
            "风": "#4ae051",
            "草": "#3a8b3a",
        }
        
        color = element_colors.get(element, "#4a90e2")
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {color};
            }}
        """)
        
        self.combo_label = QLabel()
        self.combo_label.setAlignment(Qt.AlignCenter)
        self.combo_label.setStyleSheet("""
            color: #333333;
            font-weight: bold;
            background: transparent;
        """)
        
        self.layout.addWidget(self.progress)
        self.combo_label.setParent(self.progress)
        self.combo_label.setGeometry(0, 0, self.progress.width(), self.progress.height())
        
        if max_energy > 0:
            self.update_energy(energy, max_energy)
    
    def update_energy(self, energy, max_energy=None):
        """更新能量显示"""
        if max_energy is not None:
            self.progress.setMaximum(max_energy)
            self.progress.setValue(min(energy, max_energy))
            self.combo_label.setText(f"{self.element} {min(energy, max_energy)}/{max_energy}")
            self.combo_label.setGeometry(0, 0, self.progress.width(), self.progress.height())

    def resizeEvent(self, event):
        """重写resize事件以保持组合标签居中"""
        super().resizeEvent(event)
        if hasattr(self, 'combo_label'):
            self.combo_label.setGeometry(0, 0, self.progress.width(), self.progress.height())

class EffectDisplayWidget(QWidget):
    """效果持续时间显示组件"""
    def __init__(self, name="", duration=0, max_duration=0, parent=None):
        super().__init__(parent)
        self.name = name
        self.setFixedHeight(24)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)
        
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: rgba(74, 144, 226, 0.7);
            }
        """)
        
        self.combo_label = QLabel()
        self.combo_label.setAlignment(Qt.AlignCenter)
        self.combo_label.setStyleSheet("""
            color: #333333;
            font-weight: bold;
            background: transparent;
        """)
        
        self.layout.addWidget(self.progress)
        self.combo_label.setParent(self.progress)
        self.combo_label.setGeometry(0, 0, self.progress.width(), self.progress.height())
        
        if max_duration > 0:
            self.update_duration(duration, max_duration)
    
    def update_duration(self, duration, max_duration=None):
        """更新持续时间显示"""
        if max_duration is not None and max_duration == float('inf'):
            self.progress.show()
            self.combo_label.show()
            self.combo_label.setText(self.name)
            self.combo_label.setGeometry(0, 0, self.width(), self.height())
        else:
            self.progress.show()
            self.combo_label.show()
            safe_max_duration = min(max_duration, 1000000) if max_duration else self.progress.maximum()
            self.progress.setMaximum(safe_max_duration)
            self.progress.setValue(min(duration, safe_max_duration))
            self.combo_label.setText(f"{self.name} {min(duration, safe_max_duration)}/{safe_max_duration}")
            self.combo_label.setGeometry(0, 0, self.progress.width(), self.progress.height())

    def resizeEvent(self, event):
        """重写resize事件以保持组合标签居中"""
        super().resizeEvent(event)
        if hasattr(self, 'combo_label'):
            self.combo_label.setGeometry(0, 0, self.progress.width(), self.progress.height())
