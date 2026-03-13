from __future__ import annotations

import logging
import os
import zipfile
from datetime import datetime
from typing import Any

from core.config import Config
from core.mechanics.aura import Element
from core.tool import get_current_time


# ---------------------------------------------------------
# Simulation Logger (Instance based)
# ---------------------------------------------------------
class SimulationLogger:
    """
    具体的模拟日志类。
    每个模拟实例应拥有一个独立的 Logger 实例。
    """

    def __init__(self, name: str = "Simulation", log_file: str | None = None) -> None:
        self.logger = logging.getLogger(f"Genshin.{name}.{id(self)}")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False  # 避免重复打印

        # 清除现有 handler
        self.logger.handlers.clear()

        # 1. 基础配置获取
        save_to_file = Config.get("logging.save_file")
        show_console = Config.get("logging.Emulation.console")

        # 2. 格式化器
        formatter = logging.Formatter(
            "[%(frame)s][%(name)s][%(levelname)s][%(sender)s] %(message)s"
        )

        # 3. 文件处理器
        if save_to_file:
            if not log_file:
                log_dir = Config.get("logging.Emulation.file_path")
                if not log_dir or not isinstance(log_dir, str):
                    raise ValueError("logging.Emulation.file_path 配置缺失")
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

    def _log(
        self, level: int, msg: str, payload: dict[str, Any] | None = None, sender: str = "System"
    ) -> None:
        # 动态获取当前帧
        frame = get_current_time()

        # 自动提取 [Sender] 标签 (如果 msg 以其开头)
        if msg.startswith("[") and "]" in msg:
            end_idx = msg.find("]")
            extracted_sender = msg[1:end_idx]
            if sender == "System":
                sender = extracted_sender
                msg = msg[end_idx + 1 :].strip()

        # 将 payload 和 sender 放入 extra 供 Handler 提取
        self.logger.log(
            level,
            msg,
            extra={"frame": frame, "payload": payload or {}, "sender": sender},
        )

    def log_damage(self, source: Any, target: Any, damage: Any) -> None:
        if not Config.get("logging.Emulation.damage"):
            return

        # 支持枚举或字符串
        el = damage.element[0]
        el_name = el.value if isinstance(el, Element) else str(el)

        icons: dict[str, str] = {
            "物理": "⚔️",
            "水": "🌊",
            "火": "🔥",
            "冰": "❄️",
            "风": "🌪️",
            "雷": "⚡",
            "岩": "⛰️",
            "草": "🌿",
            "冻": "🧊",
            "激": "🍃",
        }
        e_icon = icons.get(el_name, "❓")
        if el_name != "物理":
            el_name += "元素"

        msg = (
            f"{e_icon} {source.name}使用 {damage.name} 对{target.name} "
            f"造成 {damage.damage:.2f} 点 {el_name} 伤害"
        )

        payload = {
            "type": "damage",
            "source": source.name,
            "target": target.name,
            "damage_name": damage.name,
            "value": damage.damage,
            "element": el_name,
            "is_crit": getattr(damage, "is_crit", False),
        }
        self._log(logging.INFO, msg, payload, sender="Damage")

    def log_heal(self, source: Any, target: Any, heal: Any) -> None:
        if not Config.get("logging.Emulation.heal"):
            return
        msg = f"💚 {source.name} 使用 {heal.name} 治疗 {target.name} {heal.final_value:.2f} 生命值"

        payload = {
            "type": "heal",
            "source": source.name,
            "target": target.name,
            "heal_name": heal.name,
            "value": heal.final_value,
        }
        self._log(logging.INFO, msg, payload, sender="Heal")

    def log_energy(
        self, character: Any, energy_value: float, source_type: str = "微粒"
    ) -> None:
        if not Config.get("logging.Emulation.energy"):
            return
        msg = (
            f"🔋 {character.name} 获得了 {energy_value:.2f} 点元素能量 ({source_type})"
        )

        payload = {
            "type": "energy",
            "character": character.name,
            "value": energy_value,
            "source_type": source_type,
        }
        self._log(logging.INFO, msg, payload, sender="Energy")

    def log_reaction(self, source_char: Any, reaction_type: str, target: Any) -> None:
        if not Config.get("logging.Emulation.reaction"):
            return
        msg = f"🔁 {source_char.name} 触发了 {reaction_type} 反应"

        payload = {
            "type": "reaction",
            "source": source_char.name,
            "reaction": reaction_type,
            "target": target.name,
        }
        self._log(logging.INFO, msg, payload, sender="Reaction")

    def log_effect(self, owner: Any, effect_name: str, action: str = "获得") -> None:
        if not Config.get("logging.Emulation.effect"):
            return
        msg = f"✨ {owner.name} {action}了 {effect_name} 效果"

        payload = {
            "type": "effect",
            "owner": owner.name,
            "effect": effect_name,
            "action": action,
        }
        self._log(logging.INFO, msg, payload, sender="Effect")

    def log_shield(
        self, character: Any, shield_name: str, value: float, action: str = "获得"
    ) -> None:
        msg = f"🛡️ {character.name} {action}了 {shield_name} 护盾 (量级: {value:.2f})"
        payload = {
            "type": "shield",
            "character": character.name,
            "shield": shield_name,
            "value": value,
            "action": action,
        }
        self._log(logging.INFO, msg, payload, sender="Shield")

    def log_shield_break(self, character: Any, shield_name: str) -> None:
        msg = f"💥 {character.name} 的 {shield_name} 护盾已破裂"
        payload = {
            "type": "shield_break",
            "character": character.name,
            "shield": shield_name,
        }
        self._log(logging.INFO, msg, payload, sender="Shield")

    def log_skill_use(self, character: Any, skill_name: str) -> None:
        msg = f"🎯 {character.name} 释放了 {skill_name}"
        payload = {"type": "skill", "character": character.name, "skill": skill_name}
        self._log(logging.INFO, msg, payload, sender="Skill")

    def log_info(self, msg: str, sender: str = "System") -> None:
        self._log(logging.INFO, msg, sender=sender)

    def log_error(self, msg: str, sender: str = "Error") -> None:
        self._log(logging.ERROR, msg, sender=sender)

    def log_debug(self, msg: str, sender: str = "Debug") -> None:
        if Config.get("logging.Emulation.debug"):
            self._log(logging.DEBUG, msg, sender=sender)


