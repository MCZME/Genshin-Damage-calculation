from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QLabel,
                              QPushButton, QHBoxLayout, QSizePolicy, QScrollArea, QLineEdit)
from Emulation import Emulation
from ui.widget.character_status_widget import CharacterStatusWidget
from ui.widget.vertical_label_chart import VerticalLabelChart
from ui.widget.detail_info_widget import DetailInfoWidget
from ui.widget.analysis_result_widget import AnalysisResultWidget
from ui.widget.loading_widget import LoadingWidget

from setup.DataHandler import send_to_window
from setup.Logger import get_ui_logger

class ResultWindow(QMainWindow):
    def __init__(self, team_data, action_sequence):
        super().__init__()
        self.setWindowTitle("战斗数据分析")
        self.resize(900, 700)  # 设置初始窗口大小
        try:
            # 创建模拟线程
            self.simulation_thread = Emulation(team_data, action_sequence)
            self.simulation_thread.finished.connect(self._on_simulation_finished)
            self.simulation_thread.error_occurred.connect(self._on_simulation_error)
            self.simulation_thread.progress_updated.connect(self._on_simulation_progress_updated)
            self.simulation_thread.start()
        except Exception as e:
            error_msg = f"模拟过程中出错: {str(e)}"
            get_ui_logger().log_ui_error(error_msg)
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "模拟错误", error_msg)
        
        # 创建并显示加载组件
        self.loading_widget = LoadingWidget(self)
        self.loading_widget.resize(self.size())
        self.loading_widget.show()
           
    def init_ui(self):
        # 隐藏加载组件
        self.loading_widget.hide()
        self.loading_widget.deleteLater()
        
        # 主滚动区域
        self.main_widget = QScrollArea()
        self.main_widget.setWidgetResizable(True)
        self.main_widget.setStyleSheet("""
            QScrollArea {
                border: none;
                background: #f5f7fa;
            }
        """)
        
        # 主容器
        self.container = QWidget()
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        self.main_widget.setWidget(self.container)
        
        # 标题区域
        self.title_label = QLabel("战斗数据分析报告")
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #333333;
                padding-bottom: 10px;
                border-bottom: 2px solid #4a90e2;
            }
        """)
        self.main_layout.addWidget(self.title_label)
        
        # 图表区域
        self.chart_section = QWidget()
        self.chart_section.setStyleSheet("""
            QWidget {
                background: white;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        chart_layout = QVBoxLayout(self.chart_section)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        
        self.chart_title = QLabel("伤害数据统计")
        self.chart_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #333333;
                margin-bottom: 5px;
            }
        """)
        chart_layout.addWidget(self.chart_title)
        
        self.chart = VerticalLabelChart()
        self.chart.setMinimumSize(400, 400)
        self.chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.chart.bar_clicked.connect(self.on_chart_bar_clicked)
        chart_layout.addWidget(self.chart)
        
        self.main_layout.addWidget(self.chart_section)
        
        # 角色状态和详细信息区域容器
        self.status_info_container = QWidget()
        status_info_layout = QHBoxLayout(self.status_info_container)
        status_info_layout.setContentsMargins(0, 0, 0, 0)
        status_info_layout.setSpacing(10)
        
        # 角色状态区域
        self.character_section = QWidget()
        self.character_section.setStyleSheet("""
            QWidget {
                background: white;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        character_layout = QVBoxLayout(self.character_section)
        character_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建标题行布局
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 10)
        
        self.character_title = QLabel("角色状态分析")
        self.character_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #333333;
            }
        """)
        title_row.addWidget(self.character_title)
        
        # 添加输入框和按钮
        self.frame_input = QLineEdit()
        self.frame_input.setPlaceholderText("输入帧数")
        self.frame_input.setFixedWidth(100)
        self.frame_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 4px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #4a90e2;
            }
        """)
        title_row.addWidget(self.frame_input)
        
        self.frame_button = QPushButton("确定")
        self.frame_button.setFixedWidth(60)
        self.frame_button.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #3a80d2;
            }
            QPushButton:pressed {
                background-color: #2a70c2;
            }
        """)
        title_row.addWidget(self.frame_button)
        
        title_row.addStretch()
        character_layout.addLayout(title_row)
        
        self.character_status = CharacterStatusWidget(send_to_window('character'))
        self.character_status.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        character_layout.addWidget(self.character_status)
        
        # 详细信息区域
        self.detail_info_section = DetailInfoWidget()
        self.detail_info_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        # 将两个区域添加到容器
        status_info_layout.addWidget(self.character_section,1)
        status_info_layout.addWidget(self.detail_info_section,1)
        
        self.main_layout.addWidget(self.status_info_container)
        self.main_layout.addStretch(1)
        
        # 连接按钮信号
        self.frame_button.clicked.connect(self.on_frame_button_clicked)

        # 数据分析结果区域
        self.analysis_section = AnalysisResultWidget()
        self.main_layout.addWidget(self.analysis_section)
        
        self.setCentralWidget(self.main_widget)
        self.update_damage_chart()

    def on_frame_button_clicked(self):
        """处理帧数输入按钮点击事件"""
        try:
            frame = int(self.frame_input.text())
            self.update_frame(frame)
        except ValueError:
            print("请输入有效的帧数")
    
    def update_damage_chart(self):
        damage_data = send_to_window('damage')
        if not damage_data:
            return
        self.chart.set_data({frame: data['value'] for frame, data in damage_data.items()})
        self.detail_info_section.set_data({frame: data['damage'] for frame, data in damage_data.items()})
        
        # 更新分析结果
        max_hit = max(data['value'] for data in damage_data.values())
        total_dmg = sum(data['value'] for data in damage_data.values())
        duration_sec = len(damage_data) / 60
        duration_str = f"{duration_sec:.2f}"
        
        analysis_data = {
            "总伤害": total_dmg,
            "DPS": 60 * total_dmg / len(damage_data),
            "最大伤害": max_hit,
            "持续时间": duration_str,
            "暴击比率": 0  
        }
        self.analysis_section.set_data(analysis_data)
            
    def on_chart_bar_clicked(self, frame):
        """处理图表柱子点击事件"""
        self.frame_input.setText(str(frame))
        self.update_frame(frame)

    def update_frame(self, frame):
        """更新当前帧的角色状态显示"""
        self.character_status.update_frame(frame)
        self.detail_info_section.update_info(frame)

    def _on_simulation_finished(self):
        self.init_ui()

    def _on_simulation_error(self, error_msg):
        get_ui_logger().error(f"模拟过程中出错: {error_msg}")
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(self, "计算错误", f"模拟过程中出错: {error_msg}")

    def _on_simulation_progress_updated(self, data):
        """更新模拟进度"""
        if not hasattr(self, 'loading_widget') or not self.loading_widget.isVisible():
            return
            
        if "start" in data:
            # 初始化进度
            progress_data = data["start"]
            self.loading_widget.update_progress(
                progress_data["current"],
                progress_data["length"],
                progress_data["msg"]
            )
        elif "update" in data:
            # 更新进度
            progress_data = data["update"]
            self.loading_widget.update_progress(
                progress_data["current"],
                len(Emulation._actions),  # 总长度从Emulation类获取
                progress_data["msg"]
            )
