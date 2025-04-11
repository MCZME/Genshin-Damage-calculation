from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget, QPushButton, QStyle
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QObject, Signal, Qt, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from DataRequest import DR
from setup.Logger import get_ui_logger

class ImageLoader(QObject):
    loaded = Signal(QPixmap)
    error = Signal(str)

    def __init__(self):
        super().__init__()
        self.manager = QNetworkAccessManager()
        self.manager.finished.connect(self.on_reply_finished)

    def load(self, url):
        request = QNetworkRequest(QUrl(url))
        self.manager.get(request)

    def on_reply_finished(self, reply):
        try:
            status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
            content_type = reply.header(QNetworkRequest.ContentTypeHeader)
            data = reply.readAll()
            
            # 首先检查HTTP状态码
            if status_code and status_code >= 400:
                self.error.emit(f"HTTP {status_code} error")
                return
                
            # 检查内容类型是否为图片
            if content_type and not any(img_type in content_type for img_type in ["image/png", "image/jpeg", "image/webp"]):
                self.error.emit(f"Invalid content type: {content_type}")
                return
                
            # 检查数据是否为空
            if not data:
                self.error.emit("Empty image data")
                return
                
            # 尝试加载图片数据
            pixmap = QPixmap()
            if not pixmap.loadFromData(data):
                self.error.emit("Failed to load image data")
                return
                
            if pixmap.isNull():
                self.error.emit("Invalid image format")
                return
                
            self.loaded.emit(pixmap)
        except Exception as e:
            self.error.emit(f"Processing error: {str(e)}")
        finally:
            reply.deleteLater()

class ImageLoaderWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.label)
        self.setLayout(self.main_layout)
        self.loading_label = QLabel("", self)
        self.loading_label.hide()
        self.main_layout.addWidget(self.loading_label)

    def load_image(self, url):
        self.loading_label.show()
        self.loader = ImageLoader()
        self.loader.loaded.connect(self.on_image_loaded)
        self.loader.error.connect(self.on_image_error)
        self.loader.load(url)
        get_ui_logger().log_info(f"开始加载图片: {url}")

    def on_image_loaded(self, pixmap):
        self.loading_label.hide()
        self.label.setPixmap(pixmap.scaled(
            self.width(), self.height(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        ))
        get_ui_logger().log_info(f"图片加载成功")

    def on_image_error(self, error):
        get_ui_logger().log_error(f"图片加载失败: {error}")
        # 显示Qt内置错误图标
        error_icon = self.style().standardIcon(QStyle.SP_MessageBoxWarning)
        error_pixmap = error_icon.pixmap(self.width(), self.height())
        self.label.setPixmap(error_pixmap)

class ImageAvatar(ImageLoaderWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def load_image(self, name):
        SQL = f'SELECT url FROM `character_portrait` WHERE name = "{name}"'
        url = DR.read_data(SQL)[0][0]
        super().load_image(url)


class ImageButton(QPushButton):
    clicked_with_url = Signal(str)  # 新增信号，带URL参数

    def __init__(self, parent=None):
        super().__init__(parent)
        self._normal_url = ""
        self._hover_url = ""
        self._pressed_url = ""
        self._current_state = "normal"
        self.loader = ImageLoader()
        self.loader.loaded.connect(self._on_image_loaded)
        self.loader.error.connect(self._on_image_error)
        self.setCursor(Qt.PointingHandCursor)
        
    def _load_image(self, url):
        if url:
            self.loader.load(url)
            get_ui_logger().log_info(f"开始加载按钮图片: {url}")

    def _on_image_loaded(self, pixmap):
        self.setIcon(pixmap.scaled(
            self.size(), 
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))
        get_ui_logger().log_info("按钮图片加载成功")

    def _on_image_error(self, error):
        get_ui_logger().log_error(f"按钮图片加载失败: {error}")

class ImageAvatarButton(ImageButton):
    def __init__(self, parent=None):
        super().__init__(parent)

    def load_image(self, name):
        SQL = f'SELECT url FROM `character_portrait` WHERE name = "{name}"'
        url = DR.read_data(SQL)[0][0]
        super()._load_image(url)