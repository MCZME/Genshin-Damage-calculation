"""[V13.0] 伤害审计处理器

负责将离散的审计记录聚合为标准的乘区模型。

[V12.0] 支持两种伤害路径：
- 常规伤害路径：6 桶模型（CORE + BONUS + CRIT + REACT + DEF + RES）
- 剧变反应路径：4 桶模型
"""
from __future__ import annotations
from typing import Any

from .types import DomainValues, DamageTypeContext
from .constants import BUCKET_MAP, SOURCE_TYPE_MAP
from .bucket_processor import (
    create_empty_buckets,
    create_transformative_buckets,
    classify_trail_entry,
    inject_frame_snapshot,
    aggregate_buckets,
)
from .domain_calculator import (
    get_source_type,
    group_steps_by_source,
    calculate_domains,
)


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
        is_crit: bool = False
    ) -> dict[str, Any]:
        """
        [V13.0] 聚合原始审计链为 6 大乘区大类。

        Args:
            raw_trail: 审计链 [S] 项（脱水存储的动态 Buff、技能倍率、随机暴击判定）
            frame_snapshot: 帧快照 [R] 项（基础属性、面板百分比、等级、抗性）
            is_crit: 是否暴击（用于兼容旧逻辑）

        Returns:
            聚合后的 6 大乘区数据结构
        """
        buckets = create_empty_buckets()

        # 1. 遍历审计链进行归类（填充 steps）
        for entry in raw_trail:
            classify_trail_entry(entry, buckets)

        # 2. 从帧快照获取基础属性并构建 scaling_info（需要在 aggregate 之前）
        inject_frame_snapshot(frame_snapshot, buckets)

        # 3. 内部合算逻辑
        aggregate_buckets(buckets, is_crit)

        return buckets

    @staticmethod
    def process_transformative(
        damage_type_ctx: DamageTypeContext,
        raw_trail: list[dict[str, Any]],
        frame_snapshot: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """[V12.0] 处理剧变反应审计数据

        剧变反应使用 4 桶模型：
        - level_coeff: 等级系数
        - reaction_coeff: 反应系数
        - em_bonus: 精通加成
        - resistance: 抗性区

        Args:
            damage_type_ctx: 伤害类型上下文
            raw_trail: 审计链
            frame_snapshot: 帧快照

        Returns:
            剧变反应 4 桶数据结构
        """
        buckets = create_transformative_buckets()

        # 1. 填充等级系数
        buckets["level_coeff"]["value"] = damage_type_ctx.level_coeff

        # 2. 填充反应系数
        buckets["reaction_coeff"]["value"] = damage_type_ctx.reaction_coeff
        buckets["reaction_coeff"]["steps"].append({
            "stat": "反应系数",
            "value": damage_type_ctx.reaction_coeff,
            "op": "SET",
            "source": damage_type_ctx.attack_tag
        })

        # 3. 计算精通加成
        em = damage_type_ctx.elemental_mastery
        em_bonus_pct = (16 * em) / (em + 2000) * 100 if em > 0 else 0.0
        special_bonus = damage_type_ctx.special_bonus
        total_em_bonus = 1 + em_bonus_pct / 100 + special_bonus / 100

        buckets["em_bonus"]["em"] = em
        buckets["em_bonus"]["em_bonus_pct"] = em_bonus_pct
        buckets["em_bonus"]["special_bonus"] = special_bonus
        buckets["em_bonus"]["value"] = total_em_bonus

        if em > 0:
            buckets["em_bonus"]["steps"].append({
                "stat": "精通转化",
                "value": em_bonus_pct,
                "op": "ADD",
                "source": f"元素精通 {em:.0f}"
            })

        if special_bonus > 0:
            buckets["em_bonus"]["steps"].append({
                "stat": "特殊加成",
                "value": special_bonus,
                "op": "ADD",
                "source": "装备/天赋"
            })

        # 4. 处理抗性区（从审计链提取）
        for entry in raw_trail:
            stat = entry.get("stat", "")
            val = entry.get("value", 0.0)
            source = entry.get("source", "Unknown")

            if stat == "抗性区系数":
                buckets["resistance"]["multiplier"] = val
                buckets["resistance"]["steps"].append({
                    "stat": stat,
                    "value": val,
                    "op": "SET",
                    "source": source
                })
            elif stat == "减抗%":
                buckets["resistance"]["res_reduction_pct"] += val
                buckets["resistance"]["steps"].append({
                    "stat": stat,
                    "value": val,
                    "op": "ADD",
                    "source": source
                })
            elif stat == "抗性穿透%":
                buckets["resistance"]["res_penetration_pct"] += val
                buckets["resistance"]["steps"].append({
                    "stat": stat,
                    "value": val,
                    "op": "ADD",
                    "source": source
                })

        # 5. 从帧快照获取目标抗性信息
        if frame_snapshot:
            # 获取目标抗性
            target_res = frame_snapshot.get("target_resistance", 0.0)
            if target_res != 0:
                buckets["resistance"]["base_resistance"] = target_res
                buckets["resistance"]["final_resistance"] = (
                    target_res / 100.0
                    - buckets["resistance"]["res_reduction_pct"] / 100.0
                    - buckets["resistance"]["res_penetration_pct"] / 100.0
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