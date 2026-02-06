from typing import Any
from core.effect.base import BaseEffect

class FlowerOfParadiseLostEffect(BaseEffect):
    """乐园遗落之花套装效果"""
    def __init__(self, owner: Any):
        super().__init__(owner, "乐园遗落之花", duration=10*60)
        self.stack = 0

    def on_apply(self):
        self.stack = 1
        self._update_panel(1)

    def on_stack_added(self, other: 'FlowerOfParadiseLostEffect'):
        self._update_panel(-1)
        self.stack = min(4, self.stack + 1)
        self._update_panel(1)
        self.duration = self.max_duration

    def on_remove(self):
        self._update_panel(-1)

    def _update_panel(self, sign: int):
        bonus = self.stack * 25
        coeffs = self.owner.attribute_panel.get('反应系数提高', {})
        for r in ['绽放', '超绽放', '烈绽放']:
            coeffs[r] = coeffs.get(r, 0.0) + (sign * bonus)
        self.owner.attribute_panel['反应系数提高'] = coeffs
