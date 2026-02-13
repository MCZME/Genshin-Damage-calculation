from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import random

from core.systems.utils import AttributeCalculator
from core.systems.base_system import GameSystem
from core.context import EventEngine
from core.event import GameEvent, DamageEvent, EventType
from core.action.damage import Damage
from core.config import Config
from core.logger import get_emulation_logger
from core.tool import get_current_time


@dataclass
class ModifierRecord:
    """伤害修幅记录条目。"""
    source: str      # 来源 (如 "芙宁娜-气氛值", "基础攻击力")
    stat: str        # 属性名 (如 "伤害加成")
    value: float     # 数值
    op: str = "ADD"  # 操作: ADD, MULT, SET


class DamageContext:
    """伤害计算上下文 (支持全过程审计)。"""
    def __init__(self, damage: Damage, source: Any, target: Optional[Any] = None):
        self.damage = damage
        self.source = source
        self.target = target
        self.config = damage.config
        
        self.stats: Dict[str, float] = {
            "攻击力": 0.0, "生命值": 0.0, "防御力": 0.0, "元素精通": 0.0,
            "固定伤害值加成": 0.0, "伤害加成": 0.0, "暴击率": 0.0, "暴击伤害": 0.0,
            "防御区系数": 1.0, "抗性区系数": 1.0, "反应基础倍率": 1.0,
            "反应加成系数": 0.0, "独立乘区系数": 1.0,
        }
        self.audit_trail: List[ModifierRecord] = []
        self.final_result: float = 0.0
        self.is_crit: bool = False

    def add_modifier(self, source: str, stat: str, value: float, op: str = "ADD") -> None:
        if stat not in self.stats:
            self.stats[stat] = 0.0 if op == "ADD" else 1.0
        if op == "ADD": self.stats[stat] += value
        elif op == "MULT": self.stats[stat] *= value
        elif op == "SET": self.stats[stat] = value
        self.audit_trail.append(ModifierRecord(source, stat, value, op))


