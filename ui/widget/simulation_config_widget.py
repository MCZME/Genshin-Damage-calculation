import json
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, 
                              QPushButton, QSpinBox, QWidget,
                              QDialog, QVBoxLayout, QTextEdit,
                              QDialogButtonBox, QMessageBox,
                              QTableWidget, QTableWidgetItem,
                              QCheckBox, QComboBox)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
from core.Config import Config
                              
class ConfigEditorDialog(QDialog):
    """配置编辑器对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("配置编辑器")
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)

        self.setStyleSheet("""
            QComboBox[noDropdown="true"] {
                border: 0px solid #d1d5db;
                border-radius: 0px;
                background-color: white;
                padding: 6px 10px;
            }
            QComboBox[noDropdown="true"]::drop-down {
                width: 0px !important;
                border: none !important;
            }
            QComboBox[noDropdown="true"]::down-arrow {
                image: none !important;
            }
        """)
        
        # 配置表格
        self.config_table = QTableWidget()
        self.config_table.setColumnCount(3)
        self.config_table.setHorizontalHeaderLabels(["配置项", "值", "描述"])
        self.config_table.setColumnWidth(0, 200)  # 配置项列宽
        self.config_table.setColumnWidth(1, 250)  # 值列宽 
        self.config_table.setColumnWidth(2, 300)  # 描述列宽
        self.config_table.verticalHeader().setVisible(False)
        self.config_table.verticalHeader().setDefaultSectionSize(30)
        self.config_table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self._populate_config_table()
        layout.addWidget(self.config_table)
        
        # 按钮框
        button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.save_config)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _populate_config_table(self):
        """填充配置表格"""
        config = Config().config
        self.config_table.setColumnCount(3)
        self.config_table.setHorizontalHeaderLabels(["配置项", "值", "描述"])
        
        # 添加分组标题
        def add_section(title):
            row = self.config_table.rowCount()
            self.config_table.insertRow(row)
            item = QTableWidgetItem(title)
            item.setBackground(QColor("#e2e8f0"))
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            self.config_table.setItem(row, 0, item)
            self.config_table.setSpan(row, 0, 1, 3)
        
        # 添加只读信息
        def add_info_row(key, value):
            row = self.config_table.rowCount()
            self.config_table.insertRow(row)
            item = QTableWidgetItem(key)
            item.setTextAlignment(Qt.AlignCenter)
            self.config_table.setItem(row, 0, item)
            item = QTableWidgetItem(str(value))
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.config_table.setItem(row, 1, item)
            
            # 添加描述项
            desc_text = {
                "name": "项目名称",
                "version": "项目版本号", 
                "author": "项目作者",
                "description": "项目描述信息",
                "last_save_file": "上次保存的文件路径",
                "character_file_path": "角色数据文件路径",
                "artifact_file_path": "圣遗物数据文件路径",
                "batch_sim_file_path": "批量模拟文件路径",
            }.get(key, "")
            desc = QTableWidgetItem(desc_text)
            desc.setTextAlignment(Qt.AlignCenter)
            self.config_table.setItem(row, 2, desc)
        
        # 添加数值型配置项
        def add_num_row(key, value, full_key, min_val=0, max_val=100):
            row = self.config_table.rowCount()
            self.config_table.insertRow(row)
            item = QTableWidgetItem(key)
            item.setTextAlignment(Qt.AlignCenter)
            self.config_table.setItem(row, 0, item)
            
            spin = QSpinBox()
            spin.setRange(min_val, max_val)
            spin.setValue(value)
            spin.setProperty("config_key", full_key)
            self.config_table.setCellWidget(row, 1, spin)
            
            # 添加描述项
            desc_text = {
                "batch_sim_processes": "批量模拟线程数",
                "batch_sim_num": "每个线程的模拟次数"
            }.get(key, "")
            desc = QTableWidgetItem(desc_text)
            desc.setTextAlignment(Qt.AlignCenter)
            self.config_table.setItem(row, 2, desc)

        # 添加可编辑布尔项
        def add_bool_row(key, value, full_key):
            row = self.config_table.rowCount()
            self.config_table.insertRow(row)
            item = QTableWidgetItem(key)
            item.setTextAlignment(Qt.AlignCenter)
            self.config_table.setItem(row, 0, item)
            
            combo = QComboBox()
            combo.addItem("False")
            combo.addItem("True")
            combo.setCurrentIndex(1 if value else 0)
            combo.setProperty("config_key", full_key)
            combo.setProperty("noDropdown", 'true')
            
            def update_color(index):
                if index == 0:
                    combo.setStyleSheet("color: #ff0000;")
                else:
                    combo.setStyleSheet("color: #0000ff;")
            
            combo.currentIndexChanged.connect(update_color)
            update_color(combo.currentIndex())
            
            self.config_table.setCellWidget(row, 1, combo)
            
            # 添加描述项
            desc_text = {
                "open_critical": "是否开启暴击模拟",
                "save_file": "是否保存日志到文件",
                "damage": "是否记录伤害日志",
                "heal": "是否记录治疗日志", 
                "energy": "是否记录能量日志",
                "effect": "是否记录效果日志",
                "reaction": "是否记录元素反应日志",
                "object": "是否记录对象日志",
                "debug": "是否记录调试日志",
                "button_click": "是否记录按钮点击日志",
                "window_open": "是否记录窗口打开日志",
                "batch_sim": "是否开启批量模拟",
                "console": "是否开启控制台输出",
            }.get(key, "")
            desc = QTableWidgetItem(desc_text)
            desc.setTextAlignment(Qt.AlignCenter)
            self.config_table.setItem(row, 2, desc)
        
        def add_text_row(key, value):
            row = self.config_table.rowCount()
            self.config_table.insertRow(row)
            item = QTableWidgetItem(key)
            item.setTextAlignment(Qt.AlignCenter)
            self.config_table.setItem(row, 0, item)
            
            text_edit = QTextEdit()
            text_edit.setPlainText(value)
            text_edit.setProperty("config_key", key)
            self.config_table.setCellWidget(row, 1, text_edit)
            
            # 添加描述项
            desc_text = {
                "name": "配队名称",
            }.get(key, "")
            desc = QTableWidgetItem(desc_text)
            desc.setTextAlignment(Qt.AlignCenter)
            self.config_table.setItem(row, 2, desc)

        # 填充表格内容
        add_section("项目信息")
        for key, value in config["project"].items():
            add_info_row(key, value)
        
        add_section("模拟设置")
        for key, value in config["emulation"].items():
            add_bool_row(key, value, f"emulation.{key}")

        add_section("批量模拟设置")
        for key, value in config["batch"].items():
            if key in ["batch_sim_processes", "batch_sim_num"]:
                add_num_row(key, value, f"batch.{key}", 1, 100)
            elif key in ["batch_sim_file_path"]:
                add_info_row(key, value)
            elif key in ['name']:
                add_text_row(key, value)
            else:
                add_bool_row(key, value, f"batch.{key}")
        
        add_section("界面设置")
        for key, value in config["ui"].items():
            add_info_row(key, value)
        
        add_section("日志设置")
        add_bool_row("保存日志文件", config["logging"]["save_file"], "logging.save_file")
        
        add_section("模拟日志")
        for key, value in config["logging"]["Emulation"].items():
            if key != "file_path":
                add_bool_row(key, value, f"logging.Emulation.{key}")
        
        add_section("界面日志")
        for key, value in config["logging"]["UI"].items():
            if key != "file_path":
                add_bool_row(key, value, f"logging.UI.{key}")
    
    def save_config(self):
        """保存配置"""
        config = Config().config.copy()
        
        for row in range(self.config_table.rowCount()):
            widget = self.config_table.cellWidget(row, 1)
            if isinstance(widget, QComboBox):
                key = widget.property("config_key")
                value = widget.currentIndex() == 1
                keys = key.split(".")
                current = config
                for k in keys[:-1]:
                    current = current[k]
                current[keys[-1]] = value
            elif isinstance(widget, QSpinBox):
                key = widget.property("config_key")
                value = widget.value()
                keys = key.split(".")
                current = config
                for k in keys[:-1]:
                    current = current[k]
                current[keys[-1]] = value
        
        Config.config = config
        Config.save()
        self.accept()

class SimulationConfigWidget(QFrame):
    """模拟参数配置组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            SimulationConfigWidget {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                background-color: white;
                padding: 12px;
                margin: 4px;
            }
            QLabel {
                font-size: 13px;
                margin-right: 8px;
                color: #4a5568;
                font-weight: 500;
            }
            QSpinBox {
                font-size: 13px;
                padding: 4px;
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                text-align: center;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 0px;
            }
            QPushButton {
                min-width: 90px;
                font-size: 13px;
                padding: 6px 12px;
                background-color: #4299e1;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #3182ce;
            }
            QToolTip {
                font-size: 12px;
                padding: 6px;
                border-radius: 4px;
                opacity: 240;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addStretch()
        
        # 目标等级
        level_label = QLabel("目标等级:")
        self.level_spin = QSpinBox()
        self.level_spin.setRange(1, 200)
        self.level_spin.setValue(90)
        layout.addWidget(level_label)
        layout.addWidget(self.level_spin)
        layout.addStretch()
        
        # 元素抗性配置
        element_colors = {
            "火": "#ff0000",    # 红
            "水": "#0000ff",    # 蓝
            "草": "#00aa00",    # 绿
            "岩": "#aa5500",    # 棕
            "冰": "#00aaff",    # 浅蓝
            "风": "#00ffff",    # 青
            "雷": "#aa00ff",    # 紫
            "物理": "#888888"   # 灰
        }
        
        for element, color in element_colors.items():
            # 抗性数值输入
            resist_spin = QSpinBox()
            resist_spin.setFixedWidth(65)
            resist_spin.setRange(-100, 1000)
            resist_spin.setValue(10)
            resist_spin.setSuffix("%")
            resist_spin.setObjectName(f"{element}_resist_spin")
            resist_spin.setToolTip(f"""<span style='color:{color}; font-weight:bold'>{element}元素抗性</span>""")
            resist_spin.setStyleSheet(f"""
                QSpinBox {{
                    color: {color};
                    margin-right: 8px;
                    text-align: center;
                }}
                QSpinBox:hover {{
                    border: 1px solid {color};
                    background-color: rgba{(*QColor(color).getRgb()[:3], 0.1)};
                }}
            """)
            layout.addWidget(resist_spin)
            
            setattr(self, f"{element}_resist_spin", resist_spin)
        
        layout.addStretch()
        # 右侧按钮
        self.action_button = QPushButton("模拟配置")
        self.action_button.clicked.connect(self.show_config_dialog)
        layout.addWidget(self.action_button)
        layout.addStretch()

    def show_config_dialog(self):
        """显示配置对话框"""
        dialog = ConfigEditorDialog(self)
        dialog.exec()
        
    def set_config(self, config):
        """设置配置"""
        self.level_spin.setValue(config.get("level", 90))
        
        elements = ["火", "水", "草", "岩", "冰", "风", "雷", "物理"]
        for element in elements:
            spin = getattr(self, f"{element}_resist_spin")
            resist = config.get("resists", {}).get(element, "10")
            spin.setValue(int(resist))

    def get_target_data(self):
        """获取目标数据（等级和抗性）
        
        返回:
            dict: 包含目标等级和各元素抗性的字典
        """
        elements = ["火", "水", "草", "岩", "冰", "风", "雷", "物理"]
        resists = {}
        for element in elements:
            spin = getattr(self, f"{element}_resist_spin")
            resists[element] = int(spin.value())
            
        return {
            "level": self.level_spin.value(),
            "resists": resists
        }
