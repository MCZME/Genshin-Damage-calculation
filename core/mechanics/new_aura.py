from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple, Any
import math

class Element(Enum):
    PYRO = "火"
    HYDRO = "水"
    CRYO = "冰"
    ELECTRO = "雷"
    DENDRO = "草"
    ANEMO = "风"
    GEO = "岩"
    PHYSICAL = "物理"
    FROZEN = "冻"     # 冻元素
    QUICKEN = "激"    # 激元素

@dataclass
class Gauge:
    """
    元素量封装类
    附着量规律：附着量 = 0.8 * U
    衰减时长：T = 7 * U + 2.5
    """
    element: Element
    u_value: float
    max_gauge: float
    current_gauge: float
    decay_rate: float
    
    @classmethod
    def create(cls, element: Element, u_value: float):
        # 附着损耗 20%
        max_g = 0.8 * u_value
        # 高等元素论衰减公式
        duration = 7 * u_value + 2.5
        decay = max_g / duration
        return cls(element, u_value, max_g, max_g, decay)

    def update(self, dt: float):
        self.current_gauge -= self.decay_rate * dt
        if self.current_gauge < 0: self.current_gauge = 0

    def consume(self, amount: float):
        self.current_gauge -= amount
        if self.current_gauge < 0: self.current_gauge = 0

@dataclass
class ReactionResult:
    """反应结算结果"""
    name: str
    source_element: Element
    target_element: Element
    multiplier: float = 1.0
    gauge_consumed: float = 0.0

