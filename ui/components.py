from PySide6.QtWidgets import (QFrame, QVBoxLayout, QLabel, QComboBox, QPushButton,
                               QVBoxLayout)
from random import choice

class ActionCard(QFrame):
    """动作卡片组件"""
    COLORS = [
        "#FFEBEE", "#F3E5F5", "#E8EAF6", 
        "#E3F2FD", "#E0F7FA", "#E8F5E9",
        "#FFF8E1", "#FBE9E7", "#EFEBE9"
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedSize(160, 140)  # 调整卡片大小
        
        # 随机选择颜色
        bg_color = choice(self.COLORS)
        
        self.setStyleSheet(f"""
            ActionCard {{
                border: 1px solid #d1d5db;
                border-radius: 4px;
                background-color: {bg_color};
                padding: 8px;
            }}
            QComboBox {{
                min-width: 120px;
                width: 120px;
                font-size: 12px;
                margin-bottom: 5px;
            }}
            QLabel {{
                font-size: 12px;
                margin-bottom: 2px;
            }}""")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # 动作标签和下拉框
        action_label = QLabel("动作:")
        layout.addWidget(action_label)
        self.action_combo = QComboBox()
        self.action_combo.addItems(["普通攻击", "元素战技", "元素爆发"])
        layout.addWidget(self.action_combo)
        
        # 角色标签和下拉框
        char_label = QLabel("角色:")
        layout.addWidget(char_label)
        self.char_combo = QComboBox()
        self.char_combo.addItems(["角色1", "角色2", "角色3", "角色4"])
        layout.addWidget(self.char_combo)
        
        # 删除按钮
        delete_btn = QPushButton("删除")
        delete_btn.setFixedHeight(24)
        delete_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #ef4444;
                color: #ef4444;
                font-size: 12px;
                border-radius: 4px;
                background-color: white;
            }
            QPushButton:hover {
                color: white;
                background-color: #ef4444;
            }
        """)
        delete_btn.clicked.connect(self._delete_self)
        layout.addWidget(delete_btn)
        
    def _delete_self(self):
        """删除当前卡片"""
        print(f"正在删除卡片: {self}")  # 调试用
        
        # 查找action_container
        container = None
        parent = self.parent()
        while parent:
            print(f"检查父容器: {parent}, 类: {parent.__class__.__name__}")
            if hasattr(parent, 'action_container_layout'):
                container = parent
                break
            parent = parent.parent()
        
        if not container:
            print("错误: 无法找到action_container")
            return
            
        print(f"找到容器: {container}")
        layout = container.action_container_layout
        
        # 删除当前卡片
        layout.removeWidget(self)
        self.setParent(None)
        self.deleteLater()
        
        # 检查是否还有卡片
        has_cards = any(
            isinstance(layout.itemAt(i).widget(), ActionCard)
            for i in range(layout.count())
        )
        
        print(f"剩余卡片: {has_cards}")  # 调试用
        
        # 如果没有卡片了，显示提示
        if not has_cards and hasattr(container, 'hint_container'):
            print("显示初始提示")
            container.hint_container.setVisible(True)
