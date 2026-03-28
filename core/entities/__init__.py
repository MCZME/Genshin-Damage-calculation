"""
实体模块。

提供仿真世界中所有实体类型的定义。
"""

from core.entities.base_entity import BaseEntity, CombatEntity, EntityState, Faction
from core.entities.attack_entity import AttackEntity, AttackTriggerType, TargetingMode
from core.entities.scene_entity import SceneEntity
from core.entities.elemental_entities import DendroCoreEntity, CrystalShardEntity
from core.entities.lunar_entities import (
    ProsperousCoreEntity,
    ThunderCloudEntity,
    LunarCageEntity,
)

__all__ = [
    # 基础实体
    "BaseEntity",
    "CombatEntity",
    "EntityState",
    "Faction",
    # 攻击实体
    "AttackEntity",
    "AttackTriggerType",
    "TargetingMode",
    # 场景实体
    "SceneEntity",
    # 元素实体
    "DendroCoreEntity",
    "CrystalShardEntity",
    # 月曜实体
    "ProsperousCoreEntity",
    "ThunderCloudEntity",
    "LunarCageEntity",
]
