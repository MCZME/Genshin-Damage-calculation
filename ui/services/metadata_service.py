from typing import List, Dict, Any, Set
from core.data.repository import DataRepository
from core.registry import CharacterClassMap, WeaponClassMap, ArtifactSetMap
from core.logger import get_ui_logger

class MetadataService:
    """
    元数据服务：负责加载、缓存并提供游戏资产的静态信息。
    """
    def __init__(self, repo: DataRepository):
        self._repo = repo
        
        # 核心缓存
        self.char_map: Dict[str, Dict[str, Any]] = {}
        self.weapon_map: Dict[str, List[Dict[str, Any]]] = {}
        self.artifact_sets: List[str] = []
        self.target_map: Dict[str, Dict[str, Any]] = {}
        
        # 已实装名单
        self.implemented_chars: Set[str] = set()
        self.implemented_weapons: Set[str] = set()
        self.implemented_artifacts: Set[str] = set()

    def load_all(self):
        """同步加载所有必要的元数据"""
        try:
            # 1. 加载角色
            char_list = self._repo.get_all_characters()
            self.char_map = {
                c["name"]: {
                    "id": c["id"], 
                    "element": c["element"], 
                    "type": c["type"], 
                    "rarity": c.get("rarity", 5)
                }
                for c in char_list
            }
            
            # 2. 加载武器 (按类型分类缓存)
            weapon_types = ["单手剑", "双手剑", "长柄武器", "法器", "弓"]
            for wt in weapon_types:
                self.weapon_map[wt] = self._repo.get_weapons_by_type(wt)
                
            # 3. 加载圣遗物套装 (从注册表获取已实现的套装)
            self.artifact_sets = sorted(ArtifactSetMap.keys())

            # 4. 刷新已实装列表 (从注册表获取)
            self.implemented_chars = set(CharacterClassMap.keys())
            self.implemented_weapons = set(WeaponClassMap.keys())
            self.implemented_artifacts = set(ArtifactSetMap.keys())
            
            # 5. 初始化怪物映射 (未来可改为从 Repo 加载)
            self.target_map = self._get_default_target_map()
            
            get_ui_logger().log_info(
                f"MetadataService: Loaded {len(self.char_map)} characters, "
                f"{len(self.implemented_chars)} implemented."
            )
        except Exception as e:
            get_ui_logger().log_error(f"MetadataService: Load failed: {e}")

    def _get_default_target_map(self) -> Dict[str, Any]:
        """返回预定义的怪物模板"""
        return {
            "遗迹守卫": {
                "level": 90,
                "resists": {k: 10 for k in ["火", "水", "雷", "草", "冰", "岩", "风", "物理"]},
            },
            "丘丘人": {
                "level": 90,
                "resists": {k: 10 for k in ["火", "水", "雷", "草", "冰", "岩", "风", "物理"]},
            },
            "古岩龙蜥": {
                "level": 90,
                "resists": {k: 10 for k in ["火", "水", "雷", "草", "冰", "岩", "风", "物理"]},
            },
        }
