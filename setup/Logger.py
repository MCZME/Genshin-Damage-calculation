import time
from setup.Config import Config
from setup.Tool import GetCurrentTime

class BaseLogger:
    def __init__(self, name):
        self.name = name
        self.log_file = None
        
    def _write_log(self, level, message):
        """基础日志写入方法"""
        log_entry = f"[{GetCurrentTime()}][{level}][{self.name}] {message}\n"
        
        # 写入文件
        if Config.get('logging.save_file'):
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
            
        # 同时输出到控制台
        print(log_entry.strip())

class EmulationLogger(BaseLogger):
    def __init__(self):
        super().__init__("Emulation")
        self.new_log_file()
        
    def new_log_file(self):
        """创建新的日志文件"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.log_file = Config.get('logging.Emulation.file_path')+f"emulation_{timestamp}.log"
        
    def log_skill_use(self, character, skill_name):
        """记录技能使用日志"""
        message = f"{character.name} 使用 {skill_name}"
        self._write_log("INFO", message)
        
    def log_damage(self, source, target, damage):
        """记录伤害计算日志"""
        element_icons = {
            '物理': '⚔️',
            '水': '🌊', 
            '火': '🔥',
            '冰': '❄️',
            '风': '🌪️',
            '雷': '⚡',
            '岩': '⛰️',
            '草': '🌿'
        }
        e = element_icons.get(damage.element[0], '❓')
        if Config.get('logging.Emulation.damage'):
            message = (f"{e} {source.name}使用 {damage.name} 对{target.name} "
                  f"造成{damage.damage:.2f}点 {damage.element[0]+'元素' if damage.element[0] != '物理' else damage.element[0]} 伤害")
            self._write_log("DAMAGE", message)
        
    def log_heal(self, source, target, heal):
        """记录治疗效果日志"""
        if Config.get('logging.Emulation.heal'):
            message = f'💚 {source.name} 使用 {heal.name} 治疗 {target.name} {heal.final_value:.2f} 生命值'
            self._write_log("HEAL", message)

    def log_energy(self, character, energy_value):
        """记录能量恢复日志"""
        if Config.get('logging.Emulation.energy'):
            message = f"🔋 {character.name} 恢复 {energy_value:.2f} 点元素能量"
            self._write_log("ENERGY", message)

    def log_error(self, error_msg):
        """记录错误日志"""
        self._write_log("ERROR", error_msg)

class UILogger(BaseLogger):
    def __init__(self):
        super().__init__("UI")
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.log_file = Config.get('logging.UI.file_path')+f"ui_{timestamp}.log"
        
    def _write_log(self, level, message):
        """重写日志写入方法，使用现实时间"""
        log_entry = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}][{level}][{self.name}] {message}\n"
        
        # 写入文件
        if Config.get('logging.save_file'):
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
            
        # 同时输出到控制台
        print(log_entry.strip())
        
    def log_button_click(self, button_name):
        """记录按钮点击日志"""
        if Config.get('logging.UI.button_click', True):
            self._write_log("INFO", f"点击按钮: {button_name}")
        
    def log_window_open(self, window_name):
        """记录窗口打开日志"""
        if Config.get('logging.UI.window_open', True):
            self._write_log("INFO", f"打开窗口: {window_name}")
        
    def log_ui_error(self, error_msg):
        """记录UI错误日志"""
        self._write_log("ERROR", error_msg)

# 全局日志实例
_ui_logger = None
_emulation_logger = None

def logger_init():
    global _ui_logger
    global _emulation_logger
    _ui_logger = UILogger()
    _emulation_logger = EmulationLogger()


def get_emulation_logger():
    return _emulation_logger

def get_ui_logger():
    return _ui_logger

def manage_log_files(max_files=50):
    """管理日志文件，当日志文件过多时按日期打包压缩
    
    Args:
        max_files (int): 触发压缩的日志文件数量阈值，默认50
    """
    import os
    import glob
    import zipfile
    from datetime import datetime
    
    def process_logs(log_dir, file_pattern):
        """处理指定目录和模式的日志文件"""
        if not log_dir or not os.path.exists(log_dir):
            return
            
        log_files = glob.glob(os.path.join(log_dir, file_pattern))
        if len(log_files) <= max_files:
            return
            
        # 按日期分组文件
        date_groups = {}
        for file_path in log_files:
            try:
                # 从文件名提取日期部分 (emulation_YYYYMMDD_HHMMSS.log 或 ui_YYYYMMDD_HHMMSS.log)
                date_str = os.path.basename(file_path).split('_')[1][:8]
                date = datetime.strptime(date_str, '%Y%m%d').date()
                if date not in date_groups:
                    date_groups[date] = []
                date_groups[date].append(file_path)
            except (IndexError, ValueError):
                continue
                
        # 为每个日期创建压缩包
        for date, files in date_groups.items():
            if len(files) < 2:  # 同一天少于2个文件不压缩
                continue
                
            zip_name = os.path.join(log_dir, f'logs_{date.strftime("%Y%m%d")}.zip')
            with zipfile.ZipFile(zip_name, 'a', zipfile.ZIP_DEFLATED) as zipf:
                for file in files:
                    zipf.write(file, os.path.basename(file))
                    os.remove(file)  # 压缩后删除原文件
    
    # 处理模拟日志
    emulation_log_dir = Config.get('logging.Emulation.file_path')
    process_logs(emulation_log_dir, 'emulation_*.log')
    
    # 处理UI日志
    ui_log_dir = Config.get('logging.UI.file_path')
    process_logs(ui_log_dir, 'ui_*.log')
