from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget, QPushButton, QStyle
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QObject, Signal, Qt, QUrl, QSize
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from DataRequest import DR
from setup.Logger import get_ui_logger
import hashlib
import os

class ImageLoader(QObject):
    loaded = Signal(QPixmap)
    error = Signal(str)
    
    # 缓存目录路径
    CACHE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/image_cache'))
    
    def __init__(self):
        super().__init__()
        self.manager = QNetworkAccessManager()
        self.manager.finished.connect(self.on_reply_finished)
        self.memory_cache = {}  # 内存缓存字典
        # 确保缓存目录存在且有写入权限
        try:
            os.makedirs(self.CACHE_DIR, exist_ok=True)
            # 测试写入权限
            test_file = os.path.join(self.CACHE_DIR, 'test_permission')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except Exception as e:
            get_ui_logger().log_error(f"缓存目录初始化失败: {str(e)}")

    def load(self, url):
        # 检查内存缓存
        cache_key = self._get_cache_key(url)
        if cache_key in self.memory_cache:
            get_ui_logger().log_info(f"从内存缓存加载图片: {url}")
            self.loaded.emit(self.memory_cache[cache_key])
            return
            
        # 检查磁盘缓存
        cache_path = os.path.join(self.CACHE_DIR, cache_key)
        if os.path.exists(cache_path):
            pixmap = QPixmap(cache_path)
            if not pixmap.isNull():
                get_ui_logger().log_info(f"从磁盘缓存加载图片: {url}")
                self.memory_cache[cache_key] = pixmap
                self.loaded.emit(pixmap)
                return
                
        # 没有缓存则发起网络请求
        request = QNetworkRequest(QUrl(url))
        # 设置请求头避免被识别为爬虫
        request.setRawHeader(b"User-Agent", b"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
        request.setRawHeader(b"Accept-Language", b"zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7")
        self.manager.get(request)

    def _get_cache_key(self, url):
        """生成缓存键名"""
        return hashlib.md5(url.encode()).hexdigest()
        
    def on_reply_finished(self, reply):
        try:
            status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
            content_type = reply.header(QNetworkRequest.ContentTypeHeader)
            data = reply.readAll()
            url = reply.url().toString()
            cache_key = self._get_cache_key(url)
            
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
                
            # 保存到内存缓存
            self.memory_cache[cache_key] = pixmap
            
            # 保存到磁盘缓存
            cache_path = os.path.join(self.CACHE_DIR, cache_key)
            # 根据内容类型确定格式
            format_map = {
                'image/png': 'PNG',
                'image/jpeg': 'JPG',
                'image/webp': 'WEBP'
            }
            img_format = 'PNG'  # 默认格式
            if content_type:
                for ct, fmt in format_map.items():
                    if ct in content_type:
                        img_format = fmt
                        break
            
            try:
                if pixmap.save(cache_path, img_format):
                    get_ui_logger().log_info(f"图片已缓存({img_format}): {url}")
                else:
                    get_ui_logger().log_error(f"图片缓存失败: {url} (格式: {img_format})")
            except Exception as e:
                get_ui_logger().log_error(f"图片缓存异常: {url} - {str(e)}")
            
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
        self.setIconSize(QSize(56, 56))
        
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
