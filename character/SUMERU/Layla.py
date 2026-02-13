from core.context import get_context
import random
from character.SUMERU.sumeru import Sumeru
from core.base_class import (ChargedAttackSkill, ConstellationEffect, ElementalEnergy, 
                            EnergySkill, Infusion, NormalAttackSkill, PlungingAttackSkill, SkillBase, TalentEffect)
from core.BaseObject import ShieldObject, baseObject
from core.event import ChargedAttackEvent, DamageEvent EventHandler, EventType, ShieldEvent
from core.logger import get_emulation_logger
from core.team import Team
from core.tool import GetCurrentTime, summon_energy
from core.systems.contract.damage import Damage, DamageType
from core.systems.contract.shield import Shield
from core.effect.BaseEffect import Effect

class NormalAttack(NormalAttackSkill):
    def __init__(self, lv):
        super().__init__(lv)
        # 三段攻击的伤害倍率 (1-15级)
        self.damageMultipiler = {
            1: [51.22, 55.39, 59.56, 65.51, 69.68, 74.44, 80.99, 87.55, 94.1, 101.24, 108.39, 115.54, 122.68, 129.83, 136.98],
            2: [48.48, 52.43, 56.38, 62.01, 65.96, 70.47, 76.67, 82.87, 89.07, 95.84, 102.6, 109.37, 116.13, 122.9, 129.66],
            3: [72.97, 78.91, 84.85, 93.34, 99.28, 106.07, 115.4, 124.73, 134.07, 144.25, 154.43, 164.61, 174.8, 184.98, 195.16]
        }
        # 三段攻击的帧数配置 (命中帧)
        self.segment_frames = [13, 18, 55]
        # 攻击结束后的动作帧
        self.end_action_frame = 34

class ChargedAttack(ChargedAttackSkill):
    def __init__(self, lv):
        super().__init__(lv, total_frames=34)
        # 两段重击的伤害倍率 (1-15级)
        self.damageMultipiler = [
            [47.73, 51.62, 55.5, 61.05, 64.94, 69.38, 75.48, 81.59, 87.69, 94.35, 101.01, 107.67, 114.33, 120.99, 127.65],  # 第一段
            [52.55, 56.82, 61.1, 67.21, 71.49, 76.38, 83.1, 89.82, 96.54, 103.87, 111.2, 118.53, 125.87, 133.2, 140.53]   # 第二段
        ]
        # 两段攻击的命中帧
        self.hit_frames = [16, 27]

    def on_frame_update(self, target):
        if self.current_frame in self.hit_frames:
            self._apply_attack(target)

    def _apply_attack(self, target):
        event = ChargedAttackEvent(self.caster, frame=get_current_time())
        get_context().event_engine.publish(event)

        damage = Damage(
            damageMultipiler=self.damageMultipiler[self.hit_frames.index(self.current_frame)][self.lv-1],
            element=self.element,
            damageType=DamageType.CHARGED,
            name='重击-'+str(self.hit_frames.index(self.current_frame)+1),
        )
        damage_event = DamageEvent(self.caster, target, damage, get_current_time())
        get_context().event_engine.publish(damage_event)

        event = ChargedAttackEvent(self.caster, frame=get_current_time(), before=False)
        get_context().event_engine.publish(event)

class PlungingAttack(PlungingAttackSkill):
    ...

