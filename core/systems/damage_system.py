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
            "无视防御%": 0.0,
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
                # broadcast_damage 会为每个命中的目标调用 target.handle_damage(damage)
                sim_ctx.space.broadcast_damage(ctx.source, ctx.damage)
        else:
            ctx.damage.set_target(ctx.target)
            # 已明确指定目标，手动触发元素附着逻辑
            ctx.target.handle_damage(ctx.damage)

        if not ctx.damage.target:
            return False
        ctx.target = ctx.damage.target
        return True

    def _stage_2_foundation(self, ctx: DamageContext):
        """阶段二：抓取基础面板与技能倍率。"""
        src = ctx.source
        scaling_stats = cast(list[str], ctx.damage.scaling_stat)

        # 1. 抓取每一个缩放属性的快照 (不入库 [R])
        for s_name in scaling_stats:
            if s_name == "固定值":
                continue
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
                crit_mult = 1 + crit_dmg / 100.0
            else:
                crit_mult = 1.0

            # 统一入口：通过 add_modifier 写入，但不入库
            ctx.add_modifier(
                source="[随机判定]",
                stat="暴击乘数",
                value=crit_mult,
                op="SET",
                audit=False,  # 暴击乘数不需要审计链记录
            )

    def _resolve_def_res_coeffs(self, ctx: DamageContext):
        # 防御区：统一处理减防和无视防御
        l_src = float(ctx.source.level)
        k_src = l_src * 5 + 500

        # 获取面板防御力和减防百分比（效果作用于目标的防御力%负值）
        panel_def, def_reduction_pct = AttributeCalculator.get_base_def_before_reduction(ctx.target)

        # 无视防御%（攻击者侧属性，通过 DamageContext 注入）
        ignore_def_pct = ctx.stats.get("无视防御%", 0)

        # 总防御削减 = 减防% + 无视防御%
        total_reduction = (def_reduction_pct + ignore_def_pct) / 100.0
        final_def_target = panel_def * (1.0 - total_reduction)

        # 公式：防御减免率 = Def / (Def + K)
        def_reduction_rate = final_def_target / (final_def_target + k_src)
        # 乘数 = 1 - 减免率
        coeff_def = 1.0 - def_reduction_rate
        ctx.add_modifier("[环境结算]", "防御区系数", coeff_def, "SET", audit=False)

        # 抗性区：AttributeCalculator 已返回包含减抗效果的最终抗性值
        el = ctx.damage.element[0]
        el_name = el.value if isinstance(el, Element) else str(el)
        final_res_val = AttributeCalculator.get_val_by_name(ctx.target, f"{el_name}元素抗性") / 100.0

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

        # 路径 B: 月曜伤害路径
        if self._is_lunar_damage(ctx):
            self._calculate_lunar_damage(ctx)
            return

        # 路径 C: 常规伤害路径 (严格对齐规范 2.2, 2.3, 3.0)
        # 1. 核心伤害合算
        base_dmg = 0.0
        scaling_stats = cast(list[str], ctx.damage.scaling_stat)
        for s_name in scaling_stats:
            if s_name == "固定值":
                continue
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

    def _is_lunar_damage(self, ctx: DamageContext) -> bool:
        """判定是否为月曜伤害。"""
        return AttackTagResolver.is_lunar_damage(
            ctx.damage.config.attack_tag,
            ctx.damage.config.extra_attack_tags
        )

    def _calculate_lunar_damage(self, ctx: DamageContext) -> None:
        """
        月曜伤害计算。

        特点：
        - 可暴击
        - 不享受增伤加成
        - 无视防御（防御区趋近于1）
        - 有独立的擢升区
        """
        s = ctx.stats

        # 获取基础数据
        level_coeff = float(ctx.damage.data.get("等级系数", 0))
        reaction_mult = float(ctx.damage.data.get("反应倍率", 1.0))
        base_bonus = s.get("基础伤害提升", 0)

        # 月曜精通系数 = 6 × 精通 / (精通 + 2000)
        em = s["元素精通"]
        lunar_em_coeff = 6 * em / (em + 2000)

        # 反应提升
        reaction_bonus = s.get("月曜反应伤害提升", 0)
        reaction_boost = 1 + lunar_em_coeff + reaction_bonus / 100

        # 核心基础伤害
        core_damage = level_coeff * reaction_mult * (1 + base_bonus / 100) * reaction_boost

        # 附加伤害
        extra_damage = float(ctx.damage.data.get("附加伤害", 0))

        # 基础伤害区
        base_damage = core_damage + extra_damage

        # 暴击区（月曜伤害可暴击）
        crit_mult = s["暴击乘数"]

        # 抗性区
        res_coeff = s["抗性区系数"]

        # 擢升区（独立的增伤区）
        ascension_mult = 1 + s.get("月曜伤害擢升", 0) / 100

        # 最终伤害（无防御区，无增伤区）
        ctx.final_result = base_damage * crit_mult * res_coeff * ascension_mult


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
