"""月曜伤害计算流水线模块。"""

from __future__ import annotations
from typing import TYPE_CHECKING
import random

from core.systems.utils import AttributeCalculator
from core.event import GameEvent, EventType
from core.mechanics.aura import Element
from core.config import Config
from core.tool import get_current_time

from .context import DamageContext

if TYPE_CHECKING:
    from core.context import EventEngine


class LunarDamagePipeline:
    """
    月曜伤害计算流水线。

    特点：
    - 可暴击
    - 不享受增伤加成
    - 无视防御
    - 支持多角色加权求和

    公式：月曜伤害 = 基础伤害区 × 暴击区 × 抗性区 × 擢升区
    基础伤害区 = 核心基础伤害 × 反应提升 + 附加伤害
    核心基础伤害 = 等级系数 × 反应倍率 × (1 + 基础伤害提升/100%)
    反应提升 = 1 + 月曜精通系数 + (月曜反应伤害提升/100%)
    月曜精通系数 = 6 × 精通 / (精通 + 2000)
    """

    def __init__(self, engine: EventEngine):
        self.engine = engine

    def run(self, ctx: DamageContext) -> None:
        """执行月曜伤害计算。"""
        # 阶段一：目标准备
        if not self._stage_1_preparation(ctx):
            return

        # 阶段二：基础面板快照
        self._stage_2_foundation(ctx)

        # 阶段三：动态增益注入
        self._stage_3_evolution(ctx)

        # 阶段四：环境与决策结算
        self._stage_4_resolution(ctx)

        # 阶段五：月曜伤害计算
        self._stage_5_synthesis(ctx)

        # 交付结果
        ctx.damage.damage = ctx.final_result
        ctx.damage.is_crit = ctx.is_crit
        ctx.damage.data["audit_trail"] = ctx.audit_trail

    def _stage_1_preparation(self, ctx: DamageContext) -> bool:
        """阶段一：目标准备。"""
        ctx.damage.set_source(ctx.source)
        if not ctx.target:
            from core.context import get_context
            sim_ctx = get_context()
            if sim_ctx.space:
                sim_ctx.space.broadcast_damage(ctx.source, ctx.damage)
        else:
            ctx.damage.set_target(ctx.target)
            ctx.target.handle_damage(ctx.damage)

        if not ctx.damage.target:
            return False
        ctx.target = ctx.damage.target
        return True

    def _stage_2_foundation(self, ctx: DamageContext) -> None:
        """阶段二：抓取基础面板。"""
        src = ctx.source

        # 元素精通快照
        em = AttributeCalculator.get_val_by_name(src, "元素精通")
        ctx.add_modifier("[面板快照]", "元素精通", em, "SET", audit=False)

    def _stage_3_evolution(self, ctx: DamageContext) -> None:
        """阶段三：允许外部系统注入 Buff。"""
        if self.engine:
            self.engine.publish(
                GameEvent(
                    EventType.BEFORE_CALCULATE,
                    get_current_time(),
                    source=ctx.source,
                    data={"damage_context": ctx},
                )
            )

    def _stage_4_resolution(self, ctx: DamageContext) -> None:
        """阶段四：处理环境系数与随机决策。"""
        # 1. 抗性区（月曜伤害需要）
        self._resolve_resistance(ctx)

        # 2. 暴击预判定（月曜伤害可暴击）
        if Config.get("emulation.open_critical"):
            final_crit_rate = AttributeCalculator.get_final_crit_rate(ctx.source) + ctx.stats.get("暴击率", 0)
            if random.uniform(0, 100) <= final_crit_rate:
                ctx.is_crit = True
                crit_dmg = AttributeCalculator.get_final_crit_dmg(ctx.source) + ctx.stats.get("暴击伤害", 0)
                crit_mult = 1 + crit_dmg / 100.0
            else:
                crit_mult = 1.0

            ctx.add_modifier(
                source="[随机判定]",
                stat="暴击乘数",
                value=crit_mult,
                op="SET",
                audit=False,
            )

    def _resolve_resistance(self, ctx: DamageContext) -> None:
        """计算抗性区系数。"""
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

    def _stage_5_synthesis(self, ctx: DamageContext) -> None:
        """阶段五：月曜伤害计算。"""
        s = ctx.stats

        # 从 Damage.data 获取参数
        level_coeff = float(ctx.damage.data.get("等级系数", 0))
        reaction_mult = float(ctx.damage.data.get("反应倍率", 1.0))

        # 基础伤害提升
        base_bonus = s.get("基础伤害提升", 0)

        # 月曜精通系数 = 6 × 精通 / (精通 + 2000)
        em = s.get("元素精通", 0)
        lunar_em_coeff = 6 * em / (em + 2000)

        # 月曜反应伤害提升
        reaction_bonus = s.get("月曜反应伤害提升", 0)

        # 反应提升
        reaction_boost = 1 + lunar_em_coeff + reaction_bonus / 100

        # 核心基础伤害
        core_damage = level_coeff * reaction_mult * (1 + base_bonus / 100) * reaction_boost

        # 附加伤害
        extra_damage = float(ctx.damage.data.get("附加伤害", 0))
        base_damage = core_damage + extra_damage

        # 暴击区
        crit_mult = s.get("暴击乘数", 1.0)

        # 抗性区
        res_coeff = s.get("抗性区系数", 1.0)

        # 擢升区
        ascension_mult = 1 + s.get("月曜伤害擢升", 0) / 100

        # 最终伤害（无防御区，无增伤区）
        ctx.final_result = base_damage * crit_mult * res_coeff * ascension_mult
