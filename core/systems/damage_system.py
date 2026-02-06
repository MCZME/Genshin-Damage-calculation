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
            "base_atk": 0.0,
            "base_hp": 0.0,
            "base_def": 0.0,
            "base_em": 0.0,
            "flat_damage_bonus": 0.0,
            "damage_bonus": 0.0,
            "crit_rate": 0.0,
            "crit_dmg": 0.0,
            "def_mult": 1.0,
            "res_mult": 1.0,
            "reaction_mult": 1.0,
            "reaction_bonus": 0.0,
            "independent_mult": 1.0,
        }
        self.final_result: float = 0.0
        self.is_crit: bool = False

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
        # 2. 基础属性快照
        self._snapshot(ctx)
        # 3. 反应机制预处理
        self._preprocess_reaction(ctx)
        # 4. 外部修正 (兼容旧事件)
        self._apply_external_modifiers(ctx)
        # 5. 核心计算
        self._calculate(ctx)
        # 6. 同步结果
        ctx.damage.damage = ctx.final_result

    def _handle_infusion(self, ctx: DamageContext):
        """处理近战元素附魔逻辑"""
        dmg = ctx.damage
        if dmg.damage_type not in [DamageType.NORMAL, DamageType.CHARGED, DamageType.PLUNGING]:
            return
            
        infusions = [e for e in ctx.source.active_effects if isinstance(e, ElementalInfusionEffect)]
        if not infusions or dmg.data.get('不可覆盖', False):
            return
            
        # 寻找不可覆盖的附魔
        unoverridable = next((e for e in infusions if e.is_unoverridable), None)
        if unoverridable:
            dmg.element = (unoverridable.element_type, unoverridable.should_apply_infusion(dmg.damage_type))
            return
            
        # 元素优先级逻辑 (水 > 火 > 冰)
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
        s["base_atk"] = AttributeCalculator.get_attack(src)
        s["base_hp"] = AttributeCalculator.get_hp(src)
        s["base_def"] = AttributeCalculator.get_defense(src)
        s["base_em"] = AttributeCalculator.get_mastery(src)
        s["crit_rate"] = AttributeCalculator.get_crit_rate(src) * 100
        s["crit_dmg"] = AttributeCalculator.get_crit_damage(src) * 100
        s["damage_bonus"] = AttributeCalculator.get_damage_bonus(src, ctx.damage.element[0]) * 100

    def _preprocess_reaction(self, ctx: DamageContext):
        if ctx.damage.element[0] == '物理': return
        
        mult = ctx.target.apply_elemental_aura(ctx.damage)
        if mult:
            ctx.stats["reaction_mult"] = mult
            em = ctx.stats["base_em"]
            # 基础精通加成
            if ctx.damage.reaction_type and ctx.damage.reaction_type[0] != '激化反应':
                ctx.stats["reaction_bonus"] += (2.78 * em) / (em + 1400)
            # 激化特殊处理
            elif ctx.damage.reaction_type and ctx.damage.reaction_type[0] == '激化反应':
                level_coeff = ctx.damage.panel.get('等级系数', 0)
                ctx.stats["flat_damage_bonus"] += level_coeff * mult * (1 + (5 * em) / (em + 1200))

    def _apply_external_modifiers(self, ctx: DamageContext):
        """发布事件让外部系统（如圣遗物）修改 Context"""
        # [暂时兼容] 发布旧事件，因为旧系统修改的是 damage.panel
        self.engine.publish(GameEvent(EventType.BEFORE_DAMAGE_BONUS, GetCurrentTime(),
                                      character=ctx.source, target=ctx.target, damage=ctx.damage))
        self.engine.publish(GameEvent(EventType.BEFORE_CRITICAL, GetCurrentTime(),
                                      character=ctx.source, target=ctx.target, damage=ctx.damage))
        self.engine.publish(GameEvent(EventType.BEFORE_INDEPENDENT_DAMAGE, GetCurrentTime(),
                                      character=ctx.source, target=ctx.target, damage=ctx.damage))
        
        # 将 damage.panel 的变更同步进 stats (仅为过渡)
        ctx.stats["damage_bonus"] += ctx.damage.panel.get('伤害加成', 0)
        ctx.stats["crit_rate"] += ctx.damage.panel.get('暴击率', 0)
        ctx.stats["crit_dmg"] += ctx.damage.panel.get('暴击伤害', 0)
        ctx.stats["flat_damage_bonus"] += ctx.damage.panel.get('固定伤害基础值加成', 0)
        if '独立伤害加成' in ctx.damage.panel:
            ctx.stats["independent_mult"] *= (1 + ctx.damage.panel['独立伤害加成'] / 100)

        # 计算防御与抗性乘区
        self._calculate_def_res(ctx)

    def _calculate_def_res(self, ctx: DamageContext):
        # 防御
        target_def = ctx.target.defense
        attacker_lv = ctx.source.level
        ctx.stats["def_mult"] = (5 * attacker_lv + 500) / (target_def + 5 * attacker_lv + 500)
        # 抗性
        res = ctx.target.current_resistance.get(ctx.damage.element[0], 10.0)
        if res > 75: ctx.stats["res_mult"] = 1 / (1 + 4 * res / 100)
        elif res < 0: ctx.stats["res_mult"] = 1 - res / 2 / 100
        else: ctx.stats["res_mult"] = 1 - res / 100

    def _calculate(self, ctx: DamageContext):
        s = ctx.stats
        # 剧变反应逻辑
        if ctx.damage.damage_type == DamageType.REACTION:
            em_inc = (16 * s["base_em"]) / (s["base_em"] + 2000)
            bonus = ctx.damage.panel.get('反应伤害提高', 0) # 兼容
            ctx.final_result = ctx.damage.panel.get('等级系数', 0) * ctx.damage.panel.get('反应系数', 1.0) * (1 + em_inc + bonus) * s["res_mult"]
            return

        # 基础伤害
        base = self._get_base_value(ctx) + s["flat_damage_bonus"]
        # 乘区组合
        bonus_mult = 1 + s["damage_bonus"] / 100
        crit_mult = self._get_crit_mult(ctx)
        react_mult = 1.0
        if s["reaction_mult"] > 1.0:
            react_mult = s["reaction_mult"] * (1 + s["reaction_bonus"])
        
        ctx.final_result = base * bonus_mult * crit_mult * react_mult * s["def_mult"] * s["res_mult"] * s["independent_mult"]

    def _get_base_value(self, ctx: DamageContext) -> float:
        d = ctx.damage
        if isinstance(d.base_value, tuple):
            v1 = getattr(ctx.stats, f"base_{d.base_value[0][:2].lower()}", 0) # 简写映射
            # 还是用 mapping 稳妥
            mapping = {'攻击力': 'base_atk', '生命值': 'base_hp', '防御力': 'base_def', '元素精通': 'base_em'}
            val1 = ctx.stats.get(mapping.get(d.base_value[0]), 0)
            val2 = ctx.stats.get(mapping.get(d.base_value[1]), 0)
            return val1 * (d.damage_multiplier[0] / 100) + val2 * (d.damage_multiplier[1] / 100)
        
        mapping = {'攻击力': 'base_atk', '生命值': 'base_hp', '防御力': 'base_def', '元素精通': 'base_em'}
        attr_val = ctx.stats.get(mapping.get(d.base_value), 0)
        return attr_val * (d.damage_multiplier / 100)

    def _get_crit_mult(self, ctx: DamageContext) -> float:
        if Config.get('emulation.open_critical'):
            if random.uniform(0, 100) <= ctx.stats["crit_rate"]:
                ctx.is_crit = True
                return 1 + ctx.stats["crit_dmg"] / 100
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
            
            # 草原核触发 (TODO: 建议移出伤害系统)
            try:
                if self.context.team:
                    for d in [o for o in self.context.team.active_objects if isinstance(o, DendroCoreObject)]:
                        d.apply_element(dmg)
            except Exception: pass
