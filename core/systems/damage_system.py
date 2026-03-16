from __future__ import annotations
from typing import Any, cast, TYPE_CHECKING
import random

from core.systems.utils import AttributeCalculator
from core.systems.base_system import GameSystem
from core.event import GameEvent, EventType
from core.systems.contract.modifier import ModifierRecord
from core.mechanics.aura import Element
from core.config import Config
from core.logger import get_emulation_logger
from core.tool import get_current_time
from core.action.attack_tag_resolver import AttackTagResolver

if TYPE_CHECKING:
    from core.context import EventEngine
    from core.systems.contract.damage import Damage

class DamageContext:
    """伤害计算上下文 (V2.5 审计状态机)。"""

    def __init__(self, damage: Damage, source: Any, target: Any | None = None):
        self.damage = damage
        self.source = source
        self.target = target
        self.config = damage.config

        # 核心代数槽位 (根据 V2.5 审计规范定义)
        self.stats: dict[str, float] = {
            "固定伤害值加成": 0.0,
            "伤害加成": 0.0,
            "暴击率": 0.0,
            "暴击伤害": 0.0,
            "暴击乘数": 1.0,
            "防御区系数": 1.0,
            "抗性区系数": 1.0,
            "反应基础倍率": 1.0,
            "反应加成系数": 0.0,
            "元素精通": 0.0,
            "减防%": 0.0,
            "无视防御%": 0.0,
            "减抗%": 0.0,
            "抗性穿透%": 0.0,
            "独立乘区%": 0.0,  # 对应规范 2.2 中的 【独立乘区%】
            "倍率加值%": 0.0,  # 对应规范 2.2 中的 【倍率加值%】
        }
        self.audit_trail: list[ModifierRecord] = []
        self.final_result: float = 0.0
        self.is_crit: bool = False

    def add_modifier(
        self, source: str, stat: str, value: float, op: str = "ADD", audit: bool = True
    ) -> None:
        """更新数值并同步审计。"""
        if stat not in self.stats:
            self.stats[stat] = 0.0 if op == "ADD" else 1.0
            
        if op == "ADD":
            self.stats[stat] += value
        elif op == "MULT":
            self.stats[stat] *= value
        elif op == "SET":
            self.stats[stat] = value
            
        if not audit:
            return

        from core.context import get_context
        m_id = 0
        try:
            m_id = get_context().get_next_modifier_id()
        except Exception:
            pass

        self.audit_trail.append(ModifierRecord(m_id, source, stat, value, op))


