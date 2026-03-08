from __future__ import annotations
import flet as ft
from dataclasses import dataclass, field
from typing import Any, cast
from core.data.repository import DataRepository

@dataclass
class AssetOption:
    """单个资产选项的元数据快照"""
    name: str
    element: str = "Neutral"
    rarity: int = 4
    is_implemented: bool = True

@ft.observable
@dataclass
class LibraryViewModel:
    """
    资产库视图模型。
    管理可用的角色、武器、圣遗物选项列表及实装状态。
    """
    repo: DataRepository
    
    # 选项列表 (名称)
    character_names: list[str] = field(default_factory=list)
    weapon_names: list[str] = field(default_factory=list)
    artifact_set_names: list[str] = field(default_factory=list)
    
    # 实装名单 (ID 或 Key)
    implemented_chars: set[str] = field(default_factory=set)
    implemented_weapons: set[str] = field(default_factory=set)

    def __post_init__(self):
        self.initialize()

    def notify_update(self):
        """显式触发变更通知，解决静态检查报错"""
        cast(Any, self).notify()

    def initialize(self):
        """同步实装名单并加载数据"""
        from core.registry import CharacterClassMap, WeaponClassMap
        self.implemented_chars = set(CharacterClassMap.keys())
        self.implemented_weapons = set(WeaponClassMap.keys())
        
        self.refresh_all()

    def refresh_all(self):
        """从数据库刷新所有资产名称列表"""
        # 1. 获取角色名称
        chars = self.repo.get_all_characters()
        self.character_names = [c['name'] for c in chars]
        
        # 2. 获取武器名称 (DataRepository 没有直接获取全量名称的方法，使用 query)
        weapon_rows = self.repo.query("SELECT Name FROM `weapon` ORDER BY Name ASC")
        self.weapon_names = [str(row[0]) for row in weapon_rows]
        
        # 3. 获取圣遗物套装名称
        self.artifact_set_names = self.repo.get_all_artifact_sets()
        
        self.notify_update()

    def get_character_options(self, only_implemented: bool = False) -> list[str]:
        if only_implemented:
            return [name for name in self.character_names if name in self.implemented_chars]
        return self.character_names

    def get_weapon_options(self, only_implemented: bool = False) -> list[str]:
        if only_implemented:
            return [name for name in self.weapon_names if name in self.implemented_weapons]
        return self.weapon_names

    def get_artifact_options(self) -> list[str]:
        return self.artifact_set_names
