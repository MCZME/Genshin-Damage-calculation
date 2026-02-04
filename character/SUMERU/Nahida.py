from character.SUMERU.sumeru import Sumeru
from core.BaseClass import (ChargedAttackSkill, ConstellationEffect, ElementalEnergy, 
                            EnergySkill, Infusion, NormalAttackSkill, PlungingAttackSkill, SkillBase, TalentEffect)
from core.BaseObject import baseObject
from core.Event import DamageEvent, EventBus, EventHandler, EventType, GameEvent, NormalAttackEvent
from core.Logger import get_emulation_logger
from core.team import Team
from core.Tool import GetCurrentTime, summon_energy
from core.calculation.DamageCalculation import Damage, DamageType
from core.effect.BaseEffect import DefenseDebuffEffect, Effect, ElementalMasteryBoostEffect

class NormalAttack(NormalAttackSkill, Infusion):
    def __init__(self, lv, cd=0):
        super().__init__(lv, cd)
        Infusion.__init__(self)
        self.segment_frames = [23, 22, 33, 52]
        self.end_action_frame = 31
        self.damageMultipiler = {
            1: [40.3, 43.33, 46.35, 50.38, 53.4, 56.43, 60.46, 64.49, 68.52, 72.55, 76.58, 80.61, 85.65, 90.69, 95.72],
            2: [36.97, 39.75, 42.52, 46.22, 48.99, 51.76, 55.46, 59.16, 62.86, 66.55, 70.25, 73.95, 78.57, 83.19, 87.81],
            3: [45.87, 49.32, 52.76, 57.34, 60.78, 64.22, 68.81, 73.4, 77.99, 82.57, 87.16, 91.75, 97.48, 103.22, 108.95],
            4: [58.41, 62.79, 67.17, 73.01, 77.39, 81.77, 87.61, 93.45, 99.29, 105.13, 110.97, 116.81, 124.11, 131.41, 138.72]
        }

    def _apply_segment_effect(self, target):
        damage = Damage(
            damageMultipiler=self.damageMultipiler[self.current_segment+1][self.lv-1],
            element=('草', self.apply_infusion()),
            damageType=DamageType.NORMAL,
            name=f'普通攻击 第{self.current_segment+1}段'
        )
        
        damage_event = DamageEvent(self.caster, target, damage, GetCurrentTime())
        EventBus.publish(damage_event)

        normal_attack_event = NormalAttackEvent(
            self.caster, 
            frame=GetCurrentTime(), 
            before=False,
            damage=damage,
            segment=self.current_segment+1
        )
        EventBus.publish(normal_attack_event)

class ChargedAttack(ChargedAttackSkill):
    def __init__(self, lv, total_frames=66, cd=0):
        super().__init__(lv, total_frames, cd)
        self.hit_frame = 65
        self.element = ('草', 1)
        self.damageMultipiler = [
            132, 141.9, 151.8, 165, 174.9, 184.8, 198, 
            211.2, 224.4, 237.6, 250.8, 264, 280.5, 297, 313.5
        ]

class PlungingAttack(PlungingAttackSkill):
    ...

