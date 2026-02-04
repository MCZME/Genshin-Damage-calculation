from typing import List, Dict, Any, Optional
from artifact.artifact import Artifact, ArtifactManager, ArtifactPiece
from core.map import CharacterClassMap, WeaponClassMap
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
                get_emulation_logger().log("Team", f"角色 {character.name} 组装成功")
        
        if not characters:
            raise ValueError("没有有效的角色配置，无法创建队伍。")
        
        return Team(characters)

    def _build_character(self, data: Dict[str, Any]) -> Any:
        char_config = data['character']
        talents = char_config['talents'].split('/')
        
        # 1. 实例化角色类
        char_id = char_config['id']
        if char_id not in CharacterClassMap:
            get_emulation_logger().log_error(f"未找到角色 ID {char_id} 的实现类")
            return None
            
        character = CharacterClassMap[char_id](
            level=char_config['level'],
            skill_params=[int(t) for t in talents],
            constellation=char_config.get('constellation', 0)
        )

        # 2. 组装武器
        if data.get('weapon'):
            self._apply_weapon(character, data['weapon'])

        # 3. 组装圣遗物
        if data.get('artifacts'):
            self._apply_artifacts(character, data['artifacts'])

        return character

    def _apply_weapon(self, character: Any, weapon_data: Dict[str, Any]):
        weapon_name = weapon_data['name']
        if weapon_name in WeaponClassMap:
            weapon_class = WeaponClassMap[weapon_name]
            weapon = weapon_class(
                character=character,
                level=weapon_data['level'],
                lv=weapon_data.get('refinement', 1)
            )
            character.setWeapon(weapon)
        else:
            get_emulation_logger().log_error(f"未找到武器 {weapon_name} 的实现类")

    def _apply_artifacts(self, character: Any, artifacts_data: List[Dict[str, Any]]):
        artifacts = []
        for arti_data in artifacts_data:
            if not arti_data.get('main_stat'):
                continue
                
            artifacts.append(Artifact(
                name=arti_data['set_name'],
                piece=self._map_piece(arti_data['slot']),
                main=arti_data['main_stat'],
                sub=arti_data['sub_stats']
            ))
        
        if artifacts:
            am = ArtifactManager(artifacts, character)
            character.setArtifact(am)

    def _map_piece(self, slot_name: str) -> Optional[ArtifactPiece]:
        mapping = {
            '生之花': ArtifactPiece.Flower_of_Life,
            '死之羽': ArtifactPiece.Plume_of_Death,
            '时之沙': ArtifactPiece.Sands_of_Eon,
            '空之杯': ArtifactPiece.Goblet_of_Eonothem,
            '理之冠': ArtifactPiece.Circlet_of_Logos,
        }
        return mapping.get(slot_name)
