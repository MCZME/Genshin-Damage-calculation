from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QProgressBar, QSizePolicy)
from PySide6.QtCore import Qt

class TargetStatusWidget(QWidget):
    """目标状态显示组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_styles()
        
    def setup_ui(self):
        """初始化UI布局"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(20)

        self.setProperty("class", "TargetStatusWidget")
        
        # 头部区域
        header = QWidget()
        header.setProperty("class", "TargetStatusWidgetRow")
        self.header_layout = QHBoxLayout(header)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.header_layout.setSpacing(20)
        
        self.target_name = QLabel("加载中...")
        self.target_name.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        self.stats_layout = QHBoxLayout()
        self.stats_layout.setSpacing(20)
        self.stats_layout.setContentsMargins(0,0,0,5)
        
        self.resistance_layout = QHBoxLayout()
        self.resistance_layout.setSpacing(12)
        
        self.defense_badge = QLabel("0")
        self.defense_badge.setFixedHeight(40)
        self.defense_badge.setAlignment(Qt.AlignCenter)
        
        self.header_layout.addWidget(self.target_name)
        self.header_layout.addLayout(self.stats_layout)
        self.stats_layout.addLayout(self.resistance_layout)
        self.stats_layout.addWidget(self.defense_badge)
        
        # 元素附着区域
        row1 = QWidget()
        row1.setProperty("class", "TargetStatusWidgetRow")
        self.aura_layout = QHBoxLayout(row1)
        self.aura_layout.setSpacing(10)
        
        self.aura_label = QLabel("元素附着:")
        self.aura_label.setStyleSheet("font-size: 16px;")
        self.aura_tags_layout = QHBoxLayout()
        self.aura_tags_layout.setSpacing(8)
        self.aura_tags_layout.setAlignment(Qt.AlignLeft)
        
        self.aura_layout.addWidget(self.aura_label,1)
        self.aura_layout.addLayout(self.aura_tags_layout,9)
        
        # 状态效果区域
        row2 = QWidget()
        row2.setProperty("class", "TargetStatusWidgetRow")
        self.effects_layout = QVBoxLayout(row2)
        self.effects_layout.setSpacing(12)
        
        self.effects_title = QLabel("效果:")
        self.effects_title.setStyleSheet("font-size: 16px;")
        self.effects_scroll_layout = QHBoxLayout()
        self.effects_scroll_layout.setSpacing(12)
        self.effects_scroll_layout.setAlignment(Qt.AlignLeft)
        
        self.effects_layout.addWidget(self.effects_title)
        self.effects_layout.addLayout(self.effects_scroll_layout)
        
        # 添加到主布局
        self.main_layout.addWidget(header)
        self.main_layout.addWidget(row1)
        self.main_layout.addWidget(row2)
        
    def setup_styles(self):
        """设置组件样式"""
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        # 主面板样式
        self.setStyleSheet("""
            QWidget.TargetStatusWidget{
            background-color: #ffffff;
            color: #333333;
            border-radius: 16px;
            border: 1px solid #e0e0e0;
            }
            QWidget.TargetStatusWidgetRow{
                border-bottom: 2px solid #e0e0e0;
            }
        """)
        
        # 目标名称样式
        self.target_name.setStyleSheet("""
            font-size: 28px;
            font-weight: 600;
            color: #4a6baf;
        """)
        
        # 防御力徽章样式
        self.defense_badge.setStyleSheet("""
            background-color: #f5f5f5;
            padding: 8px 16px;
            font-weight: 500;
            color: #333333;
            border: 1px solid #e0e0e0;
        """)

    def set_data(self, data):
        """设置目标数据"""
        self.target_data = data
        self.update_frame()

    def update_frame(self, frame=1):
        """更新显示"""
        data = self.target_data[frame]

        if not hasattr(self, 'target_data'):
            return

        # 更新基础信息
        self.target_name.setText(data.get('name', '未知目标'))
        self.defense_badge.setText('防御力：' + str(data.get('defense', 0)))

        # 清空现有抗性显示
        while self.resistance_layout.count():
            child = self.resistance_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # 添加抗性显示
        resistance = data.get('resistance', {})
        for element, value in resistance.items():
            if value != 0:
                label = QLabel(f"{'+' if value > 0 else ''}{int(value)}%")
                label.setToolTip(f"{element}抗性")
                label.setStyleSheet(f"""
                    color: {self.get_element_color(element)};
                    font-weight: 600;
                    font-size: 14px;
                """)
                self.resistance_layout.addWidget(label)

        # 更新元素附着
        while self.aura_tags_layout.count():
            child = self.aura_tags_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for aura in data.get('elemental_aura', []):
            element = aura.get('element', '').lower()
            amount = aura.get('amount', 0)
            label = QLabel(f"{element}（{amount:.1f}）")
            label.setMaximumWidth(100)
            label.setStyleSheet(f"""
                background-color: {self.get_element_color(element)};
                color: white;
                padding: 4px 12px;
                border-radius: 16px;
                font-size: 14px;
                font-weight: 500;
                border: 1px solid rgba(0,0,0,0.1);
            """)
            self.aura_tags_layout.addWidget(label)

        # 更新状态效果
        while self.effects_scroll_layout.count():
            child = self.effects_scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for name, effect in data.get('effect', {}).items():
            effect_widget = EffectDisplayWidget(
                name=name,
                duration=effect['duration'],
                max_duration=effect['max_duration']
            )
            self.effects_scroll_layout.addWidget(effect_widget)
    
    def get_element_color(self, element):
        """获取元素对应颜色"""
        colors = {
            "火": "#ff5722",
            "水": "#2196f3",
            "雷": "#9c27b0",
            "草": "#8bc34a",
            "冰": "#00bcd4",
            "岩": "#ffc107",
            "风": "#4caf50",
            "物理": "#9e9e9e",
            '燃': '#ff5722',
            '激': '#8bc34a',
        }
        return colors.get(element.lower(), "#ffffff")

class EffectDisplayWidget(QWidget):
    """效果持续时间显示组件"""
    def __init__(self, name="", duration=0, max_duration=0, parent=None):
        super().__init__(parent)
        self.name = name
        self.setFixedHeight(24)
        self.setMaximumWidth(144)
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
                background-color: rgba(176,196,222,0.5)              
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

