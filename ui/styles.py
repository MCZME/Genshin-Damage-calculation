"""现代风格样式表"""
MODERN_STYLE = """
/* 主窗口样式 */
QMainWindow {
    background-color: #f5f7fa;
}

/* 区域样式 */
.title-area {
    background-color: #e3f2fd;
    border-radius: 4px;
    padding: 0;
    margin: 5px 0;
    font-size: 16px;
    font-weight: bold;
}

.team-area {
    background-color: #e8f5e9;
    border-radius: 4px;
}

.target-area {
    background-color: #fff3e0;
    border-radius: 4px;
}

.action-area {
    background-color: #f3e5f5;
    border-radius: 4px;
}

.button-area {
    background-color: #e0f7fa;
    border-radius: 4px;
}

/* 通用部件样式 */
QWidget {
    font-family: 'Microsoft YaHei';
    font-size: 14px;
    color: #333333;
}

/* 按钮样式 */
QPushButton {
    background-color: #4a6fa5;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #5a7fb5;
}

QPushButton:pressed {
    background-color: #3a5f95;
}

/* 输入框样式 */
QLineEdit, QTextEdit {
    border: 1px solid #d1d5db;
    border-radius: 4px;
    padding: 6px 10px;
    background-color: white;
}

QLineEdit:focus, QTextEdit:focus {
    border-color: #4a6fa5;
}

/* 标签样式 */
QLabel {
    color: #4b5563;
}

/* 组合框样式 */
QComboBox {
    border: 1px solid #d1d5db;
    border-radius: 4px;
    padding: 6px 10px;
    background-color: white;
}

/* 动画效果 */
QPushButton, QLineEdit, QComboBox {
    transition: all 0.2s ease;
}
"""
