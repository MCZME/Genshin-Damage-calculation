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

    # 剧变反应攻击标签
    TRANSFORMATIVE_TAGS = (
        "超载伤害",
        "感电伤害",
        "超导伤害",
        "碎冰伤害",
        "扩散",
        "超绽放伤害",
        "烈绽放伤害",
    )

    @staticmethod
    def detect_damage_type(attack_tag: str) -> DamageType:
        """[V15.0] 从攻击标签检测伤害类型

        Args:
            attack_tag: 攻击标签（如 "超载伤害", "普通攻击"）

        Returns:
            DamageType 枚举值
        """
        if any(tag in attack_tag for tag in AuditProcessor.TRANSFORMATIVE_TAGS):
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

        Args:
            buckets: 乘区桶数据
            db_damage: 数据库中的最终伤害值（真值）
            damage_type: 伤害类型（常规/剧变）
            tolerance: 偏差容忍度（默认 0.1%）
            event_id: 事件 ID（用于日志）

        Returns:
            ValidationResult 验证结果
        """
        if damage_type == DamageType.TRANSFORMATIVE:
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
