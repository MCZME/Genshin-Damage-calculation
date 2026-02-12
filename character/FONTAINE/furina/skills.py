from typing import Any
from core.skills.base import SkillBase, EnergySkill
from core.skills.common import ChargedAttackSkill
from core.action.damage import Damage, DamageType
from core.action.action_data import ActionFrameData
from core.event import EventHandler, EventType, GameEvent, DamageEvent
from core.tool import GetCurrentTime
from core.team import Team
from character.FONTAINE.furina.entities import Usher, Chevalmarin, Crabaletta, Singer
from character.FONTAINE.furina.talents import UniversalExaltationEffect

class SalonSolitaire(SkillBase):
    """孤心沙龙 (E技能)"""
    def __init__(self, lv: int):
        super().__init__("孤心沙龙", 56, 20*60, lv, ('水', 1))
        self.hit_frame = 18
        self.damage_multipliers = [7.86, 8.45, 9.04, 9.83, 10.42, 11.01, 11.8, 12.58, 13.37, 14.16, 14.94, 15.73, 16.71, 17.69, 18.68]

    def to_action_data(self) -> ActionFrameData:
        data = ActionFrameData(name="elemental_skill", total_frames=self.total_frames, hit_frames=[self.hit_frame])
        setattr(data, "runtime_skill_obj", self)
        return data

    def on_execute_hit(self, target: Any, hit_index: int):
        # 1. 造成瞬间伤害
        multiplier = self.damage_multipliers[self.lv - 1]
        damage = Damage(multiplier, ('水', 1), DamageType.SKILL, self.name)
        damage.set_scaling_stat('生命值')
        self.caster.event_engine.publish(DamageEvent(self.caster, target, damage, get_current_time()))

        # 2. 召唤实体 (根据当前荒芒性)
        if self.caster.arkhe == '芒性':
            Singer(self.caster, 30*60).apply()
        else:
            Usher(self.caster, 30*60).apply()
            Chevalmarin(self.caster, 30*60).apply()
            Crabaletta(self.caster, 30*60).apply()

class UniversalRevelry(EnergySkill, EventHandler):
    """万众狂欢 (Q技能)"""
    def __init__(self, lv: int):
        super().__init__("万众狂欢", 113, 15*60, lv, ('水', 1))
        self.hit_frame = 98
        self.damage_multipliers = [11.41, 12.26, 13.12, 14.26, 15.11, 15.97, 17.11, 18.25, 19.39, 20.53, 21.67, 22.81, 24.24, 25.66, 27.09]
        
        # 气氛值状态
        self.fanfare_points = 0
        self.fanfare_max = 300
        self.fanfare_initial = 0
        self.fanfare_gain_ratio = 1.0 # 2命会修改此值

    def to_action_data(self) -> ActionFrameData:
        data = ActionFrameData(name="elemental_burst", total_frames=self.total_frames, hit_frames=[self.hit_frame])
        setattr(data, "runtime_skill_obj", self)
        return data

    def on_execute_hit(self, target: Any, hit_index: int):
        # 1. 初始爆发伤害
        mult = self.damage_multipliers[self.lv - 1]
        damage = Damage(mult, ('水', 1), DamageType.BURST, self.name)
        damage.set_scaling_stat('生命值')
        self.caster.event_engine.publish(DamageEvent(self.caster, target, damage, get_current_time()))

        # 2. 开启气氛值收集
        self.fanfare_points = self.fanfare_initial
        self.caster.event_engine.subscribe(EventType.AFTER_HEALTH_CHANGE, self)
        
        # 3. 应用全队增益效果
        for member in Team.team:
            UniversalExaltationEffect(member, self.caster, self).apply()

    def handle_event(self, event: GameEvent):
        """气氛值增加逻辑"""
        if event.event_type == EventType.AFTER_HEALTH_CHANGE:
            # 变化百分比 (1% = 1点)
            change_pct = abs(event.amount) / event.source.max_hp * 100
            self.fanfare_points = min(self.fanfare_max, self.fanfare_points + change_pct * self.fanfare_gain_ratio)

    def reset_fanfare(self):
        self.fanfare_points = 0
        self.caster.event_engine.unsubscribe(EventType.AFTER_HEALTH_CHANGE, self)

class FurinaChargedAttack(ChargedAttackSkill):
    """芙宁娜重击：切换始基力"""
    def __init__(self, lv: int):
        super().__init__(lv, total_frames=47)
        self.hit_frame = 32
        self.damage_multiplier_list = [74.22, 80.26, 86.3, 94.93, 100.97, 107.88, 117.37, 126.86, 136.35, 146.71, 157.07, 167.42, 177.78, 188.13, 198.49]

    def on_execute_hit(self, target: Any, hit_index: int):
        # 1. 物理伤害
        mult = self.damage_multiplier_list[self.lv - 1]
        damage = Damage(mult, ('物理', 0), DamageType.CHARGED, "重击")
        self.caster.event_engine.publish(DamageEvent(self.caster, target, damage, get_current_time()))

        # 2. 切换始基力
        old_arkhe = self.caster.arkhe
        self.caster.arkhe = '芒性' if old_arkhe == '荒性' else '荒性'
        
        # 3. 继承召唤物时间并替换
        self._replace_summons()

    def _replace_summons(self):
        summons = [obj for obj in Team.active_objects if isinstance(obj, (Usher, Chevalmarin, Crabaletta, Singer))]
        if not summons: return
        
        # 继承剩余时间
        remaining = summons[0].life_frame - summons[0].current_frame
        for s in summons: s.remove() # 移除旧的
        
        # 创建新的
        if self.caster.arkhe == '芒性':
            Singer(self.caster, remaining).apply()
        else:
            Usher(self.caster, remaining).apply()
            Chevalmarin(self.caster, remaining).apply()
            Crabaletta(self.caster, remaining).apply()
