from typing import Dict, Any, List, Optional
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
from core.mechanics.aura import Element

# ---------------------------------------------------------
# Damage Context (State Container)
# ---------------------------------------------------------
class DamageContext:
    def __init__(self, damage: Damage, source: Any, target: Optional[Any] = None):
        self.damage = damage
        self.source = source
        self.target = target # 这里的 target 可能在广播前为 None
        
        self.stats: Dict[str, float] = {
            "攻击力": 0.0, "生命值": 0.0, "防御力": 0.0, "元素精通": 0.0,
            "固定伤害值加成": 0.0, "伤害加成": 0.0, "暴击率": 0.0, "暴击伤害": 0.0,
            "防御区系数": 1.0, "抗性区系数": 1.0, "反应基础倍率": 1.0,
            "反应加成系数": 0.0, "独立乘区系数": 1.0,
        }
        self.final_result: float = 0.0
        self.is_crit: bool = False

    def add_modifier(self, stat_name: str, value: float):
        if stat_name in self.stats: self.stats[stat_name] += value

# ---------------------------------------------------------
# Damage Pipeline (Logic Processor)
# ---------------------------------------------------------
class DamagePipeline:
    def __init__(self, engine: EventEngine):
        self.engine = engine

    def run(self, ctx: DamageContext):
        """
        核心重构：将 Pipeline 分为“广播前”和“广播后”两阶段。
        """
        # 阶段 A：广播前 (计算面板、处理附魔)
        self._handle_infusion(ctx)
        self._snapshot(ctx)
        
        # 发布计算前事件 (供各种 Buff 监听并修改面板)
        self.engine.publish(GameEvent(EventType.BEFORE_CALCULATE, GetCurrentTime(), 
                                      source=ctx.source, data={"damage_context": ctx}))
        
        # 阶段 B：广播派发 (确定受击者，触发反应逻辑)
        # 获取 CombatSpace 并广播。注意：广播过程中会调用 Target.handle_damage
        from core.context import get_context
        ctx.ctx = get_context()
        ctx.ctx.space.broadcast_damage(ctx.source, ctx.damage)
        
        # 此时 ctx.damage 已经通过广播找到了 target 并触发了反应 (存于 damage.data['reaction_results'])
        # 如果没有击中任何目标，且不是环境伤害，则提前终止
        if not ctx.damage.target:
            return

        # 更新上下文中的 target 引用
        ctx.target = ctx.damage.target
        
        # 阶段 C：广播后 (根据特定目标的抗性/防御计算最终数值)
        self._preprocess_reaction_stats(ctx)
        self._calculate_def_res(ctx)
        self._calculate(ctx)
        
        # 同步最终结果
        ctx.damage.damage = ctx.final_result

    def _handle_infusion(self, ctx: DamageContext):
        dmg = ctx.damage
        if dmg.damage_type not in [DamageType.NORMAL, DamageType.CHARGED, DamageType.PLUNGING]: return
        infusions = [e for e in ctx.source.active_effects if isinstance(e, ElementalInfusionEffect)]
        if not infusions or dmg.data.get('不可覆盖', False): return
        
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
        el_val = ctx.damage.element[0].value
        s["伤害加成"] = AttributeCalculator.get_damage_bonus(src, el_val) * 100

    def _preprocess_reaction_stats(self, ctx: DamageContext):
        """处理广播后由实体产生的反应结果"""
        results = ctx.damage.data.get('reaction_results', [])
        from core.action.reaction import ReactionCategory, ElementalReactionType
        for res in results:
            if res.category == ReactionCategory.AMPLIFYING:
                ctx.stats["反应基础倍率"] = res.multiplier
                em = ctx.stats["元素精通"]
                ctx.stats["反应加成系数"] += (2.78 * em) / (em + 1400)
            elif res.reaction_type in [ElementalReactionType.AGGRAVATE, ElementalReactionType.SPREAD]:
                from core.tool import get_reaction_multiplier
                mult = 1.15 if res.reaction_type == ElementalReactionType.AGGRAVATE else 1.25
                level_coeff = get_reaction_multiplier(ctx.source.level)
                em = ctx.stats["元素精通"]
                ctx.stats["固定伤害值加成"] += level_coeff * mult * (1 + (5 * em) / (em + 1200))

    def _calculate_def_res(self, ctx: DamageContext):
        target_def = ctx.target.defense
        attacker_lv = ctx.source.level
        ctx.stats["防御区系数"] = (5 * attacker_lv + 500) / (target_def + 5 * attacker_lv + 500)
        el_val = ctx.damage.element[0].value
        res = ctx.target.current_resistance.get(el_val, 10.0)
        if res > 75: ctx.stats["抗性区系数"] = 1 / (1 + 4 * res / 100)
        elif res < 0: ctx.stats["抗性区系数"] = 1 - res / 2 / 100
        else: ctx.stats["抗性区系数"] = 1 - res / 100

    def _calculate(self, ctx: DamageContext):
        s = ctx.stats
        if ctx.damage.damage_type == DamageType.REACTION:
            em_inc = (16 * s["元素精通"]) / (s["元素精通"] + 2000)
            level_coeff = ctx.damage.data.get('等级系数', 0)
            react_base = ctx.damage.data.get('反应系数', 1.0)
            bonus = ctx.damage.data.get('反应伤害提高', 0) 
            ctx.final_result = level_coeff * react_base * (1 + em_inc + bonus) * s["抗性区系数"]
            return

        base = self._get_base_value(ctx) + s["固定伤害值加成"]
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
            char, target, dmg = event.data['character'], event.data.get('target'), event.data['damage']
            # 注意：新架构下，target 可能是可选的，由 Pipeline 内广播确定
            ctx = DamageContext(dmg, char, target)
            self.pipeline.run(ctx)
            
            # 广播后，如果 dmg.target 已确定，则进行日志记录和事件发布
            if dmg.target:
                get_emulation_logger().log_damage(char, dmg.target, dmg)
                self.engine.publish(DamageEvent(EventType.AFTER_DAMAGE, event.frame, source=char, target=dmg.target, damage=dmg))
            
            try:
                if self.context.team:
                    for d in [o for o in self.context.team.active_objects if isinstance(o, DendroCoreObject)]:
                        d.apply_element(dmg)
            except Exception: pass
