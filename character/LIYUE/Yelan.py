import random
from character.LIYUE.liyue import Liyue
from core.BaseClass import (ChargedAttackSkill, ConstellationEffect, ElementalEnergy, EnergySkill, Infusion, 
                            NormalAttackSkill, PlungingAttackSkill, SkillBase, TalentEffect)
from core.BaseObject import baseObject
from core.Event import DamageEvent, EventBus, EventHandler, EventType
from core.Logger import get_emulation_logger
from core.Team import Team
from core.Tool import GetCurrentTime, summon_energy
from core.calculation.DamageCalculation import Damage, DamageType
from core.effect.BaseEffect import Effect, HealthBoostEffect

class NormalAttack(NormalAttackSkill):
    def __init__(self, lv):
        super().__init__(lv=lv)
        self.segment_frames = [13, 15, 26, [35, 49]]
        self.damageMultiplier = {
            1: [40.68,43.99,47.3,52.03,55.34,59.13,64.33,69.53,74.73,80.41,86.09,91.76,97.44,103.11,108.79],  
            2: [39.04,42.22,45.4,49.94,53.12,56.75,61.74,66.74,71.73,77.18,82.63,88.08,93.52,98.97,104.42],  
            3: [51.6,55.8,60,66,70.2,75,81.6,88.2,94.8,102,109.2,116.4,123.6,130.8,138], 
            4: [[32.51,35.15,37.8,41.58,44.23,47.25,51.41,55.57,59.72,64.26,68.8,73.33,77.87,82.4,86.94],
                [32.51,35.15,37.8,41.58,44.23,47.25,51.41,55.57,59.72,64.26,68.8,73.33,77.87,82.4,86.94]]
        }
        self.end_action_frame = 38 

class ChargedAttack(ChargedAttackSkill):
    def __init__(self, lv):
        super().__init__(lv=lv)
        # 普通重击参数
        self.normal_hit_frame = 86
        self.normal_total_frames = 96
        self.normal_damage = [124,133.3,142.6,155,164.3,173.6,186,198.4,
                              210.8,223.2,235.6,248,263.5,279,294.5]
        
        # 破局矢参数
        self.breakthrough_hit_frame = 32
        self.breakthrough_total_frames = 40
        self.breakthrough_damage_ratio = [11.58,12.44,13.31,14.47,15.34,16.21,17.36,18.52,
                                          19.68,20.84,21.99,23.15,24.6,26.05,27.49]
        
        # 状态变量
        self.breakthrough_arrows = 1  # 破局矢数量

    def start(self, caster):
        if not super().start(caster):
            return False
        
        # 判断使用哪种重击
        if self.breakthrough_arrows > 0:
            self.hit_frame = self.breakthrough_hit_frame
            self.total_frames = self.breakthrough_total_frames
            get_emulation_logger().log_skill_use("🔮 破局矢准备就绪")
        else:
            self.hit_frame = self.normal_hit_frame
            self.total_frames = self.normal_total_frames
            get_emulation_logger().log_skill_use("🏹 普通重击")
            
        return True

    def _apply_attack(self, target):
        if self.breakthrough_arrows > 0:
            self.breakthrough_arrows -= 1
            base_value = '生命值'
            damage_value = self.breakthrough_damage_ratio[self.lv-1]
            name = '破局矢'
            element = ('水', 1)
        else:
            damage_value = self.normal_damage[self.lv-1]
            name = '重击'
            element = ('物理', 0)
            base_value = '攻击力'
            
        # 创建伤害事件
        damage = Damage(
            damageMultiplier=damage_value,
            element=element,
            damageType=DamageType.CHARGED,
            name=name,
        )
        damage.setBaseValue(base_value)
        
        EventBus.publish(DamageEvent(self.caster, target, damage, GetCurrentTime()))

class PlungingAttack(PlungingAttackSkill):
    ...

