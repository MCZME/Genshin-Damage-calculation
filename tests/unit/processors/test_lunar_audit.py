"""
月曜反应审计处理器测试用例。

测试内容：
1. DamageType.LUNAR 类型检测
2. 月曜桶结构创建
3. 月曜伤害处理
4. 月曜伤害验证
5. UI 公式生成
"""

import pytest

from core.persistence.processors.audit.types import (
    DamageType,
    DamageTypeContext,
    CharacterContribution,
)
from core.persistence.processors.audit.processor import AuditProcessor
from core.persistence.processors.audit.bucket_processor import create_lunar_buckets
from core.persistence.processors.audit.validator import AuditValidator


class TestLunarDamageType:
    """测试月曜伤害类型检测"""

    def test_detect_lunar_bloom(self):
        """测试月绽放伤害类型检测"""
        damage_type = AuditProcessor.detect_damage_type("月绽放")
        assert damage_type == DamageType.LUNAR

    def test_detect_lunar_charged(self):
        """测试月感电伤害类型检测"""
        damage_type = AuditProcessor.detect_damage_type("月感电")
        assert damage_type == DamageType.LUNAR

    def test_detect_lunar_crystallize(self):
        """测试月结晶伤害类型检测"""
        damage_type = AuditProcessor.detect_damage_type("月结晶")
        assert damage_type == DamageType.LUNAR

    def test_detect_transformative_not_lunar(self):
        """测试剧变反应不被识别为月曜"""
        damage_type = AuditProcessor.detect_damage_type("超载伤害")
        assert damage_type == DamageType.TRANSFORMATIVE

    def test_detect_normal_not_lunar(self):
        """测试常规伤害不被识别为月曜"""
        damage_type = AuditProcessor.detect_damage_type("普通攻击")
        assert damage_type == DamageType.NORMAL


class TestLunarBuckets:
    """测试月曜桶结构"""

    def test_create_lunar_buckets_structure(self):
        """测试月曜桶结构创建"""
        buckets = create_lunar_buckets()

        # 验证 4 个桶
        assert "base_damage" in buckets
        assert "crit" in buckets
        assert "resistance" in buckets
        assert "ascension" in buckets

        # 验证桶数量
        assert len(buckets) == 4

    def test_lunar_base_damage_structure(self):
        """测试基础伤害桶结构"""
        buckets = create_lunar_buckets()
        base_damage = buckets["base_damage"]

        # 验证必要字段
        assert "level_coeff" in base_damage
        assert "reaction_mult" in base_damage
        assert "multiplier" in base_damage
        assert "contributions" in base_damage
        assert "reaction_type" in base_damage

    def test_lunar_ascension_structure(self):
        """测试擢升区桶结构"""
        buckets = create_lunar_buckets()
        ascension = buckets["ascension"]

        # 验证必要字段
        assert "multiplier" in ascension
        assert "bonus_pct" in ascension
        assert "steps" in ascension


