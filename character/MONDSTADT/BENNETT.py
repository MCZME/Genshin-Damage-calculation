from core.context import get_context
from character.character import Character, CharacterState
from core.base_class import ChargedAttackSkill, ElementalEnergy, EnergySkill, NormalAttackSkill, ConstellationEffect, PlungingAttackSkill, SkillBase, TalentEffect
from core.BaseObject import baseObject
from core.logger import get_emulation_logger
from core.team import Team
from core.effect.BaseEffect import AttackValueBoostEffect, ElementalDamageBoostEffect, ElementalInfusionEffect
from core.systems.contract.damage import Damage, DamageType
from core.event import ChargedAttackEvent, DamageEvent, ElementalSkillEvent EventHandler, EventType, GameEvent, HealEvent
from core.systems.contract.healing import Healing, HealingType
from core.tool import GetCurrentTime

class NormalAttack(NormalAttackSkill):
    def __init__(self, lv):
        super().__init__(lv)
        self.segment_frames = [13,16,21,49,50]
        self.damageMultipiler = {
            1:[44.55, 48.17, 51.8, 56.98, 60.61, 64.75, 70.45, 76.15, 81.84, 88.06, 94.28, 100.49, 106.71, 112.92, 119.14],
            2:[42.74, 46.22, 49.7, 54.67, 58.15, 62.12, 67.59, 73.06, 78.53, 84.49, 90.45, 96.42, 102.38, 108.35, 114.31],
            3:[54.61, 59.06, 63.5, 69.85, 74.3, 79.37, 86.36, 93.34, 100.33, 107.95, 115.57, 123.19, 130.81, 138.43, 146.05],
            4:[59.68, 64.54, 69.4, 76.34, 81.2, 86.75, 94.38, 102.02, 109.65, 117.98, 126.31, 134.64, 142.96, 151.29, 159.62],
            5:[71.9, 77.75, 83.6, 91.96, 97.81, 104.5, 113.7, 122.89, 132.09, 142.12, 152.15, 162.18, 172.22, 182.25, 192.28]
        }

class ChargedAttack(ChargedAttackSkill):
    def __init__(self, lv):
        super().__init__(lv, total_frames=40)
        self.damageMultipiler = [
            [55.9 + 60.72, 60.45 + 65.66, 65.0 + 70.6, 71.5 + 77.66, 76.05 + 82.6, 
             81.25 + 88.25, 88.4 + 96.02, 95.55 + 103.78, 102.7 + 111.55, 
             110.5 + 120.02, 118.3 + 128.49, 126.1 + 136.96, 133.9 + 145.44, 
             141.7 + 153.91, 149.5 + 162.38]
        ]
        self.hit_frames = [10, 21]  # 两段攻击的命中帧

    def on_frame_update(self, target):
        current_frame = self.current_frame
        # 检查是否到达命中帧
        if current_frame in self.hit_frames:
            hit_index = self.hit_frames.index(current_frame)
            self._apply_attack(target, hit_index)
        
        return current_frame >= self.total_frames

    def _apply_attack(self, target, hit_index):
        """应用重击伤害"""
        event = ChargedAttackEvent(self.caster, frame=get_current_time())
        get_context().event_engine.publish(event)

        # 计算当前段伤害
        damage_value = self.damageMultipiler[0][self.lv-1] * (0.5 if hit_index == 0 else 0.5)  # 两段各50%伤害
        damage = Damage(
            damageMultipiler=damage_value,
            element=self.element,
            damageType=DamageType.CHARGED,
            name=f'重击第{hit_index+1}段'
        )
        damage_event = DamageEvent(self.caster, target, damage, get_current_time())
        get_context().event_engine.publish(damage_event)

        event = ChargedAttackEvent(self.caster, frame=get_current_time(), before=False)
        get_context().event_engine.publish(event)
        get_emulation_logger().log_skill_use(f"⚔️ 重击第{hit_index+1}段命中")

