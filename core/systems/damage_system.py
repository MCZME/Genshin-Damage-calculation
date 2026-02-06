from typing import List, Optional, Dict, Any, Tuple
import random

from core.systems.utils import AttributeCalculator
from core.systems.base_system import GameSystem
from core.context import EventEngine
from core.event import GameEvent, DamageEvent, EventType
from core.action.damage import Damage, DamageType
from core.config import Config
from core.logger import get_emulation_logger
from core.entities.elemental_entities import DendroCoreObject
from core.effect.elemental import ElementalInfusionEffect
from core.tool import GetCurrentTime

# ---------------------------------------------------------
# Damage Context (State Container)
# ---------------------------------------------------------
class DamageContext:
    """
    伤害计算上下文。
    持有单次伤害计算过程中的所有状态。
    """
    def __init__(self, damage: Damage, source: Any, target: Any):
        self.damage = damage
        self.source = source
        self.target = target
        
        # 结构化乘区容器 (唯一真理来源)
        self.stats: Dict[str, float] = {
            "攻击力": 0.0,
            "生命值": 0.0,
            "防御力": 0.0,
            "元素精通": 0.0,
            "固定伤害值加成": 0.0,
            "伤害加成": 0.0,
            "暴击率": 0.0,
            "暴击伤害": 0.0,
            "防御区系数": 1.0,
            "抗性区系数": 1.0,
            "反应基础倍率": 1.0,
            "反应加成系数": 0.0,
            "独立乘区系数": 1.0,
        }
        
        # 预载入：从 Damage DTO 提取初始注入的数据 (例如反应系统注入的等级系数)
        self._initialize_from_data()
        
        self.final_result: float = 0.0
        self.is_crit: bool = False

    def _initialize_from_data(self):
        """从 damage.data 中提取初始参数（如等级系数、反应系数等）"""
        d = self.damage.data
        if '等级系数' in d:
            # 剧变反应的基础值直接存入固定伤害加成（如果是剧变模式）
            pass 
        # 这里可以根据需要扩展

    def add_modifier(self, stat_name: str, value: float):
        if stat_name in self.stats:
            self.stats[stat_name] += value

