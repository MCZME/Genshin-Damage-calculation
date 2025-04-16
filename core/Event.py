from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Dict, List

from core.DataHandler import send_to_handler

# --------------------------
# 事件类型枚举
# --------------------------
class EventType(Enum):
    FRAME_END = auto()  # 每帧结束时
    BEFORE_DAMAGE = auto()       # 伤害计算前
    AFTER_DAMAGE = auto()        # 伤害计算后
    BEFORE_ATTACK = auto()        # 攻击力计算前
    AFTER_ATTACK = auto()         # 攻击力计算后
    BEFORE_DAMAGE_MULTIPLIER = auto()  # 伤害倍率计算前
    AFTER_DAMAGE_MULTIPLIER = auto()   # 伤害倍率计算后
    BEFORE_DAMAGE_BONUS = auto()  # 伤害加成计算前
    AFTER_DAMAGE_BONUS = auto()   # 伤害加成计算后
    BEFORE_CRITICAL = auto()     # 暴击率计算前
    AFTER_CRITICAL = auto()      # 暴击率计算后
    BEFORE_CRITICAL_BRACKET = auto()      # 暴击伤害计算前
    AFTER_CRITICAL_BRACKET = auto()       # 暴击伤害计算后
    BEFORE_DEFENSE = auto()       # 防御力计算前
    AFTER_DEFENSE = auto()       # 防御力计算后
    BEFORE_RESISTANCE = auto()   # 抗性计算前
    AFTER_RESISTANCE = auto()    # 抗性计算后
    BEFORE_INDEPENDENT_DAMAGE = auto()  # 独立伤害倍率计算前
    AFTER_INDEPENDENT_DAMAGE = auto()   # 独立伤害倍率计算后
    BEFORE_ELEMENTAL_REACTION = auto()  # 元素反应触发前
    AFTER_ELEMENTAL_REACTION = auto()   # 元素反应触发后
    BEFORE_FREEZE = auto()       # 冻结反应前
    AFTER_FREEZE = auto()        # 冻结反应后
    BEFORE_CATALYZE = auto()     # 激化反应前
    AFTER_CATALYZE = auto()      # 激化反应后
    BEFORE_VAPORIZE = auto()     # 蒸发反应前
    AFTER_VAPORIZE = auto()      # 蒸发反应后
    BEFORE_MELT = auto()         # 融化反应前
    AFTER_MELT = auto()          # 融化反应后
    BEFORE_OVERLOAD = auto()     # 超载反应前
    AFTER_OVERLOAD = auto()      # 超载反应后
    BEFORE_SWIRL = auto()        # 扩散反应前
    AFTER_SWIRL = auto()         # 扩散反应后
    BEFORE_SHATTER = auto()      # 碎冰反应前
    AFTER_SHATTER = auto()       # 碎冰反应后
    BEFORE_BURNING = auto()      # 燃烧反应前
    AFTER_BURNING = auto()       # 燃烧反应后
    BEFORE_SUPERCONDUCT = auto()  # 超导反应前
    AFTER_SUPERCONDUCT = auto()   # 超导反应后
    BEFORE_ELECTRO_CHARGED = auto()  # 感电反应前
    AFTER_ELECTRO_CHARGED = auto()   # 感电反应后
    BEFORE_FIXED_DAMAGE = auto()  # 固定伤害加成计算前
    AFTER_FIXED_DAMAGE = auto()   # 固定伤害加成计算后

    BEFORE_HEALTH_CHANGE = auto()  # 角色血量变化前
    AFTER_HEALTH_CHANGE = auto()   # 角色血量变化后
    BEFORE_HEAL = auto()         # 治疗计算前
    AFTER_HEAL = auto()          # 治疗后
    BEFORE_HURT = auto()         # 受伤计算前
    AFTER_HURT = auto()          # 受伤后
    BEFORE_SHIELD_CREATION = auto()  # 护盾生成前
    AFTER_SHIELD_CREATION = auto()   # 护盾生成后

    BEFORE_NORMAL_ATTACK = auto()  # 普通攻击前
    AFTER_NORMAL_ATTACK = auto()   # 普通攻击后
    BEFORE_CHARGED_ATTACK = auto()  # 重击前
    AFTER_CHARGED_ATTACK = auto()   # 重击后
    BEFORE_PLUNGING_ATTACK = auto()  # 下落攻击前
    AFTER_PLUNGING_ATTACK = auto()   # 下落攻击后
    BEFORE_SKILL = auto()        # 技能使用前
    AFTER_SKILL = auto()         # 技能使用后
    BEFORE_BURST = auto()        # 爆发使用前
    AFTER_BURST = auto()         # 爆发使用后
    BEFORE_DASH = auto()         # 冲刺前
    AFTER_DASH = auto()          # 冲刺后
    BEFORE_JUMP = auto()         # 跳跃前
    AFTER_JUMP = auto()          # 跳跃后
    BEFORE_FALLING = auto()     # 下落前
    AFTER_FALLING = auto()       # 下落后

    BEFORE_ENERGY_CHANGE = auto()  # 能量变化前
    AFTER_ENERGY_CHANGE = auto()   # 能量变化后
    BEFORE_CHARACTER_SWITCH = auto()   # 角色切换前
    AFTER_CHARACTER_SWITCH = auto()    # 角色切换后
    BEFORE_NIGHTSOUL_BLESSING = auto()  # 夜魂加持之前
    AFTER_NIGHTSOUL_BLESSING = auto()  # 夜魂加持结束后
    BEFORE_NIGHT_SOUL_CHANGE = auto()  # 夜魂改变之前
    AFTER_NIGHT_SOUL_CHANGE = auto()  # 夜魂改变之后
    NightsoulBurst = auto()      # 夜魂迸发