class VeilOfSlumberShield(ShieldObject, EventHandler, Infusion):
    """安眠帷幕护盾"""
    def __init__(self, character, shield_value):
        shield = Shield(shield_value)
        event = ShieldEvent(character, shield, get_current_time())
        get_context().event_engine.publish(event)
        super().__init__(character, "安眠帷幕", "冰", event.data['shield'].shield_value, 750)
        Infusion.__init__(self, [1,0,0,0,0,0,0,1,0,0,0,0], 3*60)
        self.night_stars = 0
        self.last_night_stars_time = 0
        self.active_night_stars = False
        self.active_frame = 0
        self.damageMultipiler = [14.72, 15.82, 16.93, 18.4, 19.5, 20.61, 22.08, 23.55, 25.02, 
                                 26.5, 27.97, 29.44, 31.28, 33.12, 34.96, ]
        
        if self.character.constellation >= 6:
            self.night_stars_interval = 1.5*60*0.8
        else:
            self.night_stars_interval = 1.5*60

        self.mode = 1 # 用于产球判定
        self.last_mode_1 = 0
        self.last_mode_2 = 0

    def apply(self):
        super().apply()
        existing = next((e for e in Team.team 
                       if isinstance(e, ShieldObject) and e.name == self.name), None)
        if existing:
            existing.life_frame = self.life_frame  # 刷新持续时间
            return
            
        get_context().event_engine.subscribe(EventType.AFTER_SKILL, self)

    def on_finish(self, target):
        super().on_finish(target)
        get_emulation_logger().log_effect(f"{self.character.name}: {self.name}护盾效果结束")
        get_context().event_engine.unsubscribe(EventType.AFTER_SKILL, self)

    def handle_event(self, event):
        existing = next((e for e in Team.active_objects 
                       if isinstance(e, ShieldObject) and e.name == self.name), None)
        if not existing:
            return
        
        if (not self.active_night_stars and 
            event.data['character'] == Team.current_character and 
            event.frame - self.last_night_stars_time >= 0.3*60):
            self.night_stars = min(4, self.night_stars + 2)
            self.last_night_stars_time = event.frame

    def update(self, target):
        super().update(target)
        if self.current_frame % self.night_stars_interval == 0 and not self.active_night_stars:
            self.night_stars = min(4, self.night_stars + 1)

        if self.night_stars == 4 and not self.active_night_stars:
            self.active_night_stars = True
            if self.current_frame < 0.45*60 * self.night_stars:
                self.current_frame = 0.45*60 * self.night_stars
            self.active_frame = self.current_frame

            # 产球判断
            if self.mode == 1 and get_current_time() - self.last_mode_1 >= 3.5*60:
                self.mode = 2
                self.last_mode_1 = get_current_time()
                self.create_energy()
            elif self.mode == 2 and get_current_time() - self.last_mode_2 >= 3.5*60:
                self.mode = 1
                self.last_mode_2 = get_current_time()
                self.create_energy()


            if self.character.constellation >= 4:
                for char in Team.team:
                    DawnStarEffect(self.character, char).apply()

        if self.active_night_stars and self.current_frame - self.active_frame >= 0.45*60:
            self.active_frame = self.current_frame
            self.night_stars -= 1
            damage = Damage(
                self.damageMultipiler[self.character.Skill.lv-1],
                ('冰',self.apply_infusion()),
                DamageType.SKILL,
                '晚星'
            )
            get_context().event_engine.publish(DamageEvent(self.character, target, damage, get_current_time()))
            if self.night_stars == 0:
                self.active_night_stars = False

            if self.character.constellation >= 2:
                summon_energy(1, self.character, ('无',1),True,True,0)

    def create_energy(self,):
        if random.random() < 0.67:
            summon_energy(1, self.character, ('冰',2))
        else:
            summon_energy(2, self.character, ('冰',2))