class SeedOfSkandhaEffect(Effect, EventHandler):
    """蕴种印效果"""
    def __init__(self, caster, target, duration):
        super().__init__(caster, duration)
        self.name = "蕴种印"
        self.target = target
        self.last_trigger_time = -2.5*60
        self.base_interval = 2.5*60
        self.last_energy_time = -7*60
        self.interval_reduction = 0  # 间隔降低
        
        # 灭净三业伤害倍率
        self.damage_multipliers = [
            (103.2, 206.4), (110.94, 221.88), (118.68, 237.36), (129, 258),
            (136.74, 273.48), (144.48, 288.96), (154.8, 309.6), (165.12, 330.24),
            (175.44, 350.88), (185.76, 371.52), (196.08, 392.16), (206.4, 412.8),
            (219.3, 438.6), (232.2, 464.4), (245.1, 490.2)
        ]

    def apply(self):
        super().apply()
        seedOfSkandha = next((e for e in self.target.effects if e.name == "蕴种印"), None)
        if seedOfSkandha:
            seedOfSkandha.duration = self.duration
            return

        self.target.add_effect(self)
        # 订阅相关事件
        EventBus.subscribe(EventType.AFTER_ELEMENTAL_REACTION, self)
        EventBus.subscribe(EventType.AFTER_DAMAGE, self)

    def remove(self):
        EventBus.unsubscribe(EventType.AFTER_ELEMENTAL_REACTION, self)
        EventBus.unsubscribe(EventType.AFTER_DAMAGE, self)
        super().remove()

    def handle_event(self, event: GameEvent):
        current_time = event.frame
        # 检查触发间隔
        effective_interval = self.base_interval - self.interval_reduction
        if current_time - self.last_trigger_time < effective_interval:
            return

        # 元素反应触发
        if event.event_type == EventType.AFTER_ELEMENTAL_REACTION:
            self.last_trigger_time = current_time            
                
        # 草原核伤害触发
        elif event.event_type == EventType.AFTER_DAMAGE:
            damage = event.data['damage']
            if (damage.name in ['绽放', '烈绽放', '超绽放']):
                self.last_trigger_time = current_time

    def _trigger_tri_karma(self):
        current_time = GetCurrentTime()
        lv = self.character.Skill.lv - 1
        
        damage = Damage(
            self.damage_multipliers[lv],
            element=('草', 1.5),
            damageType=DamageType.SKILL,
            name='灭净三业'
        )
        damage.setBaseValue(('攻击力','元素精通'))
        
        damage_event = DamageEvent(
            self.character,
            self.target,
            damage,
            GetCurrentTime()
        )
        EventBus.publish(damage_event)
        get_emulation_logger().log_effect(f"🌿 {self.target.name} 触发灭净三业")
        if current_time - self.last_energy_time >= 7*60:
            summon_energy(3, self.character, ('草',2))
            self.last_energy_time = current_time

    def update(self):
        super().update(None)
        if GetCurrentTime() == self.last_trigger_time + 4:
            self._trigger_tri_karma()

class ElementalSkill(SkillBase):
    def __init__(self, lv):
        super().__init__(name="所闻遍计", total_frames=58, cd=6*60, lv=lv,
                        element=('草', 1), interruptible=True)
        self.hold = False
        self.skill_frames = {
            '点按': [13, 27],  
            '长按': [32, 58] 
        }
        
        self.damageMultipiler = {
            '点按': [98.4, 105.78, 113.16, 123, 130.38, 137.76, 147.6, 157.44, 
                   167.28, 177.12, 186.96, 196.8, 209.1, 221.4, 233.7],
            '长按': [130.4, 140.18, 149.96, 163, 172.78, 182.56, 195.6, 208.64,
                   221.68, 234.72, 247.76, 260.8, 277.1, 293.4, 309.7]
        }
        self.effect = None

    def start(self, caster, hold=False):
        if not super().start(caster):
            return False
            
        self.effect = None
        self.hold = hold
        if hold:
            self.total_frames = self.skill_frames['长按'][1]
            self.cd = 6*60
            self.cd_frame = 30
        else:
            self.total_frames = self.skill_frames['点按'][1]
            self.cd = 5*60
            self.cd_frame = 11
        return True

    def on_frame_update(self, target):
        mode = '长按' if self.hold else '点按'
        if self.current_frame == self.skill_frames[mode][0]:
            damage = Damage(
                self.damageMultipiler[mode][self.lv-1],
                element=('草', 1),
                damageType=DamageType.SKILL,
                name='所闻遍计·' + mode
            )
            EventBus.publish(DamageEvent(self.caster, target, damage, GetCurrentTime()))
            self.effect = SeedOfSkandhaEffect(self.caster, target, 25*60)
            self.effect.apply()

    def on_finish(self):
        super().on_finish()