class PlungingAttack(PlungingAttackSkill):
    """下落攻击"""
    def __init__(self, lv):
        super().__init__(lv)
        self.damageMultipiler = {
            '下坠期间伤害': [63.93, 69.14, 74.34, 81.77, 86.98, 92.93, 101.1, 109.28, 
                          117.46, 126.38, 135.3, 144.22, 153.14, 162.06, 170.98],
            '低空坠地冲击伤害': [127.84, 138.24, 148.65, 163.51, 173.92, 185.81, 202.16, 
                             218.51, 234.86, 252.7, 270.54, 288.38, 306.22, 324.05, 341.89],
            '高空坠地冲击伤害': [159.68, 172.67, 185.67, 204.24, 217.23, 232.09, 252.51, 
                             272.93, 293.36, 315.64, 337.92, 360.2, 382.48, 404.76, 427.04]
        }

class ElementalSkill(SkillBase):
    """元素战技：热情过载"""
    def __init__(self, lv):
        super().__init__("热情过载", 41, 10*60, lv, ('火', 1))
        # 点按伤害
        self.tap_damage = [137.6, 147.92, 158.24, 172, 182.32, 192.64, 206.4, 
                          220.16, 233.92, 247.68, 261.44, 275.2, 292.4, 309.6, 326.8]
        # 一段蓄力伤害(两段)
        self.hold1_damage = [
            [84, 90.3, 96.6, 105, 111.3, 117.6, 126, 134.4, 142.8, 151.2, 159.6, 168, 178.5, 189, 199.5],
            [92, 98.9, 105.8, 115, 121.9, 128.8, 138, 147.2, 156.4, 165.6, 174.8, 184, 195.5, 207, 218.5]
        ]
        # 二段蓄力伤害(三段+爆炸)
        self.hold2_damage = [
            [88, 94.6, 101.2, 110, 116.6, 123.2, 132, 140.8, 149.6, 158.4, 167.2, 176, 187, 198, 209],
            [96, 103.2, 110.4, 120, 127.2, 134.4, 144, 153.6, 163.2, 172.8, 182.4, 192, 204, 216, 228],
            [132, 141.9, 151.8, 165, 174.9, 184.8, 198, 211.2, 224.4,
             237.6, 250.8, 264, 280.5, 297, 313.5]
        ]
        self.hold_mode = 0  # 0:点按 1:一段蓄力 2:二段蓄力
        self.hit_frames = []
        self.decreases_cd = 0

    def start(self, caster, hold=0):
        if not super().start(caster):
            return False
            
        self.hold_mode = hold
        # 根据不同模式设置参数
        if hold == 0:  # 点按
            self.total_frames = 41
            self.hit_frames = [16]
            self.cd = 5 * 60 * (1 - self.decreases_cd)
            self.cd_frame = 14
        elif hold == 1:  # 一段蓄力
            self.total_frames = 97
            self.hit_frames = [45, 57]
            self.cd = 7.5 * 60* (1 - self.decreases_cd)
            self.cd_frame = 43
        elif hold == 2:  # 二段蓄力
            self.total_frames = 340
            self.hit_frames = [112, 121, 166]
            self.cd = 10 * 60* (1 - self.decreases_cd)
            
        get_emulation_logger().log_skill_use(
            f"🔥 {caster.name} 使用{'点按' if hold==0 else '一段蓄力' if hold==1 else '二段蓄力'}热情过载")
        return True

    def on_frame_update(self, target):
        current_frame = self.current_frame
        if current_frame in self.hit_frames:
            hit_index = self.hit_frames.index(current_frame)
            self._apply_attack(target, hit_index)
            
        return current_frame >= self.total_frames

    def _apply_attack(self, target, hit_index):
        """应用元素战技伤害"""
        event = ElementalSkillEvent(self.caster, get_current_time())
        get_context().event_engine.publish(event)
        
        if self.hold_mode == 0:  # 点按
            damage = Damage(
                damageMultipiler=self.tap_damage[self.lv-1],
                element=('火', 1),
                damageType=DamageType.SKILL,
                name='热情过载(点按)'
            )
        elif self.hold_mode == 1:  # 一段蓄力
            damage_value = self.hold1_damage[hit_index][self.lv-1]
            damage = Damage(
                damageMultipiler=damage_value,
                element=('火', 1),
                damageType=DamageType.SKILL,
                name=f'热情过载(一段蓄力第{hit_index+1}段)'
            )
        else:  # 二段蓄力
            if hit_index < 2:  # 前两段普通攻击
                damage_value = self.hold2_damage[hit_index][self.lv-1]
                damage = Damage(
                    damageMultipiler=damage_value,
                    element=('火', 1),
                    damageType=DamageType.SKILL,
                    name=f'热情过载(二段蓄力第{hit_index+1}段)'
                )
            else:  # 第三段爆炸
                damage = Damage(
                    damageMultipiler=self.hold2_damage[2][self.lv-1],
                    element=('火', 1),
                    damageType=DamageType.SKILL,
                    name='热情过载(爆炸)'
                )
                get_emulation_logger().log_skill_use("💥 热情过载爆炸效果触发")
                
        damage_event = DamageEvent(self.caster, target, damage, get_current_time())
        get_context().event_engine.publish(damage_event)
        
        event = ElementalSkillEvent(self.caster, get_current_time(), before=False)
        get_context().event_engine.publish(event)

    def on_finish(self):
        return super().on_finish()
    
    def on_interrupt(self):
        return super().on_interrupt()

