from typing import Any
from core.entities.base_entity import CombatEntity, Faction
from core.action.damage import Damage, DamageType
from core.event import DamageEvent, EventBus
from core.tool import GetCurrentTime, summon_energy

class GuobaEntity(CombatEntity):
    """锅巴：战场物理实体"""
    def __init__(self, caster, damage_multiplier):
        # 锅巴体型较大，半径设为 0.5m，寿命 7s
        super().__init__(
            name="锅巴",
            faction=Faction.PLAYER,
            pos=caster.pos, # 初始位置继承施法者
            hitbox=(0.5, 1.0),
            life_frame=420
        )
        self.caster = caster
        self.damage_multiplier = damage_multiplier
        self.interval = 96
        self.last_attack_time = -10

    def on_frame_update(self):
        """锅巴的攻击逻辑"""
        super().on_frame_update()
        if self.current_frame - self.last_attack_time >= self.interval:
            self._attack()
            self.last_attack_time = self.current_frame

    def _attack(self):
        # 寻找场景中的目标 (这里暂由 CombatSpace 处理范围，此处简化为发布事件)
        # 注意：未来的锅巴攻击应产生一个 Damage 对象并通过 ctx.space.broadcast 发出
        pass

class PyronadoEntity(CombatEntity):
    """旋火轮：跟随实体的环绕物"""
    def __init__(self, caster, damage_multiplier):
        duration = 600 - 56
        if caster.constellation_level >= 4:
            duration = int(duration * 1.4)
            
        super().__init__(
            name="旋火轮",
            faction=Faction.PLAYER,
            pos=caster.pos,
            hitbox=(2.0, 1.0), # 旋火轮判定范围较大
            life_frame=duration
        )
        self.caster = caster
        self.damage_multiplier = damage_multiplier

    def on_frame_update(self):
        """同步施法者位置"""
        super().on_frame_update()
        self.pos = self.caster.pos.copy()
