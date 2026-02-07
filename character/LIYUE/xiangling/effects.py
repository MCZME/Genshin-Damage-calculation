from core.effect.BaseEffect import Effect, AttackBoostEffect

class ChiliPepperEffect(AttackBoostEffect):
    """绝云朝天椒加攻效果"""
    def __init__(self, character, current_character):
        super().__init__(character, current_character, "绝云朝天椒🌶️", 10, 10*60)

class InternalExplosionEffect(Effect):
    """命座2：大火宽油的内爆状态"""
    def __init__(self, owner, damage):
        super().__init__(owner, 2*60)
        self.name = "大火宽油"
        self.damage = damage

    def on_frame_update(self):
        super().on_frame_update()
        if self.current_frame >= self.life_frame:
            self._explode()

    def _explode(self):
        # 产生爆炸伤害
        pass
