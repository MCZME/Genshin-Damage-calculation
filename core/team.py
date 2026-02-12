from typing import Any, Dict, List, Optional, Tuple, Type

from character.character import Character
from core.context import get_context
from core.event import CharacterSwitchEvent
from core.tool import get_current_time


class Team:
    """
    队伍管理类。
    负责角色编队管理、场上角色切换以及共鸣状态追踪。
    实体的物理更新与碰撞判定由 CombatSpace 负责。
    """

    def __init__(self, characters: List[Character]):
        """初始化队伍。

        Args:
            characters: 参与编队的初始化角色列表。
        """
        self.team: List[Character] = characters
        self.current_character: Optional[Character] = characters[0] if characters else None

        self.active_resonances: Dict[str, bool] = {}
        self.element_counts: Dict[str, int] = {}
        self.swap_cd: int = 60
        self.swap_cd_timer: int = 0

        if self.current_character:
            self.current_character.on_field = True

        # 自动化注册角色至战斗空间
        ctx = get_context()
        for char in self.team:
            ctx.space.register(char)

        self._update_element_counts()
        # TODO: 待 Effect 系统重建后重新实现共鸣逻辑
        # self._apply_resonance_effects()

    def get_character_by_name(self, name: str) -> Optional[Character]:
        """通过角色名称检索队伍中的角色实例。

        Args:
            name: 角色中文字符串名称。

        Returns:
            Optional[Character]: 找到的角色实例，若未找到则返回 None。
        """
        for char in self.team:
            if char.name == name:
                return char
        return None

    def _update_element_counts(self) -> None:
        """更新当前队伍中各元素的角色计数。"""
        self.element_counts = {}
        for char in self.team:
            self.element_counts[char.element] = self.element_counts.get(char.element, 0) + 1

    def swap(self, action: Tuple[str, str, Any]) -> bool:
        """执行角色切换或角色动作请求。

        Args:
            action: 动作元组 (角色名, 方法名, 参数)。

        Returns:
            bool: 动作是否成功发起。
        """
        char_name, method, params = action
        if self.current_character is None:
            return False

        # 如果目标角色已在场上，直接执行动作
        if char_name == self.current_character.name:
            return self._execute_action(self.current_character, method, params)

        # 否则尝试进行角色切换
        if self.swap_cd_timer == 0:
            target_char = self.get_character_by_name(char_name)
            if target_char:
                self._perform_switch(target_char)
                return self._execute_action(self.current_character, method, params)

        return False

    def _perform_switch(self, new_char: Character) -> None:
        """执行实际的场上角色切换逻辑。

        Args:
            new_char: 即将登场的角色实例。
        """
        from core.logger import get_emulation_logger
        old_char = self.current_character
        old_name = old_char.name if old_char else "None"
        get_emulation_logger().log_info(
            f"切换角色: {old_name} -> {new_char.name}", sender="Team"
        )

        # 发布切换事件
        get_context().event_engine.publish(
            CharacterSwitchEvent(old_char, new_char, frame=get_current_time())
        )

        if old_char:
            old_char.on_field = False
        new_char.on_field = True
        self.current_character = new_char
        self.swap_cd_timer = self.swap_cd

    def _execute_action(self, char: Character, method: str, params: Any) -> bool:
        """调用角色对象上的具体方法。

        Args:
            char: 执行动作的角色实例。
            method: 角色类中的方法名。
            params: 传递给方法的参数。

        Returns:
            bool: 角色是否具备该方法并成功调用。
        """
        if hasattr(char, method):
            attr = getattr(char, method)
            if params is not None:
                attr(params)
            else:
                attr()
            return True
        return False

    def update(self) -> None:
        """驱动编队相关的每帧逻辑 (目前仅包含切换 CD 计时)。"""
        if self.swap_cd_timer > 0:
            self.swap_cd_timer -= 1

    def reset(self) -> None:
        """重置队伍状态至初始状态。"""
        self.active_resonances.clear()
        self.swap_cd_timer = 0
        if self.current_character:
            self.current_character.on_field = False
        if self.team:
            self.current_character = self.team[0]
            self.current_character.on_field = True