class TestLunarProcessing:
    """测试月曜伤害处理"""

    @pytest.fixture
    def lunar_context(self):
        """创建月曜上下文"""
        ctx = DamageTypeContext(
            damage_type=DamageType.LUNAR,
            attack_tag="月绽放伤害",
            level_coeff=1446.0,
            reaction_coeff=1.0,
            elemental_mastery=100.0,
            base_bonus=10.0,
            ascension_bonus=20.0,
            extra_damage=50.0,
        )
        ctx.contributing_characters.append(
            CharacterContribution(
                character_name="哥伦比娅",
                damage_component=100.0,
                weight_percentage=100.0,
            )
        )
        return ctx

    def test_process_lunar_basic(self, lunar_context):
        """测试基础月曜处理"""
        buckets = AuditProcessor.process_lunar(
            damage_type_ctx=lunar_context,
            raw_trail=[],
            frame_snapshot=None,
            target_snapshot=None,
            element_type="DENDRO",
        )

        # 验证反应类型
        assert buckets["base_damage"]["reaction_type"] == "月绽放"

        # 验证等级系数
        assert buckets["base_damage"]["level_coeff"] == 1446.0

        # 验证反应倍率
        assert buckets["base_damage"]["reaction_mult"] == 1.0

        # 验证擢升乘数
        assert buckets["ascension"]["multiplier"] == 1.2

        # 验证角色贡献
        assert len(buckets["base_damage"]["contributions"]) == 1

    def test_process_lunar_with_crit(self, lunar_context):
        """测试月曜暴击处理"""
        raw_trail = [
            {"stat": "暴击乘数", "value": 2.0, "op": "SET", "source": "test"}
        ]
        frame_snapshot = {"stats": {"暴击率": 75.0}}

        buckets = AuditProcessor.process_lunar(
            damage_type_ctx=lunar_context,
            raw_trail=raw_trail,
            frame_snapshot=frame_snapshot,
            target_snapshot=None,
            element_type="DENDRO",
        )

        # 验证暴击乘数
        assert buckets["crit"]["multiplier"] == 2.0

        # 验证暴击率
        assert buckets["crit"]["crit_rate"] == 75.0

    def test_process_lunar_with_resistance(self, lunar_context):
        """测试月曜抗性处理"""
        target_snapshot = {
            "resistance": {"草": 10.0},
            "active_modifiers": [
                {"stat": "草元素抗性", "value": -20.0, "name": "风套"}
            ],
        }

        buckets = AuditProcessor.process_lunar(
            damage_type_ctx=lunar_context,
            raw_trail=[],
            frame_snapshot=None,
            target_snapshot=target_snapshot,
            element_type="DENDRO",
        )

        # 验证抗性处理
        assert "raw_data" in buckets["resistance"]

    def test_process_lunar_with_source_tracking(self, lunar_context):
        """测试月曜审计链来源追踪"""
        raw_trail = [
            {"stat": "月曜反应伤害提升", "value": 20.0, "op": "ADD", "source": "晨星与月的晓歌 (4件套后台)"},
            {"stat": "月曜反应伤害提升", "value": 40.0, "op": "ADD", "source": "晨星与月的晓歌 (4件套满辉)"},
            {"stat": "月曜伤害擢升", "value": 15.0, "op": "ADD", "source": "C1月曜伤害"},
            {"stat": "基础伤害提升", "value": 10.0, "op": "ADD", "source": "基础伤害提升效果"},
        ]

        buckets = AuditProcessor.process_lunar(
            damage_type_ctx=lunar_context,
            raw_trail=raw_trail,
            frame_snapshot=None,
            target_snapshot=None,
            element_type="DENDRO",
        )

        # 验证基础伤害提升来源
        base_bonus_steps = [
            s for s in buckets["base_damage"]["steps"]
            if s["stat"] == "基础伤害提升"
        ]
        assert len(base_bonus_steps) == 1
        assert base_bonus_steps[0]["source"] == "基础伤害提升效果"
        assert base_bonus_steps[0]["value"] == 10.0

        # 验证月曜反应伤害提升来源（多个来源）
        reaction_bonus_steps = [
            s for s in buckets["base_damage"]["steps"]
            if s["stat"] == "月曜反应伤害提升"
        ]
        assert len(reaction_bonus_steps) == 2
        sources = [s["source"] for s in reaction_bonus_steps]
        assert "晨星与月的晓歌 (4件套后台)" in sources
        assert "晨星与月的晓歌 (4件套满辉)" in sources

        # 验证擢升区来源
        ascension_steps = buckets["ascension"]["steps"]
        assert len(ascension_steps) == 1
        assert ascension_steps[0]["source"] == "C1月曜伤害"
        assert ascension_steps[0]["value"] == 15.0