# --------------------------
# 事件类
# --------------------------
class GameEvent:
    def __init__(self, event_type: EventType, frame, **kwargs):
        self.event_type = event_type
        self.frame = frame
        self.data = kwargs        # 扩展数据
        self.cancelled = False    # 是否取消事件

class FrameEndEvent(GameEvent):
    def __init__(self, frame):
        super().__init__(EventType.FRAME_END, frame)

class DamageEvent(GameEvent):
    def __init__(self, source, target, damage, frame, before=True, **kwargs):
        if before:
            damage.setSource(source)
            damage.setTarget(target)
            super().__init__(EventType.BEFORE_DAMAGE, frame=frame, character=source, target=target, damage=damage, **kwargs)
        else:
            super().__init__(EventType.AFTER_DAMAGE, frame=frame, character=source, target=target, damage=damage, **kwargs)
            send_to_handler(frame, {'event':{'type':EventType.AFTER_DAMAGE,
                                             'damage':damage}})

class CharacterSwitchEvent(GameEvent):
    def __init__(self, old_character, new_character, frame, before=True, **kwargs):
        if before:
            super().__init__(EventType.BEFORE_CHARACTER_SWITCH, frame=frame, old_character=old_character, new_character=new_character, **kwargs)
        else:
            super().__init__(EventType.AFTER_CHARACTER_SWITCH, frame=frame, old_character=old_character, new_character=new_character, **kwargs)
            send_to_handler(frame, 
                            {'event':{'type':EventType.AFTER_CHARACTER_SWITCH,
                                     'old_character':old_character,
                                     'new_character':new_character}})

class NightSoulBlessingEvent(GameEvent):
    def __init__(self, character, frame, before=True, **kwargs):
        if before:
            super().__init__(EventType.BEFORE_NIGHTSOUL_BLESSING, frame=frame, character=character, **kwargs)
        else:
            super().__init__(EventType.AFTER_NIGHTSOUL_BLESSING, frame=frame, character=character, **kwargs)
            send_to_handler(frame, {'event':{'type':EventType.AFTER_NIGHTSOUL_BLESSING,
                                             'character':character}})