class ElementalSkill(SkillBase):
    def __init__(self, lv):
        super().__init__("垂裳端凝之夜", total_frames=41, cd=12*60, lv=lv, element=("冰",1))
        # 技能伤害倍率 (1-15级)
        self.damageMultipiler = [12.8, 13.76, 14.72, 16, 16.96, 17.92, 19.2, 20.48, 21.76, 23.04, 24.32, 25.6, 27.2, 28.8, 30.4]
        # 护盾基础吸收量 (1-15级) [生命值%, 固定值]
        self.shield_values = [
            [10.8, 1040.01], [11.61, 1144.02], [12.42, 1256.71], [13.5, 1378.06], 
            [14.31, 1508.08], [15.12, 1646.76], [16.2, 1794.12], [17.28, 1950.14], 
            [18.36, 2114.83], [19.44, 2288.19], [20.52, 2470.22], [21.6, 2660.91],
            [22.95, 2860.27], [24.3, 3068.3], [25.65, 3285]
        ]
        self.hit_frame = 32
        self.cd_frame = 19

    def on_frame_update(self, target):
        if self.current_frame == self.hit_frame:
            # 造成伤害
            damage = Damage(
                self.damageMultipiler[self.lv-1],
                self.element,
                DamageType.SKILL,
                '垂裳端凝之夜'
            )
            get_context().event_engine.publish(DamageEvent(self.caster, target, damage, get_current_time()))
            
            shield_value = self.caster.maxHP * self.shield_values[self.lv-1][0] / 100 + self.shield_values[self.lv-1][1]
            VeilOfSlumberShield(self.caster, shield_value).apply()

class DreamingAegisObject(baseObject, Infusion):
    """饰梦天球对象"""
    def __init__(self, character, lv):
        super().__init__("饰梦天球", 12*60)
        Infusion.__init__(self)
        self.character = character
        self.lv = lv
        self.damage_multipliers = [
            4.65, 5, 5.35, 5.81, 6.16, 6.51, 6.97, 7.44, 7.9, 
            8.37, 8.83, 9.3, 9.88, 10.46, 11.04
        ]
        self.attack_interval = 1.5 * 60  # 1.5秒攻击间隔
        self.last_attack_time = -70
        self.last_night_stars_time = -5*60

    def on_frame_update(self, target):
        if self.current_frame >= self.last_attack_time + self.attack_interval + random.randint(18,23):
            self._attack(target)
            self.last_attack_time = self.current_frame

    def _attack(self, target):
        damage = Damage(
            self.damage_multipliers[self.lv-1],
            ("冰",self.apply_infusion()),
            DamageType.BURST,
            "星流摇床之梦"
        )
        damage.setBaseValue('生命值')
        get_context().event_engine.publish(DamageEvent(self.character, target, damage, get_current_time()))

        # 为护盾生成晚星
        shield = next((s for s in self.character.shield_effects 
                      if isinstance(s, VeilOfSlumberShield)), None)
        if shield and self.current_frame - self.last_night_stars_time >= 0.5*60:
            shield.night_stars = min(4, shield.night_stars + 1)
            self.last_night_stars_time = self.current_frame

class ElementalBurst(EnergySkill):
    def __init__(self, lv):
        super().__init__("星流摇床之梦", total_frames=65, cd=12*60, lv=lv, element="冰")
        self.lv = lv
    
    def on_frame_update(self, target):
        if self.current_frame == 36:
            DreamingAegisObject(self.caster, self.lv).apply()

class PassiveSkillEffect_1(TalentEffect):
    def __init__(self):
        super().__init__('如光骤现')

class PassiveSkillEffect_2(TalentEffect, EventHandler):
    def __init__(self):
        super().__init__('勿扰沉眠')

    def apply(self, character):
        super().apply(character)
        get_context().event_engine.subscribe(EventType.BEFORE_FIXED_DAMAGE, self)

    def handle_event(self, event):
        if event.data['character'] is not self.character:
            return
        damage = event.data['damage']
        if damage.damageType == DamageType.SKILL and damage.name == '晚星':
            damage.panel['固定伤害基础值加成'] += self.character.maxHP * 0.015
            damage.setDamageData('勿扰沉眠_伤害基础值加成', self.character.maxHP * 0.015)

class ConstellationEffect_1(ConstellationEffect):
    def __init__(self):
        super().__init__('寐领围垣')

class ConstellationEffect_2(ConstellationEffect):
    def __init__(self):
        super().__init__('归芒携信')