class InspirationFieldObject(baseObject, EventHandler):
    """鼓舞领域效果"""
    def __init__(self, character, base_atk, max_hp):
        super().__init__("鼓舞领域", 12*60)
        self.character = character
        self.base_atk = base_atk
        self.max_hp = max_hp
        self.current_char = character  # 当前在领域内的角色
        self.multipiler = {
            "持续治疗": [(6, 577.34), (6.45, 635.08), (6.9, 697.63), (7.5, 765), (7.95, 837.18), (8.4, 914.17), (9, 995.97), (9.6, 1082.58), (10.2, 1174.01),
                      (10.8, 1270.24), (11.4, 1371.29), (12, 1477.15), (12.75, 1587.82), (13.5, 1703.31), (14.25, 1823.6)],
            "攻击力加成比例": [56, 60.2, 64.4, 70, 74.2, 78.4, 84, 89.6, 95.2, 100.8, 106.4, 112, 119, 126, 133]
        }
        self.last_heal_time = -60

        if self.character.constellation >= 6:
            self.weapon_types = ['单手剑', '双手剑', '长柄武器']
            self.pyro_boost = 15

        # 订阅领域相关事件
        get_context().event_engine.subscribe(EventType.AFTER_CHARACTER_SWITCH, self)
        get_context().event_engine.subscribe(EventType.AFTER_HEALTH_CHANGE, self)

    def apply(self):
        super().apply()
        get_emulation_logger().log_object(f'{self.character.name}的{self.name}生成')
        self.on_frame_update(None)
        get_context().event_engine.subscribe(EventType.AFTER_CHARACTER_SWITCH, self) 

    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.AFTER_CHARACTER_SWITCH:
            old_char = event.data['old_character']
            new_char = event.data['new_character']
            if old_char == self.current_char:
                self.current_char = new_char
                self.on_frame_update(None)

    def on_frame_update(self, target):
        if not self.current_char:
            return

        if self.character.constellation >= 1:
            self._apply_c()
        else:
            self._apply()
        
    def _apply(self):
        # 持续治疗逻辑（每秒触发）
        current_time = get_current_time()
        if (self.current_char.currentHP / self.current_char.maxHP <= 0.7 and 
            current_time - self.last_heal_time >= 60):
            lv_index = self.character.Burst.lv - 1
            self.last_heal_time = current_time
            heal = Healing(self.multipiler["持续治疗"][lv_index],HealingType.BURST,'美妙旅程')
            heal.base_value = '生命值'
            heal_event = HealEvent(self.character, self.current_char,heal, get_current_time())
            get_context().event_engine.publish(heal_event)
        else:
            # 基础攻击加成逻辑
            lv_index = self.character.Burst.lv - 1
            atk_bonus_percent = (self.multipiler["攻击力加成比例"][lv_index]/100) * self.base_atk
            effect = AttackValueBoostEffect(self.character,self.current_char, "鼓舞领域", atk_bonus_percent, 2.1*60)
            effect.apply()

    def _apply_c(self):
        current_time = get_current_time()
        if current_time - self.last_heal_time >= 60:
            if self.current_char.currentHP / self.current_char.maxHP <= 0.7:
                lv_index = self.character.Burst.lv - 1
                self.last_heal_time = current_time
                heal = Healing(self.multipiler["持续治疗"][lv_index],HealingType.BURST,'美妙旅程')
                heal.base_value = '生命值'
                heal_event = HealEvent(self.character, self.current_char,heal, get_current_time())
                get_context().event_engine.publish(heal_event)

            lv_index = self.character.Burst.lv - 1
            atk_bonus_percent = (self.multipiler["攻击力加成比例"][lv_index]/100 + 0.2) * self.base_atk
            effect = AttackValueBoostEffect(self.character,self.current_char, "鼓舞领域_攻击力加成", atk_bonus_percent, 2.1*60)
            effect.apply()

            # 命座6效果
            if self.character.constellation >= 6 and self.current_char.type in self.weapon_types:
                # 火元素伤害加成
                elementEffect = ElementalDamageBoostEffect(self.character, self.current_char, "鼓舞领域_元素伤害", "火", self.pyro_boost,2.1*60)
                elementEffect.apply()
                Infusion = ElementalInfusionEffect(self.character,self.current_char, "鼓舞领域_火附魔", "火",2.1*60)
                Infusion.apply()

    def on_finish(self, target):
        super().on_finish(target)
        get_context().event_engine.unsubscribe(EventType.AFTER_CHARACTER_SWITCH, self)