# ---------------------------------------------------------
# Damage Pipeline (Logic Processor)
# ---------------------------------------------------------
class DamagePipeline:
    def __init__(self, engine: EventEngine):
        self.engine = engine

    def run(self, ctx: DamageContext):
        # 1. 元素附魔预处理
        self._handle_infusion(ctx)
        
        # 2. 基础属性快照 (面板属性)
        self._snapshot(ctx)
        
        # 3. 反应机制预处理 (附着消减与基础倍率)
        self._preprocess_reaction(ctx)
        
        # 4. 发布统一的计算前事件，允许外部系统通过修改 ctx.stats 来注入加成
        self._notify_modifiers(ctx)
        
        # 5. 核心计算
        self._calculate(ctx)
        
        # 6. 同步最终结果到 DTO
        ctx.damage.damage = ctx.final_result

    def _handle_infusion(self, ctx: DamageContext):
        dmg = ctx.damage
        if dmg.damage_type not in [DamageType.NORMAL, DamageType.CHARGED, DamageType.PLUNGING]:
            return
            
        infusions = [e for e in ctx.source.active_effects if isinstance(e, ElementalInfusionEffect)]
        if not infusions or dmg.data.get('不可覆盖', False):
            return
            
        unoverridable = next((e for e in infusions if e.is_unoverridable), None)
        if unoverridable:
            dmg.element = (unoverridable.element_type, unoverridable.should_apply_infusion(dmg.damage_type))
            return
            
        elements = [e.element_type for e in infusions]
        dominant = self._get_dominant_element(elements, infusions)
        dmg.element = (dominant, max(e.should_apply_infusion(dmg.damage_type) for e in infusions))

    def _get_dominant_element(self, elements, infusions):
        for e_type in ['水', '火', '冰']:
            if e_type in elements: return e_type
        return min(elements, key=lambda x: next(e.apply_time for e in infusions if e.element_type == x))

    def _snapshot(self, ctx: DamageContext):
        src = ctx.source
        s = ctx.stats
        s["攻击力"] = AttributeCalculator.get_attack(src)
        s["生命值"] = AttributeCalculator.get_hp(src)
        s["防御力"] = AttributeCalculator.get_defense(src)
        s["元素精通"] = AttributeCalculator.get_mastery(src)
        s["暴击率"] = AttributeCalculator.get_crit_rate(src) * 100
        s["暴击伤害"] = AttributeCalculator.get_crit_damage(src) * 100
        s["伤害加成"] = AttributeCalculator.get_damage_bonus(src, ctx.damage.element[0]) * 100

    def _preprocess_reaction(self, ctx: DamageContext):
        if ctx.damage.element[0] == '物理': return
        
        mult = ctx.target.apply_elemental_aura(ctx.damage)
        if mult:
            ctx.stats["反应基础倍率"] = mult
            em = ctx.stats["元素精通"]
            # 基础精通加成 (增幅反应)
            if ctx.damage.reaction_type and ctx.damage.reaction_type[0] != '激化反应':
                ctx.stats["反应加成系数"] += (2.78 * em) / (em + 1400)
            # 激化特殊处理
            elif ctx.damage.reaction_type and ctx.damage.reaction_type[0] == '激化反应':
                # 直接从 damage.data 获取等级系数
                level_coeff = ctx.damage.data.get('等级系数', 0)
                ctx.stats["固定伤害值加成"] += level_coeff * mult * (1 + (5 * em) / (em + 1200))

    def _notify_modifiers(self, ctx: DamageContext):
        """发布计算前通知，供其他系统修改 context.stats"""
        event = GameEvent(EventType.BEFORE_CALCULATE, GetCurrentTime(), character=ctx.source, damage_context=ctx)
        self.engine.publish(event)
        
        # 计算防御与抗性（在此处计算，以便事件可以修改防御或抗性相关参数，尽管目前是直接计算系数）
        self._calculate_def_res(ctx)

    def _calculate_def_res(self, ctx: DamageContext):
        # 防御区
        target_def = ctx.target.defense
        attacker_lv = ctx.source.level
        ctx.stats["防御区系数"] = (5 * attacker_lv + 500) / (target_def + 5 * attacker_lv + 500)
        
        # 抗性区
        res = ctx.target.current_resistance.get(ctx.damage.element[0], 10.0)
        if res > 75: ctx.stats["抗性区系数"] = 1 / (1 + 4 * res / 100)
        elif res < 0: ctx.stats["抗性区系数"] = 1 - res / 2 / 100
        else: ctx.stats["抗性区系数"] = 1 - res / 100

    def _calculate(self, ctx: DamageContext):
        s = ctx.stats
        # 1. 剧变反应分支
        if ctx.damage.damage_type == DamageType.REACTION:
            em_inc = (16 * s["元素精通"]) / (s["元素精通"] + 2000)
            # 从 data 获取等级系数和反应基础系数
            level_coeff = ctx.damage.data.get('等级系数', 0)
            react_base = ctx.damage.data.get('反应系数', 1.0)
            bonus = ctx.damage.data.get('反应伤害提高', 0) 
            ctx.final_result = level_coeff * react_base * (1 + em_inc + bonus) * s["抗性区系数"]
            return

        # 2. 标准伤害乘区
        # 基础伤害 = (属性 * 倍率) + 固定伤害加成
        base = self._get_base_value(ctx) + s["固定伤害值加成"]
        
        # 乘区合成
        bonus_mult = 1 + s["伤害加成"] / 100
        crit_mult = self._get_crit_mult(ctx)
        
        react_mult = 1.0
        if s["反应基础倍率"] > 1.0:
            react_mult = s["反应基础倍率"] * (1 + s["反应加成系数"])
        
        ctx.final_result = (base * bonus_mult * crit_mult * react_mult * 
                            s["防御区系数"] * s["抗性区系数"] * s["独立乘区系数"])

    def _get_base_value(self, ctx: DamageContext) -> float:
        d = ctx.damage
        if isinstance(d.base_value, tuple):
            val1 = ctx.stats.get(d.base_value[0], 0.0)
            val2 = ctx.stats.get(d.base_value[1], 0.0)
            return val1 * (d.damage_multiplier[0] / 100) + val2 * (d.damage_multiplier[1] / 100)
        
        attr_val = ctx.stats.get(d.base_value, 0.0)
        return attr_val * (d.damage_multiplier / 100)

    def _get_crit_mult(self, ctx: DamageContext) -> float:
        if Config.get('emulation.open_critical'):
            if random.uniform(0, 100) <= ctx.stats["暴击率"]:
                ctx.is_crit = True
                return 1 + ctx.stats["暴击伤害"] / 100
        return 1.0

class DamageSystem(GameSystem):
    def initialize(self, context):
        super().initialize(context)
        self.pipeline = DamagePipeline(self.engine)

    def register_events(self, engine: EventEngine):
        engine.subscribe(EventType.BEFORE_DAMAGE, self)

    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.BEFORE_DAMAGE:
            char, target, dmg = event.data['character'], event.data['target'], event.data['damage']
            ctx = DamageContext(dmg, char, target)
            self.pipeline.run(ctx)
            
            get_emulation_logger().log_damage(char, target, dmg)
            self.engine.publish(DamageEvent(char, target, dmg, event.frame, before=False))
            
            # 草原核逻辑暂存
            try:
                if self.context.team:
                    for d in [o for o in self.context.team.active_objects if isinstance(o, DendroCoreObject)]:
                        d.apply_element(dmg)
            except Exception: pass
