from typing import Any
from core.base_entity import BaseEntity
from core.event import DamageEvent, HealEvent, HurtEvent, EventType, EventHandler
from core.tool import GetCurrentTime, summon_energy
from core.action.damage import Damage, DamageType
from core.action.healing import Healing, HealingType
from core.team import Team

class SalonMember(BaseEntity, EventHandler):
    """沙龙成员基类"""
    last_energy_time = -9999

    def __init__(self, name: str, character: Any, life_frame: int):
        super().__init__(name, life_frame)
        self.character = character
        self.hp_consumption = 0 # 消耗生命值百分比
        self.attack_interval = 60
        self.last_attack_time = 0
        self.damage_multiplier_list = []

    def apply(self):
        super().apply()
        # 订阅独立伤害加成事件 (芙宁娜特色：消耗全队血量换取增伤)
        self.event_engine.subscribe(EventType.BEFORE_INDEPENDENT_DAMAGE, self)

    def on_finish(self, target: Any):
        super().on_finish(target)
        self.event_engine.unsubscribe(EventType.BEFORE_INDEPENDENT_DAMAGE, self)

    def on_frame_update(self, target: Any):
        if self.current_frame - self.last_attack_time >= self.attack_interval:
            self.last_attack_time = self.current_frame
            self._trigger_attack(target)

    def _trigger_attack(self, target: Any):
        # 1. 创建基础伤害
        multiplier = self.damage_multiplier_list[self.character.Skill.lv - 1]
        damage = Damage(
            damage_multiplier=multiplier,
            element=('水', 1),
            damage_type=DamageType.SKILL,
            name=self.name
        )
        damage.setBaseValue('生命值') # 基于生命值上限
        
        # 2. 发布伤害 (触发 BEFORE_INDEPENDENT_DAMAGE 钩子)
        self.event_engine.publish(DamageEvent(self.character, target, damage, GetCurrentTime()))
        
        # 3. 尝试产球
        self._summon_energy()

    def _summon_energy(self):
        now = GetCurrentTime()
        if now - SalonMember.last_energy_time >= 2.5 * 60:
            summon_energy(1, self.character, ('水', 2))
            SalonMember.last_energy_time = now

    def handle_event(self, event: Any):
        """处理独立增伤逻辑"""
        if event.source == self.character and event.data['damage'].name == self.name:
            # 消耗生命值并统计人数
            count = 0
            for c in Team.team:
                if c.current_hp / c.max_hp > 0.5:
                    # 发布 HurtEvent (扣除全队血量)
                    consumption = self.hp_consumption * c.max_hp / 100
                    self.event_engine.publish(HurtEvent(self.character, c, consumption, GetCurrentTime()))
                    count += 1
            
            # 独立增伤比例：100/110/120/130/140%
            boost = [100, 110, 120, 130, 140][count]
            event.data['damage'].setPanel('独立伤害加成', boost)

class Usher(SalonMember):
    """乌瑟勋爵 (章鱼)"""
    def __init__(self, character, life_frame):
        super().__init__("乌瑟勋爵", character, life_frame)
        self.damage_multiplier_list = [5.96, 6.41, 6.85, 7.45, 7.9, 8.34, 8.94, 9.54, 10.13, 10.73, 11.32, 11.92, 12.67, 13.41, 14.16]
        self.hp_consumption = 2.4
        self.attack_interval = 200
        self.last_attack_time = -self.attack_interval + 72

class Chevalmarin(SalonMember):
    """海薇玛夫人 (海马)"""
    def __init__(self, character, life_frame):
        super().__init__("海薇玛夫人", character, life_frame)
        self.damage_multiplier_list = [3.23, 3.47, 3.72, 4.04, 4.28, 4.52, 4.85, 5.17, 5.49, 5.82, 6.14, 6.46, 6.87, 7.27, 7.68]
        self.hp_consumption = 1.6
        self.attack_interval = 97
        self.last_attack_time = -self.attack_interval + 72

class Crabaletta(SalonMember):
    """谢贝蕾妲小姐 (重甲蟹)"""
    def __init__(self, character, life_frame):
        super().__init__("谢贝蕾妲小姐", character, life_frame)
        self.damage_multiplier_list = [8.29, 8.91, 9.53, 10.36, 10.98, 11.6, 12.43, 13.26, 14.09, 14.92, 15.75, 16.58, 17.61, 18.65, 19.68]
        self.hp_consumption = 3.6
        self.attack_interval = 314
        self.last_attack_time = -self.attack_interval + 30

class Singer(BaseEntity):
    """众水的歌者 (治疗)"""
    def __init__(self, character, life_frame):
        super().__init__("众水的歌者", life_frame)
        self.character = character
        self.heal_interval = 124
        self.last_heal_time = -37
        self.multipliers = [(4.8, 462.23), (5.16, 508.45), (5.52, 558.54), (6, 612.47), (6.36, 670.26), 
                           (6.72, 731.89), (7.2, 797.39), (7.68, 866.73), (8.16, 939.92), (8.64, 1016.97), 
                           (9.12, 1097.87), (9.6, 1182.63), (10.2, 1271.23), (10.8, 1363.69), (11.4, 1460)]

    def apply(self):
        super().apply()
        # 天赋2：基于生命值上限缩短治疗间隔 (最多缩短16%)
        if self.character.level > 60:
            reduction = min((self.character.max_hp // 1000) * 0.004, 0.16)
            self.heal_interval *= (1 - reduction)

    def on_frame_update(self, target: Any):
        if self.current_frame - self.last_heal_time >= self.heal_interval:
            self.last_heal_time = self.current_frame
            heal = Healing(
                base_multiplier=self.multipliers[self.character.Skill.lv - 1],
                healing_type=HealingType.SKILL,
                name=self.name
            )
            heal.base_value = '生命值'
            self.event_engine.publish(HealEvent(self.character, Team.current_character, heal, GetCurrentTime()))