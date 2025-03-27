from character.character import Character
from setup.BaseClass import ElementalEnergy, NormalAttackSkill, SkillBase, SkillSate, ConstellationEffect
from setup.BaseEffect import AttackValueBoostEffect, Effect, ElementalDamageBoostEffect, ElementalInfusionEffect
from setup.DamageCalculation import Damage, DamageType
from setup.Event import DamageEvent, EventBus, EventHandler, EventType, GameEvent, HealEvent
from setup.HealingCalculation import Healing, HealingType
from setup.Tool import GetCurrentTime

class InspirationFieldEffect(Effect, EventHandler):
    """鼓舞领域效果"""
    def __init__(self, caster, base_atk, max_hp, duration):
        super().__init__(caster)
        self.base_atk = base_atk
        self.max_hp = max_hp
        self.duration = duration * 60  # 转换为帧数
        self.field_active = True
        self.current_char = caster  # 当前在领域内的角色
        self.multipiler = {
            "持续治疗": [(6, 577.34), (6.45, 635.08), (6.9, 697.63), (7.5, 765), (7.95, 837.18), (8.4, 914.17), (9, 995.97), (9.6, 1082.58), (10.2, 1174.01),
                      (10.8, 1270.24), (11.4, 1371.29), (12, 1477.15), (12.75, 1587.82), (13.5, 1703.31), (14.25, 1823.6)],
            "攻击力加成比例": [56, 60.2, 64.4, 70, 74.2, 78.4, 84, 89.6, 95.2, 100.8, 106.4, 112, 119, 126, 133]
        }
        self.last_heal_time = 0  # 上次治疗时间（帧数）

        # 订阅领域相关事件
        EventBus.subscribe(EventType.AFTER_CHARACTER_SWITCH, self)
        EventBus.subscribe(EventType.AFTER_HEALTH_CHANGE, self)

    def apply(self):
        # 防止重复应用
        existing = next((e for e in self.character.active_effects 
                       if isinstance(e, InspirationFieldEffect)), None)
        if existing:
            return
        print("🔥 鼓舞领域展开！")
        self.current_char.add_effect(self)
        self._apply_field_effect(self.current_char)

    def _apply_field_effect(self, target):
        """应用领域效果到目标角色"""
        if not target:
            return

        # 持续治疗逻辑（每秒触发）
        current_time = GetCurrentTime()
        if target.currentHP / target.maxHP <= 0.7 and current_time - self.last_heal_time >= 60:
            lv_index = self.character.Burst.lv - 1
            self.last_heal_time = current_time
            heal = Healing(self.multipiler["持续治疗"][lv_index],HealingType.BURST,'美妙旅程')
            heal.base_value = '生命值'
            heal_event = HealEvent(self.character, target,heal, GetCurrentTime())
            EventBus.publish(heal_event)
        else:
            # 基础攻击加成逻辑
            lv_index = self.character.Burst.lv - 1
            atk_bonus_percent = (self.multipiler["攻击力加成比例"][lv_index]/100) * self.base_atk
            effect = AttackValueBoostEffect(target, "鼓舞领域", atk_bonus_percent, 5)
            effect.apply()

    def handle_event(self, event: GameEvent):
        """处理角色切换和血量变化"""
        if event.event_type == EventType.AFTER_CHARACTER_SWITCH:
            # 角色切换时，将效果转移到新角色
            old_char = event.data['old_character']
            new_char = event.data['new_character']
            if old_char == self.current_char:
                self.current_char.remove_effect(self)
                self.current_char = new_char
                self.current_char.add_effect(self)
                self._apply_field_effect(new_char)
        elif event.event_type == EventType.AFTER_HEALTH_CHANGE:
            self._apply_field_effect(self.current_char)

    def update(self, target):
        if self.duration > 0:
            self.duration -= 1
            if self.duration <= 0:
                self.remove()
        self._apply_field_effect(self.current_char)

    def remove(self):
        print("🔥 鼓舞领域消失")
        EventBus.unsubscribe(EventType.AFTER_CHARACTER_SWITCH, self)
        EventBus.unsubscribe(EventType.AFTER_HEALTH_CHANGE, self)
        self.current_char.remove_effect(self)

