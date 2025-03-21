from character.FONTAINE.fontaine import Fontaine
from character.character import CharacterState
from setup.BaseClass import NormalAttackSkill, SkillBase, SkillSate
from setup.BaseObject import ArkheObject, baseObject
from setup.DamageCalculation import Damage, DamageType
from setup.Event import DamageEvent, ElementalSkillEvent, EventBus, EventHandler, EventType, GameEvent, HealEvent
from setup.HealingCalculation import Healing, HealingType
from setup.BaseEffect import Effect
from setup.Tool import GetCurrentTime

class HealingFieldEffect(Effect, EventHandler):
    """持续恢复生命值效果"""
    def __init__(self, caster, max_hp, duration):
        super().__init__(caster)
        self.max_hp = max_hp
        self.duration = duration
        self.last_heal_time = 0
        self.current_char = caster
        
        # 订阅领域相关事件
        EventBus.subscribe(EventType.AFTER_CHARACTER_SWITCH, self)
        
        self.multipiler = [
            (2.67, 256.76), (2.87, 282.47), (3.07, 310.3), (3.33, 340.26), (3.53, 372.36),
            (3.73, 406.61), (4, 442.99), (4.27, 481.52), (4.53, 522.18), (4.8, 564.98),
            (5.07, 609.93), (5.33, 657.01), (5.67, 706.24), (6, 757.61), (6.33, 811.11)
        ]

    def apply(self):
        print("🩺 获得生命恢复效果！")
        self.current_char.add_effect(self)
        self._apply_heal(self.current_char)

    def _apply_heal(self, target):
        """应用治疗逻辑"""
        if not target:
            return
            
        current_time = GetCurrentTime()
        if current_time - self.last_heal_time >= 120:  # 每秒触发
            lv_index = self.character.Skill.lv - 1
            self.last_heal_time = current_time
            
            heal = Healing(self.multipiler[lv_index], HealingType.SKILL)
            heal.base_value = '生命值'
            heal_event = HealEvent(self.character, target, heal, current_time)
            EventBus.publish(heal_event)
            print(f"💚 {self.character.name} 治疗 {target.name} {heal.final_value:.2f} 生命值")

    def handle_event(self, event: GameEvent):
        """处理角色切换"""
        if event.event_type == EventType.AFTER_CHARACTER_SWITCH:
            old_char = event.data['old_character']
            new_char = event.data['new_character']
            if old_char == self.current_char:
                self.current_char.remove_effect(self)
                self.current_char = new_char
                self._apply_heal(new_char)

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
        self.scheduled_damage = None
        
        self.skill_frames = {'点按':[25,31,59], '长按':[41,47,55]} # [命中帧，动画帧，流涌之刃的命中帧]
        self.overload_count = 0
        self.arkhe_interval = 10*60  # 荒性伤害间隔
        self.heal_duration = 12*60  # 治疗持续时间
        self.charged_shot_ready = False
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
            damageType=DamageType.SKILL
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
        self.special_round -= 1
        damage_type = '长按伤害' if self.special_round < 1 else '「超量装药弹头」伤害'
        # 使用skill_frames定义的命中帧触发伤害
        damage = Damage(
            self.damageMultipiler[damage_type][self.lv-1],
            element=('火',2),
            damageType=DamageType.SKILL
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
                print(f"🔥 {'点按' if trigger_frame ==25 else '长按'}射击造成{damage.damage:.2f}火伤")
                del self.scheduled_damage
                
                # 生成流涌之刃
                surge_frame = self.skill_frames['点按'][2] if trigger_frame ==25 else self.skill_frames['长按'][2]
                surge_damage = Damage(
                    self.damageMultipiler['流涌之刃伤害'][self.lv-1],
                    element=('火', 0),
                    damageType=DamageType.SKILL
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
        print(f"💥 二重毁伤弹造成{self.damage.damage:.2f}火伤")
       
class ElementalBurst(SkillBase):
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
            )
            EventBus.publish(DamageEvent(self.caster, target, main_damage, current_time))
            print(f"💥🔥 爆轰榴弹造成范围火伤 {main_damage.damage:.2f}")
            
            for i in range(self.split_bullets):
                damage = Damage(
                    self.damageMultipiler['二重毁伤弹伤害'][self.lv-1],
                    element=('火', 1),
                    damageType=DamageType.BURST
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
            
class CHEVREUSE(Fontaine):
    ID = 76
    def __init__(self, level, skill_params, constellation=0):
        super().__init__(CHEVREUSE.ID, level, skill_params, constellation)
        
    def _init_character(self):
        super()._init_character()
        # 初始化普通攻击
        self.NormalAttack = NormalAttackSkill(self.skill_params[0])
        self.NormalAttack.segment_frames = [11,24,39,61]
        self.NormalAttack.damageMultipiler = {
            1:[53.13, 57.45, 61.78, 67.96, 72.28, 77.22, 84.02, 90.82, 97.61, 105.02, 112.44, 119.85, 127.26, 134.68, 142.09], 
            2:[49.31, 53.32, 57.34, 63.07, 67.09, 71.67, 77.98, 84.29, 90.59, 97.47, 104.36, 111.24, 118.12, 125, 131.88, ],
            3:[27.64 + 32.45, 29.9 + 35.09, 32.15 + 37.74, 35.36 + 41.51, 37.61 + 44.15, 40.18 + 47.17, 43.72 + 51.32, 47.25 + 55.47, 
               50.79 + 59.62, 54.65 + 64.15, 58.5 + 68.68, 62.36 + 73.21, 66.22 + 77.74, 70.08 + 82.26, 73.93 + 86.79, ],
            4:[77.26, 83.55, 89.84, 98.82, 105.11, 112.3, 122.18, 132.06, 141.95, 152.73, 163.51, 174.29, 185.07, 195.85, 206.63, ],
        }
        # 初始化元素战技
        self.Skill = ElementalSkill(self.skill_params[1])
        # 初始化元素爆发
        self.Burst = ElementalBurst(self.skill_params[2])

    def elemental_skill(self,hold=False):
        self._elemental_skill_impl(hold)
    
    def _elemental_skill_impl(self,hold):
        if self._is_change_state() and self.Skill.start(self, hold):
            self._append_state(CharacterState.SKILL)
            skillEvent = ElementalSkillEvent(self,GetCurrentTime())
            EventBus.publish(skillEvent)
