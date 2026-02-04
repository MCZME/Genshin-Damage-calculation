from abc import abstractmethod
from enum import Enum, auto
from DataRequest import DR
from core.Event import ElementalBurstEvent, ElementalSkillEvent, EventBus, EventType, GameEvent, HealChargeEvent
from core.Logger import get_emulation_logger
import core.Tool as T
from core.elementalReaction.ElementalAura import ElementalAura
from core.context import get_context
from core.action.action_manager import ActionManager
from core.action.action_data import ActionFrameData

# 角色状态枚举 (保留用于兼容性)
class CharacterState(Enum):
    IDLE = auto()        # 空闲状态
    NORMAL_ATTACK = auto()    # 普通攻击
    CHARGED_ATTACK = auto()    # 重击
    SKILL = auto()      # 元素战技
    BURST = auto()        # 元素爆发
    PLUNGING_ATTACK = auto()    # 下落攻击
    SKIP = auto()           # 跳过
    DASH = auto()            # 冲刺
    JUMP = auto()            # 跳跃
    FALL = auto()            # 下落

class Character:
    """"
    角色基类：
    角色等级为20，60等，自动视为已突破
    """
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
            "元素充能效率" : 100,
            "治疗加成" : 0,
            "受治疗加成" : 0,
            "火元素伤害加成": 0,
            "水元素伤害加成": 0,
            "雷元素伤害加成": 0,
            "冰元素伤害加成": 0,
            "岩元素伤害加成": 0,
            "风元素伤害加成": 0,
            "草元素伤害加成": 0,
            "物理伤害加成": 0,
            "生命值%" : 0,
            "攻击力%": 0,
            "防御力%": 0,
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

        self.aura = ElementalAura()
        self.maxHP = self.attributePanel['生命值'] * (1 + self.attributePanel['生命值%'] / 100) + self.attributePanel['固定生命值']
        self.currentHP = self.maxHP
        self.movement = 0
        self.height = 0
        self.falling_speed = 5
        self.weapon = None
        self.artifactManager = None
        self.on_field = False
        
        # ASM 引擎初始化
        try:
            ctx = get_context()
        except RuntimeError:
            ctx = None
        self.action_manager = ActionManager(self, ctx)
        
        self._init_character()    # 初始化特有属性
        self.apply_talents()

    @property
    def state(self):
        """兼容旧代码：从 ASM 状态推导 CharacterState 列表"""
        if not self.action_manager.current_action:
            return [CharacterState.IDLE]
        
        # 映射 ASM 动作名称到旧状态枚举
        name = self.action_manager.current_action.data.name
        mapping = {
            'normal_attack': CharacterState.NORMAL_ATTACK,
            'charged_attack': CharacterState.CHARGED_ATTACK,
            'elemental_skill': CharacterState.SKILL,
            'elemental_burst': CharacterState.BURST,
            'plunging_attack': CharacterState.PLUNGING_ATTACK,
            'dash': CharacterState.DASH,
            'jump': CharacterState.JUMP,
            'skip': CharacterState.SKIP
        }
        return [mapping.get(name, CharacterState.IDLE)]

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
        self.ChargedAttack = None
        self.PlungingAttack = None
        self.Dash = None
        self.Jump = None
        self.Skill = None
        self.Burst = None
        self.talent1 = None
        self.talent2 = None
        self.talent_effects = []  # 天赋效果列表
        self.active_effects = []  # 激活效果列表
        self.shield_effects = []  # 盾效果列表
        self.constellation_effects = [None, None, None, None, None, None]  # 命座效果列表
        self.elemental_energy = None

    def setArtifact(self,artifact):
        self.artifactManager = artifact
        self.artifactManager.updatePanel()
        self.artifactManager.setEffect()

    def setWeapon(self,weapon):
        self.weapon = weapon
        self.weapon.updatePanel()
        self.weapon.skill()

    def heal(self,amount):
        event = HealChargeEvent(self,amount,T.GetCurrentTime())
        EventBus.publish(event)
        orginHP = self.currentHP
        self.currentHP = min(self.maxHP,self.currentHP+event.data['amount'])
        event = HealChargeEvent(self,self.currentHP-orginHP,T.GetCurrentTime(),before=False)
        EventBus.publish(event)

    def hurt(self,amount):
        event = HealChargeEvent(self,-amount,T.GetCurrentTime())
        EventBus.publish(event)
        orginHP = self.currentHP
        self.currentHP = max(0,self.currentHP+event.data['amount'])
        event = HealChargeEvent(self,self.currentHP-orginHP,T.GetCurrentTime(),before=False)
        EventBus.publish(event)

    def _request_action(self, name, params=None):
        """ASM 统一动作请求入口"""
        # 获取动作帧数据
        action_data = self._get_action_data(name, params)
        return self.action_manager.request_action(action_data)

    def _get_action_data(self, name, params) -> ActionFrameData:
        """
        获取动作元数据。
        未来应从数据库或配置文件读取。目前为兼容旧逻辑，动态构造。
        """
        # 基础默认值 (旧逻辑通常假设动作完成才结束)
        # 这里尝试从旧的 Skill 对象中获取大概的时间
        total_frames = 60 # 默认 1 秒
        hit_frames = []
        
        if name == 'normal_attack':
            # 普攻旧逻辑通常在 start 时就开始了
            total_frames = 30 # 简化假设
            hit_frames = [10]
        elif name == 'elemental_skill':
            total_frames = 60
            hit_frames = [20]
        elif name == 'elemental_burst':
            total_frames = 120
            hit_frames = [40]
            
        return ActionFrameData(name=name, total_frames=total_frames, hit_frames=hit_frames)

    def skip(self, n):
        self._request_action('skip', n)

    def dash(self):
        self._request_action('dash')

    def jump(self):
        self._request_action('jump')

    def normal_attack(self, n):
        self._request_action('normal_attack', n)

    def charged_attack(self):
        self._request_action('charged_attack')

    def plunging_attack(self, is_high=False):
        self._request_action('plunging_attack', is_high)

    def elemental_skill(self):
        self._request_action('elemental_skill')
            
    def elemental_burst(self):
        self._request_action('elemental_burst')
            
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
        # 1. 更新效果与元素附着
        self.update_effects(target)
        self.aura.update()
        if self.weapon is not None:
            self.weapon.update(target)
            
        # 2. 驱动 ASM
        self.action_manager.update()
        
        # 3. 处理命座更新
        if self.constellation > 0:
            for effect in self.constellation_effects[:self.constellation]:
                if effect is not None:
                    effect.update(target)
                    
        # 4. 血量更新
        self.updateHealth()

    def updateHealth(self):
        current_maxHP = self.attributePanel['生命值'] * (1 + self.attributePanel['生命值%'] / 100) + self.attributePanel['固定生命值']

        if self.maxHP != current_maxHP:
            self.currentHP = self.currentHP * current_maxHP / self.maxHP
            self.maxHP = current_maxHP

    def update_effects(self,target):
        remove_effects = []
        for effect in self.active_effects:
            effect.update(target)
            if not effect.is_active:
                remove_effects.append(effect)
        for effect in remove_effects:
            self.remove_effect(effect)

        remove_shields = []
        for shield in self.shield_effects:
            shield.update(target)
            if not shield.is_active:
                remove_shields.append(shield)
        for shield in remove_shields:
            self.remove_shield(shield)

        for talent in self.talent_effects:
            if talent is not None:
                talent.update(target)

    def add_effect(self, effect):
        self.active_effects.append(effect)
        
    def remove_effect(self, effect):
        self.active_effects.remove(effect)

    def add_shield(self, shield):
        self.shield_effects.append(shield)

    def remove_shield(self, shield):
        self.shield_effects.remove(shield)
    
    def to_dict(self):
        return {
            'id': self.id,
            'level': self.level,
            'skill_params': self.skill_params,
            'constellation': self.constellation,
            'weapon': self.weapon.to_dict() if self.weapon else None,
            'artifacts': self.artifactManager.to_dict() if self.artifactManager else None
        }
