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
    FROZEN = "冻"
    QUICKEN = "激"

@dataclass
class Gauge:
    element: Element
    u_value: float
    max_gauge: float
    current_gauge: float
    decay_rate: float
    
    @classmethod
    def create(cls, element: Element, u_value: float):
        max_g = 0.8 * u_value
        if u_value <= 1.0: duration = 9.5
        elif u_value <= 2.0: duration = 12.0
        else: duration = 17.0
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
    name: str
    source_element: Element
    target_element: Element
    multiplier: float = 1.0
    gauge_consumed: float = 0.0

class NewAuraManager:
    def __init__(self):
        self.auras: List[Gauge] = []
        self.frozen_gauge: Optional[Gauge] = None
        self.quicken_gauge: Optional[Gauge] = None
        self.is_electro_charged: bool = False
        self.ec_timer: float = 0.0
        self.is_burning: bool = False

    def update(self, dt: float = 1/60):
        for a in self.auras[:]:
            a.update(dt)
            if a.current_gauge <= 0: self.auras.remove(a)
        if self.frozen_gauge:
            self.frozen_gauge.update(dt)
            if self.frozen_gauge.current_gauge <= 0: self.frozen_gauge = None
        if self.quicken_gauge:
            self.quicken_gauge.update(dt)
            if self.quicken_gauge.current_gauge <= 0: self.quicken_gauge = None
        if self.is_electro_charged:
            self.ec_timer += dt
            if self.ec_timer >= 1.0:
                self.ec_timer = 0
                self._apply_ec_tick()
        if self.is_burning:
            self._apply_burning_tick(dt)

    def apply_element(self, attack_element: Element, attack_u: float) -> List[ReactionResult]:
        if attack_element == Element.PHYSICAL or attack_u <= 0:
            return []

        results = []
        rem_u = attack_u
        # 核心：记录是否触发了会阻止附着的反应
        prevent_attachment = False

        # 1. 特殊状态反应 (优先)
        if self.frozen_gauge:
            tax = self._get_tax(attack_element, Element.FROZEN)
            if tax > 0:
                prevent_attachment = True # 凡反应必阻止附着
                consume = min(self.frozen_gauge.current_gauge, rem_u * tax)
                self.frozen_gauge.consume(consume)
                # 只有非风/岩攻击才损耗攻击量
                if attack_element not in [Element.ANEMO, Element.GEO]:
                    rem_u -= consume / tax
                
                name = "碎冰" if attack_element == Element.GEO else self._get_amplifying_name(attack_element, Element.CRYO)
                results.append(ReactionResult(name, attack_element, Element.FROZEN, self._get_mult(attack_element, Element.CRYO), consume))
                if self.frozen_gauge.current_gauge <= 0: self.frozen_gauge = None

        if self.quicken_gauge:
            if attack_element == Element.ELECTRO:
                results.append(ReactionResult("超激化", attack_element, Element.QUICKEN))
            elif attack_element == Element.DENDRO:
                results.append(ReactionResult("蔓激化", attack_element, Element.QUICKEN))
            else:
                tax = self._get_tax(attack_element, Element.QUICKEN)
                if tax > 0:
                    prevent_attachment = True
                    consume = min(self.quicken_gauge.current_gauge, rem_u * tax)
                    self.quicken_gauge.consume(consume)
                    if attack_element not in [Element.ANEMO, Element.GEO]:
                        rem_u -= consume / tax
                    
                    r_name = "绽放" if attack_element == Element.HYDRO else "燃烧"
                    results.append(ReactionResult(r_name, attack_element, Element.QUICKEN, 1.0, consume))
                    if self.quicken_gauge.current_gauge <= 0: self.quicken_gauge = None

        # 2. 状态转换判定 (风/岩除外)
        if attack_element not in [Element.ANEMO, Element.GEO]:
            # 冻结
            if self._check_combo(attack_element, Element.HYDRO, Element.CRYO):
                prevent_attachment = True
                target_el = Element.CRYO if attack_element == Element.HYDRO else Element.HYDRO
                existing = next(a for a in self.auras if a.element == target_el)
                consume_val = min(existing.current_gauge, attack_u) # 1:1 消耗
                self.frozen_gauge = Gauge.create(Element.FROZEN, 2.0)
                self.frozen_gauge.current_gauge = 2 * consume_val
                existing.consume(consume_val)
                if existing.current_gauge <= 0: self.auras.remove(existing)
                results.append(ReactionResult("冻结", attack_element, target_el))
                rem_u = 0 # 触发转换攻击量全损

            # 激化
            elif self._check_combo(attack_element, Element.ELECTRO, Element.DENDRO):
                prevent_attachment = True
                target_el = Element.ELECTRO if attack_element == Element.DENDRO else Element.DENDRO
                existing = next(a for a in self.auras if a.element == target_el)
                val = min(existing.current_gauge, attack_u)
                self.quicken_gauge = Gauge.create(Element.QUICKEN, 1.0)
                self.quicken_gauge.current_gauge = val
                existing.consume(val)
                if existing.current_gauge <= 0: self.auras.remove(existing)
                results.append(ReactionResult("原激化", attack_element, target_el))
                rem_u = 0

        # 3. 常规消耗反应 (仅当还有攻击量时)
        if rem_u > 0:
            for aura in self.auras[:]:
                if rem_u <= 0: break
                # 感电特殊：共存
                if {attack_element, aura.element} == {Element.HYDRO, Element.ELECTRO}:
                    self.is_electro_charged = True
                    # 感电初次碰撞视作反应，但允许附着
                    results.append(ReactionResult("感电", attack_element, aura.element))
                    continue
                
                tax = self._get_tax(attack_element, aura.element)
                if tax > 0:
                    prevent_attachment = True
                    consume = min(aura.current_gauge, rem_u * tax)
                    aura.consume(consume)
                    if attack_element not in [Element.ANEMO, Element.GEO]:
                        rem_u -= consume / tax
                    
                    r_name = self._get_reaction_name(attack_element, aura.element)
                    results.append(ReactionResult(r_name, attack_element, aura.element, self._get_mult(attack_element, aura.element), consume))
                    if aura.current_gauge <= 0: self.auras.remove(aura)

        # 4. 状态后续更新
        if self._check_combo(attack_element, Element.PYRO, Element.DENDRO) or (self.quicken_gauge and attack_element == Element.PYRO):
            self.is_burning = True

        # 5. 附着执行
        # 高等元素论：如果触发了非感电/非燃烧的消耗型反应，则严禁附着
        if rem_u > 0.001 and not prevent_attachment:
            self._attach(attack_element, attack_u)

        return results

    def _get_tax(self, attack: Element, target: Element) -> float:
        if attack in [Element.ANEMO, Element.GEO] and target == Element.QUICKEN: return 0.0
        table = {
            (Element.HYDRO, Element.PYRO): 2.0, (Element.PYRO, Element.HYDRO): 0.5,
            (Element.PYRO, Element.CRYO): 2.0, (Element.CRYO, Element.PYRO): 0.5,
            (Element.PYRO, Element.FROZEN): 2.0, (Element.PYRO, Element.QUICKEN): 0.5,
            (Element.HYDRO, Element.DENDRO): 1.0, (Element.HYDRO, Element.QUICKEN): 1.0,
            (Element.ELECTRO, Element.PYRO): 1.0, (Element.PYRO, Element.ELECTRO): 1.0,
            (Element.CRYO, Element.ELECTRO): 1.0, (Element.ELECTRO, Element.CRYO): 1.0,
            (Element.GEO, Element.FROZEN): 0.5, (Element.ANEMO, Element.FROZEN): 0.5,
        }
        if (attack, target) in table: return table[(attack, target)]
        if attack in [Element.ANEMO, Element.GEO]: return 0.5
        return 0.0

    def _apply_ec_tick(self):
        h = next((a for a in self.auras if a.element == Element.HYDRO), None)
        e = next((a for a in self.auras if a.element == Element.ELECTRO), None)
        if h and e:
            h.consume(0.4); e.consume(0.4)
            if h.current_gauge <= 0: self.auras.remove(h)
            if e.current_gauge <= 0: self.auras.remove(e)
        self.is_electro_charged = (h is not None and e is not None and h.current_gauge > 0 and e.current_gauge > 0)

    def _apply_burning_tick(self, dt: float):
        grass = next((a for a in self.auras if a.element == Element.DENDRO), None)
        if not grass: grass = self.quicken_gauge
        if grass:
            grass.consume(0.4 * dt)
            self._attach(Element.PYRO, 1.0)
            if grass.current_gauge <= 0: 
                if grass == self.quicken_gauge: self.quicken_gauge = None
                else: self.auras.remove(grass)
                self.is_burning = False
        else:
            self.is_burning = False

    def _attach(self, element: Element, u: float):
        existing = next((a for a in self.auras if a.element == element), None)
        new_a = Gauge.create(element, u)
        if existing:
            existing.current_gauge = max(existing.current_gauge, new_a.current_gauge)
            existing.decay_rate = max(existing.decay_rate, new_a.decay_rate)
        else:
            self.auras.append(new_a)

    def _get_reaction_name(self, a, b):
        m = {(Element.HYDRO, Element.PYRO): "蒸发", (Element.PYRO, Element.CRYO): "融化",
             (Element.ELECTRO, Element.PYRO): "超载", (Element.HYDRO, Element.ELECTRO): "感电",
             (Element.CRYO, Element.ELECTRO): "超导", (Element.HYDRO, Element.DENDRO): "绽放",
             (Element.ANEMO, Element.PYRO): "扩散", (Element.ANEMO, Element.HYDRO): "扩散",
             (Element.ANEMO, Element.CRYO): "扩散", (Element.ANEMO, Element.ELECTRO): "扩散",
             (Element.GEO, Element.PYRO): "结晶", (Element.GEO, Element.HYDRO): "结晶",
             (Element.GEO, Element.CRYO): "结晶", (Element.GEO, Element.ELECTRO): "结晶"}
        return m.get((a, b), m.get((b, a), "未知反应"))

    def _get_amplifying_name(self, atk, target):
        """增幅反应专用名称判定"""
        if {atk, target} == {Element.PYRO, Element.HYDRO}: return "蒸发"
        if {atk, target} == {Element.PYRO, Element.CRYO}: return "融化"
        return "扩散" if atk == Element.ANEMO else "无"

    def _get_mult(self, a, b):
        if (a, b) == (Element.HYDRO, Element.PYRO): return 2.0
        if (a, b) == (Element.PYRO, Element.HYDRO): return 1.5
        if (a, b) == (Element.PYRO, Element.CRYO): return 2.0
        if (a, b) == (Element.CRYO, Element.PYRO): return 1.5
        return 1.0

    def _check_combo(self, atk, el1, el2):
        if atk == el1: return any(a.element == el2 for a in self.auras)
        if atk == el2: return any(a.element == el1 for a in self.auras)
        return False
