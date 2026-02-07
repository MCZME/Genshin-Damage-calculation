from typing import Dict, Any, List, Optional
import random

from core.systems.utils import AttributeCalculator
from core.systems.base_system import GameSystem
from core.context import EventEngine
from core.event import GameEvent, DamageEvent, EventType
from core.action.damage import Damage, DamageType
from core.action.action_data import AOEShape
from core.config import Config
from core.logger import get_emulation_logger
from core.tool import GetCurrentTime
from core.mechanics.aura import Element
from core.effect.elemental import ElementalInfusionEffect

class DamageContext:
    """伤害计算上下文"""
    def __init__(self, damage: Damage, source: Any, target: Optional[Any] = None):
        self.damage = damage
        self.source = source
        self.target = target
        self.config = damage.config # 快捷访问攻击契约
        
        self.stats: Dict[str, float] = {
            "攻击力": 0.0, "生命值": 0.0, "防御力": 0.0, "元素精通": 0.0,
            "固定伤害值加成": 0.0, "伤害加成": 0.0, "暴击率": 0.0, "暴击伤害": 0.0,
            "防御区系数": 1.0, "抗性区系数": 1.0, "反应基础倍率": 1.0,
            "反应加成系数": 0.0, "独立乘区系数": 1.0,
        }
        self.final_result: float = 0.0
        self.is_crit: bool = False

class DamagePipeline:
    def __init__(self, engine: EventEngine):
        self.engine = engine

    def run(self, ctx: DamageContext):
        # 1. 附魔处理 (仅影响普攻/重击/下落)
        self._handle_infusion(ctx)
        
        # 2. 属性快照 (计算攻击力、精通等)
        self._snapshot(ctx)
        
        # 3. 计算前修正 (供 Buff 监听)
        self.engine.publish(GameEvent(EventType.BEFORE_CALCULATE, GetCurrentTime(), 
                                      source=ctx.source, data={"damage_context": ctx}))
        
        # 4. 空间广播与碰撞判定
        self._dispatch_broadcast(ctx)
        
        # 如果未命中任何目标，终止计算
        if not ctx.damage.target:
            return

        ctx.target = ctx.damage.target
        
        # 5. 元素反应处理 (基于广播阶段反馈的 reaction_results)
        self._preprocess_reaction_stats(ctx)
        
        # 6. 乘区结算
        self._calculate_def_res(ctx)
        self._calculate(ctx)
        
        # 7. 更新最终伤害值
        ctx.damage.damage = ctx.final_result

    def _dispatch_broadcast(self, ctx: DamageContext):
        """对接 CombatSpace 物理引擎"""
        from core.context import get_context
        sim_ctx = get_context()
        if not sim_ctx or not sim_ctx.space:
            return
            
        hb = ctx.config.hitbox
        
        # 根据契约中的 hitbox 配置决定广播方式
        if hb.shape == AOEShape.SINGLE:
            sim_ctx.space.broadcast_damage(ctx.source, ctx.damage)
        else:
            sim_ctx.space.broadcast_damage(
                ctx.source, 
                ctx.damage, 
                shape=hb.shape.name, 
                radius=hb.radius, 
                angle=hb.angle, 
                offset=hb.offset
            )

    def _handle_infusion(self, ctx: DamageContext):
        """处理元素附魔 (基于新架构 Effect 体系)"""
        dmg = ctx.damage
        # 仅对普攻系列生效
        if dmg.damage_type not in [DamageType.NORMAL, DamageType.CHARGED, DamageType.PLUNGING]:
            return
            
        infusions = [e for e in ctx.source.active_effects if isinstance(e, ElementalInfusionEffect)]
        if not infusions or dmg.data.get('不可覆盖', False):
            return
        
        # 优先级逻辑：不可覆盖附魔优先
        unoverridable = next((e for e in infusions if e.is_unoverridable), None)
        if unoverridable:
            dmg.element = (unoverridable.element_type, unoverridable.should_apply_infusion(dmg.damage_type))
            return
        
        # 元素反应优先级 (火 > 冰 > 水) 或 时间先后
        elements = [e.element_type for e in infusions]
        dominant = self._get_dominant_element(elements, infusions)
        dmg.element = (dominant, max(e.should_apply_infusion(dmg.damage_type) for e in infusions))

    def _get_dominant_element(self, elements, infusions):
        for e_type in [Element.HYDRO, Element.PYRO, Element.CRYO]:
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
        
        el = ctx.damage.element[0]
        s["伤害加成"] = AttributeCalculator.get_damage_bonus(src, el.value) * 100

    def _preprocess_reaction_stats(self, ctx: DamageContext):
        """处理广播后由实体产生的反应结果"""
        results = ctx.damage.reaction_results
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
        target_def = ctx.target.attribute_panel.get("防御力", 0)
        attacker_lv = ctx.source.level
        ctx.stats["防御区系数"] = (5 * attacker_lv + 500) / (target_def + 5 * attacker_lv + 500)
        
        el_name = ctx.damage.element[0].name
        res = ctx.target.attribute_panel.get(f"{el_name}元素抗性", 10.0)
        
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
        if isinstance(d.damage_multiplier, list):
            return sum(ctx.stats.get(d.base_value, 0) * (m/100) for m in d.damage_multiplier)
        return ctx.stats.get(d.base_value, 0) * (d.damage_multiplier / 100)

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
            char = event.data['character']
            dmg = event.data['damage']
            ctx = DamageContext(dmg, char)
            self.pipeline.run(ctx)
            
            if dmg.target:
                get_emulation_logger().log_damage(char, dmg.target, dmg)
                self.engine.publish(DamageEvent(EventType.AFTER_DAMAGE, event.frame, source=char, target=dmg.target, damage=dmg))