class ConstellationEffect_3(ConstellationEffect):
    def __init__(self):
        super().__init__('长宵宣秘')

    def apply(self, character):
        super().apply(character)
        self.character.Skill.lv = min(self.character.Skill.lv + 3, 15)

class ConstellationEffect_4(ConstellationEffect):
    def __init__(self):
        super().__init__('星示昭明')

class DawnStarEffect(Effect, EventHandler):
    def __init__(self, character, current_character):
        super().__init__(character,3*60)
        self.current_character = current_character
        self.name = '启明'
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">使普通攻击与重击造成的伤害提升，提升值相当于莱依拉生命值上限的5%。</span></p>
        """

    def apply(self):
        existing = next((e for e in self.character.active_effects if isinstance(e, DawnStarEffect)), None)
        if existing:
            existing.duration = self.duration
            return
        super().apply()
        self.current_character.add_effect(self)
        get_emulation_logger().log_effect(f'⭐ {self.current_character.name} 获得 {self.name} 效果')
        get_context().event_engine.subscribe(EventType.BEFORE_FIXED_DAMAGE,self)

    def remove(self):
        super().remove()
        get_emulation_logger().log_effect(f'⭐ {self.current_character.name} {self.name} 效果消失')
        get_context().event_engine.unsubscribe(EventType.BEFORE_FIXED_DAMAGE,self)

    def handle_event(self, event):
        damage = event.data['damage']
        if damage.damageType in [DamageType.NORMAL, DamageType.CHARGED]:
            damage.panel['固定伤害基础值加成'] += self.character.maxHP * 0.05
            damage.setDamageData('启明_伤害基础值加成', self.character.maxHP * 0.05)
            self.duration = 0.05*60

class ConstellationEffect_5(ConstellationEffect):
    def __init__(self):
        super().__init__('悬神系流')

    def apply(self, character):
        super().apply(character)
        self.character.Burst.lv = min(self.character.Burst.lv + 3, 15)

class ConstellationEffect_6(ConstellationEffect, EventHandler):
    def __init__(self):
        super().__init__('曜光灵炬')

    def apply(self, character):
        super().apply(character)
        get_context().event_engine.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)

    def handle_event(self, event):
        if event.data['character'] is not self.character:
            return
        damage = event.data['damage']
        if damage.name in ['晚星','星流摇床之梦']:
            damage.panel['伤害加成'] += 40
            damage.setDamageData('曜光灵炬_暴伤害加成', 40)

class Layla(Sumeru):
    ID = 60
    def __init__(self, level=1, skill_params=..., constellation=0):
        super().__init__(Layla.ID, level, skill_params, constellation)

    def _init_character(self):
        super()._init_character()
        self.elemental_energy = ElementalEnergy(self,('冰',40))
        self.NormalAttack = NormalAttack(self.skill_params[0])
        self.ChargedAttack = ChargedAttack(self.skill_params[0])
        self.Skill = ElementalSkill(self.skill_params[1])
        self.Burst = ElementalBurst(self.skill_params[2])
        self.talent1 = PassiveSkillEffect_1()
        self.talent2 = PassiveSkillEffect_2()
        self.constellation_effects[0] = ConstellationEffect_1()
        self.constellation_effects[1] = ConstellationEffect_2()
        self.constellation_effects[2] = ConstellationEffect_3()
        self.constellation_effects[3] = ConstellationEffect_4()
        self.constellation_effects[4] = ConstellationEffect_5()
        self.constellation_effects[5] = ConstellationEffect_6()

layla_table = {
    'id': Layla.ID,
    'name': '莱依拉',
    'type': '单手剑',
    'element': '冰',
    'rarity': '4',
    'association':'须弥',
    'normalAttack': {'攻击次数': 3},
    'chargedAttack': {},
    # 'plungingAttack': {'攻击距离':['高空', '低空']},
    'skill': {},
    'burst': {}
}