class ElementalBurst(SkillBase):
    def __init__(self, lv, caster=None):
        super().__init__(name="美妙旅程", 
                        total_frames=50, 
                        cd=15*60, 
                        lv=lv,
                        element=('火', 1), 
                        state=SkillSate.OnField,
                        caster=caster)
        self.damageMultipiler = [232.8, 250.26, 267.72, 291, 308.46, 325.92, 349.2, 372.48,
                                  395.76, 419.04, 442.32, 465.6, 494.7, 523.8, 552.9]  # 爆发伤害倍率
    
    def on_finish(self):
        return super().on_finish()
    
    def on_frame_update(self, target):
        if self.current_frame == 37:
            # 计算领域参数
            base_atk = self.caster.attributeData["攻击力"]  # 基础攻击力
            max_hp = self.caster.maxHP
            
            # 创建领域效果
            field = InspirationFieldEffect(self.caster, base_atk, max_hp, duration=12)
            field.apply()
            
            damage = Damage(
                damageMultipiler=self.damageMultipiler[self.lv-1],
                element=('火', 1),
                damageType=DamageType.BURST,
                name=self.name,
            )
            damage_event = DamageEvent(self.caster, target, damage, GetCurrentTime())
            EventBus.publish(damage_event)
            return True
        return False
    
    def on_interrupt(self):
        return super().on_interrupt()

class ConstellationEffect_1(ConstellationEffect):
    """命座1：冒险憧憬"""
    def __init__(self):
        super().__init__('冒险憧憬')
        
    def apply(self, character):
        # 保存原始方法
        original_apply = InspirationFieldEffect._apply_field_effect
        
        # 定义新的领域应用方法
        def new_apply_field_effect(self, target):
            # 移除生命值限制
            current_time = GetCurrentTime()
            
            # 保留原有治疗逻辑
            if target.currentHP / target.maxHP <= 0.7 and current_time - self.last_heal_time >= 60:
                lv_index = self.character.Burst.lv - 1
                self.last_heal_time = current_time
                heal = Healing(self.multipiler["持续治疗"][lv_index],HealingType.BURST,'美妙旅程')
                heal.base_value = '生命值'
                heal_event = HealEvent(self.character, target,heal, GetCurrentTime())
                EventBus.publish(heal_event)
            
            # 修改后的攻击加成逻辑
            lv_index = self.character.Burst.lv - 1
            base_atk = self.character.attributeData["攻击力"]
            # 基础加成 + 命座额外20%
            atk_bonus_percent = (self.multipiler["攻击力加成比例"][lv_index]/100 + 0.2) * base_atk
            effect = AttackValueBoostEffect(target, "鼓舞领域", atk_bonus_percent, 5)
            effect.apply()
        
        InspirationFieldEffect._apply_field_effect = new_apply_field_effect