class NormalAttackEvent(GameEvent):
    def __init__(self, character, frame, segment, before=True, **kwargs):
        if before:
            super().__init__(EventType.BEFORE_NORMAL_ATTACK, frame=frame, segment=segment, character=character, **kwargs)
        else:
            super().__init__(EventType.AFTER_NORMAL_ATTACK, frame=frame, segment=segment, character=character, **kwargs)
            send_to_handler(frame, {'event':{'type':EventType.AFTER_NORMAL_ATTACK,
                                             'character':character,
                                             'segment':segment}})

class ChargedAttackEvent(GameEvent):
    def __init__(self, character, frame, before=True, **kwargs):
        if before:
            super().__init__(EventType.BEFORE_CHARGED_ATTACK, frame=frame, character=character, **kwargs)
        else:
            super().__init__(EventType.AFTER_CHARGED_ATTACK, frame=frame, character=character, **kwargs)
            send_to_handler(frame, {'event':{'type':EventType.AFTER_CHARGED_ATTACK,
                                             'character':character}})

class PlungingAttackEvent(GameEvent):
    def __init__(self, character, frame, is_plunging_impact=True, before=True, **kwargs):
        if before:
            super().__init__(EventType.BEFORE_PLUNGING_ATTACK, is_plunging_impact=is_plunging_impact, frame=frame, character=character, **kwargs)
        else:
            super().__init__(EventType.AFTER_PLUNGING_ATTACK, is_plunging_impact=is_plunging_impact, frame=frame, character=character, **kwargs)
            send_to_handler(frame, {'event':{'type':EventType.AFTER_PLUNGING_ATTACK,
                                            'character':character,
                                            'is_plunging_impact':is_plunging_impact
                                             }})

class NightSoulChangeEvent(GameEvent):
    def __init__(self, character, amount, frame, before=True, **kwargs):
        if before:
            super().__init__(EventType.BEFORE_NIGHT_SOUL_CHANGE, frame=frame, character=character, amount=amount, **kwargs)
        else:
            super().__init__(EventType.AFTER_NIGHT_SOUL_CHANGE, frame=frame, character=character, amount=amount, **kwargs)
            send_to_handler(frame, {'event':{'type':EventType.AFTER_NIGHT_SOUL_CHANGE, 
                                     'character':character,
                                     'amount':amount}}) 

class ElementalBurstEvent(GameEvent):
    def __init__(self, character, frame, before=True, **kwargs):
        if before:
            super().__init__(EventType.BEFORE_BURST, frame=frame, character=character, **kwargs)
        else:
            super().__init__(EventType.AFTER_BURST, frame=frame, character=character, **kwargs)
            send_to_handler(frame, {'event':{'type':EventType.AFTER_BURST,
                                     'character':character}})

class ElementalSkillEvent(GameEvent):
    def __init__(self, character, frame, before=True, **kwargs):
        if before:
            super().__init__(EventType.BEFORE_SKILL, frame=frame, character=character, **kwargs)
        else:
            super().__init__(EventType.AFTER_SKILL, frame=frame, character=character, **kwargs)
            send_to_handler(frame, {'event':{'type':EventType.AFTER_SKILL,
                                     'character':character}})

class HealChargeEvent(GameEvent):
    def __init__(self, character, amount, frame, before=True, **kwargs):
        if before:
            super().__init__(EventType.BEFORE_HEALTH_CHANGE, frame=frame, character=character, amount=amount, **kwargs)
        else:
            super().__init__(EventType.AFTER_HEALTH_CHANGE, frame=frame, character=character, amount=amount, **kwargs)
            send_to_handler(frame, {'event':{'type':EventType.AFTER_HEALTH_CHANGE, 
                                     'character':character,
                                     'amount':amount}})

