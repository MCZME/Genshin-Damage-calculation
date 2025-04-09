from character.NATLAN.natlan import Natlan
from setup.BaseClass import ElementalEnergy, NormalAttackSkill, SkillBase, SkillSate
from setup.BaseEffect import Effect, ResistanceDebuffEffect
from setup.DamageCalculation import Damage, DamageType
from setup.Event import DamageEvent, EventBus, EventHandler, EventType, NormalAttackEvent
from setup.Logger import get_emulation_logger
from setup.Tool import GetCurrentTime
from setup.Team import Team

class BladeRollerEffect(Effect,EventHandler):
    """刃轮巡猎效果"""
    def __init__(self, character):
        super().__init__(character,0)
        self.name = "刃轮巡猎"
        self.is_active = False
        self.Multipiler = [9, 12, 15, 18, 21, 24, 27, 30, 33, 36, 39, 42, 45, 48, 51]

    def apply(self):
        BladeRoller = next((e for e in self.character.active_effects if isinstance(e, BladeRollerEffect)), None)
        if BladeRoller:
            return
        
        self.character.add_effect(self)

        self._update_samplers()

        EventBus.subscribe(EventType.BEFORE_NIGHTSOUL_BLESSING, self)
        EventBus.subscribe(EventType.AFTER_NIGHT_SOUL_CHANGE, self)

    def remove(self):
        self.character.remove_effect(self)
        self.character.romve_NightSoulBlessing()
    
    def _update_samplers(self):
        n=0
        for i in Team.team:
            if i != self.character:
                if i.element in ['火', '水', '雷', '冰']:
                    self.character.samplers[n]['element'] = i.element
                    n += 1

    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_NIGHTSOUL_BLESSING:
            for i in self.character.samplers:
                if i['element'] == '岩':
                    i['active'] = True
        elif event.event_type == EventType.AFTER_NIGHT_SOUL_CHANGE:
            if event.data['character'] == self.character:
                if self.character.current_night_soul == self.character.max_night_soul:
                    self.character.consume_night_soul(self.character.max_night_soul)
                    self.is_active = True
    
    def update(self, target):
        if self.is_active:
            effect = ResistanceDebuffEffect('源音采样',self.character,target,
                                            list(self._get_element()),
                                            self.Multipiler[self.character.skill_params[1]-1],
                                            15*60)
            effect.apply()
            self.is_active = False
            get_emulation_logger().log_effect("🎧 源音采样生效")
            self.remove()

    def _get_element(self):
        s = set()
        for i in self.character.samplers:
            s.add(i['element'])
        return s

class XilonenNormalAttack(NormalAttackSkill):
    def __init__(self, lv):
        super().__init__(lv=lv, cd=0)
        
        # 普通攻击参数
        self.normal_segment_frames = [18, 24, 36]  # 三段剑击的帧数
        self.damageMultipiler = {
            1: [51.79, 56.01, 60.22, 66.25, 70.46, 75.28, 81.9, 88.53, 95.15, 102.38, 109.61, 116.83, 124.06, 131.29, 138.51],
            2: [27.37 + 27.37, 29.6 + 29.6, 31.83 + 31.83, 35.01 + 35.01, 37.24 + 37.24, 39.79 + 39.79, 43.29 + 43.29, 46.79 + 46.79, 50.29 + 50.29, 54.11 + 54.11, 57.93 + 57.93, 61.75 + 61.75, 65.57 + 65.57, 69.39 + 69.39, 73.21 + 73.21],
            3: [72.95, 78.89, 84.83, 93.31, 99.25, 106.03, 115.36, 124.69, 134.02, 144.2, 154.38, 164.56, 174.74, 184.92, 195.1]
        }
        
        # 刃轮巡猎参数
        self.night_soul_segment_frames = [17, 20, 33, 41]  # 四段踢击的帧数
        self.night_soul_damageMultipiler = {
            1: [56.02, 60.58, 65.14, 71.66, 76.22, 81.43, 88.59, 95.76, 102.92, 110.74, 118.56, 126.38, 134.19, 142.01, 149.83],
            2: [55.05, 59.53, 64.01, 70.41, 74.89, 80.01, 87.05, 94.09, 101.13, 108.82, 116.5, 124.18, 131.86, 139.54, 147.22],
            3: [65.82, 71.17, 76.53, 84.18, 89.54, 95.66, 104.08, 112.5, 120.92, 130.1, 139.28, 148.47, 157.65, 166.84, 176.02],
            4: [86.03, 93.03, 100.03, 110.04, 117.04, 125.04, 136.04, 147.05, 158.05, 170.05, 182.06, 194.06, 206.07, 218.07, 230.07]
        }

    def start(self, caster, n):
        # 检查夜魂加持状态
        if caster.Nightsoul_Blessing:
            self.segment_frames = self.night_soul_segment_frames
            self.damageMultipiler = self.night_soul_damageMultipiler
            self.element = ('岩', 1)  # 岩元素伤害
        else:
            self.segment_frames = self.normal_segment_frames
            self.damageMultipiler = self.damageMultipiler
            self.element = ('物理', 0)  # 普通伤害
            
        if not super().start(caster, n):
            return False
        return True

    def _apply_segment_effect(self, target):
        if self.caster.Nightsoul_Blessing:
            # 夜魂状态下基于防御力的岩元素伤害
            damage = Damage(
                damageMultipiler=self.damageMultipiler[self.current_segment+1][self.lv-1],
                element=self.element,
                damageType=DamageType.NORMAL,
                name=f'刃轮巡猎·{self.name} 第{self.current_segment+1}段'
            )
            damage.baseValue = "防御力"
            damage.setDamageData('夜魂伤害', True)
        else:
            damage = Damage(
                damageMultipiler=self.damageMultipiler[self.current_segment+1][self.lv-1],
                element=self.element,
                damageType=DamageType.NORMAL,
                name=f'{self.name} 第{self.current_segment+1}段'
            )
            
        damage_event = DamageEvent(self.caster, target, damage, GetCurrentTime())
        EventBus.publish(damage_event)

        # 发布普通攻击事件
        normal_attack_event = NormalAttackEvent(
            self.caster, 
            frame=GetCurrentTime(), 
            before=False,
            damage=damage,
            segment=self.current_segment+1
        )
        EventBus.publish(normal_attack_event)

