from character.character import Character, CharacterState
from setup.BaseClass import NormalAttackSkill, SkillBase, SkillSate
from setup.DamageCalculation import Damage, DamageType
from setup.Event import DamageEvent, EventBus, EventHandler, EventType, GameEvent, NightSoulBlessingEvent, NightSoulConsumptionEvent

# todo: 
# 1. 元素战技状态切换
# 2. 驰轮车状态下攻击实现
class ElementalSkill(SkillBase,EventHandler):
    def __init__(self, lv):
        super().__init__(name="诸火武装", total_frames=60*12.4, cd=15*60, lv=lv, 
                        element=('火', 1), interruptible=False, state=SkillSate.OffField)
        self.mode = None  # 初始无形态
        self.night_soul_consumed = 0
        self.attack_interval = 0 # 神环攻击计时器
        self.time_accumulator = 0   # 时间累积器

        self.damageMultipiler ={'焚曜之环':[128,137.6,147.2,160,169.6,179.2,192,204.8,217.6,230.4,243.2,256,272],
                                '伤害':[74.4,79.98,85.56,93,98.58,104.16,111.6,119.04,126.48,133.92,141.36,148.8,158.1]}
        
        # 订阅角色切换事件
        EventBus.subscribe(EventType.CHARACTER_SWITCH, self)

    def start(self, caster, hold=False):
        if not super().start(caster):
            return False
        
        # 根据长按参数初始化形态
        self.mode = '驰轮车' if hold else '焚曜之环'  # 修正点按初始形态
        caster.current_night_soul = caster.max_night_soul
        caster.chargeNightsoulBlessing()
        print(f"🔥 进入夜魂加持状态，初始形态：{self.mode}")
        return True

    def handle_event(self, event: GameEvent):
        """处理角色切换事件"""
        if event.event_type == EventType.CHARACTER_SWITCH:
            # 当玛薇卡被切出时自动转为焚曜之环
            if event.data['old_character'] == self.caster and self.caster is not None:
                print("🔄 角色切换，变为焚曜之环形态")
                self.mode = '焚曜之环'  # 直接设置形态
                self.attack_interval = 0  # 重置攻击计时器

    def update(self, target):
        self.current_frame += 1
        if self.on_frame_update(target):
            return True
        return False

    def on_frame_update(self, target):
        if self.current_frame == 1:
            damage = Damage(damageMultipiler=self.damageMultipiler['伤害'][self.lv-1], element=('火',1), damageType=DamageType.SKILL)
            damageEvent = DamageEvent(source=self.caster, target=target, damage=damage)
            EventBus.publish(damageEvent)
            print(f"🔥 玛薇卡释放元素战技，造成伤害：{damage.damage}")
        
        # 形态特有逻辑
        if self.mode == '焚曜之环':
            nightSoulConsumptionEvent = NightSoulConsumptionEvent(character=self.caster, amount=5/60)
            EventBus.publish(nightSoulConsumptionEvent)
            self.caster.current_night_soul -= 5/60
            self._handle_sacred_ring(target)
        elif self.mode == '驰轮车':
            nightSoulConsumptionEvent = NightSoulConsumptionEvent(character=self.caster, amount=9/60)
            EventBus.publish(nightSoulConsumptionEvent)
            self.caster.current_night_soul -= 9/60
            self._handle_chariot(target)
        
        self.time_accumulator += 1
        if self.time_accumulator >= 60:
            self.time_accumulator -= 60
            print(f"🕒 夜魂剩余：{self.caster.current_night_soul:.2f}")

        # 结束检测
        if self.caster.current_night_soul <= 0:
            print("🌙 夜魂耗尽")
            self.on_finish()
            return True
        return False
    
    def _handle_sacred_ring(self, target):
        """焚曜之环攻击逻辑（每2秒攻击一次）"""
        self.attack_interval += 1
        if self.attack_interval >= 120:
            self.attack_interval = 0

            nightSoulConsumptionEvent = NightSoulConsumptionEvent(character=self.caster, amount=3)
            EventBus.publish(nightSoulConsumptionEvent)
            self.caster.current_night_soul -= 3

            damage = Damage(damageMultipiler=self.damageMultipiler['焚曜之环'][self.lv-1], element=('火',1), damageType=DamageType.SKILL)
            damageEvent = DamageEvent(source=self.caster, target=target, damage=damage)
            EventBus.publish(damageEvent)
            print(f"🔥 焚曜之环造成伤害：{damage.damage}")
            
    def _handle_chariot(self, target):
        """驰轮车形态移动攻击逻辑"""
        pass  # 移动攻击逻辑需结合角色移动系统实现

    def switch_mode(self):
        """切换形态"""
        new_mode = '驰轮车' if self.mode == '焚曜之环' else '焚曜之环'
        print(f"🔄 切换至形态：{new_mode}")
        if new_mode == '焚曜之环':
            self.attack_interval = 0
        self.mode = new_mode

    def on_finish(self):
        # 取消事件订阅
        self.caster.chargeNightsoulBlessing()
        print("🌙 夜魂加持结束")

    def on_interrupt(self):
        self.on_finish()