class TestLunarValidation:
    """测试月曜伤害验证"""

    def test_validate_lunar_damage(self):
        """测试月曜伤害验证"""
        buckets = {
            "base_damage": {
                "level_coeff": 1446.0,
                "reaction_mult": 1.0,
                "base_bonus": 0.0,
                "em_bonus_pct": 28.5,  # 6 * 100 / (100 + 2000) * 100
                "reaction_bonus": 0.0,
                "extra_damage": 0.0,
            },
            "crit": {"multiplier": 1.0},
            "resistance": {"multiplier": 0.9},
            "ascension": {"multiplier": 1.0},
        }

        result = AuditValidator.validate_lunar_damage(
            buckets=buckets,
            db_damage=1864.0,  # 预估值
            event_id=1,
        )

        # 验证计算值存在
        assert result.calc_damage > 0

    def test_validate_lunar_with_crit(self):
        """测试月曜暴击伤害验证"""
        buckets = {
            "base_damage": {
                "level_coeff": 1446.0,
                "reaction_mult": 1.0,
                "base_bonus": 0.0,
                "em_bonus_pct": 28.5,
                "reaction_bonus": 0.0,
                "extra_damage": 0.0,
            },
            "crit": {"multiplier": 2.0},  # 暴击
            "resistance": {"multiplier": 0.9},
            "ascension": {"multiplier": 1.2},
        }

        result = AuditValidator.validate_lunar_damage(
            buckets=buckets,
            db_damage=4000.0,
            event_id=2,
        )

        # 验证暴击乘数生效
        assert result.calc_damage > 2000  # 暴击后应大于 2000

    def test_validate_lunar_multi_component_two(self):
        """测试两组分加权求和验证"""
        # 使用 _component_buckets（多组分模式）
        buckets = {
            "base_damage": {
                "contributions": [],  # 单组分逻辑不走这里
            },
            "_component_buckets": [
                {"damage_value": 100.0, "character_name": "角色A"},
                {"damage_value": 60.0, "character_name": "角色B"},
            ],
            "crit": {"multiplier": 1.0},
            "resistance": {"multiplier": 1.0},
            "ascension": {"multiplier": 1.0},
        }

        result = AuditValidator.validate_lunar_damage(
            buckets=buckets,
            db_damage=130.0,  # 最高(100) + 次高/2(60/2=30) = 130
            event_id=3,
        )

        # 验证加权求和结果
        assert result.calc_damage == 130.0
        assert result.passed is True

    def test_validate_lunar_multi_component_three(self):
        """测试三组分加权求和验证"""
        buckets = {
            "base_damage": {
                "contributions": [],
            },
            "_component_buckets": [
                {"damage_value": 100.0, "character_name": "角色A"},
                {"damage_value": 60.0, "character_name": "角色B"},
                {"damage_value": 24.0, "character_name": "角色C"},
            ],
            "crit": {"multiplier": 1.0},
            "resistance": {"multiplier": 1.0},
            "ascension": {"multiplier": 1.0},
        }

        result = AuditValidator.validate_lunar_damage(
            buckets=buckets,
            db_damage=132.0,  # 最高(100) + 次高/2(30) + 其余/12(24/12=2) = 132
            event_id=4,
        )

        # 验证加权求和结果
        assert result.calc_damage == 132.0
        assert result.passed is True

    def test_validate_lunar_multi_component_many(self):
        """测试多组分（4+）加权求和验证"""
        buckets = {
            "base_damage": {
                "contributions": [],
            },
            "_component_buckets": [
                {"damage_value": 100.0, "character_name": "角色A"},
                {"damage_value": 80.0, "character_name": "角色B"},
                {"damage_value": 60.0, "character_name": "角色C"},
                {"damage_value": 40.0, "character_name": "角色D"},
            ],
            "crit": {"multiplier": 1.0},
            "resistance": {"multiplier": 1.0},
            "ascension": {"multiplier": 1.0},
        }

        # 最高(100) + 次高/2(40) + 其余/12((60+40)/12≈8.33) = 148.33
        expected = 100 + 80 / 2 + (60 + 40) / 12

        result = AuditValidator.validate_lunar_damage(
            buckets=buckets,
            db_damage=expected,
            event_id=5,
        )

        # 验证加权求和结果
        assert abs(result.calc_damage - expected) < 0.01
        assert result.passed is True

    def test_validate_lunar_contributions_mode(self):
        """测试使用 contributions 数据的多组分验证"""
        buckets = {
            "base_damage": {
                "contributions": [
                    {"damage_component": 100.0, "character_name": "角色A"},
                    {"damage_component": 60.0, "character_name": "角色B"},
                ],
            },
            "crit": {"multiplier": 1.0},
            "resistance": {"multiplier": 1.0},
            "ascension": {"multiplier": 1.0},
        }

        result = AuditValidator.validate_lunar_damage(
            buckets=buckets,
            db_damage=130.0,
            event_id=6,
        )

        # 验证加权求和结果
        assert result.calc_damage == 130.0
        assert result.passed is True

    def test_validate_lunar_single_component_fallback(self):
        """测试单组分时回退到原有验证逻辑

        [V23.0] 修复公式后：
        核心基础伤害 = 等级系数 × 反应倍率 × (1 + 基础伤害提升/100)
        反应提升 = 1 + 月曜精通加成 + 月曜反应伤害提升
        基础伤害区 = 核心基础伤害 × 反应提升 + 附加伤害
        """
        buckets = {
            "base_damage": {
                "level_coeff": 1446.0,
                "reaction_mult": 1.0,
                "base_bonus": 0.0,
                "em_bonus_pct": 28.5,
                "reaction_bonus": 0.0,
                "extra_damage": 0.0,
                "contributions": [
                    {"damage_component": 100.0, "character_name": "角色A"},
                ],
            },
            "crit": {"multiplier": 1.0},
            "resistance": {"multiplier": 1.0},
            "ascension": {"multiplier": 1.0},
        }

        result = AuditValidator.validate_lunar_damage(
            buckets=buckets,
            db_damage=1858.0,
            event_id=7,
        )

        # 单组分应使用公式计算而非加权求和
        # 计算：
        # 核心基础伤害 = 1446 * 1.0 * (1 + 0) = 1446
        # 反应提升 = 1 + 0.285 + 0 = 1.285
        # 基础伤害区 = 1446 * 1.285 + 0 = 1858.11
        assert result.calc_damage > 1850


