import pytest
from core.mechanics.new_aura import NewAuraManager, Element, Gauge

class TestAuraTheoryRigorous:
    """
    高等元素论全反应严谨性物理实验室 - 增强版
    """

    @pytest.fixture
    def manager(self):
        return NewAuraManager()

    # --- 1. 增幅反应 (蒸发/融化) 碰撞实验室 ---

    @pytest.mark.parametrize("atk_el, atk_u, target_el, target_u, expected_rem_target_g, reaction_name", [
        (Element.HYDRO, 1.0, Element.PYRO, 1.0, 0.0, "蒸发"),
        (Element.PYRO, 1.0, Element.HYDRO, 1.0, 0.3, "蒸发"),
        (Element.PYRO, 1.0, Element.CRYO, 1.0, 0.0, "融化"),
        (Element.CRYO, 1.0, Element.PYRO, 1.0, 0.3, "融化"),
    ])
    def test_amplifying_clash(self, manager, atk_el, atk_u, target_el, target_u, expected_rem_target_g, reaction_name):
        manager.apply_element(target_el, target_u)
        results = manager.apply_element(atk_el, atk_u)
        assert any(r.name == reaction_name for r in results)
        if expected_rem_target_g > 0:
            assert manager.auras[0].current_gauge == pytest.approx(expected_rem_target_g)
        else:
            assert len(manager.auras) == 0

    # --- 2. 剧变与激化实验室 ---

    @pytest.mark.parametrize("atk_el, target_el, reaction_name", [
        (Element.ELECTRO, Element.PYRO, "超载"),
        (Element.CRYO, Element.ELECTRO, "超导"),
        (Element.HYDRO, Element.DENDRO, "绽放"),
        (Element.ELECTRO, Element.DENDRO, "原激化"),
    ])
    def test_standard_reactions(self, manager, atk_el, target_el, reaction_name):
        manager.apply_element(target_el, 1.0)
        results = manager.apply_element(atk_el, 1.0)
        assert any(r.name == reaction_name for r in results)
        assert len(manager.auras) == 0

    # --- 3. 扩散(Swirl)专项实验室 - 多元素共存 ---

    def test_ec_double_swirl(self, manager):
        """测试感电态双重扩散：1U风同时消耗水和雷"""
        # 1. 构造感电态 (水雷共存)
        manager.apply_element(Element.HYDRO, 1.0) # 0.8GU
        manager.apply_element(Element.ELECTRO, 1.0) # 0.8GU
        manager.is_electro_charged = True
        
        # 2. 1U 风攻击 (tax=0.5)
        # 预期：消耗 0.5GU 水 和 0.5GU 雷。剩余各 0.3GU。
        results = manager.apply_element(Element.ANEMO, 1.0)
        
        swirl_names = [r.target_element for r in results if r.name == "扩散"]
        assert Element.HYDRO in swirl_names
        assert Element.ELECTRO in swirl_names
        
        h_gauge = next(a for a in manager.auras if a.element == Element.HYDRO)
        e_gauge = next(a for a in manager.auras if a.element == Element.ELECTRO)
        assert h_gauge.current_gauge == pytest.approx(0.3)
        assert e_gauge.current_gauge == pytest.approx(0.3)

    def test_frozen_underlying_swirl(self, manager):
        """测试冻结藏水扩散：风优先扩散冻元素，剩余风量扩散藏水"""
        # 1. 产生 1.6GU 冻元素
        manager.apply_element(Element.HYDRO, 1.0)
        manager.apply_element(Element.CRYO, 1.0)
        # 2. 补 2U 藏水 (1.6GU)
        manager.apply_element(Element.HYDRO, 2.0)
        
        assert manager.frozen_gauge is not None
        assert len(manager.auras) == 1 # 藏水
        
        # 3. 2U 强风攻击 (tax=0.5)
        # a. 强风打冻：消耗 2U * 0.5 = 1.0GU 冻。冻剩余 1.6 - 1.0 = 0.6GU。
        # b. 剩余风量 (无损) 继续打藏水：消耗 2U * 0.5 = 1.0GU 水。水剩余 1.6 - 1.0 = 0.6GU。
        # 注：风在扩散时通常是不减损 rem_u 的（除非特定机制），但在本项目逻辑中按 rem_u 衰减更严谨。
        # 这里验证是否触发了两次扩散结果。
        results = manager.apply_element(Element.ANEMO, 2.0)
        
        reaction_targets = [r.target_element for r in results if r.name == "扩散"]
        assert Element.FROZEN in reaction_targets
        assert Element.HYDRO in reaction_targets
        
        assert manager.frozen_gauge.current_gauge == pytest.approx(0.6)
        assert manager.auras[0].current_gauge == pytest.approx(0.6)

    def test_swirl_priority_with_quicken(self, manager):
        """测试扩散优先级：激化态不与风反应，风只与藏元素反应"""
        # 1. 产生激化态
        manager.apply_element(Element.DENDRO, 1.0)
        manager.apply_element(Element.ELECTRO, 1.0)
        # 2. 补藏雷 1U (0.8GU)
        manager.apply_element(Element.ELECTRO, 1.0)
        
        assert manager.quicken_gauge is not None
        assert len(manager.auras) == 1 # 藏雷
        
        # 3. 施加 1U 风
        # 预期：风不与“激元素”反应，仅与“藏雷”扩散。
        results = manager.apply_element(Element.ANEMO, 1.0)
        
        assert len([r for r in results if r.name == "扩散"]) == 1
        assert results[0].target_element == Element.ELECTRO
        assert manager.quicken_gauge.current_gauge == pytest.approx(0.8) # 激元素量不动

    # --- 4. 复杂特殊状态实验室 ---

    def test_shatter_melt_combination(self, manager):
        """岩+火 连续攻击冻结态：碎冰与融化并存"""
        manager.apply_element(Element.HYDRO, 1.0)
        manager.apply_element(Element.CRYO, 1.0) # 1.6GU 冻
        
        # 1U 岩触发碎冰 (0.5GU) -> 剩余 1.1GU 冻
        manager.apply_element(Element.GEO, 1.0)
        # 0.5U 火触发融化 (0.5*2.0=1.0GU) -> 剩余 0.1GU 冻
        results = manager.apply_element(Element.PYRO, 0.5)
        
        assert any(r.name == "融化" for r in results)
        assert manager.frozen_gauge.current_gauge == pytest.approx(0.1)

    # --- 5. 极限与边界测试 ---

    def test_gauge_refill_stronger(self, manager):
        """测试同元素覆盖：强量刷新弱量"""
        # 1. 先施加 1U 火 (0.8GU)
        manager.apply_element(Element.PYRO, 1.0)
        manager.apply_element(Element.PYRO, 2.0)
        assert manager.auras[0].current_gauge == pytest.approx(1.6)
        assert manager.auras[0].decay_rate == pytest.approx(1.6/12.0)

    def test_micro_gauge_cleanup(self, manager):
        """测试极小元素量自动清理"""
        manager.apply_element(Element.PYRO, 1.0)
        manager.auras[0].current_gauge = 0.00001
        manager.update(1/60)
        assert len(manager.auras) == 0