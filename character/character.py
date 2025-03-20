from abc import abstractmethod
from enum import Enum, auto
from DataRequest import DR
from setup.Event import ElementalBurstEvent, ElementalSkillEvent, EventBus, HealChargeEvent, NormalAttackEvent
import setup.Tool as T

# 角色状态枚举
class CharacterState(Enum):
    IDLE = auto()        # 空闲状态
    CASTING = auto()      # 施法中
    NORMAL_ATTACK = auto()    # 普通攻击
    HEAVY_ATTACK = auto()    # 重击
    SKILL = auto()      # 元素战技
    BURST = auto()        # 元素爆发

class Character:

    def __init__(self, id=1, level=1, skill_params=[1,1,1], constellation=0):
        self.id = id
        self.level = level
        self.skill_params = skill_params
        self.attributeData ={
            "生命值" : 0,
            "固定生命值": 0,
            "攻击力": 0,
            "固定攻击力":0,
            "防御力": 0,
            "固定防御力":0,
            "元素精通" : 0,
            "暴击率" : 5,
            "暴击伤害" : 50,
            "治疗加成" : 0,
            "受治疗加成" : 0,
            "元素充能效率" : 100,
            "生命值%" : 0,
            "攻击力%": 0,
            "防御力%": 0,
            "火元素伤害加成": 0,
            "水元素伤害加成": 0,
            "雷元素伤害加成": 0,
            "冰元素伤害加成": 0,
            "岩元素伤害加成": 0,
            "风元素伤害加成": 0,
            "草元素伤害加成": 0,
            "物理伤害加成": 0,
            "伤害加成": 0
        }
        SQL = "SELECT * FROM `role_stats` WHERE role_id = {}".format(self.id)
        self.data = DR.read_data(SQL)[0]
        self.name = self.data[1]
        self.element = self.data[2]
        self.type = self.data[3]
        self._get_data(level)
        self.attributePanel = self.attributeData.copy()

        self.association = None
        self.constellation = constellation

        self.maxHP = self.attributePanel['生命值'] * (1 + self.attributePanel['生命值%'] / 100) + self.attributePanel['固定生命值']
        self.currentHP = self.maxHP
        self.weapon = None
        self.artifactManager = None
        self.state = [CharacterState.IDLE]
        self.on_field = False
        self._init_character()    # 初始化特有属性
        self.apply_talents()

    def _get_data(self,level):
        l = T.level(level)
        self.attributeData["生命值"] = self.data[5+l]
        self.attributeData["攻击力"] = self.data[13+l]
        self.attributeData["防御力"] = self.data[21+l]
        t = T.attributeId(self.data[-1])
        if t != "元素伤害加成":
            self.attributeData[t] += self.data[29+l]
        else:
            self.attributeData[self.element+t] += self.data[29+l]

    @abstractmethod
    def _init_character(self):
        """初始化角色特有属性"""
        self.NormalAttack = None
        self.HeavyAttack = None
        self.Skill = None
        self.Burst = None
        self.talent1 = None
        self.talent2 = None
        self.talent_effects = []  # 天赋效果列表
        self.active_effects = []  # 激活效果列表
        self.constellation_effects = [None, None, None, None, None, None]  # 命座效果列表

    def setArtifact(self,artifact):
        self.artifactManager = artifact
        self.artifactManager.updatePanel()
        self.artifactManager.setEffect()

    def setWeapon(self,weapon):
        self.weapon = weapon
        self.weapon.updatePanel()
        self.weapon.skill()

    def setConstellation(self,c):
        self.constellation = c

    def heal(self,amount):
        event = HealChargeEvent(self,amount,T.GetCurrentTime())
        EventBus.publish(event)
        if event.cancelled:
            return
        self.currentHP = max(self.maxHP,self.currentHP+event.data['amount'])
        event = HealChargeEvent(self,event.data['amount'],T.GetCurrentTime(),before=False)
        EventBus.publish(event)

    def normal_attack(self,n):
        """普攻"""
        self._normal_attack_impl(n)

    @abstractmethod
    def _normal_attack_impl(self,n):
        """普攻具体实现"""
        if self._is_change_state() and self.NormalAttack.start(self,n):
            self._append_state(CharacterState.NORMAL_ATTACK)

    def heavy_attack(self):
        """重击（需体力）"""
        self._heavy_attack_impl()
    
    @abstractmethod
    def _heavy_attack_impl(self):
        """重击具体实现"""
        if self._is_change_state() and self.HeavyAttack.start(self):
            self._append_state(CharacterState.HEAVY_ATTACK)

    def elemental_skill(self):
        """元素战技"""
        self._elemental_skill_impl()
    
    @abstractmethod
    def _elemental_skill_impl(self):
        """元素战技具体实现"""
        if self._is_change_state() and self.Skill.start(self):
            self._append_state(CharacterState.SKILL)
            skillEvent = ElementalSkillEvent(self,T.GetCurrentTime())
            EventBus.publish(skillEvent)
            
    def elemental_burst(self):
        """元素爆发"""
        self._elemental_burst_impl()

    @abstractmethod
    def _elemental_burst_impl(self):
        """元素爆发具体实现"""
        if self._is_change_state() and self.Burst.start(self):
            self._append_state(CharacterState.BURST)
            burstEvent = ElementalBurstEvent(self,T.GetCurrentTime())
            EventBus.publish(burstEvent)
            
    def apply_talents(self):
        """应用天赋效果"""
        if self.level >= 20:
            self.talent_effects.append(self.talent1)
        if self.level >= 60:
            self.talent_effects.append(self.talent2)
        for effect in self.talent_effects:
            if effect is not None:
                effect.apply(self)
        if self.constellation > 0:
            for effect in self.constellation_effects[:self.constellation]:
                if effect is not None:
                    effect.apply(self)

    def update(self,target):
        self.update_effects(target)
        if self.weapon is not None:
            self.weapon.update(target)
        for i in self.state:
            if i == CharacterState.SKILL:
                if self.Skill.update(target):
                    self.state.remove(CharacterState.SKILL)
                    skillEvent = ElementalSkillEvent(self,T.GetCurrentTime(),False)
                    EventBus.publish(skillEvent)
            elif i == CharacterState.BURST:
                if self.Burst.update(target):
                    self.state.remove(CharacterState.BURST)
                    burstEvent = ElementalBurstEvent(self,T.GetCurrentTime(),False)
                    EventBus.publish(burstEvent)
            elif i == CharacterState.NORMAL_ATTACK:
                if self.NormalAttack.update(target):
                    self.state.remove(CharacterState.NORMAL_ATTACK)
            elif i == CharacterState.HEAVY_ATTACK:
                if self.HeavyAttack.update(target):
                    self.state.remove(CharacterState.HEAVY_ATTACK)
        if self.constellation > 0:
            for effect in self.constellation_effects[:self.constellation]:
                if effect is not None:
                    effect.update(target)
        if len(self.state) == 0:
            self._append_state(CharacterState.IDLE)
        self.updateHealth()

    def updateHealth(self):
        current_maxHP = self.attributePanel['生命值'] * (1 + self.attributePanel['生命值%'] / 100) + self.attributePanel['固定生命值']

        if self.maxHP != current_maxHP:
            self.currentHP = self.currentHP * current_maxHP / self.maxHP
            self.maxHP = current_maxHP

    def update_effects(self,target):
        for effect in self.active_effects:
            effect.update(target)
        for talent in self.talent_effects:
            if talent is not None:
                talent.update(target)

    def _append_state(self,state):
        if state is not CharacterState.IDLE:
            if CharacterState.IDLE in self.state:
                self.state.remove(CharacterState.IDLE)
            self.state.append(state)
        elif state is CharacterState.IDLE:
            self.state.clear()
            self.state.append(state)

    def _is_change_state(self):
        from setup.BaseClass import SkillSate
        for i in self.state:
            if i == CharacterState.IDLE:
                return True
            elif i == CharacterState.SKILL and self.Skill.state == SkillSate.OffField:
                return True
            elif i == CharacterState.BURST and self.Burst.state == SkillSate.OffField:
                return True
        return False

    def add_effect(self, effect):
        self.active_effects.append(effect)
        
    def remove_effect(self, effect):
        self.active_effects.remove(effect)

    def to_dict(self):
        return {
            'id': self.id,
            'level': self.level,
            'skill_params': self.skill_params,
            'constellation': self.constellation,
            'weapon': self.weapon.to_dict() if self.weapon else None,
            'artifacts': self.artifactManager.to_dict() if self.artifactManager else None
        }
