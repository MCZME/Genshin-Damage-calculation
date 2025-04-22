from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame,
                               QGridLayout, QSizePolicy)
from PySide6.QtCore import Qt

class InfoCardWidget(QWidget):
    """信息卡片组件"""
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName('InfoCardWidget')
        self.setup_ui()
    
    def setup_ui(self):
        """初始化卡片UI"""
        # 根据元素类型设置不同边框颜色
        element_colors = {
            '火': '#ff9999',
            '水': '#99ccff',
            '风': '#99ffcc',
            '雷': '#cc99ff',
            '草': '#99ff99',
            '冰': '#99ffff',
            '岩': '#ffcc99'
        }
        element = self.data.get('element', '')
        border_color = element_colors.get(element, '#cccccc')
        
        self.setStyleSheet(f"""
            QWidget#InfoCardWidget {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                padding: 10px;
                margin: 8px 5px;
                border: 2px solid {border_color};  
            }}
            
            /* 标题样式 */
            QLabel {{
                font-family: 'Segoe UI', sans-serif;
                color: #2b2d42;
                margin-bottom: 12px;
                border-bottom: 1px solid {border_color}66;
            }}
            
            /* 字段标签样式 */
            QLabel[accessibleName="field_item"] {{
                font-size: 13px;
                color: #4a4e69;
                background: transparent;
                padding: 6px 6px;
                margin: 2px;
                border: 1px solid {border_color}33;
            }}
            
            /* 数据详情标题 */
            QLabel[accessibleName="data_title"] {{
                font-size: 14px;
                color: {border_color};
                letter-spacing: 0.5px;
            }}
        """)
        
        # 主垂直布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(5)
        
        # 标题区域
        title = QLabel(f"<h2 style='margin:0;'>{self.data.get('name', '未命名')}</h2>")
        title.setStyleSheet(f"""
            QLabel {{
                color: #222222;
                margin-bottom: 5px;
                font-weight: 600;
                border-bottom: 1px solid {border_color};
                padding-bottom: 2px;
            }}
        """)
        main_layout.addWidget(title)
        
        # 基本信息部分 - 单独网格布局
        info_widget = QWidget()
        info_layout = QGridLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(0)
        
        fields = [
            ('数值', self.data.get('value', '')),
            ('来源', self.data.get('source', '')),
            ('目标', self.data.get('target', '')),
            ('元素', element),
            ('类型', self.data.get('type', '')),
            ('反应', self.data.get('reaction', ''))
        ]
        
        for i, (label, value) in enumerate(fields):
            if value:
                if label == '数值':
                    display_text = f"<b>{label}:</b> {value:.2f}"
                else:
                    display_text = f"<b>{label}:</b> {value}"
                item = QLabel(display_text)
                item.setStyleSheet(f"""
                    QLabel {{
                        font-size: 14px;
                        color: #444444;
                        padding: 0;
                        background: transparent;
                    }}
                    
                    QLabel:hover {{
                        background: transparent;
                        color: #222222;
                    }}
                """)
                info_layout.addWidget(item, i // 2, i % 2)
        
        main_layout.addWidget(info_widget)
        
        # 添加data字典内容
        if self.data.get('data'):
            data_label = QLabel("<b>数据详情:</b>")
            data_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 15px;
                    color: {border_color};
                    margin-bottom: 0px;
                    font-weight: 500;
                }}
            """)
            main_layout.addWidget(data_label)
            
            def add_dict_items(dict_data, indent=10):
                for key, val in dict_data.items():
                    if isinstance(val, dict):
                        group_label = QLabel(f"{key}:")
                        group_label.setStyleSheet(f"""
                            QLabel {{
                                font-size: 13px;
                                color: {border_color};
                                margin-left: {indent}px;
                                font-weight: bold;
                            }}
                        """)
                        main_layout.addWidget(group_label)
                        add_dict_items(val, indent + 10)
                    else:
                        if isinstance(val, (bool)):
                            item = QLabel(f"{key}: {val}")
                        elif isinstance(val, (int, float)):
                            item = QLabel(f"{key}: {val:.2f}")
                        else:
                            item = QLabel(f"{key}: {val}")
                        item.setStyleSheet(f"""
                            QLabel {{
                                font-size: 13px;
                                color: #555555;
                                margin-left: {indent}px;
                            }}
                        """)
                        main_layout.addWidget(item)
            
            add_dict_items(self.data['data'])
        
        # 添加panel字典内容 - 使用单独网格布局
        if self.data.get('panel'):
            panel_label = QLabel("<b>面板属性:</b>")
            panel_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 15px;
                    color: {border_color};
                    font-weight: 500;
                    margin-bottom: 0px;
                }}
            """)
            main_layout.addWidget(panel_label)
            
            # 创建面板属性的单独网格布局
            panel_widget = QWidget()
            panel_layout = QGridLayout(panel_widget)
            panel_layout.setContentsMargins(8, 0, 8, 0)
            panel_layout.setSpacing(0)
            
            panel_items = list(self.data['panel'].items())
            for i, (key, val) in enumerate(panel_items):
                if isinstance(val, (int, float)):
                    item = QLabel(f"{key}: {val:.2f}")
                else:
                    item = QLabel(f"{key}: {val}")
                item.setStyleSheet("""
                    QLabel {
                        font-size: 13px;
                        color: #555555;
                        margin: 1px 3px;
                    }
                """)
                panel_layout.addWidget(item, i // 3, i % 3)
            
            main_layout.addWidget(panel_widget)

class DetailInfoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = None
        self.setup_ui()

    def set_data(self, data):
        self.data = data

    def setup_ui(self):
        """初始化UI界面"""
        self.setStyleSheet("""
            QWidget {
                background: white;
                border-radius: 8px;
            }
        """)
        
        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(10)
        
        # 标题
        self.title_label = QLabel("详细信息")
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #333333;
                margin-bottom: 5px;
            }
        """)
        self.main_layout.addWidget(self.title_label)
        
        # 滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
            }
        """)
        
        # 内容容器
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(5)
        
        # 默认提示文本
        self.default_label = QLabel("点击图表或输入帧数查看详细信息")
        self.default_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #666666;
                font-style: italic;
            }
        """)
        self.content_layout.addWidget(self.default_label)
        self.content_layout.addStretch(1)
        
        self.scroll_area.setWidget(self.content_widget)
        self.main_layout.addWidget(self.scroll_area)
    
    def update_info(self, frame):
        """更新显示的信息"""
        # 清除现有内容
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        if not self.data or frame not in self.data or not self.data[frame]:
            self.content_layout.addWidget(self.default_label)
            return
            
        for card_data in self.data[frame]:
            # 创建信息卡片
            card = InfoCardWidget(card_data)
            self.content_layout.addWidget(card)
        
        self.content_layout.addStretch(1)