class ElementalSkill(SkillBase):
    def __init__(self, lv):
        super().__init__(name="萦络纵命索", total_frames=41, cd=10*60, lv=lv, element=('水', 1))
        
        # 技能参数配置
        self.hit_frame = 31  # 命中帧
        self.damageMultiplier = [22.61,24.31,26.01,28.27,29.96,31.66,33.92,36.18,38.44,40.7,42.97,45.23,48.05,50.88,53.71]
        self.breakthrough_chance = 0.34  # 破局矢触发概率
        self.cd_frame = 33
        self.stack_count = 1

    def start(self, caster):
        count = int(GetCurrentTime() - self.last_use_time / self.cd)
        if caster.constellation >= 1:
            self.stack_count = min(self.stack_count + count, 2)
        else:
            self.stack_count = min(self.stack_count + count, 1)

        if self.stack_count <= 0:
            get_emulation_logger().log_error(f'{self.name}技能还在冷却中')
            return False
        self.stack_count -= 1
        self.caster = caster
        self.current_frame = 0
        self.last_use_time = GetCurrentTime()
        get_emulation_logger().log_skill_use(f"🌀 {caster.name} 开始释放萦络纵命索")
        return True

    def on_frame_update(self, target):
        if self.current_frame == self.hit_frame:
            self._apply_skill_damage(target)

    def _apply_skill_damage(self, target):
        damage = Damage(
            damageMultiplier=self.damageMultiplier[self.lv-1],
            element=self.element,
            damageType=DamageType.SKILL,
            name='萦络纵命索'
        )
        damage.setBaseValue('生命值')

        summon_energy(4,self.caster, ('水', 2),time=80)
        
        EventBus.publish(DamageEvent(self.caster, target, damage, GetCurrentTime()))
        
        # 34%概率触发破局矢
        if random.random() < self.breakthrough_chance:
            self.caster.ChargedAttack.breakthrough_arrows = min(self.caster.ChargedAttack.breakthrough_arrows + 1, 1)
            get_emulation_logger().log_skill_use("🔮 破局矢已准备")

        if self.caster.constellation >= 4:
            for char in Team.team:
                HealthBoostEffect(self.caster, char, '诓惑者，接树移花', 10, 25*60).apply()

class ElementalBurst(EnergySkill):
    def __init__(self, lv):
        super().__init__(name="渊图玲珑骰", total_frames=91, cd=18, lv=lv, element=('水', 2))
        self.hit_frame = 76  # 命中帧
        self.damageMultiplier = [7.31,7.86,8.4,9.14,9.68,10.23,10.96,11.69,12.42,13.15,13.89,14.62,15.53,16.44,17.36]  # 技能伤害比例

    def on_frame_update(self, target):
        if self.current_frame == self.hit_frame:
            self._apply_burst_damage(target)

    def _apply_burst_damage(self, target):
        damage = Damage(
            damageMultiplier=self.damageMultiplier[self.lv-1],
            element=self.element,
            damageType=DamageType.BURST,
            name='渊图玲珑骰'
        )
        damage.setBaseValue('生命值')
        
        EventBus.publish(DamageEvent(self.caster, target, damage, GetCurrentTime()))

        linglong_dice = LinglongDiceObject(self.caster, self.lv)
        linglong_dice.apply()