class DamagePipeline:
    """[V2.5.5] 严格对齐审计规范的五阶段伤害流水线。"""

    def __init__(self, engine: EventEngine):
        self.engine = engine

    def run(self, ctx: DamageContext):
        # 阶段一：意图与目标准备
        if not self._stage_1_preparation(ctx):
            return

        # 阶段二：基础面板与契约快照 (Foundation)
        self._stage_2_foundation(ctx)

        # 阶段三：动态增益注入 (Evolution)
        self._stage_3_evolution(ctx)

        # 阶段四：环境与决策结算 (Resolution)
        self._stage_4_resolution(ctx)

        # 阶段五：终期聚合 (Synthesis)
        self._stage_5_synthesis(ctx)

        # 交付结果
        ctx.damage.damage = ctx.final_result
        ctx.damage.is_crit = ctx.is_crit  # 同步暴击状态
        ctx.damage.data["audit_trail"] = ctx.audit_trail

    def _stage_1_preparation(self, ctx: DamageContext) -> bool:
        ctx.damage.set_source(ctx.source)
        if not ctx.target:
            from core.context import get_context
            sim_ctx = get_context()
            if sim_ctx.space:
                sim_ctx.space.broadcast_damage(ctx.source, ctx.damage)
        else:
            ctx.damage.set_target(ctx.target)

        if not ctx.damage.target:
            return False
        ctx.target = ctx.damage.target
        ctx.target.handle_damage(ctx.damage)
        return True

    def _stage_2_foundation(self, ctx: DamageContext):
        """阶段二：抓取基础面板与技能倍率。"""
        src = ctx.source
        scaling_stats = cast(list[str], ctx.damage.scaling_stat)

        # 1. 抓取每一个缩放属性的快照 (不入库 [R])
        for s_name in scaling_stats:
            if s_name == "固定值": continue
            val = AttributeCalculator.get_val_by_name(src, s_name)
            ctx.add_modifier("[面板快照]", s_name, val, "SET", audit=False)

        # 2. 抓取技能倍率向量 (入库 [S])
        mults = ctx.damage.damage_multiplier
        for i, s_name in enumerate(scaling_stats):
            m_val = mults[i] if i < len(mults) else 0.0
            # stat 命名对齐规范：技能倍率%
            ctx.add_modifier("[技能契约]", f"{s_name}技能倍率%", m_val, "SET", audit=True)

        # 3. 全局基础属性快照 (不入库 [R])
        em = AttributeCalculator.get_val_by_name(src, "元素精通")
        ctx.add_modifier("[面板快照]", "元素精通", em, "SET", audit=False)

        el = ctx.damage.element[0]
        el_name = el.value if isinstance(el, Element) else str(el)
        bonus = AttributeCalculator.get_final_damage_bonus(src, el_name)
        ctx.add_modifier("[面板快照]", "伤害加成", bonus, "SET", audit=False)

    def _stage_3_evolution(self, ctx: DamageContext):
        """阶段三：允许外部系统注入 Buff。"""
        self.engine.publish(
            GameEvent(
                EventType.BEFORE_CALCULATE,
                get_current_time(),
                source=ctx.source,
                data={"damage_context": ctx},
            )
        )

    def _stage_4_resolution(self, ctx: DamageContext):
        """阶段四：处理环境系数与随机决策。"""
        # 1. 反应乘数
        for res in ctx.damage.reaction_results:
            ctx.add_modifier(f"反应:{res.reaction_type.name}", "反应基础倍率", res.multiplier, "SET", audit=False)
            if res.reaction_type.name in ("VAPORIZE", "MELT"):
                em = ctx.stats["元素精通"]
                em_inc = (2.78 * em) / (em + 1400)
                ctx.add_modifier("[精通转化]", "反应加成系数", em_inc, "ADD", audit=True)

        # 2. 防御与抗性
        self._resolve_def_res_coeffs(ctx)

        # 3. 暴击预判定
        if Config.get("emulation.open_critical"):
            final_crit_rate = AttributeCalculator.get_final_crit_rate(ctx.source) + ctx.stats.get("暴击率", 0)
            if random.uniform(0, 100) <= final_crit_rate:
                ctx.is_crit = True
                crit_dmg = AttributeCalculator.get_final_crit_dmg(ctx.source) + ctx.stats.get("暴击伤害", 0)
                ctx.stats["暴击乘数"] = 1 + crit_dmg / 100.0
                ctx.add_modifier("[随机判定]", "暴击乘数", ctx.stats["暴击乘数"], "SET", audit=False)
            else:
                ctx.stats["暴击乘数"] = 1.0

    def _resolve_def_res_coeffs(self, ctx: DamageContext):
        # 防御区 (执行用户指定的原始公式)
        l_src = float(ctx.source.level)
        k_src = l_src * 5 + 500
        
        base_def_target = AttributeCalculator.get_val_by_name(ctx.target, "防御力")
        # 减防与无视防御加法堆叠
        def_debuff = (ctx.stats.get("减防%", 0) + ctx.stats.get("无视防御%", 0)) / 100.0
        final_def_target = base_def_target * (1.0 - def_debuff)
        
        # 你的公式：防御减免率 = Def / (Def + K)
        def_reduction_rate = final_def_target / (final_def_target + k_src)
        # 乘数 = 1 - 减免率
        coeff_def = 1.0 - def_reduction_rate
        ctx.add_modifier("[环境结算]", "防御区系数", coeff_def, "SET", audit=False)

        # 抗性区
        el = ctx.damage.element[0]
        el_name = el.value if isinstance(el, Element) else str(el)
        base_res = AttributeCalculator.get_val_by_name(ctx.target, f"{el_name}元素抗性")
        res_debuff = (ctx.stats.get("减抗%", 0) + ctx.stats.get("抗性穿透%", 0)) / 100.0
        final_res_val = (base_res / 100.0) - res_debuff
        
        if final_res_val < 0:
            coeff_res = 1.0 - final_res_val / 2.0
        elif final_res_val > 0.75:
            coeff_res = 1.0 / (1.0 + 4.0 * final_res_val)
        else:
            coeff_res = 1.0 - final_res_val
        ctx.add_modifier("[抗性结算]", "抗性区系数", coeff_res, "SET", audit=False)

    def _stage_5_synthesis(self, ctx: DamageContext):
        """阶段五：纯函数合算。"""
        s = ctx.stats
        
        # 路径 A: 剧变反应路径
        if AttackTagResolver.is_transformative(ctx.damage.config.attack_tag, ctx.damage.config.extra_attack_tags):
            level_coeff = float(ctx.damage.data.get("等级系数", 0))
            react_base = float(ctx.damage.data.get("反应系数", 1.0))
            em = s["元素精通"]
            em_inc = (16 * em) / (em + 2000)
            special_bonus = s.get("反应伤害提高", 0)
            ctx.final_result = level_coeff * react_base * (1 + em_inc + special_bonus) * s["抗性区系数"]
            return

        # 路径 B: 常规伤害路径 (严格对齐规范 2.2, 2.3, 3.0)
        # 1. 核心伤害合算
        base_dmg = 0.0
        scaling_stats = cast(list[str], ctx.damage.scaling_stat)
        for s_name in scaling_stats:
            if s_name == "固定值": continue
            attr_val = s.get(s_name, 0.0)
            skill_mult = s.get(f"{s_name}技能倍率%", 0.0)
            
            # Final_Mult = 技能倍率% * (1 + 独立乘区%/100) + 倍率加值%
            final_mult = skill_mult * (1.0 + s["独立乘区%"] / 100.0) + s["倍率加值%"]
            
            # (基础属性 * Final_Mult / 100)
            base_dmg += attr_val * (final_mult / 100.0)
            
        # Core_DMG = base_dmg + 固定伤害值加成
        core_dmg = base_dmg + s["固定伤害值加成"]
        
        # 2. 全乘区聚合 (Synthesis)
        ctx.final_result = (
            core_dmg 
            * (1.0 + s["伤害加成"] / 100.0)
            * s["暴击乘数"]
            * (s["反应基础倍率"] * (1.0 + s["反应加成系数"]))
            * s["防御区系数"]
            * s["抗性区系数"]
        )


class DamageSystem(GameSystem):
    def initialize(self, context: Any):
        super().initialize(context)
        if self.engine:
            self.pipeline = DamagePipeline(self.engine)

    def register_events(self, engine: EventEngine):
        engine.subscribe(EventType.BEFORE_DAMAGE, self)

    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.BEFORE_DAMAGE:
            char = event.data["character"]
            dmg = cast('Damage', event.data["damage"])
            target = event.data.get("target")
            
            ctx = DamageContext(dmg, char, target)
            if hasattr(self, "pipeline"):
                self.pipeline.run(ctx)

            if dmg.target:
                get_emulation_logger().log_damage(char, dmg.target, dmg)
                if self.engine:
                    self.engine.publish(
                        GameEvent(
                            event_type=EventType.AFTER_DAMAGE,
                            frame=event.frame,
                            source=char,
                            data={
                                "character": char, 
                                "target": dmg.target, 
                                "target_id": getattr(dmg.target, "entity_id", None),
                                "damage": dmg
                            },
                        )
                    )
