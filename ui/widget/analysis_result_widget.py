from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt

class AnalysisResultWidget(QWidget):
    """数据分析结果组件"""
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("""
            QWidget {
                background: transparent;
                border: none;
            }
            QWidget.AnalysisResult {
                background: #F8F9FA;
                border-top: 1px solid #ddd;
                border-bottom: 1px solid #ddd;
            }
            QLabel {
                font-family: 'Helvetica Neue', Arial, sans-serif;
            }
            QLabel.metric-label {
                font-size: 14px;
                font-weight: 500;
                color: #7F8C8D;
                margin-bottom: 12px;
            }
            QLabel.value {
                font-weight: 700;
                color: #2C3E50;
                margin: 8px 0;
            }
            QLabel.small {
                font-size: 13px;
                color: #7F8C8D;
                margin-top: 8px;
            }
            QWidget.card {
                background: white;
                border-radius: 12px;
                padding: 20px 15px;
                min-height: 80px;
            }
            QWidget.max-hit {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 white, stop:1 rgba(255, 209, 102, 0.08));
                border: 1px solid rgba(255, 209, 102, 0.3);
            }
            QWidget.max-hit QLabel.value { color: #FFD166; }
            QWidget.max-hit QLabel.small { color: #FFD166; }
            
            QWidget.total-dmg {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 white, stop:1 rgba(77, 159, 255, 0.08));
                border: 1px solid rgba(77, 159, 255, 0.3);
            }
            QWidget.total-dmg QLabel.value { color: #4D9FFF; }
            QWidget.total-dmg QLabel.small { color: #4D9FFF; }
            
            QWidget.dps {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 white, stop:1 rgba(255, 77, 109, 0.08));
                border: 2px solid #FF4D6D;
            }
            QWidget.dps QLabel.value { color: #FF4D6D; }
            
            QWidget.duration {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 white, stop:1 rgba(46, 216, 163, 0.08));
                border: 1px solid rgba(46, 216, 163, 0.3);
            }
            QWidget.duration QLabel.value { color: #2ED8A3; }
            QWidget.duration QLabel.small { color: #2ED8A3; }
            
            QWidget.crit {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 white, stop:1 rgba(179, 136, 255, 0.08));
                border: 1px solid rgba(179, 136, 255, 0.3);
            }
            QWidget.crit QLabel.value { color: #B388FF; }
            QWidget.crit QLabel.small { color: #B388FF; }
        """)
        
        self.setProperty("class", "AnalysisResult")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(50, 10, 50, 10)
        layout.setSpacing(8)
        
        # 最大伤害卡片
        self.max_hit_card = self._create_card("max-hit", "最大伤害", "0", "0秒前")
        layout.addWidget(self.max_hit_card, 3)
        
        # 总伤害卡片
        self.total_damage_card = self._create_card("total-dmg", "总伤害", "0", "▲0%")
        layout.addWidget(self.total_damage_card, 4)
        
        # DPS卡片
        self.dps_card = self._create_card("dps", "每秒伤害", "0", "峰值: 0")
        layout.addWidget(self.dps_card, 5)
        
        # 持续时间卡片
        self.duration_card = self._create_card("duration", "持续时间", "00:00", "进行中")
        layout.addWidget(self.duration_card, 4)
        
        # 暴击比率卡片
        self.crit_card = self._create_card("crit", "暴击比率", "0%", "▼0%")
        layout.addWidget(self.crit_card, 3)
        
    def _create_card(self, card_type, label, value, small_text):
        """创建指标卡片"""
        card = QWidget()
        card.setProperty("class", f"card {card_type}")
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 指标标签
        label_widget = QLabel(label)
        label_widget.setProperty("class", "metric-label")
        label_widget.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_widget)
        
        # 指标值
        value_widget = QLabel(value)
        value_widget.setProperty("class", "value")
        value_widget.setAlignment(Qt.AlignCenter)
        
        # 根据卡片类型设置字体大小
        if card_type == "max-hit" or card_type == "crit":
            value_widget.setStyleSheet("font-size: 20px;")
        elif card_type == "total-dmg" or card_type == "duration":
            value_widget.setStyleSheet("font-size: 24px;")
        else:  # dps
            value_widget.setStyleSheet("font-size: 28px;")
            
        layout.addWidget(value_widget)
        
        # 辅助文本
        small_widget = QLabel(small_text)
        small_widget.setProperty("class", "small")
        small_widget.setAlignment(Qt.AlignCenter)
        layout.addWidget(small_widget)
        
        return card
        
    def set_data(self, data):
        """设置分析数据"""
        # 更新所有卡片数据
        cards = [
            (self.max_hit_card, "最大伤害", data.get("最大伤害", 0), "0秒前"),
            (self.total_damage_card, "总伤害", data.get("总伤害", 0), "▲0%"),
            (self.dps_card, "每秒伤害", data.get("DPS", 0), f"峰值: {data.get('DPS', 0)*1.2:,.1f}"),
            (self.duration_card, "持续时间", f"{data.get('持续时间', 0)}s", "进行中"), 
            (self.crit_card, "暴击比率", f"{data.get('暴击比率', 0):.1f}%", "▼0%")
        ]
        
        for card, _, value, small_text in cards:
            labels = card.findChildren(QLabel, None, Qt.FindDirectChildrenOnly)
            labels[1].setText(f"{int(value):,}" if isinstance(value, (int, float)) else str(value))
            labels[2].setText(small_text)
