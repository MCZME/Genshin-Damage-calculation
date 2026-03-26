"""设置界面状态管理器。"""
from __future__ import annotations

import flet as ft
from dataclasses import dataclass, field
from typing import Any, cast

from core.config import Config


@ft.observable
@dataclass
class SettingsState:
    """
    设置界面状态管理器。

    管理所有配置项的本地状态，支持撤销/重置操作。
    """

    # 本地配置副本，用于编辑时暂存
    _local_config: dict = field(default_factory=dict)

    # 脏标记：是否有未保存的修改
    is_dirty: bool = False

    # 当前展开的分组ID
    expanded_section: str = "emulation"

    def __post_init__(self) -> None:
        self._sync_from_config()

    def _sync_from_config(self) -> None:
        """从全局 Config 同步到本地状态"""
        self._local_config = dict(Config.config or {})
        self.is_dirty = False
        self.notify_update()

    def notify_update(self) -> None:
        """触发 UI 更新"""
        cast(Any, self).notify()

    def get_value(self, key: str, default: Any = None) -> Any:
        """获取配置值（从本地副本）"""
        keys = key.split(".")
        value = self._local_config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set_value(self, key: str, value: Any) -> None:
        """设置配置值（写入本地副本）"""
        keys = key.split(".")
        current = self._local_config

        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value
        self.is_dirty = True
        self.notify_update()

    def save_to_config(self) -> None:
        """将本地配置保存到全局 Config"""
        Config.config = self._local_config
        Config.save()
        self.is_dirty = False
        self.notify_update()

    def reset_to_config(self) -> None:
        """放弃修改，重置为全局 Config 的值"""
        self._sync_from_config()
        self.notify_update()

    def toggle_section(self, section_id: str) -> None:
        """切换展开的分组"""
        self.expanded_section = section_id if self.expanded_section != section_id else ""
        self.notify_update()
