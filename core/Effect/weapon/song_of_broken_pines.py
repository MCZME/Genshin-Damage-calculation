from typing import Any
from core.effect.base import BaseEffect
from core.tool import GetCurrentTime

class RongHuaZhiGeEffect(BaseEffect):
    """荣花之歌 - 个人效果"""
    def __init__(self, owner: Any, lv: int):
        super().__init__(owner, "荣花之歌", duration=6*60)
        self.lv = lv
        self.defense_bonus = [8, 10, 12, 14, 16]
        self.damage_bonus = [10, 12.5, 15, 17.5, 20]
        self.stack = 0
        self.last_trigger = 0

    def on_apply(self):
        self.stack = 1
        self._update_panel(1)

    def on_remove(self):
        self._update_panel(-1)

    def on_stack_added(self, other: 'RongHuaZhiGeEffect'):
        if GetCurrentTime() - self.last_trigger > 0.1*60:
            if self.stack < 2:
                self._update_panel(-1)
                self.stack += 1
                self._update_panel(1)
                if self.stack == 2:
                    # 触发全队效果
                    from core.context import get_context
                    ctx = get_context()
                    if ctx.team:
                        for char in ctx.team.team:
                            RongHuaZhiGeTeamEffect(char, self.owner, self.lv).apply()
            self.last_trigger = GetCurrentTime()
            self.duration = self.max_duration

    def _update_panel(self, sign: int):
        self.owner.attribute_panel['防御力%'] += sign * self.defense_bonus[self.lv-1] * self.stack
        for e in ['水', '火', '风', '雷', '冰', '岩']:
            self.owner.attribute_panel[f'{e}元素伤害加成'] += sign * self.damage_bonus[self.lv-1] * self.stack

class RongHuaZhiGeTeamEffect(BaseEffect):
    """荣花之歌 - 队伍效果"""
    def __init__(self, owner: Any, source_char: Any, lv: int):
        super().__init__(owner, "荣花之歌-队伍", duration=15*60)
        self.lv = lv
        self.bonus_per_1000 = [8, 10, 12, 14, 16]
        self.max_bonus = [25.6, 32, 38.4, 44.8, 51.2]
        # 计算基于施法者防御力的加成
        self.val = self._calculate_val(source_char)

    def _calculate_val(self, source):
        defense = (source.attribute_panel['防御力'] * (1 + source.attribute_panel['防御力%']/100) + 
                   source.attribute_panel['固定防御力'])
        return min((defense/1000) * self.bonus_per_1000[self.lv-1], self.max_bonus[self.lv-1])

    def on_apply(self):
        for e in ['水', '火', '风', '雷', '冰', '岩']:
            self.owner.attribute_panel[f'{e}元素伤害加成'] += self.val

    def on_remove(self):
        for e in ['水', '火', '风', '雷', '冰', '岩']:
            self.owner.attribute_panel[f'{e}元素伤害加成'] -= self.val
