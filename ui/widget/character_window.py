from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
                              QLabel, QPushButton, QComboBox, QSpinBox, QCompleter,
                              QWidget, QFormLayout, QTabWidget, QFrame,
                              QDialogButtonBox, QDoubleSpinBox, QLineEdit)
from PySide6.QtCore import Qt, Signal
from artifact.ArtfactSetEffectDict import ArtfactSetEffectDict
from character import character_table
from weapon import weapon_table

class CharacterWindow(QDialog):
    """角色信息设置窗口"""
    finished = Signal(dict)  # 自定义信号用于返回数据
    def __init__(self, parent=None):
        super().__init__(parent)
        self.result_data = None
        self.setWindowTitle("角色配置")
        self.setMinimumSize(800, 500)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setWindowFlags(Qt.Window)
        self.setStyleSheet("""
            background-color: white;
            border-radius: 6px;
        """)
        self.init_ui()
        self.load_data()
        self.char_combo.currentTextChanged.connect(self.update_weapons)

    def init_ui(self):
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 角色配置区域
        char_frame = QFrame()
        char_frame.setStyleSheet("""
            background-color: #e3f2fd;
            border-radius: 6px;
        """)
        self.char_layout = QHBoxLayout(char_frame)
        self.char_layout.setContentsMargins(10, 5, 10, 5)
        self.char_layout.setSpacing(5)
        self.char_layout.addWidget(QWidget(), stretch=1)
        
        # 头像区域
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(60, 60)
        self.avatar_label.setStyleSheet("""
            background-color: #f0f0f0;
            border-radius: 30px;
        """)
        self.char_layout.addWidget(self.avatar_label, stretch=2)
        
        # 角色名称
        self.char_combo = QComboBox()
        self.char_combo.setEditable(True)
        self.char_combo.setFixedWidth(120)
        self.char_combo.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.char_layout.addWidget(self.char_combo, stretch=1)
        self.char_layout.addWidget(QWidget(), stretch=1)

        # 等级
        self.level_spin = QSpinBox()
        self.level_spin.setRange(1, 90)
        self.level_spin.setFixedWidth(40)
        self.level_spin.setStyleSheet("""
            QSpinBox::up-button, 
            QSpinBox::down-button {
                width: 0px;
                height: 0px;
            }
        """)
        self.char_layout.addWidget(QLabel("等级:", styleSheet="color: #333;"))
        self.char_layout.addWidget(self.level_spin, stretch=1)
        self.char_layout.addWidget(QWidget(), stretch=1)
        
        # 天赋
        self.char_layout.addWidget(QLabel("天赋:", styleSheet="color: #333;"))
        for i in range(3):
            spin = QSpinBox()
            spin.setObjectName(f"talent_spin_{i}")
            spin.setRange(1, 15)
            spin.setFixedWidth(20)
            spin.setStyleSheet("""
                QSpinBox::up-button, 
                QSpinBox::down-button {
                    width: 0px;
                    height: 0px;
                }
            """)
            self.char_layout.addWidget(spin, stretch=1)
            if i < 2:
                self.char_layout.addWidget(QLabel("/", styleSheet="color: #333;"))
        self.char_layout.addWidget(QWidget(), stretch=1)
        # 命座
        self.constellation_spin = QSpinBox()
        self.constellation_spin.setRange(0, 6)
        self.constellation_spin.setFixedWidth(15)
        self.constellation_spin.setStyleSheet("""
            QSpinBox::up-button, 
            QSpinBox::down-button {
                width: 0px;
                height: 0px;
            }
        """)
        self.char_layout.addWidget(QLabel("命座:", styleSheet="color: #333;"))
        self.char_layout.addWidget(self.constellation_spin,stretch=1)
        self.char_layout.addWidget(QWidget(), stretch=1)
        
        main_layout.addWidget(char_frame, stretch=1)

        # 武器配置区域
        weapon_frame = QFrame()
        weapon_frame.setStyleSheet("""
            background-color: #e8f5e9;
            border-radius: 6px;
        """)
        weapon_layout = QHBoxLayout(weapon_frame)
        weapon_layout.setContentsMargins(10, 5, 10, 5)
        weapon_layout.setSpacing(10)
        weapon_layout.addWidget(QLabel("类型:", styleSheet="color: #333;"))
        self.weapon_type_label = QLabel("--")
        self.weapon_type_label.setStyleSheet("color: #666;")
        weapon_layout.addWidget(self.weapon_type_label)
        
        # 武器图片
        self.weapon_icon = QLabel()
        self.weapon_icon.setFixedSize(40, 40)
        self.weapon_icon.setStyleSheet("""
            background-color: #f0f0f0;
            border-radius: 4px;
        """)
        weapon_layout.addWidget(QWidget(), stretch=1)
        weapon_layout.addWidget(self.weapon_icon, stretch=1)
        
        # 武器名称
        self.weapon_combo = QComboBox()
        self.weapon_combo.setFixedWidth(120)
        weapon_layout.addWidget(self.weapon_combo, stretch=1)
        
        # 武器等级
        self.weapon_level_spin = QSpinBox()
        self.weapon_level_spin.setRange(1, 90)
        self.weapon_level_spin.setStyleSheet("""
            QSpinBox::up-button, 
            QSpinBox::down-button {
                width: 0px;
                height: 0px;
            }
        """)
        weapon_layout.addWidget(QWidget(), stretch=1)
        weapon_layout.addWidget(QLabel("等级:", styleSheet="color: #333;"))
        weapon_layout.addWidget(self.weapon_level_spin, stretch=1)

        
        # 精炼等级
        self.refinement_spin = QSpinBox()
        self.refinement_spin.setRange(1, 5)
        self.refinement_spin.setStyleSheet("""
            QSpinBox::up-button, 
            QSpinBox::down-button {
                width: 0px;
                height: 0px;
            }
        """)
        weapon_layout.addWidget(QLabel("精炼:", styleSheet="color: #333;"))
        weapon_layout.addWidget(self.refinement_spin, stretch=1)
        weapon_layout.addWidget(QWidget(), stretch=1)
        
        main_layout.addWidget(weapon_frame, stretch=1)

        # 圣遗物卡片区域
        artifact_layout = QHBoxLayout()
        artifact_layout.setContentsMargins(10, 10, 10, 10)
        artifact_layout.setSpacing(10)
        
        # 5个圣遗物卡片
        self.artifact_cards = []
        slots = ["生之花", "死之羽", "时之沙", "空之杯", "理之冠"]
        for slot in slots:
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: #f3e5f5;
                    border: 1px solid #d1c4e9;
                    border-radius: 6px;
                    padding: 5px;
                }
            """)
            
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(8, 8, 8, 8)
            card_layout.setSpacing(5)
            
            # 图片
            icon = QLabel()
            icon.setFixedSize(50, 50)
            icon.setStyleSheet("""
                background-color: #e9ecef;
                border-radius: 4px;
            """)
            card_layout.addWidget(icon, 0, Qt.AlignCenter)
            
            # 名称
            name_label = QLabel(slot)
            name_label.setStyleSheet("""
                font-size: 12px;
                font-weight: bold;
                color: #333;
            """)
            name_label.setAlignment(Qt.AlignCenter)
            name_label.mousePressEvent = lambda e, c=card, s=slot: self.show_name_dialog(c, s)
            name_label.setCursor(Qt.PointingHandCursor)
            card_layout.addWidget(name_label, stretch=1)
            
            # 主属性
            card.main_stat_btn = QPushButton("主属性")
            card.main_stat_btn.setStyleSheet("""
                QPushButton {
                    font-size: 15px;
                    color: #495057;
                    background: transparent;
                    border: none;
                    padding: 0;
                }
                QPushButton:hover {
                    color: #1976d2;
                    text-decoration: underline;
                }
            """)
            card.main_stat_btn.setCursor(Qt.PointingHandCursor)
            card.main_stat_btn.clicked.connect(lambda _, c=card, s=slot: self.edit_main_stat(c, s))
            card_layout.addWidget(card.main_stat_btn, stretch=2)
            
            # 副属性区域
            sub_stat_widget = QWidget()
            sub_stat_layout = QVBoxLayout(sub_stat_widget)
            sub_stat_layout.setContentsMargins(0, 0, 0, 0)
            sub_stat_layout.setSpacing(5)
            
            # 副属性列表
            card.sub_stats = []
            
            # 添加副属性按钮
            card.add_sub_btn = QPushButton("+ 添加副属性")
            card.add_sub_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e3f2fd;
                    color: #1976d2;
                    border: 1px solid #90caf9;
                    border-radius: 4px;
                    padding: 2px 4px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #bbdefb;
                }
            """)
            card.add_sub_btn.setFixedHeight(20)
            card.add_sub_btn.clicked.connect(lambda checked, c=card: self.add_sub_stat(c))
            sub_stat_layout.addWidget(card.add_sub_btn, alignment=Qt.AlignCenter)
            card_layout.addWidget(sub_stat_widget, stretch=3)
            
            artifact_layout.addWidget(card, stretch=1)
            self.artifact_cards.append(card)
        
        main_layout.addLayout(artifact_layout, stretch=5)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        # 重置按钮
        reset_btn = QPushButton("重置", styleSheet="""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #e53935;
            }
        """)
        reset_btn.clicked.connect(self.reset)
        btn_layout.addWidget(reset_btn)
        
        # 确认按钮
        confirm_btn = QPushButton("确认", styleSheet="""
            QPushButton {
                background-color: #4a6fa5;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #5a7fb5;
            }
        """)
        confirm_btn.clicked.connect(self.accept)
        btn_layout.addWidget(confirm_btn)
        
        main_layout.addLayout(btn_layout, stretch=1)
        self.setLayout(main_layout)

    def create_spinbox(self, min_val, max_val, label, layout, row):
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        layout.addWidget(QLabel(label, styleSheet="color: #333;"), row, 0)
        layout.addWidget(spin, row, 1)
        return spin

    def add_sub_stat(self, card):
        """添加副属性"""
        result = self.show_sub_stat_dialog()
        if result:
            # 创建副属性行容器
            stat_row = QWidget()
            stat_row_layout = QHBoxLayout(stat_row)
            stat_row_layout.setContentsMargins(0, 0, 0, 0)
            stat_row_layout.setSpacing(5)
            
            # 副属性标签
            stat_label = QLabel(result)
            stat_label.setStyleSheet("""
                font-size: 12px;
                color: #6c757d;
                border: 0px solid #ced4da;
            """)
            stat_label.setAlignment(Qt.AlignLeft)
            
            # 删除按钮
            delete_btn = QPushButton("×")
            delete_btn.setFixedSize(12, 12)
            delete_btn.setMinimumSize(12, 12)
            delete_btn.setMaximumSize(12, 12)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffebee;
                    color: #c62828;
                    border: none;
                    border-radius: 6px;
                    font-size: 8px;
                    min-width: 12px;
                    max-width: 12px;
                    min-height: 12px;
                    max-height: 12px;
                    padding: 0px;
                    margin: 0px;
                }
                QPushButton:hover {
                    background-color: #ffcdd2;
                }
            """)
            delete_btn.clicked.connect(lambda _, c=card, l=stat_label: self.remove_sub_stat(c, l))
            
            stat_row_layout.addWidget(stat_label,stretch=9)
            stat_row_layout.addWidget(delete_btn, stretch=1)
            stat_row_layout.addStretch()
            
            # 插入到副属性区域布局中
            sub_stat_widget = card.layout().itemAt(3).widget()
            sub_stat_layout = sub_stat_widget.layout()
            sub_stat_layout.insertWidget(len(card.sub_stats), stat_row)
            card.sub_stats.append((stat_row, stat_label))
            
            # 如果已经有4个副属性，隐藏添加按钮
            if len(card.sub_stats) >= 4:
                card.add_sub_btn.hide()

    def show_sub_stat_dialog(self):
        """显示副属性选择弹窗"""
        dialog = QDialog(self)
        dialog.setWindowTitle("添加副属性")
        dialog.setFixedSize(300, 200)
        
        layout = QVBoxLayout(dialog)
        
        # 属性选择
        form_layout = QFormLayout()
        stat_combo = QComboBox()
        stat_combo.addItems(["攻击力%", "生命值%", "防御力%", "元素精通", 
                           "暴击率", "暴击伤害", "元素充能效率", "防御力",
                           "攻击力", "生命值"])
        form_layout.addRow("属性:", stat_combo)
        
        # 数值输入
        value_spin = QDoubleSpinBox()
        value_spin.setRange(0, 2000)
        value_spin.setDecimals(1)
        value_spin.setSingleStep(0.1)
        form_layout.addRow("数值:", value_spin)
        
        layout.addLayout(form_layout)
        
        # 确认按钮
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.setStyleSheet("""
            QPushButton {
                background-color: #4a6fa5;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #5a7fb5;
            }
        """)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)
        
        if dialog.exec() == QDialog.Accepted:
            stat = stat_combo.currentText()
            value = value_spin.value()
            return f"{stat}: {value:.1f}%"
        return None

    def edit_main_stat(self, card, slot):
        """编辑主属性"""
        if slot in ["生之花", "死之羽"]:
            # 固定主属性
            fixed_stats = {
                "生之花": "生命值",
                "死之羽": "攻击力"
            }
            dialog = QDialog(self)
            dialog.setWindowTitle(f"设置{slot}主属性")
            dialog.setFixedSize(300, 150)
            
            layout = QVBoxLayout(dialog)
            
            # 数值输入
            form_layout = QFormLayout()
            value_spin = QDoubleSpinBox()
            value_spin.setRange(0, 4780)
            if slot == "生之花":
                value_spin.setValue(4780)
            else:
                value_spin.setValue(311)
            value_spin.setDecimals(0)
            value_spin.setSingleStep(1)
            form_layout.addRow(f"{fixed_stats[slot]}:", value_spin)
            
            layout.addLayout(form_layout)
            
            # 确认按钮
            btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            btn_box.setStyleSheet("""
                QPushButton {
                    background-color: #4a6fa5;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 12px;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #5a7fb5;
                }
            """)
            btn_box.accepted.connect(dialog.accept)
            btn_box.rejected.connect(dialog.reject)
            layout.addWidget(btn_box)
            
            if dialog.exec() == QDialog.Accepted:
                value = value_spin.value()
                card.main_stat_btn.setText(f"{fixed_stats[slot]}: {value:.0f}")
        else:
            # 其他部位可选择属性
            dialog = QDialog(self)
            dialog.setWindowTitle(f"设置{slot}主属性")
            dialog.setFixedSize(300, 200)
            
            layout = QVBoxLayout(dialog)
            
            # 属性选择
            form_layout = QFormLayout()
            stat_combo = QComboBox()
            stat_combo.addItems(["攻击力%", "生命值%", "防御力%", "元素精通", 
                               "火元素伤害加成", "水元素伤害加成", "雷元素伤害加成",
                                "冰元素伤害加成", "岩元素伤害加成", "草元素伤害加成", "风元素伤害加成", 
                               "物理伤害加成", "治疗加成", "暴击率", "暴击伤害", "元素充能效率"])
            form_layout.addRow("属性:", stat_combo)
            
            # 数值输入
            value_spin = QDoubleSpinBox()
            value_spin.setRange(0, 200)
            value_spin.setDecimals(1)
            value_spin.setSingleStep(0.1)
            form_layout.addRow("数值:", value_spin)
            
            layout.addLayout(form_layout)
            
            # 确认按钮
            btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            btn_box.setStyleSheet("""
                QPushButton {
                    background-color: #4a6fa5;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 12px;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #5a7fb5;
                }
            """)
            btn_box.accepted.connect(dialog.accept)
            btn_box.rejected.connect(dialog.reject)
            layout.addWidget(btn_box)
            
            if dialog.exec() == QDialog.Accepted:
                stat = stat_combo.currentText()
                value = value_spin.value()
                card.main_stat_btn.setText(f"{stat}: {value:.1f}%")

    def remove_sub_stat(self, card, stat_label):
        """删除副属性"""
        for i, (row, label) in enumerate(card.sub_stats):
            if label == stat_label:
                # 从布局中移除
                sub_stat_widget = card.layout().itemAt(3).widget()
                sub_stat_layout = sub_stat_widget.layout()
                sub_stat_layout.removeWidget(row)
                row.deleteLater()
                
                # 从列表中移除
                card.sub_stats.pop(i)
                
                # 如果少于4个副属性，显示添加按钮
                if len(card.sub_stats) < 4:
                    card.add_sub_btn.show()
                break

    def show_name_dialog(self, card, slot):
        """显示名称设置弹窗"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"设置{slot}名称")
        dialog.setFixedSize(300, 200)
        
        layout = QVBoxLayout(dialog)
        
        # 名称选择
        form_layout = QFormLayout()
        name_combo = QComboBox()
        name_combo.addItems(list(ArtfactSetEffectDict.keys()))
        form_layout.addRow("套装名称:", name_combo)
        
        layout.addLayout(form_layout)
        
        # 确认按钮
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.setStyleSheet("""
            QPushButton {
                background-color: #4a6fa5;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #5a7fb5;
            }
        """)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)
        
        if dialog.exec() == QDialog.Accepted:
            card.layout().itemAt(1).widget().setText(name_combo.currentText())

    def load_data(self):
        # 加载角色数据
        self.char_combo.addItems(character_table.keys())
        
        # 加载武器数据（按类型分类）
        self.all_weapons = weapon_table.copy()  # 直接存储分类数据
        
        # 初始化默认武器列表
        first_char = self.char_combo.itemText(0)
        self.update_weapons(first_char)

    def update_weapons(self, char_name):
        """根据角色类型更新武器列表"""       
        # 获取角色武器类型
        weapon_type = character_table[char_name]["type"]
        
        # 获取对应类型武器列表
        available_weapons = self.all_weapons.get(weapon_type, [])
        
        # 更新武器下拉框
        current_selection = self.weapon_combo.currentText()
        self.weapon_combo.clear()
        self.weapon_combo.addItems(available_weapons)
        
        # 保留有效选择或重置
        if current_selection in available_weapons:
            self.weapon_combo.setCurrentText(current_selection)
        elif available_weapons:
            self.weapon_combo.setCurrentIndex(0)

        # 更新类型提示
        self.weapon_type_label.setText(weapon_type.capitalize())

    def reset(self):
        """重置所有数据"""
        # 重置角色数据
        self.char_combo.setCurrentIndex(0)
        self.level_spin.setValue(1)
        for i in [8,10,12]:  # 天赋spinbox
            spin = self.char_layout.itemAt(i).widget()
            if isinstance(spin, QSpinBox):
                spin.setValue(1)
        self.constellation_spin.setValue(0)
        
        # 重置武器数据
        self.weapon_combo.setCurrentIndex(0)
        self.weapon_level_spin.setValue(1)
        self.refinement_spin.setValue(1)
        
        # 重置圣遗物数据
        for card in self.artifact_cards:
            # 重置主属性
            card.main_stat_btn.setText("主属性")
            
            # 清除副属性
            sub_stat_widget = card.layout().itemAt(3).widget()
            for j in reversed(range(sub_stat_widget.layout().count() - 1)):
                item = sub_stat_widget.layout().itemAt(j)
                if item and item.widget():
                    item.widget().deleteLater()
            card.sub_stats.clear()
            card.add_sub_btn.show()

    def accept(self):
        """确认按钮点击事件"""
        self.result_data = self.get_character_data()
        self.finished.emit(self.result_data)
        super().accept()

    def get_character_data(self):
        """获取角色配置数据"""
        # 获取天赋spinbox的值
        talent_spins = []
        # 天赋spinbox位于char_layout中索引8,10,12的位置
        for i in [8,10,12]:
            spin = self.char_layout.itemAt(i).widget()
            if isinstance(spin, QSpinBox):
                talent_spins.append(str(spin.value()))
        
        data = {
            "character": {
                "id": character_table[self.char_combo.currentText()]["id"],
                "name": self.char_combo.currentText(),
                "level": self.level_spin.value(),
                "constellation": self.constellation_spin.value(),
                "talents": "/".join(talent_spins) if talent_spins else "0/0/0"
            },
            "weapon": {
                "name": self.weapon_combo.currentText(),
                "level": self.weapon_level_spin.value(),
                "refinement": self.refinement_spin.value()
            },
            "artifacts": []
        }

        # 收集圣遗物数据
        slots = ["生之花", "死之羽", "时之沙", "空之杯", "理之冠"]
        for i, card in enumerate(self.artifact_cards):
            if card.layout().itemAt(2).widget().text() == "主属性":
                state = {}
            else:
                s = card.layout().itemAt(2).widget().text().split(":")
                state = {s[0]: float(s[1].strip('%'))}
            artifact_data = {
                "slot": slots[i],
                "set_name": card.layout().itemAt(1).widget().text(),
                "main_stat": state,
                "sub_stats": {}
            }

            # 收集副属性
            sub_stat_widget = card.layout().itemAt(3).widget()
            for j in range(sub_stat_widget.layout().count() - 1):  # 排除添加按钮
                item = sub_stat_widget.layout().itemAt(j)
                if item and item.widget():
                    row = item.widget()
                    label = row.layout().itemAt(0).widget()
                    stat_text = label.text()
                    try:
                        stat_name, stat_value = stat_text.split(":") 
                        stat_value = stat_value.strip().replace('%','')
                        artifact_data["sub_stats"][stat_name.strip()] = float(stat_value)
                    except (ValueError, IndexError) as e:
                        print(f"解析副属性错误: {stat_text}, 错误: {str(e)}")


            data["artifacts"].append(artifact_data)

        return data

    def _update_ui_from_data(self):
        """根据数据更新UI界面"""
        data = self.result_data
        if not data:
            return
            
        try:
            # 更新角色信息
            char_data = data.get("character", {})
            if char_data:
                self.char_combo.setCurrentText(char_data.get("name", ""))
                self.level_spin.setValue(char_data.get("level", 1))
                
                # 设置天赋值
                talents = char_data.get("talents", "0/0/0").split("/")
                for i, val in enumerate(talents[:3]):
                    spin = self.char_layout.itemAt(8 + i*2).widget()
                    if isinstance(spin, QSpinBox):
                        spin.setValue(int(val))
                
                self.constellation_spin.setValue(char_data.get("constellation", 0))
            
            # 更新武器信息
            weapon_data = data.get("weapon", {})
            if weapon_data:
                self.weapon_combo.setCurrentText(weapon_data.get("name", ""))
                self.weapon_level_spin.setValue(weapon_data.get("level", 1))
                self.refinement_spin.setValue(weapon_data.get("refinement", 1))
            
            # 更新圣遗物信息
            artifacts_data = data.get("artifacts", [])
            for i, artifact in enumerate(artifacts_data[:5]):  # 最多5个圣遗物
                card = self.artifact_cards[i]
                
                # 设置套装名称
                name_label = card.layout().itemAt(1).widget()
                name_label.setText(artifact.get("set_name", ""))
                
                # 设置主属性
                main_stat = artifact.get("main_stat", {})
                if main_stat:
                    for stat, value in main_stat.items():
                        card.main_stat_btn.setText(f"{stat}: {value}%")
                
                # 清除现有副属性
                sub_stat_widget = card.layout().itemAt(3).widget()
                for j in reversed(range(sub_stat_widget.layout().count() - 1)):
                    item = sub_stat_widget.layout().itemAt(j)
                    if item and item.widget():
                        item.widget().deleteLater()
                card.sub_stats.clear()
                
                # 添加新副属性
                sub_stats = artifact.get("sub_stats", {})
                for stat, value in sub_stats.items():
                    # 创建副属性行
                    stat_row = QWidget()
                    stat_row_layout = QHBoxLayout(stat_row)
                    stat_row_layout.setContentsMargins(0, 0, 0, 0)
                    stat_row_layout.setSpacing(5)
                    
                    # 副属性标签
                    # 统一副属性显示格式
                    if stat in ["攻击力%", "生命值%", "防御力%", "暴击率", "暴击伤害", "元素充能效率"]:
                        stat_label = QLabel(f"{stat}: {value}%")
                    else:
                        stat_label = QLabel(f"{stat}: {value}")
                    stat_label.setStyleSheet("""
                        font-size: 12px;
                        color: #6c757d;
                        border: 0px solid #ced4da;
                    """)
                    stat_label.setAlignment(Qt.AlignLeft)
                    
                    delete_btn = QPushButton("×")
                    delete_btn.setFixedSize(12, 12)
                    delete_btn.setMinimumSize(12, 12)
                    delete_btn.setMaximumSize(12, 12)
                    delete_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #ffebee;
                            color: #c62828;
                            border: none;
                            border-radius: 6px;
                            font-size: 8px;
                            min-width: 12px;
                            max-width: 12px;
                            min-height: 12px;
                            max-height: 12px;
                            padding: 0px;
                            margin: 0px;
                        }
                        QPushButton:hover {
                            background-color: #ffcdd2;
                        }
                    """)
                    delete_btn.clicked.connect(lambda _, c=card, l=stat_label: self.remove_sub_stat(c, l))
                    
                    stat_row_layout.addWidget(stat_label, stretch=9)
                    stat_row_layout.addWidget(delete_btn, stretch=1)
                    stat_row_layout.addStretch()
                    
                    # 添加到副属性区域
                    sub_stat_layout = sub_stat_widget.layout()
                    sub_stat_layout.insertWidget(len(card.sub_stats), stat_row)
                    card.sub_stats.append((stat_row, stat_label))
                
                # 根据副属性数量显示/隐藏添加按钮
                card.add_sub_btn.setVisible(len(card.sub_stats) < 4)
                
        except Exception as e:
            print(f"更新UI时出错: {str(e)}")
