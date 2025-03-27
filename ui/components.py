from PySide6.QtWidgets import (QFrame, QVBoxLayout, QLabel, QComboBox, QPushButton,
                               QVBoxLayout,QSizePolicy, QWidget)
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
        self.setFixedWidth(180)  # 调整卡片大小
        
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

        self.setSizePolicy(
            QSizePolicy.Policy.Fixed,  # 水平方向固定宽度（已设置 setFixedWidth(180)）
            QSizePolicy.Policy.Expanding  # 垂直方向尽可能扩展
        )
        
        # 角色名称
        self.char_label = QLabel("角色: 未设置")
        layout.addWidget(self.char_label)
        
        # 动作  
        self.action_label = QLabel("动作: 未设置")
        layout.addWidget(self.action_label)
        
        # 参数区域
        self.param_widget = QWidget()
        self.param_layout = QVBoxLayout(self.param_widget)
        self.param_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.param_widget)
        
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
                padding: 2px;
            }
            QPushButton:hover {
                color: white;
                background-color: #ef4444;
            }
        """)
        delete_btn.clicked.connect(self._delete_self)
        layout.addWidget(delete_btn)
        
    def update_data(self, data):
        """更新卡片数据"""
        self.char_label.setText(f"角色: {data.get('character', '未设置')}")
        self.action_label.setText(f"动作: {data.get('action', '未设置')}")
        
        # 清空现有参数
        while self.param_layout.count():
            item = self.param_layout.takeAt(0)
            if item.widget():
                widget = item.widget()
                widget.setParent(None)
                widget.deleteLater()
        
        # 添加参数显示
        params = data.get('params', {})
        if params:
            for name, value in params.items():
                param_label = QLabel(f"{name}: {value}", self.param_widget)
                param_label.setObjectName(f"param_label_{name}")  # 设置唯一对象名称
                self.param_layout.addWidget(param_label)
        else:
            no_params = QLabel("无特殊参数", self.param_widget)
            no_params.setObjectName("no_params_label")
            self.param_layout.addWidget(no_params)

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
