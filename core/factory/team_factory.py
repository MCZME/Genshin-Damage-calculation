from typing import List, Dict, Any, Optional
from artifact.artifact import Artifact, ArtifactManager, ArtifactPiece
from core.registry import CharacterClassMap, WeaponClassMap
from core.team import Team
from core.data.repository import DataRepository
from core.logger import get_emulation_logger


class TeamFactory:
    """
    队伍工厂类，负责从原始 JSON 数据构建 Team 实例。
    """

    def __init__(self, repository: DataRepository):
        self.repository = repository

    def create_team(self, team_config: List[Dict[str, Any]]) -> Team:
        characters = []
        for char_data in team_config:
            if not char_data or "error" in char_data:
                continue

            character = self._build_character(char_data)
            if character:
                characters.append(character)
                get_emulation_logger().log_info(
                    f"角色 {character.name} 组装成功", sender="Team"
                )

        if not characters:
            raise ValueError("没有有效的角色配置，无法创建队伍。")

        return Team(characters)

    def _build_character(self, data: Dict[str, Any]) -> Any:
        # 1. 支持 UI 嵌套结构: { "character": {...}, "weapon": {...}, "artifacts": {...} }
        # 若无嵌套则回退到 data 本身
        char_config = data.get("character", data)

        # 2. 解析天赋 (支持 "10/10/10" 或 [10, 10, 10])
        raw_talents = char_config.get("talents", [1, 1, 1])
        if isinstance(raw_talents, str):
            skill_params = [int(t) for t in raw_talents.split("/")]
        else:
            skill_params = [int(t) for t in raw_talents]

        char_id = char_config.get("id")
        level = char_config.get("level", 90)

        # 3. 从仓库获取基础属性数据并注入
        base_stats = self.repository.get_character_base_stats(char_id, level)
        char_name = base_stats.get("name")

        # 4. 实例化角色类
        if char_name not in CharacterClassMap:
            get_emulation_logger().log_error(
                f"未找到角色 {char_name} (ID: {char_id}) 的实现类"
            )
            return None

        character = CharacterClassMap[char_name](
            level=level,
            skill_params=skill_params,
            constellation=char_config.get("constellation", 0),
            base_data=base_stats,
        )

        # [V2.4 新增] 设置初始物理坐标
        pos = data.get("position", {"x": 0, "z": 0})
        character.set_position(pos.get("x", 0), pos.get("z", 0))

        # 5. 组装武器 (支持从外层或嵌套层获取)
        weapon_data = data.get("weapon")
        if weapon_data:
            self._apply_weapon(character, weapon_data)

        # 6. 组装圣遗物 (支持从外层或嵌套层获取)
        artifacts_data = data.get("artifacts")
        if artifacts_data:
            self._apply_artifacts(character, artifacts_data)

        return character

    def _apply_weapon(self, character: Any, weapon_data: Dict[str, Any]):
        weapon_name = weapon_data.get("name")
        if not weapon_name:
            return

        if weapon_name in WeaponClassMap:
            level = weapon_data.get("level", 90)
            weapon_base_stats = self.repository.get_weapon_base_stats(
                weapon_name, level
            )

            weapon_class = WeaponClassMap[weapon_name]
            weapon = weapon_class(
                character=character,
                level=level,
                lv=weapon_data.get("refinement", 1),
                base_data=weapon_base_stats,
            )
            character.set_weapon(weapon)
        else:
            get_emulation_logger().log_error(f"未找到武器 {weapon_name} 的实现类")

    def _apply_artifacts(self, character: Any, artifacts_data: Any):
        # 支持字典 (槽位名:数据) 或 列表 格式
        if isinstance(artifacts_data, dict):
            artifacts_list = list(artifacts_data.values())
        else:
            artifacts_list = artifacts_data

        artifacts = []
        for arti_data in artifacts_list:
            if not arti_data or not arti_data.get("main_stat"):
                continue

            artifacts.append(
                Artifact(
                    name=arti_data.get("set_name", "None"),
                    piece=self._map_piece(arti_data.get("slot", "")),
                    main=arti_data.get("main_stat"),
                    sub=arti_data.get("sub_stats", []),
                )
            )

        if artifacts:
            am = ArtifactManager(artifacts, character)
            character.set_artifact(am)

    def _map_piece(self, slot_name: str) -> Optional[ArtifactPiece]:
        mapping = {
            "生之花": ArtifactPiece.Flower_of_Life,
            "死之羽": ArtifactPiece.Plume_of_Death,
            "时之沙": ArtifactPiece.Sands_of_Eon,
            "空之杯": ArtifactPiece.Goblet_of_Eonothem,
            "理之冠": ArtifactPiece.Circlet_of_Logos,
            # 兼容 UI 传参
            "flower": ArtifactPiece.Flower_of_Life,
            "feather": ArtifactPiece.Plume_of_Death,
            "sands": ArtifactPiece.Sands_of_Eon,
            "goblet": ArtifactPiece.Goblet_of_Eonothem,
            "circlet": ArtifactPiece.Circlet_of_Logos,
        }
        return mapping.get(slot_name)