class TestCharacterContribution:
    """测试角色贡献数据结构"""

    def test_contribution_creation(self):
        """测试角色贡献创建"""
        contrib = CharacterContribution(
            character_name="哥伦比娅",
            damage_component=100.0,
            weight_percentage=100.0,
        )

        assert contrib.character_name == "哥伦比娅"
        assert contrib.damage_component == 100.0
        assert contrib.weight_percentage == 100.0

    def test_contribution_in_context(self):
        """测试角色贡献在上下文中"""
        ctx = DamageTypeContext(
            damage_type=DamageType.LUNAR,
            attack_tag="月绽放伤害",
        )

        ctx.contributing_characters.append(
            CharacterContribution(
                character_name="哥伦比娅",
                damage_component=100.0,
                weight_percentage=50.0,
            )
        )
        ctx.contributing_characters.append(
            CharacterContribution(
                character_name="菲林斯",
                damage_component=60.0,
                weight_percentage=30.0,
            )
        )

        assert len(ctx.contributing_characters) == 2


class TestLunarFormulaGeneration:
    """测试月曜公式生成"""

    def test_build_lunar_base_formula(self):
        """测试月曜基础伤害公式生成"""
        from ui.components.analysis.bottom_panel.formulas import build_lunar_base

        bucket_data = {
            "reaction_type": "月绽放",
            "reaction_mult": 1.0,
            "base_bonus": 10.0,
            "em_bonus_pct": 28.5,
            "reaction_bonus": 0.0,
            "extra_damage": 0.0,
            "multiplier": 1.385,
            "contributions": [],
        }

        result = build_lunar_base(bucket_data, "LUNAR_BASE", "CYAN_200")

        # 验证公式生成
        assert result.total_text == "1.39"
        assert len(result.parts) > 0

    def test_build_lunar_with_contributions(self):
        """测试带角色贡献的公式生成"""
        from ui.components.analysis.bottom_panel.formulas import build_lunar_base

        bucket_data = {
            "reaction_type": "月感电",
            "reaction_mult": 1.8,
            "base_bonus": 0.0,
            "em_bonus_pct": 30.0,
            "reaction_bonus": 0.0,
            "extra_damage": 0.0,
            "multiplier": 2.34,
            "contributions": [
                {"character_name": "菲林斯", "damage_component": 100.0, "weight_percentage": 50.0},
                {"character_name": "伊涅芙", "damage_component": 60.0, "weight_percentage": 30.0},
            ],
        }

        result = build_lunar_base(bucket_data, "LUNAR_BASE", "CYAN_200")

        # 验证角色贡献展示
        assert len(result.parts_line2) > 0

    def test_build_ascension_formula(self):
        """测试擢升区公式生成"""
        from ui.components.analysis.bottom_panel.formulas import build_ascension

        bucket_data = {
            "multiplier": 1.2,
            "bonus_pct": 20.0,
        }

        result = build_ascension(bucket_data, "ASCENSION", "PURPLE_200")

        # 验证公式生成
        assert result.total_text == "1.20"
        assert len(result.parts) > 0

    def test_build_ascension_zero(self):
        """测试无加成的擢升区"""
        from ui.components.analysis.bottom_panel.formulas import build_ascension

        bucket_data = {
            "multiplier": 1.0,
            "bonus_pct": 0.0,
        }

        result = build_ascension(bucket_data, "ASCENSION", "PURPLE_200")

        # 验证无加成时显示 1.00
        assert result.total_text == "1.00"
