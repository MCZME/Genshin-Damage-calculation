from typing import Any, List, Optional

from character.character import Character
from core.event import GameEvent, EventType
from core.tool import get_current_time


class Team:
    """
    队伍管理类 (逻辑层)。

    负责角色生命值、能量、冷却状态的全局管理，以及场上角色切换。
    解耦说明：不再自动将全员注册进 CombatSpace，物理空间应仅感知当前场上角色。
    """

    def __init__(self, characters: List[Character], context: Any = None):
        """初始化队伍。

        Args:
            characters: 参与编队的初始化角色列表。
            context: 仿真上下文。
        """
        self.ctx = context
        self.members: List[Character] = characters
        self.active_index: int = 0

        self.swap_cd: int = 60
        self.swap_cd_timer: int = 0

        # 初始化状态
        for char in self.members:
            char.on_field = False

        if self.members:
            self.members[0].on_field = True

    @property
    def current_character(self) -> Optional[Character]:
        """获取当前活跃角色 (场上角色)。"""
        if 0 <= self.active_index < len(self.members):
            return self.members[self.active_index]
        return None

    def get_members(self) -> List[Character]:
        """获取全队成员 (包含后台)。"""
        return self.members

    def get_character_by_name(self, name: str) -> Optional[Character]:
        for char in self.members:
            if char.name == name:
                return char
        return None

    def swap(self, char_name: str) -> bool:
        """根据名称请求切换角色。"""
        if self.swap_cd_timer > 0:
            return False

        target = self.get_character_by_name(char_name)
        if target and target != self.current_character:
            self._perform_switch(target)
            return True
        return False

    def _perform_switch(self, new_char: Character) -> None:
        """执行实际的场上角色切换逻辑，并同步物理位置。"""
        from core.logger import get_emulation_logger

        old_char = self.current_character

        # 1. 物理位置同步：新角色继承旧角色的坐标与朝向
        if old_char:
            new_char.pos = old_char.pos.copy()
            new_char.facing = old_char.facing
            old_char.on_field = False

        # 2. 逻辑状态变更
        new_char.on_field = True
        self.active_index = self.members.index(new_char)
        self.swap_cd_timer = self.swap_cd

        # 3. 发布事件 (供 CombatSpace 更新物理注册信息)
        if self.ctx and self.ctx.event_engine:
            self.ctx.event_engine.publish(
                GameEvent(
                    event_type=EventType.AFTER_CHARACTER_SWITCH,
                    frame=get_current_time(),
                    source=new_char,
                    data={"old_character": old_char, "new_character": new_char},
                )
            )

        get_emulation_logger().log_info(
            f"切换角色: {old_char.name if old_char else 'None'} -> {new_char.name} (坐标同步完成)",
            sender="Team",
        )

    def on_frame_update(self) -> None:
        """驱动编队相关的每帧逻辑，并同步驱动所有队员。"""
        # 1. 驱动队伍自身状态 (如切换 CD)
        if self.swap_cd_timer > 0:
            self.swap_cd_timer -= 1

        # 2. 统一驱动所有队员 (场上/场下角色)
        for char in self.members:
            # 使用 on_frame_update() 确保基类中的生命周期与帧数自增逻辑被执行
            char.on_frame_update()

    def reset(self) -> None:
        self.swap_cd_timer = 0
        self.active_index = 0
        for i, char in enumerate(self.members):
            char.on_field = i == 0
