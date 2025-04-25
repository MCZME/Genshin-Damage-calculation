import multiprocessing
from queue import Queue
from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
                              QLabel, QPushButton, QFrame, QScrollArea,
                              QFileDialog, QMessageBox)
import json
import os
from datetime import datetime
import uuid
from PySide6.QtCore import Qt

from Emulation import Emulation
from core.DataHandler import save_report
from ui.widget.image_loader_widget import ImageAvatar
from ui.widget.simulation_config_widget import SimulationConfigWidget

from .styles import MODERN_STYLE
from .widget.action_card import ActionCard
from .result_window import ResultWindow
from .widget.character_window import CharacterWindow
from .widget.action_setting_dialog import ActionSettingDialog
from core.Config import Config
from core.Logger import get_ui_logger

class MainWindow(QMainWindow):
    """主窗口类"""
    def __init__(self):
        super().__init__()
        self.logger = get_ui_logger()
        self.setWindowTitle("原神伤害计算器")
        self.setMinimumSize(960, 700)
        self.character_windows = {}  # 存储每个角色槽位的窗口
        
        # 创建中央部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)  # 取消间距，用stretch控制
        main_layout.setContentsMargins(20, 10, 20, 20)  # 增加底部边距
        central_widget.setLayout(main_layout)
        
        self.setStyleSheet(MODERN_STYLE)
        
        # 标题区域 (1/10)
        title = QLabel("原神伤害计算器")
        title.setAlignment(Qt.AlignCenter)
        title.setProperty("class", "title-area")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            margin: 0;
            padding: 0;
        """)
        main_layout.addWidget(title, stretch=1)  # 标题占1份
        
        spacer1 = QWidget()
        main_layout.addWidget(spacer1, stretch=1)
        
        # 队伍配置区域 (3/10)
        team_frame = QFrame()
        team_frame.setFrameShape(QFrame.StyledPanel)
        team_frame.setStyleSheet("""
            border: 1px solid #d1d5db;
            border-radius: 6px;
            background-color: white;
        """)
        team_layout = QVBoxLayout()
        team_layout.setAlignment(Qt.AlignCenter)
        team_layout.setContentsMargins(10, 10, 10, 10)   
        
        # 4个角色槽
        char_slots = QHBoxLayout()
        char_slots.setSpacing(20)  # 增加角色间距
        for i in range(4):
            # 创建角色槽容器
            slot_container = QWidget()
            slot_container.setFixedHeight(140)
            slot_container.setStyleSheet("""
                QWidget {
                    border: 2px dashed #aaa;
                    background-color: white;
                }
                QWidget:hover {
                    border: 2px dashed #3b82f6;
                    background-color: #f0f0f0;
                }
            """)
            slot_container.setCursor(Qt.PointingHandCursor)
            
            # 主布局
            slot_layout = QHBoxLayout(slot_container)
            slot_layout.setContentsMargins(10, 10, 10, 10)
            slot_layout.setSpacing(10)
            
            # 左侧区域 - 角色信息
            left_widget = QWidget()
            left_layout = QVBoxLayout(left_widget)
            left_layout.setContentsMargins(0, 0, 0, 0)
            left_layout.setSpacing(5)
            
            # 角色头像容器
            avatar_container = QWidget()
            avatar_container.setStyleSheet("""
                border: none;
                padding: 0;
                margin: 0;
            """)
            avatar_container.setFixedSize(50, 50)
            avatar_layout = QVBoxLayout(avatar_container)
            avatar_layout.setContentsMargins(0, 0, 0, 0)
            avatar_layout.setSpacing(0)
            
            # 删除按钮 (初始隐藏)
            delete_btn = QPushButton("×")
            delete_btn.setFixedSize(12, 12)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ef4444;
                    color: white;
                    border-radius: 5px;
                    font-size: 8px;
                    font-weight: bold;
                    border: none;
                    margin: 0;
                    padding: 0;
                }
                QPushButton:hover {
                    background-color: #dc2626;
                }
            """)
            delete_btn.clicked.connect(lambda _, idx=i: self._clear_character_slot(idx))
            
            # 头像标签
            self.avatar_label = ImageAvatar()
            self.avatar_label.setFixedSize(50, 50)
            self.avatar_label.setStyleSheet("""
                background-color: #e9ecef;
                border-radius: 25px;
            """)
            
            # 将按钮覆盖在头像上
            overlay = QWidget()
            overlay.setFixedHeight(15)
            overlay.setStyleSheet("""
                border: none;
                margin: 0;
                padding: 0;
                background-color: transparent;
            """)
            overlay_layout = QHBoxLayout(overlay)
            overlay_layout.setContentsMargins(0, 3, 3, 0)
            overlay_layout.setAlignment(Qt.AlignRight)
            overlay_layout.setSpacing(0)
            overlay_layout.addWidget(delete_btn, 0)
            left_layout.addWidget(overlay, 0, Qt.AlignRight)

            avatar_layout.addWidget(self.avatar_label)
            left_layout.addWidget(avatar_container, 0, Qt.AlignCenter)
            
            # 等级和天赋
            self.char_info = QLabel("Lv.0\n天赋:0/0/0")
            self.char_info.setStyleSheet("""
                font-size: 12px;
                color: #333;
            """)
            self.char_info.setAlignment(Qt.AlignCenter)
            left_layout.addWidget(self.char_info)
            
            slot_layout.addWidget(left_widget, stretch=2)
            
            # 右侧区域 - 武器和圣遗物
            right_widget = QWidget()
            right_layout = QVBoxLayout(right_widget)
            right_layout.setContentsMargins(0, 0, 0, 0)
            right_layout.setSpacing(5)
            
            # 武器
            self.weapon_label = QLabel("无武器")
            self.weapon_label.setStyleSheet("""
                font-size: 12px;
                color: #333;
            """)
            self.weapon_label.setAlignment(Qt.AlignCenter)
            right_layout.addWidget(self.weapon_label)
            
            # 圣遗物套装
            self.artifact_label = QLabel("无套装")
            self.artifact_label.setStyleSheet("""
                font-size: 12px;
                color: #666;
            """)
            self.artifact_label.setAlignment(Qt.AlignCenter)
            right_layout.addWidget(self.artifact_label)
            
            slot_layout.addWidget(right_widget, stretch=1)
            
            # 点击事件
            slot_container.mousePressEvent = lambda _, idx=i: self._open_character_window(idx)
            char_slots.addWidget(slot_container, stretch=1)
        team_layout.addLayout(char_slots)
        
        team_frame.setLayout(team_layout)
        main_layout.addWidget(team_frame, stretch=4)
        
        # 添加间隙
        spacer = QWidget()
        main_layout.addWidget(spacer, stretch=1)
        
        # 动作序列区域 (5/10)
        action_frame = QFrame()
        action_frame.setFrameShape(QFrame.StyledPanel)
        action_frame.setStyleSheet("""
            border-radius: 6px;
            background-color: white;
        """)
        action_layout = QVBoxLayout()
        action_layout.setContentsMargins(10, 10, 10, 10)
        action_layout.setSpacing(0)
        
        # 动作序列标题区域 (1/5高度)
        title_widget = QWidget()
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        action_label = QLabel("   动作序列")
        action_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_layout.addWidget(action_label)
        title_layout.addStretch()
        
        action_layout.addWidget(title_widget, stretch=1)
        
        # 动作序列内容区域 (4/5高度)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            border: 1px solid #d1d5db;
            border-radius: 6px;
            background-color: white;
        """)
        
        # 动作卡片容器 - 横向布局（支持拖拽）
        self.action_container = QWidget()
        self.action_container.setAcceptDrops(True)
        self.action_container_layout = QHBoxLayout(self.action_container)
        self.action_container_layout.setSpacing(10)
        self.action_container_layout.setContentsMargins(10, 10, 10, 10)
        self.action_container_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # 拖拽相关变量
        self.drag_card = None
        self.drag_pos = None
        
        # 拖拽事件处理
        def dragEnterEvent(event):
            if event.mimeData().hasText():
                event.acceptProposedAction()
        self.action_container.dragEnterEvent = dragEnterEvent

        def dropEvent(event):
            if not self.drag_card:
                return
                
            # 获取拖拽位置
            pos = event.pos()
            target_index = -1
            
            # 查找插入位置
            for i in range(self.action_container_layout.count()):
                item = self.action_container_layout.itemAt(i)
                if item.widget() and item.widget().geometry().contains(pos):
                    target_index = i
                    break
                    
            if target_index >= 0:
                # 移动卡片
                self.action_container_layout.removeWidget(self.drag_card)
                self.action_container_layout.insertWidget(target_index, self.drag_card)
                event.accept()
        self.action_container.dropEvent = dropEvent

        # 初始提示容器 (与卡片大小相同)
        self.hint_container = QWidget()
        self.hint_container.setFixedWidth(160)
        hint_layout = QVBoxLayout(self.hint_container)
        hint_label = QLabel("点击添加按钮\n创建动作序列")
        hint_label.setAlignment(Qt.AlignCenter)
        hint_label.setStyleSheet("""
            font-size: 14px; 
            color: #666;
            margin: 0;
            padding: 0;
        """)
        hint_layout.addWidget(hint_label)
        hint_layout.addStretch()
        self.hint_container.setVisible(True)
        
        self.action_container_layout.addWidget(self.hint_container)
        
        # 添加动作按钮 (与卡片大小相同)
        self.add_btn = QPushButton("+")
        # self.add_btn.setFixedWidth(160)
        self.add_btn.clicked.connect(self._add_action_card)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border-radius: 4px;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        self.action_container_layout.addWidget(self.add_btn)
        
        scroll_area.setWidget(self.action_container)
        action_layout.addWidget(scroll_area, stretch=7)
        
        action_frame.setLayout(action_layout)
        main_layout.addWidget(action_frame, stretch=5)  # 动作序列占5/10
        
        self.config_widegt = SimulationConfigWidget()
        main_layout.addWidget(self.config_widegt, stretch=1)

        # 按钮区域 (1/10)
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setSpacing(20)
        
        load_btn = QPushButton("加载")
        load_btn.setFixedWidth(60)
        load_btn.clicked.connect(self._load_data)
        
        save_btn = QPushButton("保存")
        save_btn.setFixedWidth(60)
        save_btn.clicked.connect(self._save_data)
        
        calc_btn = QPushButton("开始计算") 
        calc_btn.setFixedWidth(120)
        calc_btn.clicked.connect(self._start_calculation)
        reset_btn = QPushButton("重置")
        reset_btn.setFixedWidth(60)
        reset_btn.clicked.connect(self._reset_data)
        
        button_layout.addWidget(load_btn)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(calc_btn)
        button_layout.addWidget(reset_btn)
        
        main_layout.addWidget(button_widget, stretch=1)  # 按钮占1份
        
        # 自动加载上次配置
        self._auto_load_last_config()
        
    def _auto_load_last_config(self):
        """自动加载上次保存的配置文件"""
        from core.Config import Config
        last_config = Config.get("ui.last_save_file")
        if last_config and os.path.exists(last_config):
            try:
                with open(last_config, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # 1. 恢复角色数据
                for slot_idx, char_data in enumerate(data["team_data"]):
                    if "error" in char_data:
                        continue
                        
                    if slot_idx not in self.character_windows:
                        self.character_windows[slot_idx] = CharacterWindow(self)
                        self.character_windows[slot_idx].finished.connect(
                            lambda data, idx=slot_idx: self._update_slot_display(idx))
                    
                    char_window = self.character_windows[slot_idx]
                    char_window.result_data = char_data
                    char_window._update_ui_from_data()
                    self._update_slot_display(slot_idx)
                
                # 2. 恢复动作序列
                for i in reversed(range(self.action_container_layout.count())):
                    widget = self.action_container_layout.itemAt(i).widget()
                    if isinstance(widget, ActionCard):
                        widget.deleteLater()
                
                self.hint_container.setVisible(False)
                for action_data in data["action_sequence"]:
                    card = ActionCard(self)
                    self.action_container_layout.insertWidget(
                        self.action_container_layout.count()-1, card)
                    card.update_data({
                        "character": action_data["character"],
                        "action": action_data["action"], 
                        "params": action_data["params"]
                    })
            
                self.config_widegt.set_config(data["target_data"])
            except Exception as e:
                print(f"自动加载配置失败: {str(e)}")

    def add_widget(self, widget):
        """添加部件到主布局"""
        self.centralWidget().layout().addWidget(widget)
        
    def _start_calculation(self):
        """开始计算按钮点击处理"""
        team_data, action_sequence, target_data = self.get_data()
        self.logger.log_button_click(f"开始计算: 队伍{len(team_data)}人, 动作序列{len(action_sequence)}个")
        
        # 自动保存当前配置
        filename = f"./data/last_file.json"
        os.makedirs("./data", exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump({
                "team_data": team_data,
                "action_sequence": action_sequence,
                "target_data": target_data
            }, f, ensure_ascii=False, indent=2)
        
        # 更新最后保存的文件路径配置
        Config.set("ui.last_save_file", filename)
        Config.save()
        
        self.close()
        if Config.get("emulation.batch_sim"):
            try:
                uid = uuid.uuid4().hex
                os.mkdir(Config.get("emulation.batch_sim_file_path") + uid + '/')
                os.mkdir(Config.get("emulation.batch_sim_file_path") + uid + '/logs')
                os.mkdir(Config.get("emulation.batch_sim_file_path") + uid + '/data')
                with multiprocessing.Pool(processes=Config.get("emulation.batch_sim_processes")) as pool:
                    async_results = [pool.apply_async(
                        simulate_multi,
                        args=(team_data, 
                            action_sequence, 
                            target_data, 
                            Config.get("emulation.batch_sim_file_path"),
                            sim_id,
                            uid),
                        error_callback=error_callback,
                        callback=callback
                    ) for sim_id in range(Config.get("emulation.batch_sim_num"))]
                    results = []
                    for res in async_results:
                        try:
                            results.append(res.get(timeout=10))  # 设置超时防止卡死
                        except multiprocessing.TimeoutError:
                            get_ui_logger().log_error("任务超时")

                success_count = sum(1 for r in results if r.get("status") == "success")
                get_ui_logger().log_info(f"成功率: {success_count / len(results):.1%}")
            except Exception as e:
                error_msg = f"模拟过程中出错: {str(e)}"
                get_ui_logger().log_ui_error(error_msg)
                QMessageBox.critical(self, "模拟错误", error_msg)
        else:
            self.result_window = ResultWindow()
            self.result_window.show()
            try:
                # 创建模拟线程
                emulation = Emulation(team_data, action_sequence, target_data)
                emulation.set_log_file()
                emulation.set_quueue(Queue())
                simulation_thread = emulation.thread()
                simulation_thread.start()
                self.result_window._on_simulation_progress_updated(emulation.progress_queue)
                simulation_thread.join()
            except Exception as e:
                error_msg = f"模拟过程中出错: {str(e)}"
                get_ui_logger().log_ui_error(error_msg)
                QMessageBox.critical(self, "模拟错误", error_msg)

    def _open_character_window(self, slot_idx):
        """打开角色配置窗口"""
        self.logger.log_window_open(f"角色配置窗口(槽位{slot_idx+1})")
        if slot_idx not in self.character_windows:
            self.character_windows[slot_idx] = CharacterWindow(self)
            # 连接窗口关闭信号到更新方法
            self.character_windows[slot_idx].finished.connect(
                lambda data, idx=slot_idx: self._update_slot_display(idx))
        self.character_windows[slot_idx].show()

    def _update_slot_display(self, slot_idx):
        """更新角色槽显示"""
        print(f"开始更新槽位 {slot_idx} 的显示")  # 调试日志
        
        if slot_idx not in self.character_windows:
            print(f"错误: 槽位 {slot_idx} 没有对应的角色窗口")
            return
            
        char_window = self.character_windows[slot_idx]
        
        # 获取角色槽容器 - 在初始化时保存引用
        team_frame = self.centralWidget().layout().itemAt(2).widget()  # 队伍配置区域
        if not team_frame:
            print("错误: 找不到队伍配置区域")
            return
            
        char_slots = team_frame.layout().itemAt(0)  # 角色槽布局
        if not char_slots or slot_idx >= char_slots.count():
            print(f"错误: 无效的槽位索引 {slot_idx}")
            return
            
        slot_container = char_slots.itemAt(slot_idx).widget()
        if not slot_container:
            print(f"错误: 槽位 {slot_idx} 容器无效")
            return
        
        # 获取子部件 - 使用初始化时保存的引用
        left_widget = slot_container.layout().itemAt(0).widget()
        right_widget = slot_container.layout().itemAt(1).widget()
        
        if not left_widget or not right_widget:
            print("错误: 找不到左右部件")
            return
            
        # 获取左侧子部件
        avatar_label = left_widget.layout().itemAt(1).widget().layout().itemAt(0).widget()
        avatar_label.load_image(char_window.result_data['character']['name'])
        char_info = left_widget.layout().itemAt(2).widget()
        
        # 获取右侧子部件
        weapon_label = right_widget.layout().itemAt(0).widget()
        artifact_label = right_widget.layout().itemAt(1).widget()
        
        if not all([avatar_label, char_info, weapon_label, artifact_label]):
            print("错误: 找不到所有必需的标签部件")
            return
        
        # 检查并更新UI
        if hasattr(char_window, 'result_data') and char_window.result_data:
            data = char_window.result_data
            print(f"更新槽位 {slot_idx} 的数据: {data}")  # 调试日志
            
            try:
                # 更新角色信息
                char_info.setText(f"Lv.{data['character']['level']}\n"
                                f"天赋:{data['character']['talents']}")
                
                # 更新武器信息
                weapon_label.setText(f"{data['weapon']['name']}\n"
                                   f"Lv.{data['weapon']['level']}")
                
                # 更新圣遗物套装效果
                artifact_sets = {}
                for artifact in data['artifacts']:
                    set_name = artifact['set_name']
                    artifact_sets[set_name] = artifact_sets.get(set_name, 0) + 1
                
                set_effects = [
                    f"{set_name} {count}件" 
                    for set_name, count in artifact_sets.items() 
                    if count >= 2
                ]
                
                artifact_label.setText("\n".join(set_effects) if set_effects else "无套装")
                print(f"槽位 {slot_idx} 更新成功")
            except Exception as e:
                print(f"更新UI时出错: {str(e)}")
                # 出错时重置为初始状态
                self._reset_slot_display(char_info, weapon_label, artifact_label)
        else:
            print(f"槽位 {slot_idx} 没有有效数据，重置显示")
            self._reset_slot_display(char_info, weapon_label, artifact_label)

    def _clear_character_slot(self, slot_idx):
        """清除指定槽位的角色数据"""
        if slot_idx in self.character_windows:
            # 删除角色窗口实例
            self.character_windows[slot_idx].deleteLater()
            del self.character_windows[slot_idx]
            # 立即重置槽位显示
            self._reset_slot_display_by_index(slot_idx)
        else:
            # 对于未初始化的槽位，手动重置显示
            team_frame = self.centralWidget().layout().itemAt(2).widget()
            if not team_frame:
                return
                
            char_slots = team_frame.layout().itemAt(0)
            if not char_slots or slot_idx >= char_slots.count():
                return
                
            slot_container = char_slots.itemAt(slot_idx).widget()
            if not slot_container:
                return
            
            left_widget = slot_container.layout().itemAt(0).widget()
            right_widget = slot_container.layout().itemAt(1).widget()
            
            if left_widget and right_widget:
                char_info = left_widget.layout().itemAt(2).widget()
                weapon_label = right_widget.layout().itemAt(0).widget()
                artifact_label = right_widget.layout().itemAt(1).widget()
                self._reset_slot_display(char_info, weapon_label, artifact_label)

    def _reset_data(self):
        """重置数据"""
        self.logger.log_button_click("重置配置")
        from PySide6.QtWidgets import QMessageBox
        
        # 创建选择对话框
        msg_box = QMessageBox()
        msg_box.setWindowTitle("重置选项")
        msg_box.setText("请选择要重置的内容:")
        reset_chars = msg_box.addButton("重置角色", QMessageBox.ActionRole)
        reset_actions = msg_box.addButton("重置动作序列", QMessageBox.ActionRole)
        msg_box.addButton("取消", QMessageBox.RejectRole)
        
        msg_box.exec()
        clicked_button = msg_box.clickedButton()
        
        if clicked_button == reset_chars:  # 重置角色
            self.logger.log_button_click("执行角色重置")
            # 清空所有角色数据并更新显示
            for slot_idx in range(4):
                self._clear_character_slot(slot_idx)
        
        elif clicked_button == reset_actions:  # 重置动作序列
            self.logger.log_button_click("执行动作序列重置")
            # 删除所有动作卡片
            for i in reversed(range(self.action_container_layout.count())):
                widget = self.action_container_layout.itemAt(i).widget()
                if isinstance(widget, ActionCard):
                    widget.deleteLater()
            
            # 显示初始提示并确保布局更新
            if hasattr(self, 'hint_container') and self.hint_container:
                self.hint_container.setVisible(True)
                self.action_container.layout().update()

    def _reset_slot_display(self, char_info, weapon_label, artifact_label):
        """重置角色槽显示为初始状态"""
        char_info.setText("Lv.0\n天赋:0/0/0")
        weapon_label.setText("无武器")
        artifact_label.setText("无套装")
        # 重置头像显示为背景状态
        avatar_container = char_info.parent().layout().itemAt(1).widget()
        avatar_label = avatar_container.layout().itemAt(0).widget()
        avatar_label.clear_image()

    def _reset_slot_display_by_index(self, slot_idx):
        """通过槽位索引重置显示"""
        # 获取角色槽容器
        team_frame = self.centralWidget().layout().itemAt(2).widget()
        if not team_frame:
            return
            
        char_slots = team_frame.layout().itemAt(0)
        if not char_slots or slot_idx >= char_slots.count():
            return
            
        slot_container = char_slots.itemAt(slot_idx).widget()
        if not slot_container:
            return
            
        # 获取左右部件
        left_widget = slot_container.layout().itemAt(0).widget()
        right_widget = slot_container.layout().itemAt(1).widget()
        
        if left_widget and right_widget:
            char_info = left_widget.layout().itemAt(2).widget()
            weapon_label = right_widget.layout().itemAt(0).widget()
            artifact_label = right_widget.layout().itemAt(1).widget()
            self._reset_slot_display(char_info, weapon_label, artifact_label)

    def _add_action_card(self):
        """添加动作卡片"""
        self.logger.log_button_click("添加动作卡片")
        # 检查是否有角色
        has_character = False
        character_names = []
        for window in self.character_windows.values():
            if hasattr(window, 'result_data') and window.result_data:
                has_character = True
                character_names.append(window.result_data['character']['name'])
        
        if not has_character:
            error_msg = "添加动作卡片失败: 请先设置角色"
            self.logger.log_ui_error(error_msg)
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "警告", error_msg)
            return
            
        # 弹出设置对话框
        from character import character_table
        dialog = ActionSettingDialog({k: character_table[k] for k in character_names}, parent=self)
        dialog.setting_completed.connect(lambda data: self._handle_action_data(data))
        dialog.exec()
            
    def _handle_action_data(self, data):
        """处理动作数据并创建卡片"""
        try:
            # 隐藏初始提示
            if hasattr(self, 'hint_container') and self.hint_container:
                self.hint_container.setVisible(False)
            
            # 创建卡片
            card = ActionCard(self)
            # 在添加按钮之前插入新卡片
            insert_pos = max(0, self.action_container_layout.count()-1)
            self.action_container_layout.insertWidget(insert_pos, card)
            
            # 更新卡片数据
            self._update_action_card(card, data)
            
            # 记录成功创建动作卡片
            action_info = f"角色:{data['character']} 动作:{data['action']}"
            if data.get('params'):
                params_str = ', '.join(f"{k}:{v}" for k,v in data['params'].items())
                action_info += f" 参数:{params_str}"
            self.logger.log_button_click(f"成功创建动作卡片 - {action_info}")
            
            # 确保滚动到最右侧
            scroll_area = self.findChild(QScrollArea)
            if scroll_area:
                scroll_bar = scroll_area.horizontalScrollBar()
                # 使用定时器确保在布局更新后执行滚动
                from PySide6.QtCore import QTimer
                QTimer.singleShot(100, lambda: scroll_bar.setValue(scroll_bar.maximum()))
        except Exception as e:
            error_msg = f"创建动作卡片失败: {str(e)}"
            self.logger.log_ui_error(error_msg)

    def _update_action_card(self, card, data):
        """更新动作卡片显示"""
        try:
            card.update_data(data)
            action_info = f"角色:{data['character']} 动作:{data['action']}"
            if data.get('params'):
                params_str = ', '.join(f"{k}:{v}" for k,v in data['params'].items())
                action_info += f" 参数:{params_str}"
            self.logger.log_button_click(f"成功更新动作卡片 - {action_info}")
        except Exception as e:
            error_msg = f"更新动作卡片失败: {str(e)}"
            self.logger.log_ui_error(error_msg)

    def _save_data(self):
        """保存数据到文件"""
        self.logger.log_button_click("保存配置")
        try:
            # 确保data目录存在
            os.makedirs("./data", exist_ok=True)
            
            # 让用户选择保存位置和文件名
            filename, _ = QFileDialog.getSaveFileName(
                self, 
                "保存配置", 
                "./data", 
                "JSON文件 (*.json)"
            )
            
            # 如果用户取消选择，使用自动生成的文件名
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"./data/config_{timestamp}.json"
            
            # 获取数据
            team_data, action_sequence, target_data = self.get_data()
            
            # 保存到文件
            with open(filename, "w", encoding="utf-8") as f:
                json.dump({
                    "team_data": team_data,
                    "action_sequence": action_sequence,
                    'target_data': target_data
                }, f, ensure_ascii=False, indent=2)
            
            # 更新最后保存的文件路径配置
            from core.Config import Config
            Config.set("ui.last_save_file", filename)
            Config.save()
                
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "保存成功", f"配置已保存到: {filename}")
            self.logger.log_button_click(f"成功保存配置到: {filename}")
            
        except Exception as e:
            error_msg = f"保存配置时出错: {str(e)}"
            self.logger.log_ui_error(error_msg)
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "保存失败", error_msg)

    def _load_data(self):
        """从文件加载数据"""
        self.logger.log_button_click("加载配置")
        try:
            # 选择文件
            filename, _ = QFileDialog.getOpenFileName(
                self, "选择配置文件", "./data", "JSON文件 (*.json)")
            
            if not filename:
                return
                
            # 读取文件
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # 1. 恢复角色数据
            for slot_idx, char_data in enumerate(data["team_data"]):
                if "error" in char_data:
                    continue
                    
                # 创建或获取角色窗口
                if slot_idx not in self.character_windows:
                    self.character_windows[slot_idx] = CharacterWindow(self)
                    self.character_windows[slot_idx].finished.connect(
                        lambda data, idx=slot_idx: self._update_slot_display(idx))
                
                # 设置角色数据
                char_window = self.character_windows[slot_idx]
                char_window.result_data = char_data
                char_window._update_ui_from_data()
                self._update_slot_display(slot_idx)
            
            # 2. 恢复动作序列
            # 清除现有动作卡片
            for i in reversed(range(self.action_container_layout.count())):
                widget = self.action_container_layout.itemAt(i).widget()
                if isinstance(widget, ActionCard):
                    widget.deleteLater()
            
            # 重建动作卡片
            self.hint_container.setVisible(False)
            for action_data in data["action_sequence"]:
                card = ActionCard(self)
                self.action_container_layout.insertWidget(
                    self.action_container_layout.count()-1, card)
                card.update_data({
                    "character": action_data["character"],
                    "action": action_data["action"],
                    "params": action_data["params"]
                })
            
            # 3. 恢复目标数据
            self.config_widegt.set_config(data['target_data'])

            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "加载成功", f"已从 {filename} 加载配置")
            self.logger.log_button_click(f"成功加载配置: {filename}")
            
        except Exception as e:
            error_msg = f"加载配置时出错: {str(e)}"
            self.logger.log_ui_error(error_msg)
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "加载失败", error_msg)

    def get_data(self):
        """获取当前配置数据"""
        # 1. 收集队伍信息
        team_data = []
        for slot_idx in range(4):  # 遍历4个角色槽
            if slot_idx in self.character_windows:
                char_window = self.character_windows[slot_idx]
                if hasattr(char_window, 'result_data') and char_window.result_data:
                    team_data.append(char_window.result_data)
                else:
                    team_data.append({"error": f"角色槽 {slot_idx+1} 未配置有效数据"})
            else:
                team_data.append({"error": f"角色槽 {slot_idx+1} 未配置"})

        # 2. 收集动作序列
        action_sequence = []
        for i in range(self.action_container_layout.count()):
            widget = self.action_container_layout.itemAt(i).widget()
            if isinstance(widget, ActionCard):
                # 从卡片UI反向提取数据
                action_data = {
                    "character": widget.char_label.text().replace("角色: ", ""),
                    "action": widget.action_label.text().replace("动作: ", ""),
                    "params": {}
                }
                
                # 提取参数
                for j in range(widget.param_layout.count()):
                    param_widget = widget.param_layout.itemAt(j).widget()
                    if isinstance(param_widget, QLabel) and ":" in param_widget.text():
                        name, value = param_widget.text().split(":", 1)
                        action_data["params"][name.strip()] = value.strip()

                action_sequence.append(action_data)

        target_data = self.config_widegt.get_target_data()

        # 3. 验证数据
        if not any(data.get("character") for data in team_data if isinstance(data, dict)):
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "错误", "至少需要配置一个角色")
            return

        if not action_sequence:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "错误", "请添加至少一个动作")
            return
        
        if not target_data:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "错误", "请配置目标数据")
            return

        return team_data, action_sequence, target_data


def simulate_multi(team_data, action_sequence, target_data, sim_file_path, sim_id, uid):
    Emulation.emulation_init()
    from main import init
    init()
    e = Emulation(team_data, action_sequence, target_data)
    return e.simulate_multi(sim_file_path, sim_id, uid)

def error_callback(error):
    get_ui_logger().log_ui_error(error)

def callback(result):
    if result['status'] == 'success':
        get_ui_logger().log_info(f"模拟完成: {result['sim_id']}")
    else:
        get_ui_logger().log_ui_error(f"模拟失败: {result['sim_id']}")