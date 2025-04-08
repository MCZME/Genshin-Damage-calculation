from character.FONTAINE.fontaine import Fontaine
from character.character import CharacterState
from setup.BaseClass import ConstellationEffect, ElementalEnergy, EnergySkill, NormalAttackSkill, SkillBase, SkillSate, TalentEffect
from setup.BaseObject import ArkheObject, baseObject
from setup.DamageCalculation import Damage, DamageType
from setup.Event import DamageEvent, ElementalSkillEvent, EventBus, EventHandler, EventType, GameEvent, HealEvent
from setup.HealingCalculation import Healing, HealingType
from setup.BaseEffect import AttackBoostEffect, Effect, ElementalDamageBoostEffect, ResistanceDebuffEffect
from setup.Team import Team
from setup.Tool import GetCurrentTime, summon_energy

class HealingFieldEffect(Effect, EventHandler):
    """持续恢复生命值效果"""
    def __init__(self, caster, max_hp, duration):
        super().__init__(caster,duration)
        self.name = "生命恢复"
        self.max_hp = max_hp
        self.duration = duration
        self.last_heal_time = 0
        self.current_char = caster
        self.heal_triggered = False
        
        self.multipiler = [
            (2.67, 256.76), (2.87, 282.47), (3.07, 310.3), (3.33, 340.26), (3.53, 372.36),
            (3.73, 406.61), (4, 442.99), (4.27, 481.52), (4.53, 522.18), (4.8, 564.98),
            (5.07, 609.93), (5.33, 657.01), (5.67, 706.24), (6, 757.61), (6.33, 811.11)
        ]

    def apply(self):
        healingFieldEffect = next((effect for effect in self.current_char.active_effects if isinstance(effect, HealingFieldEffect)), None)
        if healingFieldEffect:
            healingFieldEffect.duration = self.duration
            return

        print(f"🩺 {self.current_char.name}获得生命恢复效果！")
        self.current_char.add_effect(self)
        self._apply_heal(self.current_char)
         # 订阅领域相关事件
        EventBus.subscribe(EventType.AFTER_CHARACTER_SWITCH, self)

    def _apply_heal(self, target):
        """应用治疗逻辑"""
        if not target:
            return
            
        current_time = GetCurrentTime()
        if current_time - self.last_heal_time >= 120:  # 每秒触发
            lv_index = self.character.Skill.lv - 1
            self.last_heal_time = current_time
            
            heal = Healing(self.multipiler[lv_index], HealingType.SKILL,'近迫式急促拦射')
            heal.base_value = '生命值'
            heal_event = HealEvent(self.character, target, heal, current_time)
            EventBus.publish(heal_event)

    def handle_event(self, event: GameEvent):
        """处理角色切换"""
        if event.event_type == EventType.AFTER_CHARACTER_SWITCH:
            old_char = event.data['old_character']
            new_char = event.data['new_character']
            if old_char == self.current_char:
                self.current_char.remove_effect(self)
                self.current_char = new_char
                self.apply()

    def update(self, target):
        if self.duration > 0:
            self.duration -= 1
            if self.duration <= 0:
                self.remove()
        self._apply_heal(self.current_char)

    def remove(self):
        print("🩺 生命恢复效果消失")
        EventBus.unsubscribe(EventType.AFTER_CHARACTER_SWITCH, self)
        self.current_char.remove_effect(self)