class MayaPalaceObject(baseObject,EventHandler):
    """摩耶之殿领域对象"""
    def __init__(self, character, lv, duration, pyro_count=0, electro_count=0, hydro_count=0):
        super().__init__("摩耶之殿", duration)
        self.character = character
        self.current_character = character
        self.lv = lv
        if character.constellation >= 1:
            self.pyro_count = pyro_count + 1
            self.electro_count = electro_count + 1
            self.hydro_count = hydro_count + 1
        else:
            self.pyro_count = pyro_count
            self.electro_count = electro_count
            self.hydro_count = hydro_count
        
        # 增益参数
        self.damage_bonus = [
            [14.88, 16, 17.11, 18.6, 19.72, 20.83, 22.32, 23.81, 25.3, 26.78, 28.27, 29.76, 31.62, 33.48, 35.34],  # 1火
            [22.32, 23.99, 25.67, 27.9, 29.57, 31.25, 33.48, 35.71, 37.94, 40.18, 42.41, 44.64, 47.43, 50.22, 53.01]  # 2火
        ]
        self.interval_reduction = [
            [0.25, 0.27, 0.29, 0.31, 0.33, 0.35, 0.37, 0.4, 0.42, 0.45, 0.47, 0.5, 0.53, 0.56, 0.59],  # 1雷
            [0.37, 0.4, 0.43, 0.47, 0.49, 0.52, 0.56, 0.6, 0.63, 0.67, 0.71, 0.74, 0.79, 0.84, 0.88]   # 2雷
        ]
        self.duration_extension = [
            [3.34, 3.59, 3.85, 4.18, 4.43, 4.68, 5.02, 5.35, 5.68, 6.02, 6.35, 6.69, 7.11, 7.52, 7.94],  # 1水
            [5.02, 5.39, 5.77, 6.27, 6.65, 7.02, 7.52, 8.03, 8.53, 9.03, 9.53, 10.03, 10.66, 11.29, 11.91]  # 2水
        ]
        
    def apply(self):
        super().apply()
        if self.character.level >= 20:
            self.getEM()
            self.setEM()
        # 应用领域效果
        self._apply_effects()
        EventBus.subscribe(EventType.BEFORE_DAMAGE_BONUS,self)
        EventBus.subscribe(EventType.AFTER_CHARACTER_SWITCH,self)
        
    def _apply_effects(self):
        """应用领域效果到角色"""  
        # 雷元素效果：减少攻击间隔
        if self.electro_count > 0:
            count_idx = min(self.electro_count, 2) - 1
            self.reduction = self.interval_reduction[count_idx][self.lv - 1] * 60
            get_emulation_logger().log_effect(f"⚡ 雷元素效果：攻击间隔减少{self.reduction*60:.2f}秒")
        # 水元素效果：延长领域持续时间
        if self.hydro_count > 0:
            count_idx = min(self.hydro_count, 2) - 1
            extension = self.duration_extension[count_idx][self.lv - 1] * 60 
            self.life_frame += extension
            get_emulation_logger().log_effect(f"💧 水元素效果：摩耶之殿持续时间延长{extension/60:.2f}秒")

    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_DAMAGE_BONUS:
            if event.data['character'] == self.character and event.data['damage'].name == '灭净三业':
                event.data['damage'].panel['伤害加成'] += self.damage_bonus[min(2,self.pyro_count)-1][self.lv - 1]
                event.data['damage'].setDamageData('摩耶之殿_伤害加成', self.damage_bonus[min(2,self.pyro_count)-1][self.lv - 1])
        elif event.event_type == EventType.AFTER_CHARACTER_SWITCH:
            if self.current_character == event.data['old_character']:
                self.removeEM()
                self.getEM()
                self.current_character = event.data['new_character']
                self.setEM()

    def getEM(self):
        self.EM = max([em.attributePanel['元素精通'] for em in Team.team]) * 0.25

    def setEM(self):
        self.current_character.attributePanel['元素精通'] += self.EM

    def removeEM(self):
        self.current_character.attributePanel['元素精通'] -= self.EM

    def on_frame_update(self, target):
        self.removeEM()
        self.getEM()
        self.setEM()
        if self.character.Skill.effect:
            self.character.Skill.effect.interval_reduction = self.reduction

    def on_finish(self, target):
        super().on_finish(target)
        self.removeEM()