class LinglongDiceObject(baseObject, EventHandler, Infusion):
    def __init__(self, character, lv):
        super().__init__("玄掷玲珑", 15*60)
        Infusion.__init__(self)
        self.character = character
        self.lv = lv
        self.damage_ratio = [4.87,5.24,5.6,6.09,6.46,6.82,7.31,7.8,8.28,8.77,9.26,9.74,10.35,10.96,11.57]
        self.last_attack_time = -60
        self.attack_interval = 60
        self.attack_active = False
        self.skill_active = False

        self.c2_time = -1.8 * 60

    def apply(self):
        super().apply()
        get_emulation_logger().log_skill_use("🎲 玄掷玲珑已生效")
        EventBus.subscribe(EventType.BEFORE_NORMAL_ATTACK, self)
        EventBus.subscribe(EventType.AFTER_NORMAL_ATTACK, self)
        EventBus.subscribe(EventType.AFTER_DAMAGE, self)

    def on_finish(self, target):
        super().on_finish(target)
        EventBus.unsubscribe(EventType.BEFORE_NORMAL_ATTACK, self)
        EventBus.unsubscribe(EventType.AFTER_NORMAL_ATTACK, self)
        EventBus.unsubscribe(EventType.AFTER_DAMAGE, self)

    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_NORMAL_ATTACK:
            self.attack_active = True
        elif (event.event_type == EventType.AFTER_DAMAGE and 
              event.data['damage'].damageType == DamageType.SKILL and
              event.data['character'] == self.character):
            self.skill_active = True
        elif event.event_type == EventType.AFTER_NORMAL_ATTACK:
            self.attack_active = False

    def on_frame_update(self, target):
        if self.attack_active and self.current_frame - self.last_attack_time >= self.attack_interval:
            self.last_attack_time = self.current_frame
            self._apply_linglong_damage(target)
        if self.skill_active:
            self.skill_active = False
            self._apply_linglong_damage(target) 

    def _apply_linglong_damage(self, target):
        for _ in range(3):
            damage = Damage(
                damageMultipiler=self.damage_ratio[self.lv-1],
                element=('水', self.apply_infusion()),
                damageType=DamageType.BURST,
                name='玄掷玲珑协同攻击'
            )
            damage.setBaseValue('生命值')
            
            EventBus.publish(DamageEvent(self.character, target, damage, GetCurrentTime()))

        if self.character.constellation >= 2 and self.current_frame - self.c2_time >= 1.8 * 60:
            damage = Damage(
                damageMultipiler=14,
                element=('水', 1),
                damageType=DamageType.BURST,
                name='玄掷玲珑-水箭'
            )
            damage.setBaseValue('生命值')
            self.c2_time = self.current_frame
            
            EventBus.publish(DamageEvent(self.character, target, damage, GetCurrentTime()))
        
class PassiveSkillEffect_1(TalentEffect):
    def __init__(self):
        super().__init__('猜先有方') 

    def apply(self, character):
        super().apply(character)

    def update(self, target):
        if GetCurrentTime() == 1:
            s = set()
            for char in Team.team:
                s.add(char.element)
            bonus = [6,12,18,30][len(s)]
            self.character.attributePanel['生命值%'] += bonus
            get_emulation_logger().log_skill_use(f"✨ {self.character.name} 猜先有方：获得{bonus}%生命值")

class PassiveSkillEffect_2(TalentEffect, EventHandler):
    def __init__(self):
        super().__init__('妙转随心')
        self.is_bonus = False
        self.bonus = 0
        self.last_tigger_time = 0

    def apply(self, character):
        super().apply(character)
        EventBus.subscribe(EventType.OBJECT_CREATE, self)
        EventBus.subscribe(EventType.OBJECT_DESTROY, self)
        EventBus.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)

    def handle_event(self, event):
        if event.event_type == EventType.OBJECT_CREATE:
            if event.data['object'].name == '玄掷玲珑':
                if self.is_bonus:
                    self.bonus = 0
                    self.last_tigger_time = event.frame
                else:
                    self.is_bonus = True
                    self.bonus = 0
                    self.last_tigger_time = event.frame
        elif event.event_type == EventType.OBJECT_DESTROY:
            if event.data['object'].name == '玄掷玲珑':
                if self.is_bonus:
                    self.bonus = 0
                    self.last_tigger_time = 0
                    self.is_bonus = False
        elif event.event_type == EventType.BEFORE_DAMAGE_BONUS:
            if event.data['character'] == Team.current_character and self.is_bonus:
                event.data['damage'].panel['伤害加成'] += self.bonus
                event.data['damage'].setDamageData(self.name+"_伤害加成",self.bonus)

    def update(self, target):
        if self.is_bonus:
            self.bonus = min(50,self.bonus+3.5/60)