class ElementalSkill(SkillBase, EventHandler):
    def __init__(self, lv):
        super().__init__(name="近迫式急促拦射", total_frames=30, cd=15*60, lv=lv,
                        element=('火', 1), interruptible=True, state=SkillSate.OnField)
        self.cd_frame = 18
        self.scheduled_damage = None
        self.hold = False  # 添加长按状态标识
        
        self.skill_frames = {'点按':[25,31,59], '长按':[41,47,55]} # [命中帧，动画帧，流涌之刃的命中帧]
        self.overload_count = 0
        self.arkhe_interval = 10*60  # 荒性伤害间隔
        self.heal_duration = 12*60  # 治疗持续时间
        self.charged_shot = False
        self.special_round = 0  # 超量装药弹头数量
        
        self.damageMultipiler = {
            '点按伤害':[115.2, 123.84, 132.48, 144, 152.64, 161.28, 172.8, 184.32, 195.84, 207.36, 218.88, 230.4, 244.8, 259.2, 273.6, ],
            '长按伤害':[172.8, 185.76, 198.72, 216, 228.96, 241.92, 259.2, 276.48, 293.76, 311.04, 328.32, 345.6, 367.2, 388.8, 410.4, ],
            '「超量装药弹头」伤害':[282.4, 303.58, 324.76, 353, 374.18, 395.36, 423.6, 451.84, 480.08, 508.32, 536.56, 564.8, 600.1, 635.4, 670.7, ],
            '流涌之刃伤害':[28.8, 30.96, 33.12, 36, 38.16, 40.32, 43.2, 46.08, 48.96, 51.84, 54.72, 57.6, 61.2, 64.8, 68.4, ],
           }
        
        # 订阅超载反应事件
        EventBus.subscribe(EventType.BEFORE_OVERLOAD, self)
        self.last_arkhe_time = 0  # 记录上次荒性伤害时间

    def start(self, caster, hold=False):
        if not super().start(caster):
            return False
            
        # 根据按键类型初始化不同模式
        self.hold = hold
        if hold:
            self._start_charged_shot()
        else:
            self._start_quick_shot()
        # 启动治疗效果
        self._apply_heal_effect()
            
        return True

    def _start_quick_shot(self):
        """短按模式初始化"""
        self.total_frames = self.skill_frames['点按'][1]  # 使用动画帧作为总帧数
        # 在skill_frames定义的命中帧时触发伤害
        damage = Damage(
            self.damageMultipiler['点按伤害'][self.lv-1],
            element=('火',1),
            damageType=DamageType.SKILL,
            name=self.name + ' 点按伤害'
        )
        self.scheduled_damage = (damage, self.skill_frames['点按'][0])
        
    def _apply_heal_effect(self):
        """应用治疗效果"""
        if not self.caster:
            return
            
        # 创建治疗效果实例
        heal_effect = HealingFieldEffect(
            caster=self.caster,
            max_hp=self.caster.maxHP,
            duration=self.heal_duration
        )
        # 应用效果
        heal_effect.apply()

    def _start_charged_shot(self):
        """长按模式初始化"""
        self.total_frames = self.skill_frames['长按'][1]  # 使用动画帧作为总帧数
        damage_type = '长按伤害' if self.special_round < 1 else '「超量装药弹头」伤害'
        if damage_type == '「超量装药弹头」伤害':
            self.special_round -= 1
            self.charged_shot = True
        # 使用skill_frames定义的命中帧触发伤害
        damage = Damage(
            self.damageMultipiler[damage_type][self.lv-1],
            element=('火',2),
            damageType=DamageType.SKILL,
            name=self.name + ' ' +damage_type.split('伤害')[0]
        )
        self.scheduled_damage = (damage, self.skill_frames['长按'][0])

    def handle_event(self, event: GameEvent):
        """处理超载反应事件"""
        if event.event_type == EventType.BEFORE_OVERLOAD:
            if self.special_round < 1:
                self.special_round = 1
                print("🔋 获得超量装药弹头")
    
    def on_frame_update(self, target):
        # 处理预定伤害
        if hasattr(self, 'scheduled_damage'):
            damage, trigger_frame = self.scheduled_damage
            if self.current_frame == trigger_frame:
                event =  DamageEvent(self.caster, target, damage, GetCurrentTime())
                EventBus.publish(event)
                del self.scheduled_damage
                
                # 生成流涌之刃
                surge_frame = self.skill_frames['点按'][2] if trigger_frame ==25 else self.skill_frames['长按'][2]
                surge_damage = Damage(
                    self.damageMultipiler['流涌之刃伤害'][self.lv-1],
                    element=('火', 0),
                    damageType=DamageType.SKILL,
                    name='流涌之刃'
                )
                surge = ArkheObject(
                    name="流涌之刃",
                    character=self.caster,
                    arkhe_type='荒性',
                    damage=surge_damage,
                    life_frame=surge_frame - trigger_frame
                )
                surge.apply()
                print(f"🌊 生成流涌之刃")
                summon_energy(4, self.caster, ('火', 2))
        return False
    
    def on_interrupt(self):
        super().on_interrupt()

    def on_finish(self):
        super().on_finish()

class DoubleDamageBullet(baseObject):
    """二重毁伤弹对象"""
    def __init__(self, caster, damage):
        super().__init__(name="二重毁伤弹", life_frame=58) 
        self.caster = caster
        self.damage = damage

    def on_finish(self,target):
        # 在二重毁伤弹结束时触发伤害
        event = DamageEvent(self.caster, target, self.damage, GetCurrentTime())
        EventBus.publish(event)

    def on_frame_update(self, target):
        return super().on_frame_update(target)
       
