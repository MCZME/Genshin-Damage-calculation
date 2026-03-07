from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import flet as ft
from core.data.repository import DataRepository

@dataclass
class AssetOption:
    """轻量级资产选项 DTO (Data Transfer Object)"""
    id: str
    name: str
    icon_path: str
    rarity: int
    element: str = "Neutral"
    type: str = "Unknown"
    is_implemented: bool = True

@ft.observable
class LibraryViewModel:
    """
    资产库视图模型：管理全局静态资产元数据。
    负责加载数据库数据并转换为 UI 友好的 AssetOption 列表。
    """
    def __init__(self, repo: DataRepository):
        self._repo = repo
        self._chars: List[AssetOption] = []
        self._weapons: Dict[str, List[AssetOption]] = {}
        self._artifacts: List[str] = []
        
        # 缓存已实装名单
        self.implemented_chars = set()
        self.implemented_weapons = set()
        
    def initialize(self):
        """同步实装名单并加载数据"""
        from core.registry import CharacterClassMap, WeaponClassMap, ArtifactSetMap
        self.implemented_chars = set(CharacterClassMap.keys())
        self.implemented_weapons = set(WeaponClassMap.keys())
        
        self.refresh_data()

    def refresh_data(self):
        """重新从仓库加载元数据"""
        # 1. 加载角色列表
        raw_chars = self._repo.get_all_characters()
        self._chars = [
            AssetOption(
                id=str(c["id"]), name=c["name"], rarity=c["rarity"],
                element=c["element"], type=c["type"],
                icon_path=f"assets/avatars/{c['id']}.png",
                is_implemented=c["name"] in self.implemented_chars
            ) for c in raw_chars
        ]
        
        # 2. 加载武器 (按类型缓存)
        weapon_types = ["单手剑", "双手剑", "长柄武器", "法器", "弓"]
        for wt in weapon_types:
            raw_ws = self._repo.get_weapons_by_type(wt)
            self._weapons[wt] = [
                AssetOption(
                    id=w["name"], name=w["name"], rarity=w["rarity"],
                    type=wt, icon_path=f"assets/weapons/{w['name']}.png",
                    is_implemented=w["name"] in self.implemented_weapons
                ) for w in raw_ws
            ]
            
        # 3. 加载圣遗物套装
        self._artifacts = self._repo.get_all_artifact_sets()
        self.notify()

    @property
    def character_options(self) -> List[AssetOption]:
        """获取所有可用角色选项"""
        return self._chars

    def get_weapon_options(self, weapon_type: str) -> List[AssetOption]:
        """根据武器类型获取可选武器"""
        return self._weapons.get(weapon_type, [])

    @property
    def artifact_set_options(self) -> List[str]:
        """获取所有圣遗物套装名称"""
        return self._artifacts