class ConstellationEffect_2(ConstellationEffect,EventHandler):
    """命座2：踏破绝境"""
    def __init__(self):
        super().__init__('踏破绝境')
        self.original_er = 0
        self.is_active = False  # 添加状态标记
        
    def apply(self, character):
        self.character = character
        EventBus.subscribe(EventType.AFTER_HEALTH_CHANGE, self)
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
        EventBus.unsubscribe(EventType.AFTER_HEALTH_CHANGE, self)
        if self.is_active:
            self.character.attributePanel['元素充能效率'] = self.original_er
            self.is_active = False

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
        # 修改领域效果类
        original_init = InspirationFieldEffect.__init__
        
        def patched_init(self, caster, base_atk, max_hp, duration):
            original_init(self, caster, base_atk, max_hp, duration)
            
            # 添加火伤加成和附魔效果
            self.weapon_types = ['单手剑', '双手剑', '长柄武器']
            self.pyro_boost = 15
    
        def new_apply_field_effect(self, target):
            # 原始领域效果
            current_time = GetCurrentTime()
            if target.currentHP / target.maxHP <= 0.7 and current_time - self.last_heal_time >= 60:
                lv_index = self.character.Burst.lv - 1
                self.last_heal_time = current_time
                heal = Healing(self.multipiler["持续治疗"][lv_index],HealingType.BURST,'美妙旅程')
                heal.base_value = '生命值'
                heal_event = HealEvent(self.character, target,heal, GetCurrentTime())
                EventBus.publish(heal_event)
            
            # 命座6效果
            if target.type in self.weapon_types:
                # 火元素伤害加成
                elementEffect = ElementalDamageBoostEffect(target, "鼓舞领域", "火", self.pyro_boost,5)
                elementEffect.apply()
            
            # 攻击力加成
            lv_index = self.character.Burst.lv - 1
            atk_bonus_percent = (self.multipiler["攻击力加成比例"][lv_index]/100+0.2) * self.base_atk
            effect = AttackValueBoostEffect(target, "鼓舞领域", atk_bonus_percent, 5)
            Infusion = ElementalInfusionEffect(target, "鼓舞领域", "火",5)
            effect.apply()
            Infusion.apply()
            
        InspirationFieldEffect.__init__ = patched_init
        InspirationFieldEffect._apply_field_effect = new_apply_field_effect

# todo
# 元素战技
# 重击
# 天赋1 2
# 命座3 4
class BENNETT(Character):
    ID = 19
    def __init__(self,lv,skill_params,constellation=0):
        super().__init__(BENNETT.ID,lv,skill_params,constellation)
        self.association = '蒙德'

    def _init_character(self):
        super()._init_character()
        self.elemental_energy = ElementalEnergy(self,('火',60))
        self.NormalAttack = NormalAttackSkill(self.skill_params[0])
        self.NormalAttack.segment_frames = [13,16,21,49,50]
        self.NormalAttack.damageMultipiler = {
            1:[44.55, 48.17, 51.8, 56.98, 60.61, 64.75, 70.45, 76.15, 81.84, 88.06, 94.28, 100.49, 106.71, 112.92, 119.14],
            2:[42.74, 46.22, 49.7, 54.67, 58.15, 62.12, 67.59, 73.06, 78.53, 84.49, 90.45, 96.42, 102.38, 108.35, 114.31],
            3:[54.61, 59.06, 63.5, 69.85, 74.3, 79.37, 86.36, 93.34, 100.33, 107.95, 115.57, 123.19, 130.81, 138.43, 146.05],
            4:[59.68, 64.54, 69.4, 76.34, 81.2, 86.75, 94.38, 102.02, 109.65, 117.98, 126.31, 134.64, 142.96, 151.29, 159.62],
            5:[71.9, 77.75, 83.6, 91.96, 97.81, 104.5, 113.7, 122.89, 132.09, 142.12, 152.15, 162.18, 172.22, 182.25, 192.28]
        }
        self.Burst = ElementalBurst(self.skill_params[2])
        self.constellation_effects[0] = ConstellationEffect_1()
        self.constellation_effects[1] = ConstellationEffect_2()
        self.constellation_effects[4] = ConstellationEffect_5()
        self.constellation_effects[5] = ConstellationEffect_6()

bennett_table = {
    'id':BENNETT.ID,
    'name':'班尼特',
    'element':'火',
    'association':'蒙德',
    'rarity':4,
    'type':'单手剑',
    'normalAttack': {'攻击次数': 5},
    # 'chargedAttack': {},
    # 'plungingAttack': {'攻击距离':['高空', '低空']},
    # 'skill': {},
    'burst': {}
}