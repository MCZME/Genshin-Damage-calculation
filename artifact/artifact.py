from enum import Enum
from typing import Any, Optional
from core.registry import ArtifactSetMap


class ArtifactPiece(Enum):
    Flower_of_Life = 0
    Plume_of_Death = 1
    Sands_of_Eon = 2
    Goblet_of_Eonothem = 3
    Circlet_of_Logos = 4


class Artifact:
    """圣遗物单项数据类。"""

    def __init__(
        self,
        name: str,
        piece: ArtifactPiece,
        main: dict[str, float] = None,
        sub: dict[str, float] = None,
    ):
        self.name = name
        self.piece = piece
        self.main = main or {}
        self.sub = sub or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "piece": self.piece.name,
            "main": self.main,
            "sub": self.sub,
        }


class ArtifactManager:
    """
    圣遗物管理器。
    """

    def __init__(self, artifacts: list[Artifact], character: Any):
        self.character = character
        self.artifacts: dict[str, Optional[Artifact]] = {
            "Flower_of_Life": None,
            "Plume_of_Death": None,
            "Sands_of_Eon": None,
            "Goblet_of_Eonothem": None,
            "Circlet_of_Logos": None,
        }
        for artifact in artifacts:
            self.artifacts[artifact.piece.name] = artifact

    def apply_static_stats(self) -> None:
        """[核心重构] 将5件圣遗物的所有主副词条通过审计链应用到角色面板。"""
        # 1. 汇总所有词条
        totals: dict[str, float] = {}
        for artifact in self.artifacts.values():
            if artifact:
                for k, v in {**artifact.main, **artifact.sub}.items():
                    totals[k] = totals.get(k, 0.0) + v

        # 2. 通过审计链注入
        for key, val in totals.items():
            if val <= 0:
                continue

            # 智能映射：攻击力/生命值/防御力 不带%的存入固定值乘区
            if key in ["攻击力", "生命值", "防御力"]:
                stat_name = f"固定{key}"
            else:
                stat_name = key

            self.character.add_modifier(
                source="圣遗物",
                stat=stat_name,
                value=val
            )

    def set_effect(self) -> None:
        """激活套装效果 (主要用于注册动态监听器或应用加成)。"""
        set_counts: dict[str, int] = {}
        for artifact in self.artifacts.values():
            if artifact:
                set_counts[artifact.name] = set_counts.get(artifact.name, 0) + 1

        for name, count in set_counts.items():
            cls = ArtifactSetMap.get(name)
            if not cls:
                continue

            effect_instance = cls()
            if count >= 2:
                effect_instance.apply_2_set_effect(self.character)
            if count >= 4:
                effect_instance.apply_4_set_effect(self.character)

    def to_dict(self) -> dict[str, Any]:
        return {"set": [art.to_dict() for art in self.artifacts.values() if art]}