class ElementalReactionEvent(GameEvent):
    def __init__(self,elementalReaction, frame, before=True, **kwargs):
        if before:
            super().__init__(EventType.BEFORE_ELEMENTAL_REACTION, frame=frame, elementalReaction=elementalReaction, **kwargs)
        else:
            super().__init__(EventType.AFTER_ELEMENTAL_REACTION, frame=frame, elementalReaction=elementalReaction, **kwargs)
            send_to_handler(frame, {'event':{'type':EventType.AFTER_ELEMENTAL_REACTION,
                                     'elementalReaction':elementalReaction}})

class HealEvent(GameEvent):
    def __init__(self, source, target, healing, frame, before=True, **kwargs):
        if before:
            healing.set_source(source)
            healing.set_target(target)
            super().__init__(EventType.BEFORE_HEAL, frame=frame, character=source, target=target, healing=healing, **kwargs)
        else:
            super().__init__(EventType.AFTER_HEAL, frame=frame, character=source, target=target, healing=healing, **kwargs)
            send_to_handler(frame, {'event':{'type':EventType.AFTER_HEAL,
                                             'healing':healing,}})

class HurtEvent(GameEvent):
    def __init__(self, source, target, amount, frame, before=True, **kwargs):
        if before:
            super().__init__(EventType.BEFORE_HURT, frame=frame, character=source, target=target, amount=amount, **kwargs)
        else:
            super().__init__(EventType.AFTER_HURT, frame=frame, character=source, target=target, amount=amount, **kwargs)
            send_to_handler(frame, {'event':{'type':EventType.AFTER_HURT,
                                             'character':source,
                                             'target':target,
                                             'amount':amount,}})

class ShieldEvent(GameEvent):
    def __init__(self, source, shield, frame, before=True, **kwargs):
        if before:
            super().__init__(EventType.BEFORE_SHIELD_CREATION, frame=frame, character=source, shield=shield, **kwargs)
        else:
            super().__init__(EventType.AFTER_SHIELD_CREATION, frame=frame, character=source, shield=shield, **kwargs)
            send_to_handler(frame, {'event':{'type':EventType.BEFORE_SHIELD_CREATION,
                                             'character':source,
                                             'shield':shield,}})

class EnergyChargeEvent(GameEvent):
    def __init__(self, character, amount, frame, is_fixed=False, is_alone=False,before=True, **kwargs):
        if before:
            super().__init__(EventType.BEFORE_ENERGY_CHANGE, frame=frame, character=character, is_alone=is_alone,amount=amount, is_fixed=is_fixed, **kwargs)
        else:
            super().__init__(EventType.AFTER_ENERGY_CHANGE, frame=frame, character=character, is_alone=is_alone, amount=amount, is_fixed=is_fixed, **kwargs)
            send_to_handler(frame, {'event':{'type':EventType.AFTER_ENERGY_CHANGE,
                                     'character':character,
                                     'amount':amount,
                                     'is_fixed':is_fixed,
                                     'is_alone':is_alone}})
# --------------------------
# 事件处理器接口
# --------------------------
class EventHandler(ABC):
    @abstractmethod
    def handle_event(self, event: GameEvent):
        pass

# --------------------------
# 事件总线（单例）
# --------------------------
class EventBus:
    _instance = None
    _handlers: Dict[EventType, List[EventHandler]] = {}

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def subscribe(cls, event_type: EventType, handler: EventHandler):
        if event_type not in cls._handlers:
            cls._handlers[event_type] = []
        cls._handlers[event_type].append(handler)

    @classmethod
    def unsubscribe(cls, event_type: EventType, handler: EventHandler):
        if event_type in cls._handlers:
            cls._handlers[event_type].remove(handler)
            if not cls._handlers[event_type]:
                del cls._handlers[event_type]

    @classmethod
    def publish(cls, event: GameEvent):
        if event.event_type in cls._handlers:
            for handler in cls._handlers[event.event_type]:
                if event.cancelled:
                    break
                handler.handle_event(event)

    @classmethod
    def clear(cls):
        cls._handlers.clear()
