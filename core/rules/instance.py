"""规则实例定义。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from core.rules.base import RuleTypeBase


@dataclass
class RuleInstance:
    """
    规则实例：具体的规则应用配置。

    规则实例引用一个规则类型，持有具体参数值，
    是实际被配置、保存、应用的单元。
    """

    # 实例唯一标识
    instance_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    # 引用的规则类型 ID
    rule_type_id: str = ""
    # 具体参数
    params: dict[str, Any] = field(default_factory=dict)
    # 是否启用
    enabled: bool = True

    # 运行时缓存（不持久化）
    _rule_type: RuleTypeBase | None = field(default=None, repr=False, compare=False)

    def get_rule_type(self) -> RuleTypeBase | None:
        """
        获取关联的规则类型对象。

        Returns:
            规则类型实例，如果未找到返回 None
        """
        if self._rule_type is None and self.rule_type_id:
            from core.registry import RuleTypeMap
            self._rule_type = RuleTypeMap.get(self.rule_type_id)
        return self._rule_type

    def to_dict(self) -> dict[str, Any]:
        """
        序列化为字典（不含运行时缓存）。

        Returns:
            可 JSON 序列化的字典
        """
        return {
            "instance_id": self.instance_id,
            "rule_type_id": self.rule_type_id,
            "params": self.params,
            "enabled": self.enabled
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RuleInstance:
        """
        从字典创建实例。

        Args:
            data: 字典数据

        Returns:
            RuleInstance 实例
        """
        return cls(
            instance_id=data.get("instance_id", str(uuid.uuid4())[:8]),
            rule_type_id=data.get("rule_type_id", ""),
            params=data.get("params", {}),
            enabled=data.get("enabled", True)
        )
