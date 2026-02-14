import pytest
from core.mechanics.aura import AuraManager, Element
from core.systems.contract.reaction import ElementalReactionType, ReactionCategory

class TestAuraTheoryRigorous:
    """
    高等元素论全反应严谨性物理实验室 - 正式集成版
    """

    @pytest.fixture
    def manager(self):
        return AuraManager()

    # --- 1. 增幅反应 (蒸发/融化) 碰撞实验室 ---

    @pytest.mark.parametrize("atk_el, atk_u, target_el, target_u, expected_rem_target_g, expected_type", [
        (Element.HYDRO, 1.0, Element.PYRO, 1.0, 0.0, ElementalReactionType.VAPORIZE),
        (Element.PYRO, 1.0, Element.HYDRO, 1.0, 0.3, ElementalReactionType.VAPORIZE),
        (Element.PYRO, 1.0, Element.CRYO, 1.0, 0.0, ElementalReactionType.MELT),
        (Element.CRYO, 1.0, Element.PYRO, 1.0, 0.3, ElementalReactionType.MELT),
    ])
    def test_amplifying_clash(self, manager, atk_el, atk_u, target_el, target_u, expected_rem_target_g, expected_type):
        manager.apply_element(target_el, target_u)
        results = manager.apply_element(atk_el, atk_u)
        
        assert any(r.reaction_type == expected_type for r in results)
        assert all(r.category == ReactionCategory.AMPLIFYING for r in results if r.reaction_type == expected_type)
        
        if expected_rem_target_g > 0:
            assert manager.auras[0].current_gauge == pytest.approx(expected_rem_target_g)
        else:
            assert len(manager.auras) == 0

    # --- 2. 剧变与激化实验室 ---

    @pytest.mark.parametrize("atk_el, target_el, expected_type", [
        (Element.ELECTRO, Element.PYRO, ElementalReactionType.OVERLOAD),
        (Element.CRYO, Element.ELECTRO, ElementalReactionType.SUPERCONDUCT),
        (Element.HYDRO, Element.DENDRO, ElementalReactionType.BLOOM),
        (Element.ELECTRO, Element.DENDRO, ElementalReactionType.QUICKEN),
    ])
    def test_standard_reactions(self, manager, atk_el, target_el, expected_type):
        manager.apply_element(target_el, 1.0)
        results = manager.apply_element(atk_el, 1.0)
        
        assert any(r.reaction_type == expected_type for r in results)
        assert len(manager.auras) == 0

    # --- 3. 扩散(Swirl)专项实验室 - 多元素共存 ---

    def test_ec_double_swirl(self, manager):
        """测试感电态双重扩散：验证 DTO 中的 target_element 识别"""
        manager.apply_element(Element.HYDRO, 1.0)
        manager.apply_element(Element.ELECTRO, 1.0)
        manager.is_electro_charged = True
        
        results = manager.apply_element(Element.ANEMO, 1.0)
        
        swirl_targets = [r.target_element for r in results if r.reaction_type == ElementalReactionType.SWIRL]
        assert Element.HYDRO in swirl_targets
        assert Element.ELECTRO in swirl_targets
        assert all(r.category == ReactionCategory.TRANSFORMATIVE for r in results)

    def test_frozen_underlying_swirl(self, manager):
        """测试冻结藏水扩散"""
        manager.apply_element(Element.HYDRO, 1.0)
        manager.apply_element(Element.CRYO, 1.0)
        manager.apply_element(Element.HYDRO, 2.0)
        
        results = manager.apply_element(Element.ANEMO, 2.0)
        
        reaction_types = [r.reaction_type for r in results]
        assert ElementalReactionType.SWIRL in reaction_types
        
        # 验证扩散的目标包含特殊状态和常规附着
        targets = [r.target_element for r in results]
        assert Element.FROZEN in targets
        assert Element.HYDRO in targets

    # --- 4. 激化进阶实验室 ---

    def test_swirl_priority_with_quicken(self, manager):
        """测试扩散优先级：验证激化态不反应"""
        manager.apply_element(Element.DENDRO, 1.0)
        manager.apply_element(Element.ELECTRO, 1.0)
        manager.apply_element(Element.ELECTRO, 1.0) # 藏雷
        
        results = manager.apply_element(Element.ANEMO, 1.0)
        
        # 应该只有一个扩散反应（针对藏雷），没有针对激元素的反应
        swirls = [r for r in results if r.reaction_type == ElementalReactionType.SWIRL]
        assert len(swirls) == 1
        assert swirls[0].target_element == Element.ELECTRO

    # --- 5. 复杂特殊状态实验室 ---

    def test_shatter_melt_combination(self, manager):
        manager.apply_element(Element.HYDRO, 1.0)
        manager.apply_element(Element.CRYO, 1.0)
        
        manager.apply_element(Element.GEO, 1.0) # 碎冰
        results = manager.apply_element(Element.PYRO, 0.5) # 融化
        
        assert any(r.reaction_type == ElementalReactionType.MELT for r in results)
        assert manager.frozen_gauge.current_gauge == pytest.approx(0.1)

    # --- 6. 极限与边界测试 ---

    def test_gauge_refill_stronger(self, manager):
        manager.apply_element(Element.PYRO, 1.0)
        manager.apply_element(Element.PYRO, 2.0)
        assert manager.auras[0].current_gauge == pytest.approx(1.6)
        assert manager.auras[0].decay_rate == pytest.approx(1.6/12.0)

    def test_micro_gauge_cleanup(self, manager):
        manager.apply_element(Element.PYRO, 1.0)
        manager.auras[0].current_gauge = 0.00001
        manager.update(1/60)
        assert len(manager.auras) == 0
