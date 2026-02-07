from typing import Any
from core.entities.base_entity import CombatEntity, Faction
from core.action.damage import Damage, DamageType
from core.mechanics.aura import Element
from core.event import DamageEvent, EventBus
from core.tool import GetCurrentTime, summon_energy

class GuobaEntity(CombatEntity):
    """锅巴：战场物理实体"""
    def __init__(self, caster, lv):
        # 锅巴体型 0.5m，高度 1.0m
        super().__init__(
            name="锅巴",
            faction=Faction.PLAYER,
            pos=caster.pos, 
            hitbox=(0.5, 1.0),
            life_frame=420
        )
        self.caster = caster
        self.lv = lv
        # 喷火倍率表
        self.multiplier_table = [111.28, 119.63, 127.97, 139.1, 147.45, 155.79, 166.92, 178.05, 189.18, 200.3, 211.43, 222.56, 236.47, 250.38, 264.29]
        self.interval = 96
        self.last_attack_time = -10

    def on_frame_update(self):
        super().on_frame_update()
        if self.current_frame - self.last_attack_time >= self.interval:
            self._attack()
            self.last_attack_time = self.current_frame

    def _attack(self):
        """执行喷火广播"""
        multiplier = self.multiplier_table[self.lv - 1]
        
        # 构造喷火伤害 (扇形 AOE)
        damage = Damage(
            damage_multiplier=multiplier,
            element=(Element.PYRO, 1.0),
            damage_type=DamageType.SKILL,
            name="锅巴喷火",
            aoe_shape='SECTOR',
            radius=5.0,
            fan_angle=60.0
        )
        
        # 通过场景广播派发
        if self.ctx and self.ctx.space:
            self.ctx.space.broadcast_damage(self, damage)
            # 产球逻辑
            summon_energy(1, self.caster, (Element.PYRO, 2))

class PyronadoEntity(CombatEntity):
    """旋火轮：跟随实体的环绕物"""
    def __init__(self, caster, lv):
        duration = 600 - 56
        if caster.constellation_level >= 4:
            duration = int(duration * 1.4)
            
        super().__init__(
            name="旋火轮",
            faction=Faction.PLAYER,
            pos=caster.pos,
            hitbox=(2.5, 1.0), # 判定半径较大
            life_frame=duration
        )
        self.caster = caster
        self.lv = lv
        self.multiplier_table = [112, 120.4, 128.8, 140, 148.4, 156.8, 168, 179.2, 190.4, 201.6, 212.8, 224, 238, 252, 266]
        self.interval = 72 # 约 1.2 秒一圈 (简化)
        self.last_attack_time = -72

    def on_frame_update(self):
        # 1. 物理位置跟随
        self.pos = self.caster.pos.copy()
        super().on_frame_update()
        
        # 2. 旋转伤害广播
        if self.current_frame - self.last_attack_time >= self.interval:
            self._attack()
            self.last_attack_time = self.current_frame

    def _attack(self):
        multiplier = self.multiplier_table[self.lv - 1]
        damage = Damage(
            damage_multiplier=multiplier,
            element=(Element.PYRO, 1.0),
            damage_type=DamageType.BURST,
            name="旋火轮伤害",
            aoe_shape='CIRCLE', # 简化为圆形判定
            radius=2.5
        )
        if self.ctx and self.ctx.space:
            self.ctx.space.broadcast_damage(self, damage)