class NewAuraManager:
    """
    重构后的元素管理器
    完全模拟“高等元素论”：克制系数、优先级、状态转换、共存机制。
    """
    def __init__(self):
        self.auras: List[Gauge] = []
        # 特殊状态槽
        self.frozen_gauge: Optional[Gauge] = None  # 冻
        self.quicken_gauge: Optional[Gauge] = None # 激
        
        # 状态计时器
        self.is_electro_charged: bool = False
        self.ec_timer: float = 0.0
        self.is_burning: bool = False
        self.burning_timer: float = 0.0

    def update(self, dt: float = 1/60):
        """随帧更新：处理自然衰减和状态跳字"""
        # 1. 常规附着衰减
        for a in self.auras[:]:
            a.update(dt)
            if a.current_gauge <= 0: self.auras.remove(a)
        
        # 2. 冻/激元素衰减
        if self.frozen_gauge:
            self.frozen_gauge.update(dt)
            if self.frozen_gauge.current_gauge <= 0: self.frozen_gauge = None
        if self.quicken_gauge:
            self.quicken_gauge.update(dt)
            if self.quicken_gauge.current_gauge <= 0: self.quicken_gauge = None

        # 3. 感电逻辑：每秒扣除 0.4GU
        if self.is_electro_charged:
            self.ec_timer += dt
            if self.ec_timer >= 1.0:
                self.ec_timer = 0
                self._apply_ec_tick()

        # 4. 燃烧逻辑：火维持，消耗草 0.4GU/s
        if self.is_burning:
            self._apply_burning_tick(dt)

    def apply_element(self, attack_element: Element, attack_u: float) -> List[ReactionResult]:
        """
        核心结算：处理一次元素施加
        :param attack_element: 攻击元素类型
        :param attack_u: 攻击元素量 (GU)
        """
        if attack_element == Element.PHYSICAL or attack_u <= 0:
            return []

        results = []
        rem_atk_g = attack_u
        has_reacted = False

        # --- A. 优先级 1：特殊状态反应 (冻/激) ---
        
        # 1. 冻结反应 (火/雷/风/岩/大剑)
        if self.frozen_gauge and self._get_tax(attack_element, Element.FROZEN) > 0:
            rem_atk_g = self._react_with_state(attack_element, rem_atk_g, "FROZEN", results)
            has_reacted = True

        # 2. 激化反应 (水/火/雷/草)
        if self.quicken_gauge and self._get_tax(attack_element, Element.QUICKEN) > 0:
            if attack_element in [Element.ELECTRO, Element.DENDRO]:
                # 超/蔓激化不消耗激元素量，仅触发
                results.append(ReactionResult("超激化" if attack_element == Element.ELECTRO else "蔓激化", 
                                              attack_element, Element.QUICKEN))
            else:
                rem_atk_g = self._react_with_state(attack_element, rem_atk_g, "QUICKEN", results)
                has_reacted = True

        # --- B. 优先级 2：常规附着反应 ---
        
        # 处理一对多反应 (风/岩)
        if attack_element in [Element.ANEMO, Element.GEO]:
            results.extend(self._handle_trigger_elements(attack_element, rem_atk_g))
            return results

        # 标准消耗反应
        for aura in self.auras[:]:
            if rem_atk_g <= 0: break
            tax = self._get_tax(attack_element, aura.element)
            if tax > 0:
                has_reacted = True
                consume = min(aura.current_gauge, rem_atk_g * tax)
                aura.consume(consume)
                rem_atk_g -= consume / tax
                results.append(ReactionResult(self._get_name(attack_element, aura.element), 
                                              attack_element, aura.element, self._get_mult(attack_element, aura.element), consume))
                if aura.current_gauge <= 0: self.auras.remove(aura)

        # --- C. 优先级 3：状态转换与新附着 ---
        
        # 1. 产生冻结 (水+冰)
        if self._check_combo(attack_element, Element.HYDRO, Element.CRYO):
            self._trigger_freeze(attack_element, attack_u)
            results.append(ReactionResult("冻结", attack_element, Element.CRYO if attack_element == Element.HYDRO else Element.HYDRO))
            rem_atk_g = 0

        # 2. 产生激化 (雷+草)
        elif self._check_combo(attack_element, Element.ELECTRO, Element.DENDRO):
            self._trigger_quicken(attack_element, attack_u)
            results.append(ReactionResult("原激化", attack_element, Element.DENDRO if attack_element == Element.ELECTRO else Element.ELECTRO))
            rem_atk_g = 0

        # 3. 产生燃烧 (火+草)
        elif self._check_combo(attack_element, Element.PYRO, Element.DENDRO):
            self.is_burning = True
            results.append(ReactionResult("燃烧", attack_element, Element.DENDRO))
            # 燃烧开启后会维持火附着，不阻止附着

        # 4. 感电 (水+雷)
        elif self._check_combo(attack_element, Element.HYDRO, Element.ELECTRO):
            self.is_electro_charged = True
            has_reacted = True # 感电属于共存反应

        # 5. 附着 (未触发消耗型反应)
        if not has_reacted and rem_atk_g > 0:
            self._attach(attack_element, attack_u)

        return results

    # --- 辅助算法 ---

    def _get_tax(self, attack: Element, target: Element) -> float:
        """消耗系数 table"""
        table = {
            (Element.HYDRO, Element.PYRO): 2.0, (Element.PYRO, Element.HYDRO): 0.5,
            (Element.PYRO, Element.CRYO): 2.0, (Element.CRYO, Element.PYRO): 0.5,
            (Element.PYRO, Element.FROZEN): 2.0, (Element.PYRO, Element.QUICKEN): 0.5, # 火打激化按火打草算
            (Element.HYDRO, Element.DENDRO): 1.0, (Element.HYDRO, Element.QUICKEN): 1.0, # 水打激化按水打草算(绽放)
        }
        if (attack, target) in table: return table[(attack, target)]
        if attack in [Element.ANEMO, Element.GEO]: return 0.5
        return 1.0 if self._is_reactive(attack, target) else 0.0

    def _react_with_state(self, attack: Element, u: float, state: str, results: List[ReactionResult]) -> float:
        target = self.frozen_gauge if state == "FROZEN" else self.quicken_gauge
        if not target: return u
        base_el = Element.CRYO if state == "FROZEN" else Element.DENDRO
        tax = self._get_tax(attack, base_el)
        if tax > 0:
            consume = min(target.current_gauge, u * tax)
            target.consume(consume)
            name = "碎冰" if (state == "FROZEN" and attack == Element.GEO) else self._get_name(attack, base_el)
            results.append(ReactionResult(name, attack, base_el, self._get_mult(attack, base_el), consume))
            return u - (consume / tax)
        return u

    def _trigger_freeze(self, attack: Element, u: float):
        target_el = Element.CRYO if attack == Element.HYDRO else Element.HYDRO
        existing = next((a for a in self.auras if a.element == target_el), None)
        if existing:
            frozen_val = 2 * min(existing.current_gauge, u)
            self.frozen_gauge = Gauge.create(Element.FROZEN, frozen_val / 0.8)
            existing.consume(min(existing.current_gauge, u))
            if existing.current_gauge <= 0: self.auras.remove(existing)

    def _trigger_quicken(self, attack: Element, u: float):
        target_el = Element.ELECTRO if attack == Element.DENDRO else Element.DENDRO
        existing = next((a for a in self.auras if a.element == target_el), None)
        if existing:
            val = min(existing.current_gauge, u)
            self.quicken_gauge = Gauge.create(Element.QUICKEN, val / 0.8)
            existing.consume(val)
            if existing.current_gauge <= 0: self.auras.remove(existing)

    def _apply_ec_tick(self):
        h = next((a for a in self.auras if a.element == Element.HYDRO), None)
        e = next((a for a in self.auras if a.element == Element.ELECTRO), None)
        if h and e:
            h.consume(0.4); e.consume(0.4)
            if h.current_gauge <= 0: self.auras.remove(h)
            if e.current_gauge <= 0: self.auras.remove(e)
        self.is_electro_charged = (h is not None and e is not None and h.current_gauge > 0 and e.current_gauge > 0)

    def _apply_burning_tick(self, dt: float):
        # 燃烧：消耗草，产生火附着
        grass = next((a for a in self.auras if a.element == Element.DENDRO), None)
        if not grass: 
            self.is_burning = False; return
        grass.consume(0.4 * dt) # 0.4GU/s 消耗
        # 维持火量 (通常燃烧会自动补充弱火)
        self._attach(Element.PYRO, 1.0)
        if grass.current_gauge <= 0: 
            self.auras.remove(grass); self.is_burning = False

    def _attach(self, element: Element, u: float):
        existing = next((a for a in self.auras if a.element == element), None)
        new_a = Gauge.create(element, u)
        if existing:
            existing.current_gauge = max(existing.current_gauge, new_a.current_gauge)
        else:
            self.auras.append(new_a)

    def _handle_trigger_elements(self, attack: Element, u: float) -> List[ReactionResult]:
        res = []
        for aura in self.auras[:]:
            tax = 0.5
            if aura.element in [Element.PYRO, Element.HYDRO, Element.CRYO, Element.ELECTRO]:
                consume = min(aura.current_gauge, u * tax)
                aura.consume(consume)
                res.append(ReactionResult("扩散" if attack == Element.ANEMO else "结晶", attack, aura.element, 1.0, consume))
                if aura.current_gauge <= 0: self.auras.remove(aura)
        return res

    def _get_name(self, a, b):
        m = {(Element.HYDRO, Element.PYRO): "蒸发", (Element.PYRO, Element.CRYO): "融化",
             (Element.ELECTRO, Element.PYRO): "超载", (Element.HYDRO, Element.ELECTRO): "感电",
             (Element.CRYO, Element.ELECTRO): "超导", (Element.HYDRO, Element.DENDRO): "绽放"}
        return m.get((a, b), m.get((b, a), "未知反应"))

    def _get_mult(self, a, b):
        if (a, b) == (Element.HYDRO, Element.PYRO): return 2.0
        if (a, b) == (Element.PYRO, Element.HYDRO): return 1.5
        if (a, b) == (Element.PYRO, Element.CRYO): return 2.0
        if (a, b) == (Element.CRYO, Element.PYRO): return 1.5
        return 1.0

    def _is_reactive(self, a, b): return self._get_name(a, b) != "未知反应"
    
    def _check_combo(self, atk, el1, el2):
        if atk == el1: return any(a.element == el2 for a in self.auras)
        if atk == el2: return any(a.element == el1 for a in self.auras)
        return False