class ElementalBurst(SkillBase, EventHandler):
    def __init__(self, lv):
        super().__init__(name="燔天之时", total_frames=60*2.375, cd=18*60, lv=lv,
                        element=('火', 1), state=SkillSate.OnField)

        self.furnace_duration = 7*60  # 7秒持续
        self.has_furnace = False

        # 战意系统属性
        self.max_battle_will = 200
        self.battle_will = 0
        self.last_will_gain_time = 0  # 最后获得战意的时间戳
        
        # 状态标志
        self.in_furnace = False

        # 控制标志
        self.ttt = 0 # 控制日志打印
        
        # 订阅事件
        EventBus.subscribe(EventType.CHARACTER_SWITCH, self)
        EventBus.subscribe(EventType.BEFORE_NORMAL_ATTACK, self)
        EventBus.subscribe(EventType.BEFORE_NIGHT_SOUL_CONSUMPTION, self)

    def start(self, caster):
        if self.battle_will < 50:
            print("❌ 战意不足，无法施放元素爆发")
            return False
        if not super().start(caster):
            return False
        
        # 消耗所有战意
        self.consumed_will = self.battle_will
        self.battle_will = 0
        
        return True

    # 坠日斩
    def _perform_plunge_attack(self,target):
        
        print(f"🔥 坠日斩造成 点火元素伤害")

    def handle_event(self, event: GameEvent):
        # 角色切换，死生之炉状态结束
        if event.event_type == EventType.CHARACTER_SWITCH:
            if event.data['old_character'] == self.caster and self.in_furnace:
                self.in_furnace = False
        # 普通攻击获得战意
        elif event.event_type == EventType.BEFORE_NORMAL_ATTACK:
            if event.data['frame']-self.last_will_gain_time >= 6:
                self.gain_battle_will(1.5)
                self.last_will_gain_time = event.data['frame']
        elif event.event_type == EventType.BEFORE_NIGHT_SOUL_CONSUMPTION:
            self.gain_battle_will(event.data['amount'])


    def update(self, target):
        self.current_frame += 1
        if self.current_frame == self.total_frames:
            # 进入死生之炉状态
            self.in_furnace = True
            self.caster.current_night_soul = min(self.caster.max_night_soul, self.caster.current_night_soul + 10)
            self._perform_plunge_attack(target)
        elif self.current_frame >= self.furnace_duration+self.total_frames:
            self.on_finish()
            return True
        return False

    def on_frame_update(self, target):
        return super().on_frame_update(target)

    def on_finish(self):
        self.in_furnace = False
        print("🕳️ 死生之炉状态结束")

    def on_interrupt(self):
        self.on_finish()

    def gain_battle_will(self, amount):
        self.battle_will = min(self.max_battle_will, self.battle_will + amount)
        if self.ttt % 60 == 0:
            print(f"🔥 获得战意：{self.battle_will:.2f}")
        self.ttt += 1

class MAVUIKA(Character):
    ID = 92
    def __init__(self,level,skill_params):
        super().__init__(self.ID,level,skill_params)
        self.NormalAttack = NormalAttackSkill(skill_params[0])
        self.Skill = ElementalSkill(skill_params[1])
        self.Burst = ElementalBurst(skill_params[2])

    def _init_character(self):
        super()._init_character()
        self.max_night_soul = 80 # 夜魂值上限
        self.current_night_soul = 0
        self.Nightsoul_Blessing = False # 夜魂加持状态
        self.before_nightsoulBlessingevent = NightSoulBlessingEvent(self)
        self.after_nightsoulBlessingevent = NightSoulBlessingEvent(self, before=False)

    def elemental_skill(self,hold=False):
        self._elemental_skill_impl(hold)

    def _elemental_skill_impl(self,hold=False):
        if self.state == CharacterState.IDLE and self.Skill.start(self,hold):
            self.state = CharacterState.SKILL
         # 已处于技能状态时切换形态
        elif self.state == CharacterState.SKILL:
            self.Skill.switch_mode()

    def chargeNightsoulBlessing(self):
        if self.Nightsoul_Blessing:
            EventBus.publish(self.after_nightsoulBlessingevent)
            self.Nightsoul_Blessing = False
        else:
            EventBus.publish(self.before_nightsoulBlessingevent)
            self.Nightsoul_Blessing = True
            print(f"🌙 夜魂加持，夜魂值上限提升至{self.max_night_soul}")