class ElementalSkill(SkillBase):
    """元素战技：音火锻淬"""
    def __init__(self, lv):
        super().__init__(
            name="音火锻淬",
            total_frames=19,  # 技能动画帧数
            cd=7 * 60,
            lv=lv,
            element=('岩', 1),
            interruptible=False,
            state=SkillSate.OnField
        )
        self.damageMultipiler = [
            179.2, 192.64, 206.08, 224, 237.44, 250.88, 268.8, 286.72, 304.64,
            322.56, 340.48, 358.4, 380.8, 403.2, 425.6]
        self.hit_frame = 9  # 命中帧数

    def start(self, caster):
        BladeRoller = next((e for e in caster.active_effects if isinstance(e, BladeRollerEffect)), None)
        if BladeRoller:
            BladeRoller.remove()
            get_emulation_logger().log_skill_use(f'{caster.name}退出刃轮巡猎状态')
            return False
        if self.cd_timer > 0:
            get_emulation_logger().log_error(f'{self.name}技能还在冷却中')
            return False  # 技能仍在冷却中
        self.caster = caster
        self.current_frame = 0
        self.last_use_time = GetCurrentTime()

        # 获得夜魂值并进入夜魂状态
        self.caster.gain_night_soul(45)
        self.caster.gain_NightSoulBlessing()

        effect = BladeRollerEffect(self.caster)
        effect.apply()

        return True

    def on_frame_update(self, target):
        if self.current_frame == self.hit_frame:
            damage = Damage(
                self.damageMultipiler[self.lv-1],
                element=('岩', 1),
                damageType=DamageType.SKILL,
                name='音火锻淬'
            )
            damage.baseValue = "防御力"
            damage.setDamageData('夜魂伤害', True)
            
            event = DamageEvent(self.caster, target, damage, GetCurrentTime())
            EventBus.publish(event)
            
            print("🎵 音火锻淬！")

    def on_finish(self):
        super().on_finish()

    def on_interrupt(self):
        return super().on_interrupt()

# todo
# 希诺宁的夜魂加持状态具有如下限制：处于夜魂加持状态下时，希诺宁的夜魂值有9秒的时间限制，超过时间限制后，希诺宁的夜魂值将立刻耗竭。
# 处于夜魂加持状态下时，夜魂值耗竭后，希诺宁将无法通过固有天赋「四境四象回声」产生夜魂值。
class Xilonen(Natlan):
    ID = 89
    def __init__(self, level=1, skill_params=..., constellation=0):
        super().__init__(Xilonen.ID, level, skill_params, constellation)

    def _init_character(self):
        super()._init_character()
        self.elemental_energy = ElementalEnergy(self,('岩',60))
        self.max_night_soul = 90
        self.NormalAttack = XilonenNormalAttack(lv=self.skill_params[0])
        self.Skill = ElementalSkill(lv=self.skill_params[1])
        
        # 初始化3个源音采样器
        self.samplers = [{'element': '岩', 'active': False} for _ in range(3)]

Xilonen_table = {
    'id': Xilonen.ID,
    'name': '希诺宁',
    'type': '单手剑',
    'element': '岩',
    'rarity': 5,
    'association':'纳塔',
    'normalAttack': {'攻击次数': 4},
    'skill': {},
    'burst': {}
}