class ElementalBurst(EnergySkill):
    def __init__(self, lv, caster=None):
        super().__init__(name="美妙旅程", 
                        total_frames=50, 
                        cd=15*60, 
                        lv=lv,
                        element=('火', 1), 
                        caster=caster)
        self.damageMultipiler = [232.8, 250.26, 267.72, 291, 308.46, 325.92, 349.2, 372.48,
                                  395.76, 419.04, 442.32, 465.6, 494.7, 523.8, 552.9]
    
    def on_finish(self):
        return super().on_finish()
    
    def on_frame_update(self, target):
        if self.current_frame == 37:
            # 计算领域参数
            base_atk = self.caster.attributePanel["攻击力"]
            max_hp = self.caster.maxHP
            
            # 创建领域效果
            field = InspirationFieldObject(self.caster, base_atk, max_hp)
            field.apply()
            
            damage = Damage(
                damageMultipiler=self.damageMultipiler[self.lv-1],
                element=('火', 1),
                damageType=DamageType.BURST,
                name=self.name,
            )
            damage_event = DamageEvent(self.caster, target, damage, get_current_time())
            get_context().event_engine.publish(damage_event)
            return True
        return False
    
    def on_interrupt(self):
        return super().on_interrupt()

class PassiveSkillEffect_1(TalentEffect):
    """天赋1：热情复燃"""
    def __init__(self):
        super().__init__("热情复燃")
    
    def apply(self, character):
        super().apply(character)
        self.character.Skill.decreases_cd += 0.2

class PassiveSkillEffect_2(TalentEffect):
    """天赋2：无畏的热血"""
    def __init__(self):
        super().__init__("无畏的热血")
    
    def apply(self, character):
        super().apply(character)
        for o in Team.active_objects:
            if isinstance(o,InspirationFieldObject):
                self.character.Skill.decreases_cd += 0.5
        
class ConstellationEffect_1(ConstellationEffect):
    """命座1：冒险憧憬"""
    def __init__(self):
        super().__init__('冒险憧憬')
        
    def apply(self, character):
        super().apply(character)

