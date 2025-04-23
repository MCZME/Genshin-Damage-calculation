from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QHBoxLayout,
                              QSizePolicy, QScrollArea, QGridLayout)
from PySide6.QtCore import Qt
from core.Logger import get_ui_logger

class ObjectStatusWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.data = {}
        self.object_widgets = {}  # 保存物体名称对应的UI元素
        
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(5)
        
        # 标题
        self.title_label = QLabel("场上物体状态")
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
                background: transparent;
            }
        """)
        
        # 内容容器 - 使用网格布局
        self.content_widget = QWidget()
        self.content_layout = QGridLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(10)
        self.content_layout.setHorizontalSpacing(15)
        
        self.scroll_area.setWidget(self.content_widget)
        self.main_layout.addWidget(self.scroll_area)
        
        # 初始提示
        self.hint_label = QLabel("暂无物体数据")
        self.hint_label.setAlignment(Qt.AlignCenter)
        self.hint_label.setStyleSheet("""
            QLabel {
                color: #999999;
                font-size: 14px;
            }
        """)
        self.content_layout.addWidget(self.hint_label)
        
        self.setStyleSheet("""
            QWidget {
                background: white;
                border-radius: 8px;
                padding: 15px;
            }
        """)
    
    def set_data(self, data):
        self.data = data
        if not data:
            return
        
        # 移除提示标签
        if self.hint_label:
            self.hint_label.hide()
            self.hint_label.deleteLater()
            self.hint_label = None
        
        # 更新显示
        self.update_frame(self.current_frame)
    
    def update_frame(self, frame):
        if not self.data:
            return
            
        obj_list = self.data.get(frame, [])
        
        # 获取当前帧所有物体唯一标识
        current_keys = {f"{obj['name']}_{obj.get('id', id(obj))}" for obj in obj_list}
        
        # 处理需要移除的物体
        for key in list(self.object_widgets.keys()):
            if key not in current_keys:
                widget = self.object_widgets.pop(key)
                widget['container'].hide()
                widget['container'].deleteLater()
        
        # 更新或添加物体
        for obj in obj_list:
            name = obj['name']
            obj_id = obj.get('id', id(obj))
            key = f"{name}_{obj_id}"
            current = obj['current_frame']
            life = obj['life_frame']
            percent = (life - current) / life * 100 if life > 0 else 0
            
            if key in self.object_widgets:
                # 更新现有物体
                widget = self.object_widgets[key]
                widget['progress_fg'].resize(int(percent * 2), 20)
                widget['text_label'].setText(f"{name} ({int(percent)}%)")
                # 根据进度调整文本颜色
                if percent > 50:
                    widget['text_label'].setStyleSheet("""
                        QLabel {
                            font-size: 12px;
                            color: white;
                            font-weight: bold;
                        }
                    """)
                else:
                    widget['text_label'].setStyleSheet("""
                        QLabel {
                            font-size: 12px;
                            color: #333333;
                            font-weight: bold;
                        }
                    """)
            else:
                # 创建新物体UI
                # 创建进度条容器
                progress_container = QWidget()
                progress_container.setFixedHeight(30)
                progress_container.setStyleSheet("""
                    QWidget {
                        background: transparent;
                        border-radius: 10px;
                    }
                """)
                
                # 进度条背景
                progress_bg = QWidget(progress_container)
                progress_bg.setGeometry(0, 5, 200, 20)  # 调整y位置为5，使进度条垂直居中
                progress_bg.setStyleSheet("""
                    QWidget {
                        background: #e0e0e0;
                        border-radius: 10px;
                    }
                """)
                progress_bg.lower()  # 确保在文本标签下方
                
                # 进度条前景
                progress_fg = QWidget(progress_bg)
                progress_fg.setGeometry(0, 0, int(percent * 2), 20)
                progress_fg.setStyleSheet("""
                    QWidget {
                        background: #4a90e2;
                        border-radius: 10px;
                    }
                """)
                
                # 添加文本标签到容器（确保在最上层且可见）
                text_label = QLabel(name, progress_container)
                text_label.setAlignment(Qt.AlignCenter)
                text_label.setGeometry(0, 0, 200, 30)  # 覆盖整个容器高度
                text_label.setStyleSheet("""
                    QLabel {
                        font-size: 12px;
                        color: #333333;
                        font-weight: bold;
                        background: transparent;
                        padding: 0;
                        margin: 0;
                        qproperty-alignment: 'AlignCenter';
                    }
                """)
                text_label.raise_()  # 确保在最上层
                text_label.show()   # 强制显示
                
                # 计算当前widget在网格中的位置
                count = len(self.object_widgets)
                row = count // 3
                col = count % 3
                self.content_layout.addWidget(progress_container, row, col)
                
                self.object_widgets[key] = {
                    'container': progress_container,
                    'progress_fg': progress_fg,
                    'text_label': text_label
                }
