from PySide6.QtWidgets import (QDialog, QVBoxLayout, QWidget, QLabel, 
                             QHBoxLayout, QGridLayout, QProgressBar,
                             QRadioButton, QScrollArea, QSizePolicy,QPushButton,QStyle)
from PySide6.QtCore import Qt

class CharacterStatusDialog(QDialog):
    """角色状态详情弹窗"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.prop_widgets = {}
        self.effect_widgets = {}
        self.setWindowTitle("角色详情")
        self.setMinimumSize(800, 800)
        
        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 0, 10)
        self.main_layout.setSpacing(10)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
            }
            QScrollArea QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 18px;
                padding: 2px;
            }
            QScrollArea QScrollBar::handle:vertical {
                background: #8ab4e8;
                min-height: 30px;
                margin: 0 1px;
                width: 14px;
            }
            QScrollArea QScrollBar::handle:vertical:hover {
                background: #7aa3d8;
            }
            QScrollArea QScrollBar::handle:vertical:pressed {
                background: #6a92c8;
            }
            QScrollArea QScrollBar::add-line:vertical,
            QScrollArea QScrollBar::sub-line:vertical {
                height: 0;
                subcontrol-position: none;
            }
            QScrollArea QScrollBar::add-page:vertical,
            QScrollArea QScrollBar::sub-page:vertical {
                background: #e0e0e0;
            }
        """)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_layout.setSpacing(0)  # 设置为0以便自定义间距和边框
        
        scroll.setWidget(self.content_widget)
        self.main_layout.addWidget(scroll)
        
        # 样式设置
        self.setStyleSheet("""
            background-color: #ffffff;
            border-radius: 0px;
            padding: 8px;
        """)
        self.close_btn = QPushButton()
        self.close_btn.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_FileDialogDetailedView')))
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                font-size: 18px;
                color: #666666;
            }
            QPushButton:hover {
                background: rgba(0, 0, 0, 0.05);
                color: #333333;
            }
        """)
        self.close_btn.clicked.connect(self.close)
        self.radio_buttons = []  # 存储所有单选按钮

    def set_data(self, data):
        """设置角色数据"""   
        self._clear_content()  
        # 第一行：角色信息 + 设置按钮
        top = QWidget()
        top.setStyleSheet("""
            border: none;
            border-top: 1px solid #e0e0e0;
                          """)
        top_row = QHBoxLayout(top)
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
        top_row.addWidget(self.close_btn)
        
        self.content_layout.addWidget(top)
        
        # 显示血条
        if 'currentHP' in data and 'maxHP' in data:
            hp_container = QWidget()
            hp_container.data = { 
                    "type": "HP",
                    "current": data['currentHP'],
                    "max": data['maxHP']
                    }
            hp_container.setStyleSheet('''border: none;
                    border-top: 1px solid #e0e0e0;
                    border-bottom: 1px solid #e0e0e0;
                    border-left: none;
                    border-right: none;
                    margin-bottom: 10px;''')
            hp_layout = QHBoxLayout(hp_container)
            hp_layout.setContentsMargins(0, 0, 0, 0)
            hp_layout.setSpacing(0)
            
            self.hp_bar = QProgressBar()
            self.hp_bar.setRange(0, data['maxHP'])
            self.hp_bar.setValue(data['currentHP'])
            self.hp_bar.setTextVisible(True)
            self.hp_bar.setFormat(f"生命值：{int(data['currentHP'])}/{int(data['maxHP'])}")
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
                "额外属性": ['生命值%', '攻击力%', '防御力%', '伤害加成', '反应系数提高']
            }
                
            for category, props in categories.items():
                has_props = any(p in data['panel'] for p in props)
                if not has_props:
                    continue
                    
                category_container = QWidget()
                category_container.setStyleSheet("""
                    border: none;
                    border-top: 1px solid #e0e0e0;
                    border-bottom: 1px solid #e0e0e0;
                    margin-bottom: 10px;
                """)
                self.category_layout = QHBoxLayout(category_container)
                self.category_layout.setContentsMargins(0, 0, 0, 0)
                self.category_layout.setSpacing(0)
                category_label = QLabel(category)
                category_label.setStyleSheet("""
                    font-weight: bold; 
                    margin-top: 5px; 
                    color: #333333;
                    border-top: none;
                """)
                self.category_layout.addWidget(category_label)
                parent_radio = self.link_to_radio_btn(category_container, self.category_layout, is_parent=True)
                self.content_layout.addWidget(category_container)
                
                self.panel_grid = QGridLayout()
                self.panel_grid.setHorizontalSpacing(15)
                self.panel_grid.setVerticalSpacing(5)
                
                row = 0
                col = 0
                for prop in props:
                    if prop not in data['panel']:
                        continue
                        
                    value = data['panel'][prop]
                    prop_container = QWidget()

                    if prop in ['生命值','攻击力','防御力']:
                        display_text = f"<b>{prop}:</b> {int(value)} + {(data['panel']['固定'+prop]+value*data['panel'][prop+'%']/100):.0f}"
                        value = data['panel']['固定'+prop]+ value*data['panel'][prop+'%']/100 + value
                    elif prop == '反应系数提高':
                        display_text = f"<b>{prop}:</b> {list(value.keys())[0]} - {list(value.values())[0]}"
                    else:
                        display_text = f"<b>{prop}:</b> {value}"
                    prop_container.data = { 
                            "category": category,
                            "prop": prop,
                            "value": value
                            }
                    
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
                    
                    child_radio = self.link_to_radio_btn(prop_container, prop_layout)
                    parent_radio.child_radios.append(child_radio)
                    
                    self.panel_grid.addWidget(prop_container, row, col)
                    self.prop_widgets[prop] = prop_container
                    
                    col += 1
                    if col >= 3:
                        col = 0
                        row += 1
                
                self.content_layout.addLayout(self.panel_grid)
        
        # 显示效果属性
        if 'effect' in data and isinstance(data['effect'], dict):
            effects_container = QWidget()
            effects_container.data = {
                "type": "Effects",
            }
            effects_container.setStyleSheet("""
                border: none;
                border-bottom: 1px solid #e0e0e0;
                margin-bottom: 10px;
            """)
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
            parent_radio = self.link_to_radio_btn(effects_container, effects_layout, is_parent=True)
            parent_radio.child_radios = []
            self.effects_data = {}
            self.content_layout.addWidget(effects_container)
            
            effect_container = QWidget()
            effect_container.setStyleSheet("""
                background-color: rgba(74, 144, 226, 0.1);
                border-radius: 8px;
                padding: 2px;
            """)
            self.effect_layout = QGridLayout(effect_container)
            self.effect_layout.setContentsMargins(0, 0, 0, 0)
            self.effect_layout.setHorizontalSpacing(5)
            self.effect_layout.setVerticalSpacing(5)
            
            row = 0
            col = 0
            for key, value in data['effect'].items():
                duration = value.get('duration', 0)
                max_duration = value.get('max_duration', 0)
                msg = value.get('msg', '')
                effect_widget = EffectDisplayWidget(
                    name=key,
                    duration=duration,
                    max_duration=max_duration,
                    msg=msg)
                effect_widget.data = {
                    "type": "Effect",
                    "name": key,
                    "duration": value.get('duration', 0),
                    "max_duration": value.get('max_duration', 0),
                    "msg": value.get('msg', '')
                    }
                self.effect_layout.addWidget(effect_widget, row, col)
                self.effects_data[key] = effect_widget.data
                self.effect_widgets[key] = effect_widget
                
                col += 1
                if col >= 4:
                    col = 0
                    row += 1
            
            self.content_layout.addWidget(effect_container)
        
        # 显示元素能量
        if 'elemental_energy' in data and isinstance(data['elemental_energy'], dict):
            category_container = QWidget()
            category_container.data = {
                "type": "Elemental Energy",
            }
            category_container.setStyleSheet("""
                border: none;
                border-bottom: 1px solid #e0e0e0;
                margin-bottom: 10px;
            """)
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
            parent_radio = self.link_to_radio_btn(category_container, category_layout, is_parent=True)
            parent_radio.child_radios = []
            self.energy_data = {}
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
            self.energy_widget = EnergyDisplayWidget(
                element=element,
                energy=energy,
                max_energy=max_energy)
            self.energy_widget.data = {
                    "type": "Energy",
                    "element": data['elemental_energy'].get('element'),
                    "current": data['elemental_energy'].get('energy'),
                    "max": data['elemental_energy'].get('max_energy')
                    }
            energy_layout.addWidget(self.energy_widget)
            self.energy_data = self.energy_widget.data
            
            self.content_layout.addWidget(energy_container)

        for i in self.radio_buttons[:2]:
            i.setChecked(True)

    def _clear_content(self):
        """清除现有内容"""
        # 删除所有子部件
        for i in reversed(range(self.content_layout.count())):
            item = self.content_layout.itemAt(i)
            widget = item.widget() if item else None
            if widget:
                widget.setParent(None)
        # 清空部件字典
        self.prop_widgets.clear()
        self.effect_widgets.clear()
        # 清空单选按钮列表
        self.radio_buttons.clear()

    def link_to_radio_btn(self, widget, layout, is_parent=False):
        """添加单选按钮并设置点击事件"""
        radio_btn = QRadioButton()
        radio_btn.setStyleSheet("color: #4a90e2;border: none;background-color: none;")
        layout.addWidget(radio_btn)
        layout.setAlignment(radio_btn, Qt.AlignRight)
        radio_btn.is_parent = is_parent
        self.radio_buttons.append(radio_btn)

        # 如果是父级按钮，初始化子按钮列表
        if is_parent:
            radio_btn.child_radios = []
            radio_btn.toggled.connect(self.on_parent_radio_toggled)

        widget.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        widget.setCursor(Qt.PointingHandCursor)

        def toggle_radio(event, btn=radio_btn):
            btn.setChecked(not btn.isChecked())
        widget.mousePressEvent = toggle_radio

        return radio_btn
    
    def on_parent_radio_toggled(self, checked):
        """父级单选按钮状态变化时触发"""
        parent_radio = self.sender()
        if hasattr(parent_radio, 'child_radios'):
            for child_radio in parent_radio.child_radios:
                child_radio.setChecked(checked)

    def get_selected_data(self):
        """获取选中数据（自动处理父级包含子级逻辑）"""
        selected_data = []
        processed_parents = set()

        # 第一轮：处理所有被选中的父级按钮
        for radio in self.radio_buttons:
            if not radio.isChecked() or not radio.is_parent:
                continue

            # 获取父级容器数据（如果有实际数据）
            parent_container = self._find_data_container(radio)
            if parent_container and hasattr(parent_container, 'data'):
                # 仅添加特定类型的父级数据（如HP）
                if parent_container.data.get("type") in ["HP"]:
                    selected_data.append(parent_container.data)

            if parent_container and parent_container.data.get("type") == "Elemental Energy":
                selected_data.append(self.energy_data)
                continue
            if parent_container and parent_container.data.get("type") == "Effects":
                selected_data.extend(self.effects_data.values())
                continue

            # 收集所有子级数据
            for child_radio in radio.child_radios:
                if child_radio.is_parent:  # 防止无限递归
                    continue
                container = self._find_data_container(child_radio)
                if container and container.data not in selected_data:
                    selected_data.append(container.data)
            processed_parents.add(radio)

        # 第二轮：处理独立选中的子级按钮
        for radio in self.radio_buttons:
            if radio.isChecked() and not radio.is_parent:
                # 检查是否已被父级处理
                parent_radio = self._find_parent_radio(radio)
                if parent_radio in processed_parents:
                    continue

                container = self._find_data_container(radio)
                if container and container.data not in selected_data:
                    selected_data.append(container.data)

        return selected_data

    def _find_data_container(self, radio):
        """查找数据容器（兼容多级布局）"""
        current_widget = radio.parent()
        while current_widget:
            if hasattr(current_widget, 'data'):
                # 跳过纯容器型数据（如分类标题）
                if isinstance(current_widget.data, dict) and "prop" in current_widget.data:
                    return current_widget
                if current_widget.data.get("type") in ["HP", "Effects", "Elemental Energy"]:
                    return current_widget
            current_widget = current_widget.parent()
        return None    
    
    def _find_parent_radio(self, radio):
        """查找父级单选按钮"""
        current_widget = radio.parent()
        while current_widget:
            if hasattr(current_widget, 'child_radios'):
                return current_widget
            current_widget = current_widget.parent()
        return None

    def update_data(self, new_data):
        """增量更新数据"""
        # 更新生命值
        if 'currentHP' in new_data:
            self.hp_bar.setValue(new_data['currentHP'])
            self.hp_bar.setFormat(f"生命值：{int(new_data['currentHP'])}/{int(new_data['maxHP'])}")
            self.hp_bar.parent().data = { 
                    "type": "HP",
                    "current": new_data['currentHP'],
                    "max": new_data['maxHP']
                }
        
        # 更新面板属性
        if 'panel' in new_data:
            # 查找额外属性的网格布局
            grid_layout = self.panel_grid
            category_container = self.category_layout
            
            for prop in new_data['panel'].keys():
                if prop in ['固定生命值','固定攻击力','固定防御力']:
                    continue
                    
                if prop in self.prop_widgets:
                    # 更新现有属性
                    value = new_data['panel'][prop]
                    if prop in ['生命值','攻击力','防御力']:
                        display_text = f"<b>{prop}:</b> {int(value)} + {int(new_data['panel']['固定'+prop] + value*new_data['panel'][prop+'%']/100)}"
                        self.prop_widgets[prop].data['value'] = int(value) + new_data['panel']['固定'+prop]+value*new_data['panel'][prop+'%']/100
                    elif prop == '反应系数提高':
                        display_text = f"<b>{prop}:</b> {list(value.keys())[0]} - {list(value.values())[0]}"
                        self.prop_widgets[prop].data['value'] = value
                    else:
                        display_text = f"<b>{prop}:</b> {value:.1f}"
                        self.prop_widgets[prop].data['value'] = value
                    # 获取部件中的QLabel并更新文本
                    for child in self.prop_widgets[prop].children():
                        if isinstance(child, QLabel):
                            child.setText(display_text)
                            break
                    
                elif grid_layout:  # 只处理能找到额外属性布局的情况
                    # 创建新属性部件
                    value = new_data['panel'][prop]
                    prop_container = QWidget()
                    prop_container.data = {
                        "category": "额外属性",
                        "prop": prop,
                        "value": value
                    }
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
                    
                    display_text = f"<b>{prop}:</b> {value}"
                    combined_label = QLabel(display_text)
                    combined_label.setStyleSheet("""
                        color: #4a90e2; 
                        min-width: 140px;
                        padding: 2px;
                        background-color: none;
                        border: none
                    """)
                    prop_layout.addWidget(combined_label)
                    
                    # 链接到额外属性的父级单选按钮
                    parent_radio = None
                    for radio in self.radio_buttons:
                        if radio.is_parent and radio.parent().widget() == category_container:
                            parent_radio = radio
                            break
                    
                    child_radio = self.link_to_radio_btn(prop_container, prop_layout)
                    if parent_radio:
                        parent_radio.child_radios.append(child_radio)
                    
                    # 找到网格布局中第一个空位
                    position_found = False
                    for row in range(grid_layout.rowCount()):
                        for col in range(3):
                            if not grid_layout.itemAtPosition(row, col):
                                grid_layout.addWidget(prop_container, row, col)
                                position_found = True
                                break
                        if position_found:
                            break
                    if not position_found:  # 追加到新行
                        grid_layout.addWidget(prop_container, grid_layout.rowCount(), 0)
                    
                    self.prop_widgets[prop] = prop_container
        
        # 更新元素能量
        if 'elemental_energy' in new_data:
            self.energy_widget.update_energy(
                new_data['elemental_energy']['energy'],
                new_data['elemental_energy']['max_energy']
            )
            self.energy_data = {
                "type": "Energy",
                "element": new_data['elemental_energy'].get('element'),
                "current": new_data['elemental_energy'].get('energy'),
                "max": new_data['elemental_energy'].get('max_energy')
            }
        
        # 更新效果持续时间
        if 'effect' in new_data:
            # 首先收集当前所有效果名称
            current_effects = set(new_data['effect'].keys())
            
            # 检查并移除已经消失的效果
            for effect_name in list(self.effect_widgets.keys()):
                if effect_name not in current_effects:
                    # 从布局中移除部件
                    widget = self.effect_widgets[effect_name]
                    widget.setParent(None)
                    widget.deleteLater()
                    # 从字典中移除
                    del self.effects_data[effect_name]
                    del self.effect_widgets[effect_name]
            
            # 更新或添加效果
            for effect_name, effect_data in new_data['effect'].items():
                if effect_name in self.effect_widgets:
                    # 更新现有效果
                    self.effect_widgets[effect_name].update_duration(
                        effect_data['duration'],
                        effect_data['max_duration'],
                        effect_data['msg']
                    )
                    
                    self.effects_data[effect_name] = {
                        "type": "Effect",
                        "name": effect_name,
                        "duration": effect_data.get('duration', 0),
                        "max_duration": effect_data.get('max_duration', 0),
                        "msg": effect_data.get('msg', '')
                    }

                    # 如果效果已结束，也移除它
                    if effect_data['duration'] <= 0:
                        widget = self.effect_widgets[effect_name]
                        widget.setParent(None)
                        widget.deleteLater()
                        del self.effect_widgets[effect_name]
                else:
                    # 只添加持续时间大于0的新效果
                    if effect_data['duration'] > 0:
                        # 创建新的效果部件
                        effect_widget = EffectDisplayWidget(
                            name=effect_name,
                            duration=effect_data['duration'],
                            max_duration=effect_data['max_duration'],
                            msg=effect_data['msg']
                        )
                        effect_widget.data = {
                            "type": "Effect",
                            "name": effect_name,
                            "duration": effect_data.get('duration', 0),
                            "max_duration": effect_data.get('max_duration', 0),
                            "msg": effect_data.get('msg', '')
                        }
                        self.effects_data[effect_name]=effect_widget.data
                        
                        # 直接访问效果网格布局容器
                        effect_grid_container = self.effect_layout
                        if effect_grid_container and isinstance(effect_grid_container.layout(), QGridLayout):
                            grid_layout = effect_grid_container.layout()
                            # 找到网格布局中第一个空位
                            position_found = False
                            for row in range(grid_layout.rowCount()):
                                for col in range(4):
                                    if not grid_layout.itemAtPosition(row, col):
                                        grid_layout.addWidget(effect_widget, row, col)
                                        position_found = True
                                        break
                                if position_found:
                                    break
                            if not position_found:  # 追加到新行
                                grid_layout.addWidget(effect_widget, grid_layout.rowCount(), 0)
                            
                            self.effect_widgets[effect_name] = effect_widget
       
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
            self.combo_label.setText(f"{self.element} {min(energy, max_energy):.1f}/{max_energy}")
            self.combo_label.setGeometry(0, 0, self.progress.width(), self.progress.height())

    def resizeEvent(self, event):
        """重写resize事件以保持组合标签居中"""
        super().resizeEvent(event)
        if hasattr(self, 'combo_label'):
            self.combo_label.setGeometry(0, 0, self.progress.width(), self.progress.height())

class EffectDisplayWidget(QWidget):
    """效果持续时间显示组件"""
    def __init__(self, name="", duration=0, max_duration=0, msg="",parent=None):
        super().__init__(parent)
        self.name = name
        self.setFixedHeight(24)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setToolTip(msg)
        self.setStyleSheet("""
            QToolTip {
                background-color: rgba(100, 160, 220, 0.8);
                border-radius: 0;
            }
        """)
        
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
    
    def update_duration(self, duration, max_duration=None, msg=""):
        """更新持续时间显示"""
        if max_duration is not None and max_duration == float('inf'):
            self.progress.show()
            self.combo_label.show()
            self.combo_label.setText(self.name)
            self.combo_label.setGeometry(0, 0, self.width(), self.height())
            self.setToolTip(msg)
        else:
            self.progress.show()
            self.combo_label.show()
            safe_max_duration = min(max_duration, 1000000) if max_duration else self.progress.maximum()
            self.progress.setMaximum(safe_max_duration)
            self.progress.setValue(min(duration, safe_max_duration))
            self.combo_label.setText(f"{self.name} {min(duration, safe_max_duration)}/{safe_max_duration}")
            self.combo_label.setGeometry(0, 0, self.progress.width(), self.progress.height())
            self.setToolTip(msg)

    def resizeEvent(self, event):
        """重写resize事件以保持组合标签居中"""
        super().resizeEvent(event)
        if hasattr(self, 'combo_label'):
            self.combo_label.setGeometry(0, 0, self.progress.width(), self.progress.height())
