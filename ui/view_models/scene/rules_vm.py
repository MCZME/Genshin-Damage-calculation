"""规则配置 ViewModel。"""

from __future__ import annotations

import json
import os
import uuid

import flet as ft
from dataclasses import dataclass, field
from typing import Any

from core.registry import RuleTypeMap
from core.logger import get_ui_logger


# 目标类型的显示名称
TARGET_DISPLAY_NAMES: dict[str, str] = {
    "all_characters": "所有角色",
    "all_targets": "所有目标"
}


@ft.observable
@dataclass
class RuleInstanceVM:
    """单条规则实例 ViewModel。"""

    instance_id: str
    rule_type_id: str
    target: str = "all_characters"
    params: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

    # 运行时缓存（不参与响应式）
    _rule_type: Any = field(default=None, repr=False, compare=False)

    def get_rule_type(self) -> Any:
        """获取关联的规则类型对象。"""
        if self._rule_type is None:
            self._rule_type = RuleTypeMap.get(self.rule_type_id)
        return self._rule_type

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典。"""
        return {
            "instance_id": self.instance_id,
            "rule_type_id": self.rule_type_id,
            "target": self.target,
            "params": self.params,
            "enabled": self.enabled
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RuleInstanceVM:
        """从字典创建实例。"""
        return cls(
            instance_id=data.get("instance_id", str(uuid.uuid4())[:8]),
            rule_type_id=data.get("rule_type_id", ""),
            target=data.get("target", "all_characters"),
            params=data.get("params", {}),
            enabled=data.get("enabled", True)
        )


@ft.observable
@dataclass
class RulesViewModel:
    """规则配置 ViewModel。"""

    instances: list[RuleInstanceVM] = field(default_factory=list)

    @property
    def rule_type_schemas(self) -> dict[str, dict[str, Any]]:
        """获取所有已注册规则类型的 schema。"""
        schemas = {}
        for rule_type_id, rule_type in RuleTypeMap.items():
            schemas[rule_type_id] = rule_type.get_schema()
        return schemas

    @property
    def target_display_names(self) -> dict[str, str]:
        """获取目标类型显示名称。"""
        return TARGET_DISPLAY_NAMES

    def add_rule(
        self,
        rule_type_id: str,
        target: str = "all_characters",
        params: dict[str, Any] | None = None
    ) -> None:
        """添加新规则实例。"""
        instance = RuleInstanceVM(
            instance_id=str(uuid.uuid4())[:8],
            rule_type_id=rule_type_id,
            target=target,
            params=params or self._get_default_params(rule_type_id)
        )
        self.instances.append(instance)

    def remove_rule(self, instance_id: str) -> None:
        """移除规则实例。"""
        self.instances = [i for i in self.instances if i.instance_id != instance_id]

    def update_rule_target(self, instance_id: str, target: str) -> None:
        """更新规则目标。"""
        for instance in self.instances:
            if instance.instance_id == instance_id:
                instance.target = target
                break

    def update_rule_param(self, instance_id: str, key: str, value: Any) -> None:
        """更新规则参数。"""
        for instance in self.instances:
            if instance.instance_id == instance_id:
                instance.params[key] = value
                break

    def toggle_rule_enabled(self, instance_id: str) -> None:
        """切换规则启用状态。"""
        for instance in self.instances:
            if instance.instance_id == instance_id:
                instance.enabled = not instance.enabled
                break

    def clear_rules(self) -> None:
        """清空所有规则实例。"""
        self.instances.clear()

    def to_dict(self) -> dict[str, Any]:
        """导出为字典格式。"""
        return {"rules": [i.to_dict() for i in self.instances]}

    def load_from_dict(self, data: dict[str, Any]) -> None:
        """从字典加载。"""
        self.instances = [RuleInstanceVM.from_dict(r) for r in data.get("rules", [])]

    def save_to_file(self, filepath: str) -> None:
        """保存规则配置到文件。"""
        if not filepath.endswith(".json"):
            filepath += ".json"
        if not os.path.isabs(filepath):
            filepath = os.path.join("data/rules", filepath)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=4)
        get_ui_logger().log_info(f"规则配置已保存: {filepath}")

    def load_from_file(self, filepath: str) -> bool:
        """从文件加载规则配置。"""
        if not filepath.endswith(".json"):
            filepath += ".json"
        if not os.path.isabs(filepath):
            filepath = os.path.join("data/rules", filepath)
        if not os.path.exists(filepath):
            get_ui_logger().log_info(f"规则配置文件不存在: {filepath}")
            return False
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.load_from_dict(data)
        get_ui_logger().log_info(f"规则配置已加载: {filepath}")
        return True

    def _get_default_params(self, rule_type_id: str) -> dict[str, Any]:
        """获取规则类型的默认参数。"""
        rule_type = RuleTypeMap.get(rule_type_id)
        if rule_type is None:
            return {}
        schema = rule_type.get_schema()
        return {p["key"]: p.get("default") for p in schema.get("params", [])}

    def get_rule_display_name(self, rule_type_id: str) -> str:
        """获取规则类型的显示名称。"""
        rule_type = RuleTypeMap.get(rule_type_id)
        if rule_type is None:
            return rule_type_id
        return rule_type.display_name

    def sync_to_system(self, rule_system: Any) -> None:
        """将当前状态同步到规则系统。"""
        from core.rules.instance import RuleInstance
        rule_system.clear_instances()
        for vm in self.instances:
            rule_system.add_instance(RuleInstance(
                instance_id=vm.instance_id,
                rule_type_id=vm.rule_type_id,
                target=vm.target,
                params=vm.params.copy(),
                enabled=vm.enabled
            ))

    def sync_from_system(self, rule_system: Any) -> None:
        """从规则系统同步状态。"""
        self.instances = [
            RuleInstanceVM(
                instance_id=i.instance_id,
                rule_type_id=i.rule_type_id,
                target=i.target,
                params=i.params.copy(),
                enabled=i.enabled
            )
            for i in rule_system.get_instances()
        ]
