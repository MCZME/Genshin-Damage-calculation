from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout, 
                              QProgressBar)
from PySide6.QtCore import Qt
from PySide6.QtGui import (QColor, QPainter, QBrush, 
                           QPen, QLinearGradient)

class LoadingWidget(QWidget):
    """加载组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                height: 8px;
                background: rgba(0, 0, 0, 0.05);
                border-radius: 4px;
                border: 1px solid rgba(0, 0, 0, 0.1);
            }
            QProgressBar::chunk {
                border-radius: 4px;
                background: qlineargradient(
                    spread:pad, x1:0, y1:0.5, x2:1, y2:0.5, 
                    stop:0 #4a90e2, stop:1 #50e3c2);
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # 进度文本
        self.progress_text = QLabel("0%")
        self.progress_text.setAlignment(Qt.AlignCenter)
        self.progress_text.setStyleSheet("""
            font-size: 14px;
            color: #333333;
            font-weight: 500;
            margin-top: 5px;
        """)
        layout.addWidget(self.progress_text)
        
        # 加载文本
        self.text_label = QLabel("计算中...")
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setStyleSheet("""
            font-size: 16px;
            color: #333333;
            font-weight: bold;
            margin-top: 5px;
        """)
        layout.addWidget(self.text_label)
        
    def showEvent(self, event):
        """显示时启动动画"""
        super().showEvent(event)
        
    def hideEvent(self, event):
        """隐藏时停止动画"""
        super().hideEvent(event)
        
    def paintEvent(self, event):
        """绘制半透明背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制渐变背景
        gradient = QLinearGradient(self.rect().topLeft(), self.rect().bottomRight())
        gradient.setColorAt(0, QColor(240, 240, 245, 200))
        gradient.setColorAt(1, QColor(230, 230, 240, 200))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
        painter.drawRoundedRect(self.rect(), 8, 8)
        
    def update_progress(self, current, total, message):
        """更新进度显示"""
        progress = int((current / total) * 100) if total > 0 else 0
        
        # 确保在主线程更新UI
        from PySide6.QtWidgets import QApplication
        self.progress_bar.setValue(progress)
        self.progress_text.setText(f"{progress}%")
        self.text_label.setText(message)        
        # 确保组件在最前并可见
        self.raise_()
        self.show()        
        # 强制处理事件队列并刷新
        QApplication.instance().processEvents()
        self.progress_bar.repaint()
        self.repaint()