class ElementalBurst(EnergySkill):
    """元素爆发：轰烈子母弹"""
    def __init__(self, lv):
        super().__init__(name="轰烈子母弹", total_frames=60, cd=15*60, lv=lv,
                        element=('火', 3), interruptible=False, state=SkillSate.OnField)
        self.skill_frames = [59,60] # 命中帧 动画帧
        self.split_bullets = 8  # 分裂的二重毁伤弹数量
        
        self.damageMultipiler = {
            '爆轰榴弹伤害':[368.16, 395.77, 423.38, 460.2, 487.81, 515.42, 552.24, 589.06, 
                      625.87, 662.69, 699.5, 736.32, 782.34, 828.36, 874.38, ],
            '二重毁伤弹伤害':[49.09, 52.77, 56.45, 61.36, 65.04, 68.72, 73.63, 78.54, 83.45,
                        88.36, 93.27, 98.18, 104.31, 110.45, 116.58, ],
        }

    def start(self, caster):
        if not super().start(caster):
            return False
        self.total_frames = self.skill_frames[1]  # 使用动画帧作为总帧数
        return True

    def on_frame_update(self, target):
        current_time = GetCurrentTime()
        
        if self.current_frame == self.skill_frames[0]:
            main_damage = Damage(
                self.damageMultipiler['爆轰榴弹伤害'][self.lv-1],
                element=('火', 2),
                damageType=DamageType.BURST,
                name=self.name
            )
            EventBus.publish(DamageEvent(self.caster, target, main_damage, current_time))
            
            for i in range(self.split_bullets):
                damage = Damage(
                    self.damageMultipiler['二重毁伤弹伤害'][self.lv-1],
                    element=('火', 1),
                    damageType=DamageType.BURST,
                    name='二重毁伤弹'
                )
                bullet = DoubleDamageBullet(
                    caster=self.caster,
                    damage=damage
                )
                bullet.apply()
    
    def on_interrupt(self):
        super().on_interrupt()

    def on_finish(self):
        return super().on_finish()

class CoordinatedTacticsEffect(Effect, EventHandler):
    def __init__(self, source, target):
        super().__init__(source,duration=60)
        self.current_character = target
        self.name = '协同战法'
        self.elements = ['火', '雷']
        self.duration = 60

    def apply(self):
        coordinatedTacticsEffect = next((effect for effect in self.current_character.active_effects 
                                         if isinstance(effect, CoordinatedTacticsEffect)), None)
        if coordinatedTacticsEffect:
            coordinatedTacticsEffect.duration = self.duration
            return
        EventBus.subscribe(EventType.AFTER_OVERLOAD, self)
        self.current_character.add_effect(self)

    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.AFTER_OVERLOAD:   
            self._apply_debuff(event.data['target'])
    
    def _apply_debuff(self, target):
        debuff = ResistanceDebuffEffect(
            name=self.name,
            source=self.character,
            target=target,
            elements=self.elements,
            debuff_rate=40,
            duration=6*60
        )
        debuff.apply()

    def remove(self):
        self.current_character.remove_effect(self)
        EventBus.unsubscribe(EventType.AFTER_OVERLOAD, self)

class PassiveSkillEffect_1(TalentEffect):
    def __init__(self):
        super().__init__('尖兵协同战法')     

    def apply(self, character):
        super().apply(character)
        for c in Team.team:
            effect = CoordinatedTacticsEffect(character, c)
            effect.apply()

    def check_team_condition(self):
        element_counts = Team.element_counts
        fire_count = element_counts.get('火', 0)
        electro_count = element_counts.get('雷', 0)
        return (
            (fire_count + electro_count) == len(Team.team) 
            and fire_count >= 1 
            and electro_count >= 1
        )
    
    def update(self, target):
        if self.check_team_condition(): 
            for c in Team.team:
                effect = CoordinatedTacticsEffect(self.character, c)
                effect.apply()
        else:
            for c in Team.team:
                for effect in c.active_effects:
                    if isinstance(effect, CoordinatedTacticsEffect):
                        effect.remove()
                        break
        return super().update(target)
    
class PassiveSkillEffect_2(TalentEffect, EventHandler):
    def __init__(self):
        super().__init__('纵阵武力统筹')

    def apply(self, character):
        super().apply(character)
        EventBus.subscribe(EventType.AFTER_SKILL, self)

    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.AFTER_SKILL and event.data['character'] == self.character:
            if self.character.Skill.charged_shot:
                maxHP = self.character.maxHP
                bonus = int(maxHP) % 1000
                if bonus > 40:
                    bonus = 40
                for c in Team.team:
                    if c.element in ['火', '雷']:
                        effect = AttackBoostEffect(c, self.name, bonus, 30*60)
                        effect.apply()
                self.character.Skill.charged_shot = False