class ElementalBurst(EnergySkill):
    def __init__(self, lv):
        super().__init__(name="心景幻成", total_frames=112, cd=13.5*60, lv=lv,
                        element=('草', 1))
        self.duration = 15 * 60
        self.expand_frame = 66
        
    def on_frame_update(self, target):
        if self.current_frame == self.expand_frame:
            # 检测队伍元素类型
            pyro_count = 0
            electro_count = 0
            hydro_count = 0
            
            for char in Team.team:
                if char.element == '火':
                    pyro_count += 1
                elif char.element == '雷':
                    electro_count += 1
                elif char.element == '水':
                    hydro_count += 1
                    
            # 创建摩耶之殿领域
            maya_palace = MayaPalaceObject(
                self.caster,
                self.lv,
                self.duration,
                pyro_count,
                electro_count,
                hydro_count
            )
            maya_palace.apply()
            get_emulation_logger().log_skill_use("✨ 展开「摩耶之殿」领域")

class PassiveSkillEffect_1(TalentEffect):
    def __init__(self):
        super().__init__('净善摄受明论')

class PassiveSkillEffect_2(TalentEffect,EventHandler):
    def __init__(self):
        super().__init__('慧明缘觉智论')

    def apply(self, character):
        super().apply(character)
        EventBus.subscribe(EventType.BEFORE_DAMAGE_BONUS,self)
        EventBus.subscribe(EventType.BEFORE_CRITICAL,self)

    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_DAMAGE_BONUS:
            if event.data['character'] == self.character and event.data['damage'].name == '灭净三业':
                EM = max(0, self.character.attributePanel['元素精通'] - 200)
                event.data['damage'].panel['伤害加成'] +=  min(EM * 0.1,80)
                event.data['damage'].setDamageData('慧明缘觉智论_伤害加成', min(EM * 0.1,80))
        elif event.event_type == EventType.BEFORE_CRITICAL:
            if event.data['character'] == self.character and event.data['damage'].name == '灭净三业':
                EM = max(0, self.character.attributePanel['元素精通'] - 200)
                event.data['damage'].panel['暴击率']+= min(EM * 0.03,24)
                event.data['damage'].setDamageData('慧明缘觉智论_暴击率', min(EM * 0.03,24))

class ConstellationEffect_1(ConstellationEffect):
    def __init__(self):
        super().__init__('心识蕴藏之种')

class ConstellationEffect_2(ConstellationEffect,EventHandler):
    def __init__(self):
        super().__init__('正等善见之根')

    def apply(self, character):
        super().apply(character)
        EventBus.subscribe(EventType.BEFORE_CALCULATE,self)
        EventBus.subscribe(EventType.AFTER_AGGRAVATE,self)
        EventBus.subscribe(EventType.AFTER_QUICKEN,self)
        EventBus.subscribe(EventType.AFTER_SPREAD,self)

    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_CALCULATE:
            e = next((e for e in event.data['target'].effects if isinstance(e, SeedOfSkandhaEffect)), None)
            if not e:
                return
            if (event.data['damage'].damageType == DamageType.REACTION and 
                event.data['damage'].name in ['燃烧', '绽放', '超绽放', '烈绽放']):
                event.data['damage'].panel['暴击伤害'] = 100
                event.data['damage'].setDamageData('正等善见之根_暴击伤害', 100)
                event.data['damage'].panel['暴击率'] = 20
                event.data['damage'].setDamageData('正等善见之根_暴击率', 20)
        elif event.event_type in [EventType.AFTER_AGGRAVATE,EventType.AFTER_QUICKEN,EventType.AFTER_SPREAD]:
            target = event.data['elementalReaction'].target
            DefenseDebuffEffect(self.character, target, 30, 8*60,'正等善见之根_防御降低').apply()