# ---------------------------------------------------------
# UI Logger (独立实例)
# ---------------------------------------------------------
class UILogger:
    def __init__(self) -> None:
        self.logger = logging.getLogger("Genshin.UI")

        # 根据配置动态设置日志级别
        if Config.get("logging.UI.debug"):
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

        log_dir = Config.get("logging.UI.file_path")
        if not log_dir or not isinstance(log_dir, str):
            raise ValueError("logging.UI.file_path 配置缺失")
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

    def log_info(self, msg: str) -> None:
        self.logger.info(msg)

    def log_warning(self, msg: str) -> None:
        self.logger.warning(msg)

    def log_error(self, msg: str) -> None:
        self.logger.error(msg)

    def log_debug(self, msg: str) -> None:
        if Config.get("logging.UI.debug"):
            self.logger.debug(msg)

    def log_window_open(self, name: str) -> None:
        self.logger.info(f"打开窗口: {name}")

    def log_button_click(self, name: str) -> None:
        self.logger.info(f"点击按钮: {name}")


# ---------------------------------------------------------
# 全局访问代理 (去全局化过渡)
# ---------------------------------------------------------
_default_ui_logger: UILogger | None = None
_fallback_emulation_logger: SimulationLogger | None = None


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
        if hasattr(ctx, "logger") and ctx.logger:
            return ctx.logger
    except RuntimeError:
        pass

    global _fallback_emulation_logger
    if _fallback_emulation_logger is None:
        _fallback_emulation_logger = SimulationLogger("Default")
    return _fallback_emulation_logger


def logger_init() -> None:
    get_ui_logger()
    get_emulation_logger()


def manage_log_files(*, max_files: int = 50) -> None:
    """
    日志管理：压缩旧日志以节省空间。

    当 .log 文件数超过 max_files 时，将多余的旧日志压缩到一个 zip 文件中。

    Args:
        max_files: 每个日志目录保留的最大 .log 文件数
    """
    log_dirs: list[str] = []
    try:
        emulation_path = Config.get("logging.Emulation.file_path")
        if emulation_path and isinstance(emulation_path, str):
            log_dirs.append(emulation_path)
        ui_path = Config.get("logging.UI.file_path")
        if ui_path and isinstance(ui_path, str):
            log_dirs.append(ui_path)
    except Exception:
        return

    for log_dir in log_dirs:
        if not os.path.exists(log_dir):
            continue

        # 获取所有 .log 文件
        log_files = [
            os.path.join(log_dir, f)
            for f in os.listdir(log_dir)
            if f.endswith(".log")
        ]

        # 按修改时间从旧到新排序
        log_files.sort(key=os.path.getmtime)

        # 如果 .log 文件超过 max_files，压缩最旧的 max_files 个到一个 zip 包
        if len(log_files) > max_files:
            to_archive = log_files[:max_files]
            _archive_log_files(log_dir, to_archive)


def _archive_log_files(log_dir: str, files: list[str]) -> None:
    """将多个日志文件压缩到一个按时间命名的 zip 文件中。"""
    from datetime import datetime

    # 生成唯一的 zip 文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"logs_archive_{timestamp}.zip"
    zip_path = os.path.join(log_dir, zip_name)

    # 避免文件名冲突
    counter = 1
    while os.path.exists(zip_path):
        zip_name = f"logs_archive_{timestamp}_{counter}.zip"
        zip_path = os.path.join(log_dir, zip_name)
        counter += 1

    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in files:
                zipf.write(file_path, os.path.basename(file_path))
        # 压缩成功后删除原文件
        for file_path in files:
            os.remove(file_path)
    except Exception as e:
        print(f"[LogManager] 压缩失败: {e}")