class ConstellationEffect_1(ConstellationEffect):
    def __init__(self):
        super().__init__('与谋者，以局入局')

    def apply(self, character):
        super().apply(character)
        self.character.Skill.stack_count = 2

class ConstellationEffect_2(ConstellationEffect):
    def __init__(self):
        super().__init__('入彀者，多多益善')

class ConstellationEffect_3(ConstellationEffect):
    def __init__(self):
        super().__init__('晃盅者，琼畟药骰')

    def  apply(self, character):
        super().apply(character)
        self.character.Burst.lv = min(15,self.character.Burst.lv+3)

class ConstellationEffect_4(ConstellationEffect):
    def __init__(self):
        super().__init__('诓惑者，接树移花')

class ConstellationEffect_5(ConstellationEffect):
    def __init__(self):
        super().__init__('坐庄者，三仙戏法')

    def apply(self, character):
        super().apply(character)
        self.character.Skill.lv = min(15,self.character.Skill.lv+3)

class ConstellationEffect_6(ConstellationEffect, EventHandler):
    def __init__(self):
        super().__init__('取胜者，大小通吃')

    def apply(self, character):
        super().apply(character)
        EventBus.subscribe(EventType.BEFORE_BURST, self)

    def handle_event(self, event):
        if event.data['character'] == self.character:
            MastermindEffect(self.character).apply()

class MastermindEffect(Effect, EventHandler):
    def __init__(self, character):
        super().__init__(character, 25*60)
        self.breakthrough_arrows = 5
        self.damage_ratio = [11.58,12.44,13.31,14.47,15.34,16.21,17.36,18.52,
                            19.68,20.84,21.99,23.15,24.6,26.05,27.49]
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">获得{self.breakthrough_arrows}次破局失</span></p>
        """
    
    def apply(self):
        exiting = next((e for e in self.character.active_effects if isinstance(e, MastermindEffect)),None)
        if exiting:
            exiting.breakthrough_arrows = 5
            exiting.duration = self.duration
            return
        
        super().apply()
        self.character.add_effect(self)
        get_emulation_logger().log_effect(f"✨ {self.character.name} 取胜者，大小通吃：获得{self.breakthrough_arrows}次破局失")
        EventBus.subscribe(EventType.BEFORE_DAMAGE_BONUS,self)

    def remove(self):
        super().remove()
        get_emulation_logger().log_effect(f"✨ {self.character.name} 取胜者，大小通吃：结束")

    def handle_event(self, event):
        damage = event.data['damage']
        if self.character == damage.source and damage.damageType == DamageType.NORMAL and self.breakthrough_arrows > 0:
            damage.damageMultipiler = self.damage_ratio[self.character.skill_params[0]] * 1.56
            damage.element = ('水', 1)
            damage.damageType = DamageType.CHARGED
            damage.setBaseValue('生命值')
            damage.name = '破局失'
            damage.setDamageData('取胜者，大小通吃','6命破局失')
            self.breakthrough_arrows -= 1
            if self.breakthrough_arrows == 0:
                self.remove()

class Yelan(Liyue):
    ID = 46
    def __init__(self, level=1, skill_params=..., constellation=0):
        super().__init__(Yelan.ID, level, skill_params, constellation)

    def _init_character(self):
        super()._init_character()
        self.elemental_energy = ElementalEnergy(self,('水',70))
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

yelan_table = {
    'id': Yelan.ID,
    'name': '夜兰',
    'type': '弓',
    'element': '水',
    'rarity': 5,
    'association':'璃月',
    'normalAttack': {'攻击次数': 4},
    'chargedAttack': {},
    # 'plungingAttack': {'攻击距离':['高空', '低空']},
    'skill': {},
    'burst': {}
}