class DamagePipeline:
    def __init__(self, engine: EventEngine):
        self.engine = engine

    def run(self, ctx: DamageContext):
        self._snapshot(ctx)
        
        self.engine.publish(GameEvent(EventType.BEFORE_CALCULATE, get_current_time(), 
                                      source=ctx.source, data={"damage_context": ctx}))
        
        if not ctx.target:
            self._dispatch_broadcast(ctx)
        else:
            ctx.damage.set_target(ctx.target)
            ctx.target.handle_damage(ctx.damage)
        
        if not ctx.damage.target: return
        ctx.target = ctx.damage.target
        
        self._preprocess_reaction_stats(ctx)
        self._calculate_def_res(ctx)
        
        self._calculate(ctx)
        
        ctx.damage.damage = ctx.final_result
        ctx.damage.data["audit_trail"] = ctx.audit_trail

    def _snapshot(self, ctx: DamageContext):
        src = ctx.source
        from core.action.attack_tag_resolver import AttackTagResolver, AttackCategory
        categories = AttackTagResolver.resolve_categories(ctx.config.attack_tag, ctx.config.extra_attack_tags)
        
        # 1. 基础面板注入
        ctx.add_modifier("角色基础面板", "攻击力", AttributeCalculator.get_attack(src), "SET")
        ctx.add_modifier("角色基础面板", "生命值", AttributeCalculator.get_hp(src), "SET")
        ctx.add_modifier("角色基础面板", "防御力", AttributeCalculator.get_defense(src), "SET")
        ctx.add_modifier("角色基础面板", "元素精通", AttributeCalculator.get_mastery(src), "SET")
        
        # 2. 暴击区注入
        ctx.add_modifier("基础暴击", "暴击率", AttributeCalculator.get_crit_rate(src)*100, "SET")
        ctx.add_modifier("基础爆伤", "暴击伤害", AttributeCalculator.get_crit_damage(src)*100, "SET")
        
        # 3. 动态增伤区注入
        bonus = AttributeCalculator.get_damage_bonus(src) # 通用全增伤
        el_name = ctx.damage.element[0]
        if el_name != "无":
            el_bonus_key = f"{el_name}元素伤害加成" if el_name != "物理" else "物理伤害加成"
            bonus += src.attribute_panel.get(el_bonus_key, 0.0) / 100
            
        if AttackCategory.NORMAL in categories: bonus += src.attribute_panel.get("普通攻击伤害加成", 0.0) / 100
        if AttackCategory.CHARGED in categories: bonus += src.attribute_panel.get("重击伤害加成", 0.0) / 100
        if AttackCategory.PLUNGING in categories: bonus += src.attribute_panel.get("下落攻击伤害加成", 0.0) / 100
        if AttackCategory.SKILL in categories: bonus += src.attribute_panel.get("元素战技伤害加成", 0.0) / 100
        if AttackCategory.BURST in categories: bonus += src.attribute_panel.get("元素爆发伤害加成", 0.0) / 100
        
        ctx.add_modifier("总和伤害加成区", "伤害加成", bonus * 100, "SET")

    def _calculate_def_res(self, ctx: DamageContext):
        target_def = ctx.target.attribute_panel.get("防御力", 0)
        coeff_def = (5 * ctx.source.level + 500) / (target_def + 5 * ctx.source.level + 500)
        ctx.add_modifier("防御减免", "防御区系数", coeff_def, "SET")
        
        el_name = ctx.damage.element[0]
        res = ctx.target.attribute_panel.get(f"{el_name}元素抗性", 10.0)
        coeff_res = 1.0
        if res > 75: coeff_res = 1 / (1 + 4 * res / 100)
        elif res < 0: coeff_res = 1 - res / 2 / 100
        else: coeff_res = 1 - res / 100
        ctx.add_modifier(f"{el_name}抗性修正", "抗性区系数", coeff_res, "SET")

    def _calculate(self, ctx: DamageContext):
        s = ctx.stats
        from core.action.attack_tag_resolver import AttackTagResolver, AttackCategory
        categories = AttackTagResolver.resolve_categories(ctx.config.attack_tag, ctx.config.extra_attack_tags)

        # 剧变反应结算
        if AttackCategory.REACTION in categories:
            em_inc = (16 * s["元素精通"]) / (s["元素精通"] + 2000)
            level_coeff = ctx.damage.data.get('等级系数', 0)
            react_base = ctx.damage.data.get('反应系数', 1.0)
            bonus = ctx.damage.data.get('反应伤害提高', 0) 
            ctx.final_result = level_coeff * react_base * (1 + em_inc + bonus) * s["抗性区系数"]
            ctx.audit_trail.append(ModifierRecord("剧变反应基础", "最终伤害", ctx.final_result, "SET"))
            return

        # 基础增伤区合算
        base_val = self._get_base_value(ctx)
        
        bonus_mult = 1 + s["伤害加成"] / 100
        crit_mult = self._get_crit_mult(ctx)
        
        react_mult = 1.0
        if s["反应基础倍率"] > 1.0:
            react_mult = s["反应基础倍率"] * (1 + s["反应加成系数"])
        
        ctx.final_result = (
            (base_val + s["固定伤害值加成"]) * 
            bonus_mult * crit_mult * react_mult * 
            s["防御区系数"] * s["抗性区系数"] * s["独立乘区系数"]
        )

    def _get_base_value(self, ctx: DamageContext) -> float:
        d = ctx.damage
        val = ctx.stats.get(d.scaling_stat, 0)
        multiplier = d.damage_multiplier / 100
        return val * multiplier

    def _get_crit_mult(self, ctx: DamageContext) -> float:
        if Config.get('emulation.open_critical'):
            if random.uniform(0, 100) <= ctx.stats["暴击率"]:
                ctx.is_crit = True
                ctx.audit_trail.append(ModifierRecord("暴击判定", "暴击乘数", 1 + ctx.stats["暴击伤害"]/100, "MULT"))
                return 1 + ctx.stats["暴击伤害"] / 100
        return 1.0

    def _dispatch_broadcast(self, ctx: DamageContext):
        from core.context import get_context
        sim_ctx = get_context()
        hb = ctx.config.hitbox
        sim_ctx.space.broadcast_damage(
            ctx.source, ctx.damage, 
            shape=hb.shape.name, radius=hb.radius, height=hb.height, 
            width=hb.width, length=hb.length, offset=hb.offset
        )

    def _preprocess_reaction_stats(self, ctx: DamageContext):
        for res in ctx.damage.reaction_results:
            ctx.add_modifier(f"反应:{res.reaction_type.name}", "反应基础倍率", res.multiplier, "SET")


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
