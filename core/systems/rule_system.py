"""规则子系统：管理规则实例的完整生命周期。"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TYPE_CHECKING

from core.systems.base_system import GameSystem
from core.rules.base import RuleTypeBase, ApplyMode
from core.rules.instance import RuleInstance
from core.registry import RuleTypeMap
from core.logger import get_emulation_logger

if TYPE_CHECKING:
    from core.context import EventEngine


class RuleSystem(GameSystem):
    """
    规则子系统。

    管理规则实例的完整生命周期，作为 SimulationContext 的子系统运行。
    支持两种应用模式：一次性应用和事件订阅应用。
    """

    def __init__(self) -> None:
        super().__init__()
        self._logger = get_emulation_logger()
        self._instances: list[RuleInstance] = []
        self._subscriptions: dict[str, Callable] = {}
        self._applied: bool = False

    def register_events(self, engine: EventEngine) -> None:
        """注册事件监听。"""
        # 规则系统通过 apply_all() 在模拟开始前触发，订阅类规则在此注册事件
        pass

    # === 实例管理 ===

    def add_instance(self, instance: RuleInstance) -> None:
        """添加规则实例。"""
        self._instances.append(instance)
        self._logger.log_debug(
            f"规则实例已注册: [{instance.rule_type_id}]",
            sender="RuleSystem"
        )

    def remove_instance(self, instance_id: str) -> None:
        """移除规则实例。"""
        keys_to_remove = [k for k in self._subscriptions if k.startswith(f"{instance_id}:")]
        for key in keys_to_remove:
            self._unsubscribe_by_key(key)
        self._instances = [i for i in self._instances if i.instance_id != instance_id]

    def get_instance(self, instance_id: str) -> RuleInstance | None:
        """获取指定实例。"""
        for instance in self._instances:
            if instance.instance_id == instance_id:
                return instance
        return None

    def get_instances(self) -> list[RuleInstance]:
        """获取所有实例。"""
        return self._instances.copy()

    def clear_instances(self) -> None:
        """清空所有实例并取消所有订阅。"""
        for key in list(self._subscriptions.keys()):
            self._unsubscribe_by_key(key)
        self._instances.clear()
        self._applied = False

    # === 规则应用 ===

    def apply_all(self) -> None:
        """应用所有已启用的规则实例。"""
        if self._applied:
            return

        once_count = 0
        subscribe_count = 0

        for instance in self._instances:
            if not instance.enabled:
                continue

            rule_type = instance.get_rule_type()
            if rule_type is None:
                self._logger.log_info(f"未知规则类型: {instance.rule_type_id}", sender="RuleSystem")
                continue

            if rule_type.apply_mode == ApplyMode.ONCE:
                self._apply_once(instance, rule_type)
                once_count += 1
            else:
                self._subscribe(instance, rule_type)
                subscribe_count += 1

        self._applied = True
        self._logger.log_info(
            f"已应用 {once_count} 条一次性规则，{subscribe_count} 条订阅规则",
            sender="RuleSystem"
        )

    def _apply_once(self, instance: RuleInstance, rule_type: RuleTypeBase) -> None:
        """一次性应用规则。"""
        if self.context is None:
            return

        rule_type.apply(instance.params, self.context)

        self._logger.log_debug(
            f"规则 [{rule_type.display_name}] 已应用",
            sender="RuleSystem"
        )

    def _subscribe(self, instance: RuleInstance, rule_type: RuleTypeBase) -> None:
        """订阅事件。"""
        if self.context is None or self.engine is None:
            return
        event_type = rule_type.get_event_filter()
        if not event_type:
            return

        ctx = self.context  # 捕获以供闭包使用

        def handler(event: Any) -> None:
            rule_type.on_event(event, instance.params, ctx)

        self.engine.subscribe(event_type, handler)
        key = f"{instance.instance_id}:{event_type}"
        self._subscriptions[key] = handler

        self._logger.log_debug(
            f"规则 [{rule_type.display_name}] 已订阅事件: {event_type}",
            sender="RuleSystem"
        )

    def _unsubscribe_by_key(self, key: str) -> None:
        """根据 key 取消订阅。"""
        handler = self._subscriptions.pop(key, None)
        if handler is None or self.engine is None:
            return
        event_type = key.split(":")[1]
        self.engine.unsubscribe(event_type, handler)

    # === 持久化 ===

    def export_config(self) -> dict[str, Any]:
        """导出为配置字典。"""
        return {"rules": [i.to_dict() for i in self._instances]}

    def import_config(self, data: dict[str, Any]) -> None:
        """从配置字典导入。"""
        self._instances = [RuleInstance.from_dict(r) for r in data.get("rules", [])]
        self._applied = False

    # === 静态辅助 ===

    @staticmethod
    def get_available_rule_types() -> dict[str, dict[str, Any]]:
        """获取所有已注册规则类型的 schema。"""
        schemas = {}
        for rule_type_id, rule_type in RuleTypeMap.items():
            schemas[rule_type_id] = rule_type.get_schema()
        return schemas
