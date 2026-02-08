from core.entities.base_entity import CombatEntity, Faction
from core.action.damage import Damage, DamageType
from core.mechanics.aura import Element
from core.tool import summon_energy

class GuobaEntity(CombatEntity):
    """锅巴：战场物理实体"""
    def __init__(self, caster, lv):
        super().__init__(
            name="锅巴",
            faction=Faction.PLAYER,
            pos=caster.pos, 
            hitbox=(0.5, 1.0),
            life_frame=420
        )
        self.caster = caster
        self.lv = lv
        self.multiplier_table = [111.28, 119.63, 127.97, 139.1, 147.45, 155.79, 166.92, 178.05, 189.18, 200.3, 211.43, 222.56, 236.47, 250.38, 264.29]
        self.interval = 96
        self.last_attack_time = -10

    def on_frame_update(self):
        super().on_frame_update()
        if self.current_frame - self.last_attack_time >= self.interval:
            self._attack()
            self.last_attack_time = self.current_frame

    def _attack(self):
        multiplier = self.multiplier_table[self.lv - 1]
        # 锅巴喷火是独立附着 (Independent)
        config = AttackConfig(icd_tag="Independent", element_u=1.0)
        damage = Damage(
            damage_multiplier=multiplier,
            element=(Element.PYRO, 1.0),
            damage_type=DamageType.SKILL,
            name="锅巴喷火",
            aoe_shape='CYLINDER', 
            radius=5.0,
            config=config
        )
        if self.ctx and self.ctx.space:
            self.ctx.space.broadcast_damage(self, damage)
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
            hitbox=(2.5, 1.0),
            life_frame=duration
        )
        self.caster = caster
        self.lv = lv
        self.multiplier_table = [112, 120.4, 128.8, 140, 148.4, 156.8, 168, 179.2, 190.4, 201.6, 212.8, 224, 238, 252, 266]
        self.interval = 72
        self.last_attack_time = -72

    def on_frame_update(self):
        self.pos = self.caster.pos.copy()
        super().on_frame_update()
        
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
            aoe_shape='CYLINDER',
            radius=2.5
        )
        if self.ctx and self.ctx.space:
            self.ctx.space.broadcast_damage(self, damage)
