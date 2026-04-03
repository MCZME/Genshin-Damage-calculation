"""[V15.0] 审计数据验证器

负责验证审计链数据的完整性和一致性。
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValidationResult:
    """验证结果"""

    passed: bool  # 是否通过
    calc_damage: float = 0.0  # 计算值
    db_damage: float = 0.0  # 数据库值
    deviation_pct: float = 0.0  # 偏差百分比
    deviation_direction: str = ""  # "high" | "low" | "equal"
    errors: list[str] = field(default_factory=list)  # 错误信息列表


# 默认偏差容忍度（0.1%）
DEFAULT_TOLERANCE = 0.001


class AuditValidator:
    """审计数据验证器"""

    @staticmethod
    def validate_normal_damage(
        buckets: dict[str, Any],
        db_damage: float,
        tolerance: float = DEFAULT_TOLERANCE,
        event_id: int | None = None,
    ) -> ValidationResult:
        """验证常规伤害

        公式：最终伤害 = core_dmg × bonus × crit × reaction × defense × resistance
        """
        from .coefficient_calculator import (
            calculate_defense_coefficient,
            calculate_resistance_coefficient,
        )

        errors: list[str] = []

        # 计算核心伤害
        core_dmg = AuditValidator._calculate_core_damage(buckets.get("core_dmg", {}))

        # 获取各乘区系数
        bonus_mult = buckets.get("bonus", {}).get("multiplier", 1.0)
        crit_mult = buckets.get("crit", {}).get("multiplier", 1.0)
        reaction_mult = buckets.get("reaction", {}).get("multiplier", 1.0)

        # 防御区/抗性区：优先使用 raw_data 计算
        def_bucket = buckets.get("defense", {})
        def_raw = def_bucket.get("raw_data", {})
        def_mult = (
            calculate_defense_coefficient(def_raw)
            if def_raw
            else def_bucket.get("multiplier", 1.0)
        )

        res_bucket = buckets.get("resistance", {})
        res_raw = res_bucket.get("raw_data", {})
        res_mult = (
            calculate_resistance_coefficient(res_raw)
            if res_raw
            else res_bucket.get("multiplier", 1.0)
        )

        # 计算最终伤害
        calc_damage = (
            core_dmg * bonus_mult * crit_mult * reaction_mult * def_mult * res_mult
        )

        return AuditValidator._perform_validation(
            calc_damage=calc_damage,
            db_damage=db_damage,
            tolerance=tolerance,
            event_id=event_id,
            errors=errors,
        )

    @staticmethod
    def validate_transformative_damage(
        buckets: dict[str, Any],
        db_damage: float,
        tolerance: float = DEFAULT_TOLERANCE,
        event_id: int | None = None,
    ) -> ValidationResult:
        """验证剧变反应伤害

        [V16.0] 更新为 3 桶模型
        公式：伤害 = 等级系数 × 反应乘区 × 抗性区
        其中反应乘区 = 反应系数 × (1 + 精通收益 + 特殊加成)
        """
        from .coefficient_calculator import calculate_resistance_coefficient

        level_coeff = buckets.get("level_coeff", {}).get("value", 0.0)

        # [V16.0] 从 reaction 桶获取反应乘区数据
        reaction_bucket = buckets.get("reaction", {})
        reaction_mult = reaction_bucket.get("multiplier", 1.0)

        res_bucket = buckets.get("resistance", {})
        res_raw = res_bucket.get("raw_data", {})
        res_mult = (
            calculate_resistance_coefficient(res_raw)
            if res_raw
            else res_bucket.get("multiplier", 1.0)
        )

        calc_damage = level_coeff * reaction_mult * res_mult

        return AuditValidator._perform_validation(
            calc_damage=calc_damage,
            db_damage=db_damage,
            tolerance=tolerance,
            event_id=event_id,
            errors=[],
        )

    @staticmethod
    def _calculate_core_damage(core_bucket: dict) -> float:
        """计算核心伤害"""
        scaling_info = core_bucket.get("scaling_info", [])
        independent_pct = core_bucket.get("independent_pct", 0.0)
        bonus_pct = core_bucket.get("bonus_pct", 0.0)  # 严格对齐规范：倍率加值%
        flat = core_bucket.get("flat", 0.0)

        if scaling_info:
            # 根据 V2.5 规范：最终倍率 = 技能倍率% * (1 + 独立乘区%/100) + 倍率加值%
            base_dmg = sum(
                info.get("total_val", 0)* (info.get("skill_mult", 0) * (1.0 + independent_pct / 100.0)+ bonus_pct) / 100 for info in scaling_info
            )
        else:
            # 兼容旧逻辑
            base_dmg = core_bucket.get("total", 0) * core_bucket.get("multiplier", 1.0)
            if independent_pct > 0:
                base_dmg *= 1 + independent_pct / 100
            if bonus_pct > 0:
                # 注：在旧的非 scaling_info 路径中，暂维持乘法逻辑以兼容
                base_dmg *= 1 + bonus_pct / 100

        return base_dmg + flat

    @staticmethod
    def _perform_validation(
        calc_damage: float,
        db_damage: float,
        tolerance: float,
        event_id: int | None,
        errors: list[str],
    ) -> ValidationResult:
        """执行验证"""
        from core.logger import get_ui_logger

        # 数据库值为空时跳过验证
        if not db_damage or db_damage == 0:
            return ValidationResult(
                passed=True,
                calc_damage=calc_damage,
                db_damage=db_damage,
            )

        # 计算偏差
        deviation = abs(calc_damage - db_damage)
        deviation_pct = (deviation / db_damage) * 100

        # 偏差方向
        if calc_damage > db_damage:
            direction = "high"
        elif calc_damage < db_damage:
            direction = "low"
        else:
            direction = "equal"

        # 判定是否通过
        passed = deviation_pct <= tolerance * 100

        # 输出日志
        event_tag = f"Event#{event_id}" if event_id else "Unknown"
        status_icon = "✓" if passed else "✗"

        log_msg = f"[验证] {event_tag}: 计算值={calc_damage:,.2f}, 数据库={db_damage:,.2f}, 偏差={deviation_pct:.2f}% {status_icon}"

        logger = get_ui_logger()
        if passed:
            logger.log_info(log_msg)
        else:
            logger.log_warning(log_msg)
            errors.append(f"偏差超标: {deviation_pct:.2f}%")

        return ValidationResult(
            passed=passed,
            calc_damage=calc_damage,
            db_damage=db_damage,
            deviation_pct=deviation_pct,
            deviation_direction=direction,
            errors=errors,
        )

    @staticmethod
    def validate_lunar_damage(
        buckets: dict[str, Any],
        db_damage: float,
        tolerance: float = DEFAULT_TOLERANCE,
        event_id: int | None = None,
    ) -> ValidationResult:
        """验证月曜反应伤害

        [V17.0] 新增
        [V19.0] 支持多组分加权求和验证

        公式：最终伤害 = 基础伤害 × 暴击区 × 抗性区 × 擢升区

        其中基础伤害 = (等级系数 × 反应倍率 + 附加伤害) × (1 + 基础提升 + 月曜精通加成 + 反应加成)

        多组分加权求和公式：
        最终伤害 = 最高组 + 次高组÷2 + 其余组之和÷12
        """
        # 检查是否为多组分模式
        component_buckets = buckets.get("_component_buckets", [])
        contributions = buckets.get("base_damage", {}).get("contributions", [])

        if component_buckets and len(component_buckets) > 1:
            # 多组分: 使用 _component_buckets 数据加权求和
            return AuditValidator._validate_multi_component_lunar(
                component_buckets=component_buckets,
                buckets=buckets,
                db_damage=db_damage,
                tolerance=tolerance,
                event_id=event_id,
            )
        elif contributions and len(contributions) > 1:
            # 多组分: 使用 contributions 数据加权求和
            return AuditValidator._validate_contributions_lunar(
                contributions=contributions,
                db_damage=db_damage,
                tolerance=tolerance,
                event_id=event_id,
            )
        else:
            # 单组分: 原有逻辑
            return AuditValidator._validate_single_component_lunar(
                buckets=buckets,
                db_damage=db_damage,
                tolerance=tolerance,
                event_id=event_id,
            )

    @staticmethod
    def _validate_single_component_lunar(
        buckets: dict[str, Any],
        db_damage: float,
        tolerance: float,
        event_id: int | None,
    ) -> ValidationResult:
        """单组分月曜伤害验证

        公式：最终伤害 = 基础伤害 × 暴击区 × 抗性区 × 擢升区
        """
        from .coefficient_calculator import calculate_resistance_coefficient

        # 计算基础伤害
        base_bucket = buckets.get("base_damage", {})
        level_coeff = base_bucket.get("level_coeff", 0.0)
        reaction_mult = base_bucket.get("reaction_mult", 1.0)
        base_bonus = base_bucket.get("base_bonus", 0.0)
        em_bonus_pct = base_bucket.get("em_bonus_pct", 0.0)
        reaction_bonus = base_bucket.get("reaction_bonus", 0.0)
        extra_damage = base_bucket.get("extra_damage", 0.0)

        # 基础伤害 = 等级系数 × 反应倍率 × (1 + 基础提升 + 月曜精通 + 反应加成) + 附加伤害
        core_damage = level_coeff * reaction_mult * (
            1 + base_bonus / 100 + em_bonus_pct / 100 + reaction_bonus / 100
        ) + extra_damage

        # 暴击区
        crit_mult = buckets.get("crit", {}).get("multiplier", 1.0)

        # 抗性区
        res_bucket = buckets.get("resistance", {})
        res_raw = res_bucket.get("raw_data", {})
        res_mult = (
            calculate_resistance_coefficient(res_raw)
            if res_raw
            else res_bucket.get("multiplier", 1.0)
        )

        # 擢升区
        ascension_mult = buckets.get("ascension", {}).get("multiplier", 1.0)

        # 计算最终伤害
        calc_damage = core_damage * crit_mult * res_mult * ascension_mult

        return AuditValidator._perform_validation(
            calc_damage=calc_damage,
            db_damage=db_damage,
            tolerance=tolerance,
            event_id=event_id,
            errors=[],
        )

    @staticmethod
    def _validate_multi_component_lunar(
        component_buckets: list[dict],
        buckets: dict[str, Any],
        db_damage: float,
        tolerance: float,
        event_id: int | None,
    ) -> ValidationResult:
        """多组分月曜伤害验证（使用 _component_buckets）

        从各组分的 damage_value 提取伤害值，进行加权求和后验证。

        Args:
            component_buckets: 组分桶列表，每个包含 damage_value 等字段
            buckets: 完整桶数据（用于可能的扩展验证）
            db_damage: 数据库真值
            tolerance: 偏差容忍度
            event_id: 事件 ID
        """
        # 提取各组分的伤害值
        damages = [cb.get("damage_value", 0.0) for cb in component_buckets]

        # 加权求和
        calc_damage = AuditValidator._calculate_weighted_damage(damages)

        return AuditValidator._perform_validation(
            calc_damage=calc_damage,
            db_damage=db_damage,
            tolerance=tolerance,
            event_id=event_id,
            errors=[],
        )

    @staticmethod
    def _validate_contributions_lunar(
        contributions: list[dict],
        db_damage: float,
        tolerance: float,
        event_id: int | None,
    ) -> ValidationResult:
        """多组分月曜伤害验证（使用 contributions）

        从各角色贡献的 damage_component 提取伤害值，进行加权求和后验证。

        Args:
            contributions: 角色贡献列表，每个包含 damage_component 字段
            db_damage: 数据库真值
            tolerance: 偏差容忍度
            event_id: 事件 ID
        """
        # 提取各组分的伤害值
        damages = [c.get("damage_component", 0.0) for c in contributions]

        # 加权求和
        calc_damage = AuditValidator._calculate_weighted_damage(damages)

        return AuditValidator._perform_validation(
            calc_damage=calc_damage,
            db_damage=db_damage,
            tolerance=tolerance,
            event_id=event_id,
            errors=[],
        )

    @staticmethod
    def _calculate_weighted_damage(damages: list[float]) -> float:
        """加权求和计算月曜伤害

        公式：最终伤害 = 最高 + 次高÷2 + 其余之和÷12

        Args:
            damages: 各组分伤害值列表

        Returns:
            加权求和后的最终伤害
        """
        if not damages:
            return 0.0

        sorted_damages = sorted(damages, reverse=True)

        if len(sorted_damages) == 1:
            return sorted_damages[0]
        elif len(sorted_damages) == 2:
            return sorted_damages[0] + sorted_damages[1] / 2
        else:
            return sorted_damages[0] + sorted_damages[1] / 2 + sum(sorted_damages[2:]) / 12
