from character.character import Character
from setup.BaseClass import Effect, SkillBase, SkillSate
from setup.BaseEffect import AttackBoostEffect, AttackValueBoostEffect
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
        EventBus.subscribe(EventType.CHARACTER_SWITCH, self)
        EventBus.subscribe(EventType.AFTER_HEALTH_CHANGE, self)

    def apply(self):
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
            heal = Healing(self.multipiler["持续治疗"][lv_index],HealingType.BURST)
            heal.base_value = '攻击力'
            heal_event = HealEvent(self.character, target,heal, GetCurrentTime())
            EventBus.publish(heal_event)
            print(f"💚 {self.character.name} 治疗 {target.name} {heal.final_value} 生命值")
        # 攻击加成逻辑
        else:
            lv_index = self.character.Burst.lv - 1
            atk_bonus_percent = (self.multipiler["攻击力加成比例"][lv_index]/100)*self.base_atk
            effect = AttackValueBoostEffect(target, "鼓舞领域", atk_bonus_percent, 2)  # 百分比加成
            effect.apply()

    def handle_event(self, event: GameEvent):
        """处理角色切换和血量变化"""
        if event.event_type == EventType.CHARACTER_SWITCH:
            # 角色切换时，将效果转移到新角色
            old_char = event.data['old_character']
            new_char = event.data['new_character']
            if old_char == self.current_char:
                self.current_char.remove_effect(self)
                self.current_char = new_char
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
        EventBus.unsubscribe(EventType.CHARACTER_SWITCH, self)
        EventBus.unsubscribe(EventType.AFTER_HEALTH_CHANGE, self)
        self.caster.remove_effect(self)

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
                damageType=DamageType.BURST
            )
            damage_event = DamageEvent(self.caster, target, damage, GetCurrentTime())
            EventBus.publish(damage_event)
            print(f"🔥 {self.caster.name} 对 {target.name} 造成了 {damage.damage:.2f} 点伤害")
            return True
        return False
    
    def on_interrupt(self):
        return super().on_interrupt()

class BENNETT(Character):
    ID = 19
    def __init__(self,lv,skill_params,constellation=0):
        super().__init__(BENNETT.ID,lv,skill_params,constellation)
        self.association = '蒙德'

    def _init_character(self):
        super()._init_character()
        self.Burst = ElementalBurst(self.skill_params[2])
