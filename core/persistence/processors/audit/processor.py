"""[V13.0] 伤害审计处理器

负责将离散的审计记录聚合为标准的乘区模型。

[V12.0] 支持两种伤害路径：
- 常规伤害路径：6 桶模型（CORE + BONUS + CRIT + REACT + DEF + RES）
- 剧变反应路径：4 桶模型

[V15.0] 新增验证功能
"""

from __future__ import annotations
from typing import Any

from .types import DomainValues, DamageTypeContext, DamageType
from .constants import BUCKET_MAP, SOURCE_TYPE_MAP
from .bucket_processor import (
    create_empty_buckets,
    create_transformative_buckets,
    create_lunar_buckets,
    classify_trail_entry,
    inject_frame_snapshot,
    inject_target_modifiers,
    aggregate_buckets,
    collect_def_res_raw_data,
    collect_resistance_raw_data,
)
from .domain_calculator import (
    get_source_type,
    group_steps_by_source,
    calculate_domains,
)
from core.action.attack_tag_resolver import AttackTagResolver
from .validator import AuditValidator, ValidationResult, DEFAULT_TOLERANCE


class AuditProcessor:
    """
    [V13.0] 伤害审计处理器。

    负责将离散的审计记录聚合为标准的乘区模型。

    [V12.0] 新增剧变反应路径支持。
    """

    # 暴露常量供外部访问
    BUCKET_MAP = BUCKET_MAP
    SOURCE_TYPE_MAP = SOURCE_TYPE_MAP

    @staticmethod
    def process_detail(
        raw_trail: list[dict[str, Any]],
        frame_snapshot: dict[str, Any] | None = None,
        target_snapshot: dict[str, Any] | None = None,
        is_crit: bool = False,
        element_type: str = "",
    ) -> dict[str, Any]:
        """
        [V13.0] 聚合原始审计链为 6 大乘区大类。

        [V14.0] 新增 target_snapshot 参数，用于处理目标侧修饰符（减防、减抗等）
        [V14.1] 新增 element_type 参数，用于抗性区原始数据收集

        Args:
            raw_trail: 审计链 [S] 项（脱水存储的动态 Buff、技能倍率、随机暴击判定）
            frame_snapshot: 帧快照 [R] 项（攻击者的基础属性、面板百分比、等级、抗性）
            target_snapshot: 目标快照 [R] 项（目标的修饰符，如减防、减抗等）
            is_crit: 是否暴击（用于兼容旧逻辑）
            element_type: 元素类型（用于抗性区数据收集）

        Returns:
            聚合后的 6 大乘区数据结构
        """
        buckets = create_empty_buckets()

        # 1. 遍历审计链进行归类（填充 steps）
        for entry in raw_trail:
            classify_trail_entry(entry, buckets)

        # 2. 从帧快照获取基础属性并构建 scaling_info（需要在 aggregate 之前）
        inject_frame_snapshot(frame_snapshot, buckets)

        # 3. [V14.0] 从目标快照注入减防/减抗修饰符
        inject_target_modifiers(target_snapshot, buckets, element_type)

        # 4. 内部合算逻辑
        aggregate_buckets(buckets, is_crit)

        # 5. [V14.1] 收集防御区和抗性区原始数据（供 UI 端计算系数）
        collect_def_res_raw_data(frame_snapshot, target_snapshot, buckets, element_type)

        return buckets

    @staticmethod
    def process_transformative(
        damage_type_ctx: DamageTypeContext,
        raw_trail: list[dict[str, Any]],
        frame_snapshot: dict[str, Any] | None = None,
        target_snapshot: dict[str, Any] | None = None,
        element_type: str = "",
    ) -> dict[str, Any]:
        """[V12.0] 处理剧变反应审计数据

        剧变反应使用 3 桶模型：
        - level_coeff: 等级系数
        - reaction: 反应乘区（反应系数 × 精通加成）
        - resistance: 抗性区

        [V14.0] 新增 target_snapshot 参数，用于处理目标侧修饰符
        [V14.1] 新增 element_type 参数，用于抗性区原始数据收集
        [V16.0] 合并 reaction_coeff + em_bonus 为 reaction 桶

        Args:
            damage_type_ctx: 伤害类型上下文
            raw_trail: 审计链
            frame_snapshot: 帧快照
            target_snapshot: 目标快照
            element_type: 元素类型（用于抗性区数据收集）

        Returns:
            剧变反应 3 桶数据结构
        """
        from core.systems.contract.reaction import ElementalReactionType

        buckets = create_transformative_buckets()

        # 1. 填充等级系数
        buckets["level_coeff"]["value"] = damage_type_ctx.level_coeff

        # 2. 填充反应乘区（反应系数 × 精通加成）
        # 2.1 从 attack_tag 提取反应类型中文名称
        attack_tag = damage_type_ctx.attack_tag
        reaction_type = attack_tag.replace("伤害", "").replace("扩散", "扩散")
        # 尝试从枚举获取更准确的中文名称
        reaction_type_map = {
            "超载": ElementalReactionType.OVERLOAD,
            "感电": ElementalReactionType.ELECTRO_CHARGED,
            "超导": ElementalReactionType.SUPERCONDUCT,
            "碎冰": ElementalReactionType.SHATTER,
            "扩散": ElementalReactionType.SWIRL,
            "超绽放": ElementalReactionType.HYPERBLOOM,
            "烈绽放": ElementalReactionType.BURGEON,
            "绽放": ElementalReactionType.BLOOM,
        }
        for tag, rt_enum in reaction_type_map.items():
            if tag in attack_tag:
                reaction_type = rt_enum.value
                break

        buckets["reaction"]["reaction_type"] = reaction_type
        buckets["reaction"]["reaction_base"] = damage_type_ctx.reaction_coeff

        # 2.2 计算精通加成
        em = damage_type_ctx.elemental_mastery
        em_bonus_pct = (16 * em) / (em + 2000) * 100 if em > 0 else 0.0
        special_bonus = damage_type_ctx.special_bonus

        buckets["reaction"]["em"] = em
        buckets["reaction"]["em_bonus_pct"] = em_bonus_pct
        buckets["reaction"]["special_bonus"] = special_bonus

        # 2.3 计算总乘数
        total_multiplier = damage_type_ctx.reaction_coeff * (
            1 + em_bonus_pct / 100 + special_bonus / 100
        )
        buckets["reaction"]["multiplier"] = total_multiplier

        # 2.4 添加步骤（用于域详情展示）
        buckets["reaction"]["steps"].append(
            {
                "stat": "反应系数",
                "value": damage_type_ctx.reaction_coeff,
                "op": "SET",
                "source": attack_tag,
            }
        )

        if em > 0:
            buckets["reaction"]["steps"].append(
                {
                    "stat": "精通转化",
                    "value": em_bonus_pct,
                    "op": "ADD",
                    "source": f"元素精通 {em:.0f}",
                }
            )

        if special_bonus > 0:
            buckets["reaction"]["steps"].append(
                {
                    "stat": "特殊加成",
                    "value": special_bonus,
                    "op": "ADD",
                    "source": "装备/天赋",
                }
            )

        # 3. 处理抗性区（从审计链提取）
        for entry in raw_trail:
            stat = entry.get("stat", "")
            val = entry.get("value", 0.0)
            source = entry.get("source", "Unknown")

            if stat == "抗性区系数":
                buckets["resistance"]["multiplier"] = val
                buckets["resistance"]["steps"].append(
                    {"stat": stat, "value": val, "op": "SET", "source": source}
                )

        # 4. 从目标快照获取目标抗性信息
        if target_snapshot:
            # 从目标快照的 resistance 字段获取基础抗性
            # resistance 格式: {"火": 10.0, "水": 10.0, ...}
            target_resistance = target_snapshot.get("resistance", {})

            # 元素名称映射
            element_name_map = {
                "PHYSICAL": "物理",
                "PYRO": "火",
                "HYDRO": "水",
                "ELECTRO": "雷",
                "CRYO": "冰",
                "ANEMO": "风",
                "GEO": "岩",
                "DENDRO": "草",
            }
            el_name = element_name_map.get(element_type, element_type)

            base_res = target_resistance.get(el_name, 0.0)
            if base_res != 0:
                buckets["resistance"]["base_resistance"] = base_res
                buckets["resistance"]["final_resistance"] = base_res / 100.0

        # 5. [V14.0] 从目标快照注入减抗修饰符
        inject_target_modifiers(target_snapshot, buckets, element_type)

        # 6. [V15.0] 仅收集抗性区原始数据（剧变反应无防御区）
        collect_resistance_raw_data(
            frame_snapshot, target_snapshot, buckets, element_type
        )

        return buckets

    @staticmethod
    def process_lunar(
        damage_type_ctx: DamageTypeContext,
        raw_trail: list[dict[str, Any]],
        frame_snapshot: dict[str, Any] | None = None,
        target_snapshot: dict[str, Any] | None = None,
        element_type: str = "",
    ) -> dict[str, Any]:
        """[V17.0] 处理月曜反应审计数据

        月曜反应使用 4 桶模型：
        - base_damage: 基础伤害（等级系数 × 反应倍率 × 精通加成）
        - crit: 暴击乘区（月曜可暴击）
        - resistance: 抗性区
        - ascension: 擢升区（独立增伤区）

        特点：
        - 无增伤区（不享受角色增伤）
        - 无防御区（无视防御）

        Args:
            damage_type_ctx: 伤害类型上下文
            raw_trail: 审计链
            frame_snapshot: 帧快照
            target_snapshot: 目标快照
            element_type: 元素类型（用于抗性区数据收集）

        Returns:
            月曜反应 4 桶数据结构
        """
        from core.systems.contract.reaction import ElementalReactionType

        buckets = create_lunar_buckets()

        # 1. 填充基础伤害桶
        attack_tag = damage_type_ctx.attack_tag
        buckets["base_damage"]["level_coeff"] = damage_type_ctx.level_coeff
        buckets["base_damage"]["reaction_mult"] = damage_type_ctx.reaction_coeff
        buckets["base_damage"]["base_bonus"] = damage_type_ctx.base_bonus
        buckets["base_damage"]["extra_damage"] = damage_type_ctx.extra_damage

        # [V24.0] 存储角色伤害路径数据
        buckets["base_damage"]["damage_type"] = damage_type_ctx.damage_type_detail
        buckets["base_damage"]["scaling_stat"] = damage_type_ctx.scaling_stat
        buckets["base_damage"]["attr_val"] = damage_type_ctx.attr_val
        buckets["base_damage"]["skill_mult"] = damage_type_ctx.skill_mult

        # 1.1 从 attack_tag 提取反应类型中文名称
        reaction_type_map = {
            "月绽放": ElementalReactionType.LUNAR_BLOOM,
            "月感电": ElementalReactionType.LUNAR_CHARGED,
            "月结晶": ElementalReactionType.LUNAR_CRYSTALLIZE,
        }
        reaction_type = ""
        for tag, rt_enum in reaction_type_map.items():
            if tag in attack_tag:
                reaction_type = rt_enum.value
                break
        buckets["base_damage"]["reaction_type"] = reaction_type

        # 1.2 计算月曜精通加成：6 × EM / (EM + 2000)
        em = damage_type_ctx.elemental_mastery
        em_bonus_pct = (6 * em) / (em + 2000) * 100 if em > 0 else 0.0
        buckets["base_damage"]["em_bonus_pct"] = em_bonus_pct

        # 1.3 从上下文获取反应加成
        reaction_bonus = damage_type_ctx.special_bonus  # 复用 special_bonus 字段
        buckets["base_damage"]["reaction_bonus"] = reaction_bonus

        # 1.4 计算基础伤害乘数
        base_mult = damage_type_ctx.reaction_coeff * (
            1 + damage_type_ctx.base_bonus / 100 + em_bonus_pct / 100 + reaction_bonus / 100
        )
        buckets["base_damage"]["multiplier"] = base_mult

        # 1.5 添加步骤（用于域详情展示）
        # [V24.0] 根据伤害类型添加不同的步骤
        if damage_type_ctx.damage_type_detail == "character":
            # 角色伤害路径：显示属性值和技能倍率
            if damage_type_ctx.scaling_stat:
                buckets["base_damage"]["steps"].append(
                    {
                        "stat": damage_type_ctx.scaling_stat,
                        "value": damage_type_ctx.attr_val,
                        "op": "SET",
                        "source": "[面板快照]",
                    }
                )
            if damage_type_ctx.skill_mult > 0:
                buckets["base_damage"]["steps"].append(
                    {
                        "stat": "技能倍率%",
                        "value": damage_type_ctx.skill_mult,
                        "op": "MULT",
                        "source": "技能",
                    }
                )
        else:
            # 反应伤害路径：显示等级系数
            buckets["base_damage"]["steps"].append(
                {
                    "stat": "等级系数",
                    "value": damage_type_ctx.level_coeff,
                    "op": "SET",
                    "source": "角色等级",
                }
            )
        buckets["base_damage"]["steps"].append(
            {
                "stat": "反应倍率",
                "value": damage_type_ctx.reaction_coeff,
                "op": "MULT",
                "source": reaction_type or attack_tag,
            }
        )

        # [V22.0] 从审计链提取月曜专用修饰符来源
        # 提取基础伤害提升来源
        base_bonus_mods = [
            entry for entry in raw_trail
            if entry.get("stat") == "基础伤害提升"
        ]
        for mod in base_bonus_mods:
            buckets["base_damage"]["steps"].append(
                {
                    "stat": "基础伤害提升",
                    "value": mod.get("value", 0.0),
                    "op": mod.get("op", "ADD"),
                    "source": mod.get("source", "装备/天赋"),
                }
            )

        if em > 0:
            buckets["base_damage"]["steps"].append(
                {
                    "stat": "月曜精通转化",
                    "value": em_bonus_pct,
                    "op": "ADD",
                    "source": f"元素精通 {em:.0f}",
                }
            )

        # 提取月曜反应伤害提升来源
        reaction_bonus_mods = [
            entry for entry in raw_trail
            if entry.get("stat") == "月曜反应伤害提升"
        ]
        for mod in reaction_bonus_mods:
            buckets["base_damage"]["steps"].append(
                {
                    "stat": "月曜反应伤害提升",
                    "value": mod.get("value", 0.0),
                    "op": mod.get("op", "ADD"),
                    "source": mod.get("source", "装备/天赋"),
                }
            )

        if damage_type_ctx.extra_damage > 0:
            buckets["base_damage"]["steps"].append(
                {
                    "stat": "附加伤害",
                    "value": damage_type_ctx.extra_damage,
                    "op": "ADD",
                    "source": "其他来源",
                }
            )

        # 1.6 填充角色贡献列表（加权求和用）
        buckets["base_damage"]["contributions"] = [
            {
                "character_name": c.character_name,
                "damage_component": c.damage_component,
                "weight_percentage": c.weight_percentage,
            }
            for c in damage_type_ctx.contributing_characters
        ]

        # [V18.0] 构建组分桶数据（用于多行展示）
        contributions = damage_type_ctx.contributing_characters
        if contributions:
            # 按伤害值排序
            sorted_contributions = sorted(
                contributions,
                key=lambda c: c.damage_component,
                reverse=True
            )

            component_buckets = []
            for i, contrib in enumerate(sorted_contributions[:2]):  # 只取前两名（最高组、次高组）
                if contrib.component_data:
                    comp_data = contrib.component_data
                    comp_bucket = {
                        "rank": "最高组" if i == 0 else "次高组",
                        "character_name": contrib.character_name,
                        "damage_value": comp_data.damage_value,
                        "weight": comp_data.weight,
                        "base_damage": {
                            "value": comp_data.base_damage,
                            "multiplier": comp_data.base_damage,
                        },
                        "crit": {
                            "multiplier": comp_data.crit_multiplier,
                            "is_crit": comp_data.is_crit,
                            "crit_rate": comp_data.crit_rate,
                        },
                        "resistance": {
                            "multiplier": comp_data.resistance_multiplier,
                        },
                    }
                    component_buckets.append(comp_bucket)

            if component_buckets:
                buckets["_component_buckets"] = component_buckets

        # 2. 处理暴击区（月曜可暴击）
        for entry in raw_trail:
            stat = entry.get("stat", "")
            val = entry.get("value", 0.0)
            source = entry.get("source", "Unknown")

            if stat == "暴击乘数":
                buckets["crit"]["multiplier"] = val
                buckets["crit"]["steps"].append(
                    {"stat": stat, "value": val, "op": "SET", "source": source}
                )

        # 从帧快照获取暴击率
        if frame_snapshot:
            base_crit_rate = frame_snapshot.get("stats", {}).get("暴击率", 0.0)
            buckets["crit"]["crit_rate"] = base_crit_rate

        # 3. 处理抗性区
        for entry in raw_trail:
            stat = entry.get("stat", "")
            val = entry.get("value", 0.0)
            source = entry.get("source", "Unknown")

            if stat == "抗性区系数":
                buckets["resistance"]["multiplier"] = val
                buckets["resistance"]["steps"].append(
                    {"stat": stat, "value": val, "op": "SET", "source": source}
                )

        # 从目标快照获取抗性信息
        if target_snapshot:
            target_resistance = target_snapshot.get("resistance", {})
            element_name_map = {
                "PHYSICAL": "物理",
                "PYRO": "火",
                "HYDRO": "水",
                "ELECTRO": "雷",
                "CRYO": "冰",
                "ANEMO": "风",
                "GEO": "岩",
                "DENDRO": "草",
            }
            el_name = element_name_map.get(element_type, element_type)
            base_res = target_resistance.get(el_name, 0.0)
            if base_res != 0:
                buckets["resistance"]["base_resistance"] = base_res
                buckets["resistance"]["final_resistance"] = base_res / 100.0

        # 注入减抗修饰符
        inject_target_modifiers(target_snapshot, buckets, element_type)
        collect_resistance_raw_data(frame_snapshot, target_snapshot, buckets, element_type)

        # 4. 处理擢升区
        ascension_bonus = damage_type_ctx.ascension_bonus
        buckets["ascension"]["bonus_pct"] = ascension_bonus
        buckets["ascension"]["multiplier"] = 1 + ascension_bonus / 100

        # [V22.0] 从审计链提取擢升区来源
        ascension_mods = [
            entry for entry in raw_trail
            if entry.get("stat") == "月曜伤害擢升"
        ]
        for mod in ascension_mods:
            buckets["ascension"]["steps"].append(
                {
                    "stat": "月曜伤害擢升",
                    "value": mod.get("value", 0.0),
                    "op": mod.get("op", "ADD"),
                    "source": mod.get("source", "装备/天赋"),
                }
            )

        return buckets

    @staticmethod
    def get_source_type(source: str) -> str:
        """[V10.0] 从来源名称推断来源类型"""
        return get_source_type(source)

    @staticmethod
    def group_steps_by_source(steps: list[dict]) -> list[Any]:
        """[V10.0] 将步骤按来源分组为域"""
        return group_steps_by_source(steps)

    @staticmethod
    def calculate_domains(steps: list[dict]) -> DomainValues:
        """[V11.0] 计算域值并分组修饰符"""
        return calculate_domains(steps)

    # ============================================================
    # [V15.0] 验证功能
    # ============================================================

    @staticmethod
    def detect_damage_type(attack_tag: str) -> DamageType:
        """[V15.0] 从攻击标签检测伤害类型

        [V17.0] 新增月曜反应类型检测
        [V18.0] 统一使用 AttackTagResolver 进行检测

        Args:
            attack_tag: 攻击标签（如 "超载伤害", "普通攻击", "月绽放"）

        Returns:
            DamageType 枚举值
        """
        if AttackTagResolver.is_lunar_damage(attack_tag):
            return DamageType.LUNAR
        if AttackTagResolver.is_transformative(attack_tag):
            return DamageType.TRANSFORMATIVE
        return DamageType.NORMAL

    @staticmethod
    def validate(
        buckets: dict[str, Any],
        db_damage: float,
        damage_type: DamageType,
        tolerance: float = DEFAULT_TOLERANCE,
        event_id: int | None = None,
    ) -> ValidationResult:
        """验证伤害计算结果

        [V15.0] 新增：验证审计链计算结果与数据库真值的一致性
        [V17.0] 新增：月曜反应验证路径

        Args:
            buckets: 乘区桶数据
            db_damage: 数据库中的最终伤害值（真值）
            damage_type: 伤害类型（常规/剧变/月曜）
            tolerance: 偏差容忍度（默认 0.1%）
            event_id: 事件 ID（用于日志）

        Returns:
            ValidationResult 验证结果
        """
        if damage_type == DamageType.LUNAR:
            return AuditValidator.validate_lunar_damage(
                buckets=buckets,
                db_damage=db_damage,
                tolerance=tolerance,
                event_id=event_id,
            )
        elif damage_type == DamageType.TRANSFORMATIVE:
            return AuditValidator.validate_transformative_damage(
                buckets=buckets,
                db_damage=db_damage,
                tolerance=tolerance,
                event_id=event_id,
            )
        else:
            return AuditValidator.validate_normal_damage(
                buckets=buckets,
                db_damage=db_damage,
                tolerance=tolerance,
                event_id=event_id,
            )
