from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QComboBox, QPushButton, QFormLayout, QSpinBox, QWidget)
from PySide6.QtCore import Qt, Signal

class ActionSettingDialog(QDialog):
    """动作设置对话框"""
    setting_completed = Signal(dict)  # 参数: {"character": str, "action": str, "params": dict}

    # 合法动作键与中文名称映射
    ACTION_MAP = {
        "normalAttack": "普通攻击",
        "chargedAttack": "重击",
        "plungingAttack": "下落攻击",
        "skill": "元素战技",
        "burst": "元素爆发",
        'skip': '跳过',
        'dash': '冲刺',
        'jump': '跳跃'
    }

    def __init__(self, character_data: dict, parent=None):
        super().__init__(parent)
        self.character_data = character_data
        self.setWindowTitle("动作设置")
        self.setMinimumWidth(300)
        
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # 表单布局
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)
        
        # 角色选择
        self.char_combo = QComboBox()
        self.char_combo.addItems(self.character_data.keys())
        self.char_combo.currentTextChanged.connect(self._update_actions)
        form_layout.addRow("角色:", self.char_combo)
        
        # 动作选择
        self.action_combo = QComboBox()
        self.action_combo.currentTextChanged.connect(self._setup_params)
        form_layout.addRow("动作:", self.action_combo)
        
        # 参数区域
        self.param_widget = QWidget()
        self.param_layout = QVBoxLayout(self.param_widget)
        form_layout.addRow("参数:", self.param_widget)
        
        main_layout.addLayout(form_layout)
        
        # 初始化默认值
        self._update_actions()
        
        # 按钮区域
        button_layout = QHBoxLayout()
        confirm_btn = QPushButton("确定")
        confirm_btn.clicked.connect(self._confirm)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(confirm_btn)
        button_layout.addWidget(cancel_btn)
        main_layout.addLayout(button_layout)

    def _update_actions(self):
        """更新动作列表（过滤合法动作）"""
        current_char = self.char_combo.currentText()
        char_actions = self.character_data.get(current_char, {})
        
        # 过滤出合法动作键并转换中文显示
        valid_actions = [self.ACTION_MAP[k] for k in char_actions.keys() if k in self.ACTION_MAP]
        self.action_combo.clear()
        self.action_combo.addItems(valid_actions)
        self._setup_params()

    def _setup_params(self):
        """根据参数结构生成输入控件"""
        # 清空旧控件
        while self.param_layout.count():
            item = self.param_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        current_char = self.char_combo.currentText()
        current_action_cn = self.action_combo.currentText()
        
        # 反向查找动作键
        action_key = next((k for k, v in self.ACTION_MAP.items() if v == current_action_cn), None)
        if not action_key or current_char not in self.character_data:
            return
            
        # 获取参数配置字典 {描述: 值}
        params_dict = self.character_data[current_char].get(action_key, {})
        
        # 动态生成控件
        if not params_dict:
            widget = QLabel("没有特殊参数")
            self.param_layout.addWidget(widget)
        else:
            for desc, value in params_dict.items():
                self.param_layout.addWidget(QLabel(f"{desc}:"))
                
                # 数字类型（最大值约束）
                if isinstance(value, (int, float)):
                    widget = QSpinBox()
                    widget.setMaximum(int(value))
                    widget.setMinimum(0)
                    widget.setValue(int(value))  # 默认设为最大值
                    
                # 列表类型（选项约束）
                elif isinstance(value, list):
                    widget = QComboBox()
                    widget.addItems(value)
                    
                else:
                    widget = QLabel("不支持的参数类型")
                
                self.param_layout.addWidget(widget)

    def _confirm(self):
        """确认设置"""
        if not self.char_combo.currentText():
            return
            
        # 收集参数值
        params = {}
        for i in range(self.param_layout.count()):
            widget = self.param_layout.itemAt(i).widget()
            if isinstance(widget, QSpinBox):
                label = self.param_layout.itemAt(i-1).widget().text().replace(":", "")
                params[label] = widget.value()
            elif isinstance(widget, QComboBox):
                label = self.param_layout.itemAt(i-1).widget().text().replace(":", "")
                params[label] = widget.currentText()
                
        data = {
            "character": self.char_combo.currentText(),
            "action": self.action_combo.currentText(),
            "params": params
        }
        self.setting_completed.emit(data)
        self.accept()