class ConstellationEffect_2(ConstellationEffect,EventHandler):
    """命座2：踏破绝境"""
    def __init__(self):
        super().__init__('踏破绝境')
        self.original_er = 0
        self.is_active = False  # 添加状态标记
        
    def apply(self, character):
        self.character = character
        get_context().event_engine.subscribe(EventType.AFTER_HEALTH_CHANGE, self)
        self._update_energy_recharge()
        
    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.AFTER_HEALTH_CHANGE and event.data['character'].id == self.character.id:
            self._update_energy_recharge()
                
    def _update_energy_recharge(self):
        current_hp_ratio = self.character.currentHP / self.character.maxHP
        if current_hp_ratio <= 0.7 and not self.is_active:
            # 应用加成
            self.character.attributePanel['元素充能效率'] += 30
            self.is_active = True
            print(f"⚡ {self.character.name} 触发命座2：元素充能效率提高30%")
        elif current_hp_ratio > 0.7 and self.is_active:
            # 移除加成
            self.character.attributePanel['元素充能效率'] -= 30
            self.is_active = False
            print(f"⚡ {self.character.name} 命座2效果解除")
                
    def remove(self):
        get_context().event_engine.unsubscribe(EventType.AFTER_HEALTH_CHANGE, self)
        if self.is_active:
            self.character.attributePanel['元素充能效率'] = self.original_er
            self.is_active = False

class ConstellationEffect_3(ConstellationEffect):
    """命座3：热情如火"""
    def __init__(self):
        super().__init__("热情如火")
    
    def apply(self, character):
        super().apply(character)
        self.character.Skill.lv = min(15, self.character.Skill.lv + 3)

class ConstellationEffect_4(ConstellationEffect):
    """命座4：冒险精神"""
    def __init__(self):
        super().__init__("冒险精神")
        # TODO: 实现命座4效果

class ConstellationEffect_5(ConstellationEffect):
    """命座5：开拓的心魂"""
    def __init__(self):
        super().__init__('开拓的心魂')
        
    def apply(self, character):
        super().apply(character)
        burst_lv = character.Burst.lv+3
        if burst_lv > 15:
            burst_lv = 15
        character.Burst = ElementalBurst(burst_lv)

class ConstellationEffect_6(ConstellationEffect):
    """命座6：烈火与勇气"""
    def __init__(self):
        super().__init__('烈火与勇气')
        
    def apply(self, character):
        super().apply(character)

# TODO : 
# 1.实现命座4效果
# 2.天赋2：二段蓄力不会将班尼特自身击飞。
class BENNETT(Character):
    ID = 19
    def __init__(self,level,skill_params,constellation=0):
        super().__init__(BENNETT.ID,level,skill_params,constellation)
        self.association = '蒙德'

    def _init_character(self):
        super()._init_character()
        self.elemental_energy = ElementalEnergy(self,('火',60))
        self.NormalAttack = NormalAttack(self.skill_params[0])
        self.ChargedAttack = ChargedAttack(self.skill_params[0])
        self.PlungingAttack = PlungingAttack(self.skill_params[0])
        self.Skill = ElementalSkill(self.skill_params[1])
        self.talent1 = PassiveSkillEffect_1()
        self.talent2 = PassiveSkillEffect_2()
        self.Burst = ElementalBurst(self.skill_params[2])
        self.constellation_effects[0] = ConstellationEffect_1()
        self.constellation_effects[1] = ConstellationEffect_2()
        self.constellation_effects[2] = ConstellationEffect_3()
        self.constellation_effects[3] = ConstellationEffect_4()
        self.constellation_effects[4] = ConstellationEffect_5()
        self.constellation_effects[5] = ConstellationEffect_6()

    def elemental_skill(self,hold=0):
        self._elemental_skill_impl(hold)

    def _elemental_skill_impl(self,hold):
        if self.Skill.start(self,hold):
            self._append_state(CharacterState.SKILL)
            skillEvent = ElementalSkillEvent(self,get_current_time())
            get_context().event_engine.publish(skillEvent)

bennett_table = {
    'id':BENNETT.ID,
    'name':'班尼特',
    'element':'火',
    'association':'蒙德',
    'rarity':4,
    'type':'单手剑',
    'normalAttack': {'攻击次数': 5},
    'chargedAttack': {},
    'plungingAttack': {'攻击距离':['高空', '低空']},
    'skill': {'释放时长':['点按','一段蓄力','二段蓄力']},
    'burst': {}
}

