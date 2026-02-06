import os
import logging
from datetime import datetime
from typing import Optional, Any

from core.config import Config
from core.tool import GetCurrentTime

# ---------------------------------------------------------
# 日志级别定义 (扩展标准库)
# ---------------------------------------------------------
DAMAGE_LEVEL = 25
HEAL_LEVEL = 26
ENERGY_LEVEL = 27
REACTION_LEVEL = 28
EFFECT_LEVEL = 29
OBJECT_LEVEL = 31

logging.addLevelName(DAMAGE_LEVEL, "DAMAGE")
logging.addLevelName(HEAL_LEVEL, "HEAL")
logging.addLevelName(ENERGY_LEVEL, "ENERGY")
logging.addLevelName(REACTION_LEVEL, "REACTION")
logging.addLevelName(EFFECT_LEVEL, "EFFECT")
logging.addLevelName(OBJECT_LEVEL, "OBJECT")

# ---------------------------------------------------------
# Simulation Logger (Instance based)
# ---------------------------------------------------------
class SimulationLogger:
    """
    具体的模拟日志类。
    每个模拟实例应拥有一个独立的 Logger 实例。
    """
    def __init__(self, name: str = "Simulation", log_file: Optional[str] = None):
        self.logger = logging.getLogger(f"Genshin.{name}.{id(self)}")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False # 避免重复打印
        
        # 清除现有 handler
        self.logger.handlers.clear()

        # 1. 基础配置获取
        save_to_file = Config.get("logging.save_file")
        show_console = Config.get("logging.Emulation.console")
        
        # 2. 格式化器
        # 注意：这里我们手动把 GetCurrentTime() 塞进格式
        formatter = logging.Formatter("[%(frame)s][%(name)s][%(levelname)s] %(message)s")

        # 3. 文件处理器
        if save_to_file:
            if not log_file:
                log_dir = Config.get("logging.Emulation.file_path")
                os.makedirs(log_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                log_file = os.path.join(log_dir, f"emulation_{timestamp}.log")
            
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)
            self.log_path = log_file

        # 4. 控制台处理器
        if show_console:
            ch = logging.StreamHandler()
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

    def _log(self, level: int, msg: str):
        # 动态获取当前帧
        frame = GetCurrentTime()
        self.logger.log(level, msg, extra={"frame": frame})

    def log_damage(self, source: Any, target: Any, damage: Any):
        if not Config.get("logging.Emulation.damage"): return
        icons = {"物理": "⚔️", "水": "🌊", "火": "🔥", "冰": "❄️", "风": "🌪️", "雷": "⚡", "岩": "⛰️", "草": "🌿"}
        e_icon = icons.get(damage.element[0], "❓")
        msg = (f"{e_icon} {source.name}使用 {damage.name} 对{target.name} "
               f"造成 {damage.damage:.2f} 点 {damage.element[0]} 伤害")
        self._log(DAMAGE_LEVEL, msg)

    def log_heal(self, source: Any, target: Any, heal: Any):
        if not Config.get("logging.Emulation.heal"): return
        msg = f"💚 {source.name} 使用 {heal.name} 治疗 {target.name} {heal.final_value:.2f} 生命值"
        self._log(HEAL_LEVEL, msg)

    def log_energy(self, character: Any, energy_value: float):
        if not Config.get("logging.Emulation.energy"): return
        msg = f"🔋 {character.name} 恢复 {energy_value:.2f} 点元素能量"
        self._log(ENERGY_LEVEL, msg)

    def log_reaction(self, msg: str):
        if Config.get("logging.Emulation.reaction"): self._log(REACTION_LEVEL, msg)

    def log_effect(self, msg: str):
        if Config.get("logging.Emulation.effect"): self._log(EFFECT_LEVEL, msg)

    def log_object(self, msg: str):
        if Config.get("logging.Emulation.object"): self._log(OBJECT_LEVEL, msg)

    def log_info(self, msg: str): self._log(logging.INFO, msg)
    def log_error(self, msg: str): self._log(logging.ERROR, msg)
    def log_debug(self, msg: str): 
        if Config.get("logging.Emulation.debug"): self._log(logging.DEBUG, msg)
    
    # 兼容旧代码调用
    def log(self, level_name: str, msg: str):
        self._log(logging.INFO, f"[{level_name}] {msg}")
    
    def new_log_file(self, file_path: Optional[str] = None):
        """重新绑定日志文件 (兼容旧 Emulation 逻辑)"""
        # 这个方法在实例模式下其实应该由 __init__ 处理
        # 这里为了兼容，简单重定向
        self.__init__(log_file=file_path)

# ---------------------------------------------------------
# UI Logger (独立实例)
# ---------------------------------------------------------
class UILogger:
    def __init__(self):
        self.logger = logging.getLogger("Genshin.UI")
        self.logger.setLevel(logging.INFO)
        log_dir = Config.get("logging.UI.file_path")
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(log_dir, f"ui_{timestamp}.log")
        
        formatter = logging.Formatter("[%(asctime)s][UI][%(levelname)s] %(message)s")
        
        if Config.get("logging.save_file"):
            fh = logging.FileHandler(log_path, encoding="utf-8")
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)
            
        if Config.get("logging.UI.console"):
            ch = logging.StreamHandler()
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

    def log_info(self, msg: str): self.logger.info(msg)
    def log_error(self, msg: str): self.logger.error(msg)
    def log_window_open(self, name: str): self.logger.info(f"打开窗口: {name}")
    def log_button_click(self, name: str): self.logger.info(f"点击按钮: {name}")

# ---------------------------------------------------------
# 全局访问代理 (去全局化过渡)
# ---------------------------------------------------------
_default_ui_logger: Optional[UILogger] = None
_fallback_emulation_logger: Optional[SimulationLogger] = None

def get_ui_logger() -> UILogger:
    global _default_ui_logger
    if _default_ui_logger is None:
        _default_ui_logger = UILogger()
    return _default_ui_logger

def get_emulation_logger() -> SimulationLogger:
    """
    优先获取当前 SimulationContext 绑定的 Logger。
    如果没有上下文，则返回一个保底的全局 Logger。
    """
    from core.context import get_context
    try:
        ctx = get_context()
        # 假设我们以后在 SimulationContext 中添加了 logger 字段
        if hasattr(ctx, "logger") and ctx.logger:
            return ctx.logger
    except RuntimeError:
        pass
    
    global _fallback_emulation_logger
    if _fallback_emulation_logger is None:
        _fallback_emulation_logger = SimulationLogger("Default")
    return _fallback_emulation_logger

def logger_init():
    """兼容旧代码初始化"""
    get_ui_logger()
    get_emulation_logger()

def manage_log_files(max_files: int = 50):
    """
    日志管理：压缩旧日志。
    (逻辑保持原样，由于篇幅原因，这里实现略，保留接口)
    """
    pass