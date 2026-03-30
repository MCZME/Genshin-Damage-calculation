from typing import Any
from weapon.weapon import Weapon
from core.registry import register_weapon


@register_weapon("学徒笔记", "法器")
class ApprenticeNotes(Weapon):
    """
    学徒笔记：没有任何特性的少年的笔记。
    """

    ID = 171  # 对应原生数据 ID

    def __init__(
        self,
        character: Any,
        level: int = 1,
        lv: int = 1,
        base_data: dict[str, Any] | None = None,
    ):
        super().__init__(character, ApprenticeNotes.ID, level, lv, base_data)

    def skill(self) -> None:
        """学徒笔记没有武器技能。"""
        pass
