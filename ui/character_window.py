from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                              QLabel, QPushButton, QComboBox, QSpinBox, QCompleter,
                              QListWidget, QFormLayout, QTabWidget, QFrame,
                              QDialog, QDialogButtonBox, QDoubleSpinBox)
from PySide6.QtCore import Qt

class CharacterWindow(QWidget):
    """角色信息设置窗口"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("角色配置")
        self.setMinimumSize(800, 500)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setWindowFlags(Qt.Window)
        self.setStyleSheet("""
            background-color: white;
            border-radius: 6px;
        """)
        self.init_ui()
        self.load_demo_data()

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
        char_layout = QHBoxLayout(char_frame)
        char_layout.setContentsMargins(10, 5, 10, 5)
        char_layout.setSpacing(5)
        char_layout.addWidget(QWidget(), stretch=1)
        
        # 头像区域
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(60, 60)
        self.avatar_label.setStyleSheet("""
            background-color: #f0f0f0;
            border-radius: 30px;
        """)
        char_layout.addWidget(self.avatar_label, stretch=2)
        
        # 角色名称
        self.char_combo = QComboBox()
        self.char_combo.setEditable(True)
        self.char_combo.setFixedWidth(120)
        self.char_combo.completer().setCompletionMode(QCompleter.PopupCompletion)
        char_layout.addWidget(self.char_combo, stretch=1)
        char_layout.addWidget(QWidget(), stretch=1)

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
        char_layout.addWidget(QLabel("等级:", styleSheet="color: #333;"))
        char_layout.addWidget(self.level_spin, stretch=1)
        char_layout.addWidget(QWidget(), stretch=1)
        
        # 天赋
        char_layout.addWidget(QLabel("天赋:", styleSheet="color: #333;"))
        for i in range(3):
            spin = QSpinBox()
            spin.setRange(1, 15)
            spin.setFixedWidth(15)
            spin.setStyleSheet("""
                QSpinBox::up-button, 
                QSpinBox::down-button {
                    width: 0px;
                    height: 0px;
                }
            """)
            char_layout.addWidget(spin, stretch=1)
            if i < 2:
                char_layout.addWidget(QLabel("/", styleSheet="color: #333;"))
        char_layout.addWidget(QWidget(), stretch=1)
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
        char_layout.addWidget(QLabel("命座:", styleSheet="color: #333;"))
        char_layout.addWidget(self.constellation_spin,stretch=1)
        char_layout.addWidget(QWidget(), stretch=1)
        
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
        confirm_btn.clicked.connect(self.close)

        main_layout.addWidget(confirm_btn, stretch=1)
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
                           "暴击率", "暴击伤害", "元素充能效率"])
        form_layout.addRow("属性:", stat_combo)
        
        # 数值输入
        value_spin = QDoubleSpinBox()
        value_spin.setRange(0, 100)
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
            value_spin.setRange(0, 1000)
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
                               "元素伤害加成", "物理伤害加成", "治疗加成", "暴击率", "暴击伤害"])
            form_layout.addRow("属性:", stat_combo)
            
            # 数值输入
            value_spin = QDoubleSpinBox()
            value_spin.setRange(0, 100)
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

    def load_demo_data(self):
        # 模拟后端数据
        characters = ["雷电将军", "钟离", "甘雨", "胡桃", "枫原万叶"] * 5
        self.char_combo.addItems(characters)
        
        # 武器数据
        weapons = ["天空之脊", "护摩之杖", "终末嗟叹之诗"] * 6
        self.weapon_combo.addItems(weapons)
