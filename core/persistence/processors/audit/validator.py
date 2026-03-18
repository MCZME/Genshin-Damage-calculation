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
        bonus_pct = core_bucket.get("bonus_pct", 0.0)
        flat = core_bucket.get("flat", 0.0)

        if scaling_info:
            base_dmg = sum(
                info.get("total_val", 0) * info.get("skill_mult", 0) / 100
                for info in scaling_info
            )
        else:
            base_dmg = core_bucket.get("total", 0) * core_bucket.get("multiplier", 1.0)

        if independent_pct > 0:
            base_dmg *= 1 + independent_pct / 100
        if bonus_pct > 0:
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