class ConstellationEffect_1(ConstellationEffect, EventHandler):
    def __init__(self):
        super().__init__('稳固阵线的魄力')
        self.cooldown = 0  # 冷却时间计数器

    def apply(self, character):
        super().apply(character)
        EventBus.subscribe(EventType.AFTER_OVERLOAD, self)

    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.AFTER_OVERLOAD and event.data['character'] != self.character:
            if self.cooldown <= 0 and event.data['character'].level >= 20:
                self.cooldown = 10 * 60  # 10秒冷却
                summon_energy(1, self.character, ('火', 6),True,True)

class ConstellationEffect_2(ConstellationEffect, EventHandler):
    def __init__(self):
        super().__init__('协同殉爆的狙击')
        self.cooldown = 0  # 冷却时间计数器
        self.triggered = False
        
    def apply(self, character):
        super().apply(character)
        EventBus.subscribe(EventType.AFTER_DAMAGE, self)
        
    def handle_event(self, event: GameEvent):
        if (event.event_type == EventType.AFTER_DAMAGE and event.data['damage'].damageType == DamageType.SKILL and 
            event.data['character'] == self.character and self.character.Skill.hold and not self.triggered):
            
            self.triggered = True
            self.cooldown = 10 * 60  # 10秒冷却
            # 触发两次殉爆伤害
            for _ in range(2):
                explosion_damage = Damage(
                    120,
                    element=('火', 1),
                    damageType=DamageType.SKILL,
                    name='连锁殉爆'
                )
                explosion_event = DamageEvent(
                    self.character,
                    event.data['target'],
                    explosion_damage,
                    GetCurrentTime()
                )
                EventBus.publish(explosion_event)
   
    def update(self, target):
        if self.cooldown > 0:
            self.cooldown -= 1
            if self.cooldown <= 0:
                self.triggered = False

class ConstellationEffect_3(ConstellationEffect):
    """命座3：娴熟复装的技巧"""
    def __init__(self):
        super().__init__('娴熟复装的技巧')
        
    def apply(self, character):
        super().apply(character)
        skill_lv = character.Skill.lv + 3
        if skill_lv > 15:
            skill_lv = 15
        character.Skill = ElementalSkill(skill_lv)

class ConstellationEffect_5(ConstellationEffect):
    """命座5：增量火力的毁伤"""
    def __init__(self):
        super().__init__('增量火力的毁伤')
        
    def apply(self, character):
        super().apply(character)
        skill_lv = character.Burst.lv + 3
        if skill_lv > 15:
            skill_lv = 15
        character.Burst = ElementalBurst(skill_lv)

class PyroElectroBuffEffect(ElementalDamageBoostEffect):
    """火雷元素伤害加成效果"""
    def __init__(self, source):
        super().__init__(
            character=source,
            name='终结罪恶的追缉',
            element_type='火',  # 继承基类参数，实际处理双元素
            bonus=0,  # 动态计算
            duration=8 * 60  # 单层持续时间
        )
        self.stacks = []  # 存储各层剩余时间（每层独立计时）
        self.elements = ['火', '雷'] 
        self.current_character = None

    def apply(self, target):
         # 获取或创建buff效果
        buff = next((eff for eff in target.active_effects 
                        if isinstance(eff, PyroElectroBuffEffect)), None)
        if buff is None:
            target.add_effect(self)
            self.current_character = target
            self.stacks = [8 * 60]  # 初始1层，持续8秒
            self._update_total_bonus()
            self.setEffect()
        # 添加新层（最多3层），每层独立持续8秒
        else:
            buff.removeEffect() 
            if len(buff.stacks) < 3:
                buff.stacks.append(8 * 60)
            else:
                buff.stacks[buff.stacks.index(min(buff.stacks))] = 8 * 60

            buff._update_total_bonus()
            buff.setEffect()   

    def _update_total_bonus(self):
        """更新总伤害加成值"""
        self.bonus = 20 * len(self.stacks)  

    def update(self, target):
        # 更新所有层持续时间并移除过期层
        old_stacks = len(self.stacks)
        self.stacks = [t - 1 for t in self.stacks]
        self.stacks = [t for t in self.stacks if t > 0]
        new_stacks = len(self.stacks)

        if old_stacks != new_stacks:
            self.bonus = 20 * old_stacks
            self.removeEffect()
            self._update_total_bonus()
            self.setEffect()
        
        if not self.stacks:
            self.remove()
        else:
            # 更新基类持续时间以保证效果不被提前移除
            self.duration = max(self.stacks)  

    def remove(self):
        self.current_character.remove_effect(self)

    def setEffect(self):
        for element in self.elements:
            self.current_character.attributePanel[f'{element}元素伤害加成'] += self.bonus
        print(f"{self.current_character.name}获得{self.name}效果，火/雷元素伤害提升{self.bonus}%")

    def removeEffect(self):
        for element in self.elements:
            self.current_character.attributePanel[f'{element}元素伤害加成'] -= self.bonus
        print(f"{self.current_character.name}: {self.name}的火/雷元素伤害加成效果结束，移除了{self.bonus}%加成")

