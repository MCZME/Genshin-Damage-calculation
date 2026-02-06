from enum import Enum
from typing import Any, Dict, List, Optional
from core.registry import ArtifactSetMap

class ArtifactPiece(Enum):
    Flower_of_Life = 0
    Plume_of_Death = 1
    Sands_of_Eon = 2
    Goblet_of_Eonothem = 3
    Circlet_of_Logos = 4

class Artifact:
    """圣遗物单项数据类。"""
    def __init__(self, name: str, piece: ArtifactPiece, main: Dict[str, float] = None, sub: Dict[str, float] = None):
        self.name = name
        self.piece = piece
        if main is None:
            raise ValueError("圣遗物主属性不能为空")
        self.main = main
        self.sub = sub or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "piece": self.piece.name,
            "main": self.main,
            "sub": self.sub
        }

class ArtifactManager:
    """
    圣遗物管理器。
    负责处理圣遗物的数值加成与套装效果触发。
    """
    def __init__(self, artifacts: List[Artifact], character: Any):
        self.character = character
        self.artifacts: Dict[str, Optional[Artifact]] = {
            "Flower_of_Life": None,
            "Plume_of_Death": None,
            "Sands_of_Eon": None,
            "Goblet_of_Eonothem": None,
            "Circlet_of_Logos": None
        }
        for artifact in artifacts:
            self.artifacts[artifact.piece.name] = artifact
    
    def update_panel(self) -> None:
        """将圣遗物基础数值应用到角色面板。"""
        panel_totals: Dict[str, float] = {}
        for artifact in self.artifacts.values():
            if artifact:
                # 合并主属性
                for k, v in artifact.main.items():
                    panel_totals[k] = panel_totals.get(k, 0.0) + v
                # 合并副属性
                for k, v in artifact.sub.items():
                    panel_totals[k] = panel_totals.get(k, 0.0) + v
        
        # 严格使用新架构的 attribute_panel
        attr_panel = self.character.attribute_panel
        
        for key, val in panel_totals.items():
            if key == "攻击力":
                attr_panel["固定攻击力"] = attr_panel.get("固定攻击力", 0.0) + val
            elif key == "生命值":
                attr_panel["固定生命值"] = attr_panel.get("固定生命值", 0.0) + val
            elif key == "防御力":
                attr_panel["固定防御力"] = attr_panel.get("固定防御力", 0.0) + val
            else:
                attr_panel[key] = attr_panel.get(key, 0.0) + val
    
    def set_effect(self) -> None:
        """激活套装效果。"""
        set_counts: Dict[str, int] = {}
        for artifact in self.artifacts.values():
            if artifact:
                set_counts[artifact.name] = set_counts.get(artifact.name, 0) + 1
        
        for name, count in set_counts.items():
            cls = ArtifactSetMap.get(name)
            if not cls:
                continue
            
            # 实例化套装效果
            effect_instance = cls()
            if count >= 2:
                effect_instance.apply_2_set_effect(self.character)
            if count >= 4:
                effect_instance.apply_4_set_effect(self.character)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "set": [art.to_dict() for art in self.artifacts.values() if art]
        }
