"""月曜伤害计算流水线模块。"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any
import random

from core.systems.utils import AttributeCalculator
from core.event import GameEvent, EventType
from core.mechanics.aura import Element
from core.config import Config
from core.tool import get_current_time, get_reaction_multiplier

from .context import DamageContext

if TYPE_CHECKING:
    from core.context import EventEngine


class LunarDamagePipeline:
    """
    月曜伤害计算流水线。

    月曜伤害分为两种类型：
    1. 反应伤害：由雷暴云/月笼等实体造成，使用等级基数计算，支持多组分加权求和
    2. 角色伤害：由角色技能直接造成，使用属性×属性倍率计算

    共同特点：
    - 可暴击（各组分独立判定）
    - 不享受增伤加成
    - 无视防御
    - 有独立的擢升区

    反应伤害公式：
    基础伤害区 = 等级基数 × 反应倍率 × (1 + 基础伤害提升/100%) × 反应提升 + 附加伤害
    反应提升 = 1 + 月曜精通系数 + 反应造成的伤害提升/100%
    月曜精通系数 = 6 × 精通 / (精通 + 2000)
    最终伤害 = 基础伤害区 × 组分暴击区 × 组分擢升区 × 抗性区

    多组分加权求和公式：
    最终伤害 = 最高 + 次高÷2 + 其余之和÷12

    角色伤害公式：
    核心基础伤害 = 属性 × 属性倍率 × 反应倍率 × (1 + 基础伤害提升/100%)
    基础伤害区 = 核心基础伤害 × 反应提升 + 附加伤害
    最终伤害 = 基础伤害区 × 暴击区 × 擢升区 × 抗性区
    """

    def __init__(self, engine: EventEngine):
        self.engine = engine

    def run(self, ctx: DamageContext) -> None:
        """执行月曜伤害计算。"""
        # 检查是否为多组分反应伤害（有 source_characters 列表）
        source_characters = ctx.damage.data.get("source_characters")
        if source_characters and len(source_characters) > 0:
            # 多组分反应伤害：逐个计算后加权求和
            self._run_multi_component(ctx, source_characters)
        else:
            # 单一伤害：正常流程
            self._run_single(ctx)

    def _run_single(self, ctx: DamageContext) -> None:
        """执行单一月曜伤害计算。"""
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

    def _run_multi_component(self, ctx: DamageContext, source_characters: list[Any]) -> None:
        """
        执行多组分反应伤害计算。

        为每个来源角色独立计算伤害组分，然后加权求和。
        组分贡献存储到 ctx.damage.data["contributions"] 用于持久化。

        [V18.0] 新增：保存各组分的独立乘区数据（基础伤害、暴击、抗性）
        """
        from core.systems.contract.damage import Damage
        from core.systems.contract.attack import AttackConfig
        from core.persistence.processors.audit.types import (
            CharacterContribution,
            ComponentDamageData,
        )

        target = ctx.target
        reaction_mult = float(ctx.damage.data.get("反应倍率", 1.0))
        attack_tag = ctx.damage.config.attack_tag
        damage_name = ctx.damage.name
        element = ctx.damage.element[0]

        damage_components: list[tuple[Any, float, ComponentDamageData]] = []
        contributions: list[CharacterContribution] = []

        for char in source_characters:
            # 为每个角色创建独立的 Damage 和 Context
            dmg = Damage(
                element=(element, 0.0),
                config=AttackConfig(attack_tag=attack_tag),
                name=damage_name,
            )
            dmg.add_data("等级系数", get_reaction_multiplier(char.level))
            dmg.add_data("反应倍率", reaction_mult)
            dmg.add_data("伤害类型", "反应伤害")
            dmg.set_source(char)
            dmg.set_target(target)

            # 创建独立的上下文并计算
            component_ctx = DamageContext(dmg, char, target)
            self._run_single(component_ctx)

            # [V18.0] 提取组分独立的乘区数据
            component_data = ComponentDamageData(
                character_name=char.name,
                damage_value=dmg.damage,
                weight=1.0,  # 稍后根据排序设置
                base_damage=component_ctx.stats.get("月曜基础伤害区", 0.0),
                crit_multiplier=component_ctx.stats.get("暴击乘数", 1.0),
                resistance_multiplier=component_ctx.stats.get("抗性区系数", 1.0),
                audit_steps=[
                    {"source": m.source, "stat": m.stat, "value": m.value, "op": m.op}
                    for m in component_ctx.audit_trail
                ],
                is_crit=component_ctx.is_crit,
                crit_rate=component_ctx.stats.get("暴击率", 0.0),
                crit_dmg=component_ctx.stats.get("暴击伤害", 0.0),
            )

            damage_components.append((char, dmg.damage, component_data))
            contributions.append(CharacterContribution(
                character_name=char.name,
                damage_component=dmg.damage,
                weight_percentage=0.0,  # 稍后计算
                component_data=component_data,
            ))

        # 加权求和
        final_damage = self._calculate_weighted_damage(
            [(c, d, comp) for c, d, comp in damage_components]
        )

        # 按伤害值排序，设置权重
        sorted_components = sorted(damage_components, key=lambda x: x[1], reverse=True)
        for i, (char, dmg_val, comp_data) in enumerate(sorted_components):
            if i == 0:
                comp_data.weight = 1.0  # 最高组
            elif i == 1:
                comp_data.weight = 0.5  # 次高组
            else:
                comp_data.weight = 1.0 / 12  # 其余组

        # 计算实际权重百分比
        if final_damage > 0:
            for c in contributions:
                c.weight_percentage = c.damage_component / final_damage * 100

        # 将结果写入原始上下文
        ctx.final_result = final_damage
        ctx.damage.damage = final_damage
        ctx.damage.data["contributions"] = contributions
        ctx.is_crit = False

    def _calculate_weighted_damage(
        self,
        damage_components: list[tuple[Any, float, Any]]
    ) -> float:
        """
        加权求和计算月曜伤害。

        公式：最终伤害 = 最高 + 次高÷2 + 其余之和÷12

        Args:
            damage_components: 元组列表 (角色对象, 伤害值, 组分数据)
        """
        if not damage_components:
            return 0.0

        damages = sorted([d[1] for d in damage_components], reverse=True)

        if len(damages) == 1:
            return damages[0]
        elif len(damages) == 2:
            return damages[0] + damages[1] / 2
        else:
            return damages[0] + damages[1] / 2 + sum(damages[2:]) / 12

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

        # 如果是角色伤害类型，需要额外抓取缩放属性
        if self._is_character_damage(ctx):
            scaling_stat = ctx.damage.scaling_stat
            if scaling_stat and scaling_stat[0] != "固定值":
                attr_val = AttributeCalculator.get_val_by_name(src, scaling_stat[0])
                ctx.add_modifier("[面板快照]", scaling_stat[0], attr_val, "SET", audit=False)

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

    def _is_character_damage(self, ctx: DamageContext) -> bool:
        """
        判定是否为角色伤害类型。

        角色伤害：由角色技能直接造成，有属性倍率
        反应伤害：由雷暴云/月笼等实体造成，使用等级基数

        判定逻辑：
        1. 如果 damage.data 中明确标记了 "伤害类型" 为 "角色伤害"，则为角色伤害
        2. 如果 damage.data 中明确标记了 "伤害类型" 为 "反应伤害"，则为反应伤害
        3. 如果有等级系数且没有非零的属性倍率，则为反应伤害
        4. 否则，检查 scaling_stat 是否为有效属性

        Returns:
            True 如果是角色伤害，False 如果是反应伤害
        """
        # 优先检查显式标记
        damage_type = ctx.damage.data.get("伤害类型")
        if damage_type == "角色伤害":
            return True
        if damage_type == "反应伤害":
            return False

        # 如果有等级系数但没有有效的属性倍率，认为是反应伤害
        has_level_coeff = ctx.damage.data.get("等级系数") is not None
        has_valid_mult = (
            ctx.damage.damage_multiplier
            and len(ctx.damage.damage_multiplier) > 0
            and ctx.damage.damage_multiplier[0] > 0
        )

        if has_level_coeff and not has_valid_mult:
            return False

        # 默认：检查 scaling_stat 是否为有效属性
        scaling_stat = ctx.damage.scaling_stat
        if scaling_stat and len(scaling_stat) > 0:
            return scaling_stat[0] != "固定值"
        return False

    def _stage_5_synthesis(self, ctx: DamageContext) -> None:
        """阶段五：月曜伤害计算。"""
        if self._is_character_damage(ctx):
            self._calculate_character_damage(ctx)
        else:
            self._calculate_reaction_damage(ctx)

    def _calculate_reaction_damage(self, ctx: DamageContext) -> None:
        """
        计算反应伤害（雷暴云/月笼攻击）。

        公式：
        基础伤害区 = 等级基数 × 反应倍率 × (1 + 基础伤害提升/100%) × 反应提升 + 附加伤害
        反应提升 = 1 + 月曜精通系数 + 反应造成的伤害提升/100%
        最终伤害 = 基础伤害区 × 暴击区 × 擢升区 × 抗性区
        """
        s = ctx.stats

        # 从 Damage.data 获取参数
        level_coeff = float(ctx.damage.data.get("等级系数", 0))
        reaction_mult = float(ctx.damage.data.get("反应倍率", 1.0))

        # 基础伤害提升
        base_bonus = s.get("基础伤害提升", 0)

        # 月曜精通系数 = 6 × 精通 / (精通 + 2000)
        em = s.get("元素精通", 0)
        lunar_em_coeff = 6 * em / (em + 2000)

        # 月曜反应伤害提升（反应造成的伤害提升）
        reaction_bonus = s.get("月曜反应伤害提升", 0)

        # 反应提升
        reaction_boost = 1 + lunar_em_coeff + reaction_bonus / 100

        # 核心基础伤害
        core_damage = level_coeff * reaction_mult * (1 + base_bonus / 100) * reaction_boost

        # 附加伤害
        extra_damage = float(ctx.damage.data.get("附加伤害", 0))

        # 基础伤害区
        base_damage = core_damage + extra_damage

        # [V18.0] 保存基础伤害区到 stats，用于多组分展示
        ctx.stats["月曜基础伤害区"] = base_damage

        # 暴击区（组分暴击区）
        crit_mult = s.get("暴击乘数", 1.0)

        # 擢升区（组分擢升区）
        ascension_mult = 1 + s.get("月曜伤害擢升", 0) / 100

        # 抗性区
        res_coeff = s.get("抗性区系数", 1.0)

        # 最终伤害（无防御区，无增伤区）
        ctx.final_result = base_damage * crit_mult * res_coeff * ascension_mult

    def _calculate_character_damage(self, ctx: DamageContext) -> None:
        """
        计算角色伤害（角色技能直接造成）。

        公式：
        核心基础伤害 = 属性 × 属性倍率 × 反应倍率 × (1 + 基础伤害提升/100%)
        基础伤害区 = 核心基础伤害 × 反应提升 + 附加伤害
        反应提升 = 1 + 月曜精通系数 + 月曜反应伤害提升/100%
        最终伤害 = 基础伤害区 × 暴击区 × 擢升区 × 抗性区
        """
        s = ctx.stats

        # 获取缩放属性和倍率
        scaling_stat = ctx.damage.scaling_stat
        damage_mult = ctx.damage.damage_multiplier

        # 属性值
        attr_val = 0.0
        if scaling_stat and len(scaling_stat) > 0 and scaling_stat[0] != "固定值":
            attr_val = s.get(scaling_stat[0], 0)

        # 属性倍率（技能倍率）
        skill_mult = damage_mult[0] if damage_mult else 0.0

        # 反应倍率（月感电 3.0 / 月结晶 1.6 / 月绽放 1.0）
        reaction_mult = float(ctx.damage.data.get("反应倍率", 1.0))

        # 基础伤害提升
        base_bonus = s.get("基础伤害提升", 0)

        # 核心基础伤害 = 属性 × 属性倍率 × 反应倍率 × (1 + 基础伤害提升/100%)
        core_damage = attr_val * skill_mult / 100 * reaction_mult * (1 + base_bonus / 100)

        # 月曜精通系数 = 6 × 精通 / (精通 + 2000)
        em = s.get("元素精通", 0)
        lunar_em_coeff = 6 * em / (em + 2000)

        # 月曜反应伤害提升
        reaction_bonus = s.get("月曜反应伤害提升", 0)

        # 反应提升
        reaction_boost = 1 + lunar_em_coeff + reaction_bonus / 100

        # 附加伤害
        extra_damage = float(ctx.damage.data.get("附加伤害", 0))

        # 基础伤害区 = 核心基础伤害 × 反应提升 + 附加伤害
        base_damage = core_damage * reaction_boost + extra_damage

        # 暴击区
        crit_mult = s.get("暴击乘数", 1.0)

        # 擢升区
        ascension_mult = 1 + s.get("月曜伤害擢升", 0) / 100

        # 抗性区
        res_coeff = s.get("抗性区系数", 1.0)

        # 最终伤害
        ctx.final_result = base_damage * crit_mult * res_coeff * ascension_mult