class ConstellationEffect_6(ConstellationEffect, EventHandler):
    '''命座6：终结罪恶的追缉'''
    def __init__(self):
        super().__init__('终结罪恶的追缉')
        self.heal_triggered = False
        
    def apply(self, character):
        super().apply(character)
        EventBus.subscribe(EventType.AFTER_HEAL, self)
        # 在HealingFieldEffect添加12秒后全队治疗
        original_remove = HealingFieldEffect.remove
        def new_remove(self):
            original_remove(self)
            if self.character.constellation >= 6 and not self.heal_triggered:
                self.heal_triggered = True
                # 12秒后触发全队治疗
                for c in Team.team:
                    heal = Healing(10, HealingType.SKILL,name='终结罪恶的追缉')
                    heal.base_value = '生命值'
                    heal_event = HealEvent(self.character, c, heal, GetCurrentTime())
                    EventBus.publish(heal_event)
        HealingFieldEffect.remove = new_remove
            
    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.AFTER_HEAL:
            heal_source = event.data['character']
            if heal_source == self.character and event.data['healing'].name == '近迫式急促拦射':
                member = event.data['target']
                buff = PyroElectroBuffEffect(self.character)
                buff.apply(member)

# todo:
# 1. 命座1，4
# 2. 重击
# 3. 天赋和命座测试
class CHEVREUSE(Fontaine):
    ID = 76
    def __init__(self, level, skill_params, constellation=0):
        super().__init__(CHEVREUSE.ID, level, skill_params, constellation)
        
    def _init_character(self):
        super()._init_character()
        self.elemental_energy = ElementalEnergy(self,('火',60))
        self.NormalAttack = NormalAttackSkill(self.skill_params[0])
        self.NormalAttack.segment_frames = [11,24,39,61]
        self.NormalAttack.damageMultipiler = {
            1:[53.13, 57.45, 61.78, 67.96, 72.28, 77.22, 84.02, 90.82, 97.61, 105.02, 112.44, 119.85, 127.26, 134.68, 142.09], 
            2:[49.31, 53.32, 57.34, 63.07, 67.09, 71.67, 77.98, 84.29, 90.59, 97.47, 104.36, 111.24, 118.12, 125, 131.88, ],
            3:[27.64 + 32.45, 29.9 + 35.09, 32.15 + 37.74, 35.36 + 41.51, 37.61 + 44.15, 40.18 + 47.17, 43.72 + 51.32, 47.25 + 55.47, 
               50.79 + 59.62, 54.65 + 64.15, 58.5 + 68.68, 62.36 + 73.21, 66.22 + 77.74, 70.08 + 82.26, 73.93 + 86.79, ],
            4:[77.26, 83.55, 89.84, 98.82, 105.11, 112.3, 122.18, 132.06, 141.95, 152.73, 163.51, 174.29, 185.07, 195.85, 206.63, ],
        }
        self.Skill = ElementalSkill(self.skill_params[1])
        self.Burst = ElementalBurst(self.skill_params[2])
        self.talent1 = PassiveSkillEffect_1()
        self.talent2 = PassiveSkillEffect_2()
        self.constellation_effects[0] = ConstellationEffect_1()
        self.constellation_effects[1] = ConstellationEffect_2()
        self.constellation_effects[2] = ConstellationEffect_3()
        self.constellation_effects[4] = ConstellationEffect_5()
        self.constellation_effects[5] = ConstellationEffect_6()

    def elemental_skill(self,hold=False):
        self._elemental_skill_impl(hold)
    
    def _elemental_skill_impl(self,hold):
        if self._is_change_state() and self.Skill.start(self, hold):
            self._append_state(CharacterState.SKILL)
            skillEvent = ElementalSkillEvent(self,GetCurrentTime())
            EventBus.publish(skillEvent)


chevreuse_table = {
    'id': CHEVREUSE.ID,
    'name': '夏沃蕾',
    'type': '长柄武器',
    'rarity': 4,
    'element': '火',
    'association': '枫丹',
    'normalAttack': {'攻击次数': 4},
    # 'chargedAttack': {},
    # 'plungingAttack': {'攻击距离':['高空', '低空']},
    'skill': {'释放时间':['长按','点按']},
    'burst': {}
}