class ConstellationEffect_3(ConstellationEffect):
    def __init__(self):
        super().__init__('熏习成就之芽')

    def apply(self, character):
        super().apply(character)
        self.character.Skill.lv = min(15, self.character.Skill.lv + 3)

class ConstellationEffect_4(ConstellationEffect,EventHandler):
    def __init__(self):
        super().__init__('比量现行之茎')
        # 因为只有一个目标且不会死亡，所以直接用添加一个效果来实现
        # 附近处于所闻遍计的蕴种印状态下的敌人数量为1/2/3/4或更多时，纳西妲的元素精通提升100/120/140/160点

    def apply(self, character):
        super().apply(character)
        EventBus.subscribe(EventType.AFTER_SKILL,self)

    def handle_event(self, event):
        if event.event_type == EventType.AFTER_SKILL:
            if event.data['character'] == self.character:
                ElementalMasteryBoostEffect(self.character, self.character, '比量现行之茎_元素精通', 100, 25*60).apply()

class ConstellationEffect_5(ConstellationEffect):
    def __init__(self):
        super().__init__('妙谛破愚之叶')

    def apply(self, character):
        super().apply(character)
        self.character.Burst.lv = min(15, self.character.Burst.lv + 3)

class KarmicOblivionEffect(Effect,EventHandler):
    def __init__(self, character):
        super().__init__(character, 10*60)
        self.name = '大辨圆成之实'
        self.last_attack_time = -60
        self.hit_count = 0
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">施放心景幻成后，纳西妲的普通攻击或重击命中处于所闻遍计的蕴种印状态下的敌人时，
        将对该敌人及其所处连结中的所有敌人释放灭净三业·业障除，
        基于纳西妲攻击力的200%与元素精通的400%，造成草元素伤害。</span></p>
        """

    def apply(self):
        super().apply()
        EventBus.subscribe(EventType.AFTER_DAMAGE,self)

    def remove(self):
        super().remove()
        EventBus.unsubscribe(EventType.AFTER_DAMAGE,self)

    def handle_event(self, event):
        if event.data['character'] != self.character:
            return
        if event.event_type == EventType.AFTER_DAMAGE and event.data['damage'].damageType in [DamageType.NORMAL,DamageType.CHARGED]:
            if event.frame - self.last_attack_time > 0.2*60:
                if self.hit_count >= 6:
                    self.remove()
                    self.hit_count = 0
                damage = Damage((200,400),('草', 1),DamageType.SKILL,'灭净三业·业障')
                damage.setBaseValue(('攻击力', '元素精通'))
                EventBus.publish(DamageEvent(self.character, event.data['target'], damage, GetCurrentTime()))
                self.last_attack_time = event.frame
                self.hit_count += 1    

class ConstellationEffect_6(ConstellationEffect,EventHandler):
    def __init__(self):
        super().__init__('大辨圆成之实')

    def apply(self, character):
        super().apply(character)
        EventBus.subscribe(EventType.OBJECT_CREATE,self)

    def handle_event(self, event):
        if event.event_type == EventType.OBJECT_CREATE:
            if isinstance(event.data['object'],MayaPalaceObject):
                KarmicOblivionEffect(self.character).apply()
                
class Nahida(Sumeru):
    ID = 59
    def __init__(self, level=1, skill_params=..., constellation=0):
        super().__init__(Nahida.ID, level, skill_params, constellation)

    def _init_character(self):
        super()._init_character()
        self.elemental_energy = ElementalEnergy(self,('草',50))
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

nahida_table = {
    'id': Nahida.ID,
    'name': '纳西妲',
    'type': '法器',
    'element': '草',
    'rarity': 5,
    'association':'须弥',
    'normalAttack': {'攻击次数': 4},
    'chargedAttack': {},
    'plungingAttack': {'攻击距离':['高空', '低空']},
    'skill': {},
    'burst': {}
}
