from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from core.systems.contract.reaction import (
    REACTION_CLASSIFICATION,
    ElementalReactionType,
    ReactionCategory,
    ReactionResult,
)


class Element(Enum):
    """元素类型枚举。"""

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
    NONE = "无"


@dataclass
class Gauge:
    """
    元素量载体。
    遵循原神“附着论”，管理元素量的衰减与消耗。
    """

    element: Element
    u_value: float  # 初始元素量 (1U, 2U, 4U)
    max_gauge: float  # 最大附着量 (通常为 0.8 * u_value)
    current_gauge: float  # 当前剩余附着量
    decay_rate: float  # 衰减速率 (每秒扣除量)

    @classmethod
    def create(cls, element: Element, u_value: float) -> "Gauge":
        """工厂方法：根据初始 U 值创建附着。"""
        max_g = 0.8 * u_value
        if u_value <= 1.0:
            duration = 9.5
        elif u_value <= 2.0:
            duration = 12.0
        else:
            duration = 17.0
        decay = max_g / duration
        return cls(element, u_value, max_g, max_g, decay)

    def update(self, dt: float) -> None:
        """更新衰减逻辑。"""
        self.current_gauge -= self.decay_rate * dt
        if self.current_gauge < 0:
            self.current_gauge = 0.0

    def consume(self, amount: float) -> None:
        """消耗元素量。"""
        self.current_gauge -= amount
        if self.current_gauge < 0:
            self.current_gauge = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """序列化输出。"""
        return {
            "element": self.element.value,
            "value": round(self.current_gauge, 3),
            "max": round(self.max_gauge, 3),
        }


class AuraManager:
    """
    附着管理器。
    负责实体的元素附着状态维护、反应优先级判定及元素量结算。
    """

    def __init__(self) -> None:
        self.auras: List[Gauge] = []
        self.frozen_gauge: Optional[Gauge] = None
        self.quicken_gauge: Optional[Gauge] = None

        self.is_electro_charged: bool = False
        self.ec_timer: float = 0.0

        self.is_burning: bool = False
        self.burning_timer: float = 0.0

    def export_state(self) -> Dict[str, Any]:
        """导出当前实体的所有附着状态快照。"""
        res = {
            "regular": [a.to_dict() for a in self.auras],
            "frozen": self.frozen_gauge.to_dict() if self.frozen_gauge else None,
            "quicken": self.quicken_gauge.to_dict() if self.quicken_gauge else None,
            "states": [],
        }
        if self.is_electro_charged:
            res["states"].append("感电")
        if self.is_burning:
            res["states"].append("燃烧")
        return res

    def update(self, owner: Any, dt: float = 1 / 60) -> None:
        """每帧驱动附着衰减与周期性反应。"""
        for a in self.auras[:]:
            a.update(dt)
            if a.current_gauge <= 0:
                self.auras.remove(a)

        if self.frozen_gauge:
            self.frozen_gauge.update(dt)
            if self.frozen_gauge.current_gauge <= 0:
                self.frozen_gauge = None

        if self.quicken_gauge:
            self.quicken_gauge.update(dt)
            if self.quicken_gauge.current_gauge <= 0:
                self.quicken_gauge = None

        if self.is_electro_charged:
            self.ec_timer += dt
            if self.ec_timer >= 1.0:
                self.ec_timer = 0.0
                self._apply_ec_tick(owner)

        if self.is_burning:
            self.burning_timer += dt
            if self.burning_timer >= 0.25:  # 燃烧伤害频率为 0.25s 一次
                self.burning_timer = 0.0
                self._apply_burning_tick(owner, dt, is_damage_frame=True)
            else:
                self._apply_burning_tick(owner, dt, is_damage_frame=False)

    def apply_element(self, element: Any, attack_u: float) -> List[ReactionResult]:
        """
        应用外部元素攻击。
        """
        if not isinstance(element, Element):
            attack_element = Element(element)
        else:
            attack_element = element

        if attack_element in [Element.PHYSICAL, Element.NONE] or attack_u <= 0:
            return []

        results: List[ReactionResult] = []
        rem_u = attack_u
        prevent_attachment = False

        # 1. 特殊状态判定
        if self.frozen_gauge:
            tax = self._get_tax(attack_element, Element.FROZEN)
            if tax > 0:
                prevent_attachment = True
                consume = min(self.frozen_gauge.current_gauge, rem_u * tax)
                self.frozen_gauge.consume(consume)
                if attack_element not in [Element.ANEMO, Element.GEO]:
                    rem_u -= consume / tax
                r_type = (
                    ElementalReactionType.SHATTER
                    if attack_element == Element.GEO
                    else self._map_reaction(attack_element, Element.CRYO)
                )
                results.append(
                    self._create_result(r_type, attack_element, Element.FROZEN, consume)
                )
                if self.frozen_gauge.current_gauge <= 0:
                    self.frozen_gauge = None

        if self.quicken_gauge:
            if attack_element == Element.ELECTRO:
                results.append(
                    self._create_result(
                        ElementalReactionType.AGGRAVATE, attack_element, Element.QUICKEN
                    )
                )
            elif attack_element == Element.DENDRO:
                results.append(
                    self._create_result(
                        ElementalReactionType.SPREAD, attack_element, Element.QUICKEN
                    )
                )
            else:
                tax = self._get_tax(attack_element, Element.QUICKEN)
                if tax > 0:
                    prevent_attachment = True
                    consume = min(self.quicken_gauge.current_gauge, rem_u * tax)
                    self.quicken_gauge.consume(consume)
                    if attack_element not in [Element.ANEMO, Element.GEO]:
                        rem_u -= consume / tax
                    r_type = (
                        ElementalReactionType.BLOOM
                        if attack_element == Element.HYDRO
                        else ElementalReactionType.BURNING
                    )
                    results.append(
                        self._create_result(
                            r_type, attack_element, Element.QUICKEN, consume
                        )
                    )
                    if self.quicken_gauge.current_gauge <= 0:
                        self.quicken_gauge = None

        # 2. 状态转换
        if attack_element not in [Element.ANEMO, Element.GEO]:
            if self._check_combo(attack_element, Element.HYDRO, Element.CRYO):
                prevent_attachment = True
                target_el = (
                    Element.CRYO if attack_element == Element.HYDRO else Element.HYDRO
                )
                existing = next(a for a in self.auras if a.element == target_el)
                consume_val = min(existing.current_gauge, attack_u)
                self.frozen_gauge = Gauge.create(Element.FROZEN, 2.0)
                self.frozen_gauge.current_gauge = 2.0 * consume_val
                existing.consume(consume_val)
                if existing.current_gauge <= 0:
                    self.auras.remove(existing)
                results.append(
                    self._create_result(
                        ElementalReactionType.FREEZE, attack_element, target_el
                    )
                )
                rem_u -= consume_val
            elif self._check_combo(attack_element, Element.ELECTRO, Element.DENDRO):
                prevent_attachment = True
                target_el = (
                    Element.ELECTRO
                    if attack_element == Element.DENDRO
                    else Element.DENDRO
                )
                existing = next(a for a in self.auras if a.element == target_el)
                val = min(existing.current_gauge, attack_u)
                self.quicken_gauge = Gauge.create(Element.QUICKEN, 1.0)
                self.quicken_gauge.current_gauge = val
                existing.consume(val)
                if existing.current_gauge <= 0:
                    self.auras.remove(existing)
                results.append(
                    self._create_result(
                        ElementalReactionType.QUICKEN, attack_element, target_el
                    )
                )
                rem_u -= val

        # 3. 常规反应
        if rem_u > 0:
            for aura in self.auras[:]:
                if rem_u <= 0:
                    break
                if {attack_element, aura.element} == {Element.HYDRO, Element.ELECTRO}:
                    if not self.is_electro_charged:
                        self.is_electro_charged = True
                        results.append(
                            self._create_result(
                                ElementalReactionType.ELECTRO_CHARGED,
                                attack_element,
                                aura.element,
                            )
                        )
                    continue
                tax = self._get_tax(attack_element, aura.element)
                if tax > 0:
                    prevent_attachment = True
                    consume = min(aura.current_gauge, rem_u * tax)
                    aura.consume(consume)
                    if attack_element not in [Element.ANEMO, Element.GEO]:
                        rem_u -= consume / tax
                    r_type = self._map_reaction(attack_element, aura.element)
                    results.append(
                        self._create_result(
                            r_type, attack_element, aura.element, consume
                        )
                    )
                    if aura.current_gauge <= 0:
                        self.auras.remove(aura)

        # 4. 最终状态
        if self._check_combo(attack_element, Element.HYDRO, Element.ELECTRO):
            self.is_electro_charged = True
        if self._check_combo(attack_element, Element.PYRO, Element.DENDRO) or (
            self.quicken_gauge and attack_element == Element.PYRO
        ):
            self.is_burning = True

        if attack_element in [Element.ANEMO, Element.GEO]:
            return results
        if rem_u > 0.001 and not prevent_attachment:
            self._attach(attack_element, rem_u)
        return results

    def has_aura(self, element_name: str) -> bool:
        """检查实体是否带有特定元素的附着或状态。"""
        if element_name == "冻结" or element_name == "冻":
            return self.frozen_gauge is not None
        if element_name == "激化" or element_name == "激":
            return self.quicken_gauge is not None
        return any(a.element.value == element_name for a in self.auras)

    def _create_result(
        self,
        r_type: ElementalReactionType,
        source: Element,
        target: Element,
        consume: float = 0.0,
    ) -> ReactionResult:
        category = REACTION_CLASSIFICATION.get(r_type, ReactionCategory.STATUS)
        mult = (
            self._get_mult(source, target)
            if category == ReactionCategory.AMPLIFYING
            else 1.0
        )
        return ReactionResult(
            reaction_type=r_type,
            category=category,
            source_element=source,
            target_element=target,
            multiplier=mult,
            gauge_consumed=consume,
        )

    def _map_reaction(self, atk: Element, target: Element) -> ElementalReactionType:
        table = {
            (Element.HYDRO, Element.PYRO): ElementalReactionType.VAPORIZE,
            (Element.PYRO, Element.HYDRO): ElementalReactionType.VAPORIZE,
            (Element.PYRO, Element.CRYO): ElementalReactionType.MELT,
            (Element.CRYO, Element.PYRO): ElementalReactionType.MELT,
            (Element.ELECTRO, Element.PYRO): ElementalReactionType.OVERLOAD,
            (Element.PYRO, Element.ELECTRO): ElementalReactionType.OVERLOAD,
            (Element.ELECTRO, Element.HYDRO): ElementalReactionType.ELECTRO_CHARGED,
            (Element.HYDRO, Element.ELECTRO): ElementalReactionType.ELECTRO_CHARGED,
            (Element.CRYO, Element.ELECTRO): ElementalReactionType.SUPERCONDUCT,
            (Element.ELECTRO, Element.CRYO): ElementalReactionType.SUPERCONDUCT,
            (Element.HYDRO, Element.DENDRO): ElementalReactionType.BLOOM,
            (Element.DENDRO, Element.HYDRO): ElementalReactionType.BLOOM,
            (Element.ANEMO, Element.PYRO): ElementalReactionType.SWIRL,
            (Element.ANEMO, Element.HYDRO): ElementalReactionType.SWIRL,
            (Element.ANEMO, Element.CRYO): ElementalReactionType.SWIRL,
            (Element.ANEMO, Element.ELECTRO): ElementalReactionType.SWIRL,
            (Element.GEO, Element.PYRO): ElementalReactionType.CRYSTALLIZE,
            (Element.GEO, Element.HYDRO): ElementalReactionType.CRYSTALLIZE,
            (Element.GEO, Element.CRYO): ElementalReactionType.CRYSTALLIZE,
            (Element.GEO, Element.ELECTRO): ElementalReactionType.CRYSTALLIZE,
        }
        return table.get(
            (atk, target), table.get((target, atk), ElementalReactionType.VAPORIZE)
        )

    def _get_tax(self, attack: Element, target: Element) -> float:
        if attack in [Element.ANEMO, Element.GEO] and target == Element.QUICKEN:
            return 0.0
        table = {
            (Element.HYDRO, Element.PYRO): 2.0,
            (Element.PYRO, Element.HYDRO): 0.5,
            (Element.PYRO, Element.CRYO): 2.0,
            (Element.CRYO, Element.PYRO): 0.5,
            (Element.PYRO, Element.FROZEN): 2.0,
            (Element.PYRO, Element.QUICKEN): 0.5,
            (Element.HYDRO, Element.DENDRO): 1.0,
            (Element.DENDRO, Element.HYDRO): 1.0,
            (Element.HYDRO, Element.QUICKEN): 1.0,
            (Element.ELECTRO, Element.PYRO): 1.0,
            (Element.PYRO, Element.ELECTRO): 1.0,
            (Element.CRYO, Element.ELECTRO): 1.0,
            (Element.ELECTRO, Element.CRYO): 1.0,
            (Element.GEO, Element.FROZEN): 0.5,
            (Element.ANEMO, Element.FROZEN): 0.5,
        }
        if (attack, target) in table:
            return table[(attack, target)]
        if attack in [Element.ANEMO, Element.GEO]:
            return 0.5
        return 0.0

    def _apply_ec_tick(self, owner: Any) -> None:
        """驱动感电跳电逻辑。"""
        from core.event import GameEvent, EventType
        from core.tool import get_current_time

        h = next((a for a in self.auras if a.element == Element.HYDRO), None)
        e = next((a for a in self.auras if a.element == Element.ELECTRO), None)
        if h and e:
            h.consume(0.4)
            e.consume(0.4)
            if hasattr(owner, "event_engine"):
                owner.event_engine.publish(
                    GameEvent(
                        event_type=EventType.ELECTRO_CHARGED_TICK,
                        frame=get_current_time(),
                        source=owner,
                        data={"target": owner},
                    )
                )
            if h.current_gauge <= 0:
                self.auras.remove(h)
            if e.current_gauge <= 0:
                self.auras.remove(e)
        self.is_electro_charged = h is not None and e is not None

    def _apply_burning_tick(self, owner: Any, dt: float, is_damage_frame: bool) -> None:
        """驱动燃烧逻辑：周期性消耗草/激、自挂火并产生范围伤害。"""
        from core.event import GameEvent, EventType
        from core.tool import get_current_time

        grass = next((a for a in self.auras if a.element == Element.DENDRO), None)
        if not grass:
            grass = self.quicken_gauge
        if grass:
            # 1. 元素消耗：每秒 0.4U
            grass.consume(0.4 * dt)
            # 2. 自挂火：保持火附着
            self._attach(Element.PYRO, 1.0)
            # 3. 产生范围伤害事件 (每 0.25s 一次)
            if is_damage_frame and hasattr(owner, "event_engine"):
                owner.event_engine.publish(
                    GameEvent(
                        event_type=EventType.BURNING_TICK,
                        frame=get_current_time(),
                        source=owner,
                        data={"target": owner},
                    )
                )
            if grass.current_gauge <= 0:
                if grass == self.quicken_gauge:
                    self.quicken_gauge = None
                else:
                    self.auras.remove(grass)
                self.is_burning = False
        else:
            self.is_burning = False

    def _attach(self, element: Element, u: float) -> None:
        existing = next((a for a in self.auras if a.element == element), None)
        new_a = Gauge.create(element, u)
        if existing:
            existing.current_gauge = max(existing.current_gauge, new_a.current_gauge)
            existing.decay_rate = new_a.decay_rate
        else:
            self.auras.append(new_a)

    def _get_mult(self, a: Element, b: Element) -> float:
        target = Element.CRYO if b == Element.FROZEN else b
        if (a, target) == (Element.HYDRO, Element.PYRO):
            return 2.0
        if (a, target) == (Element.PYRO, Element.HYDRO):
            return 1.5
        if (a, target) == (Element.PYRO, Element.CRYO):
            return 2.0
        if (a, target) == (Element.CRYO, Element.PYRO):
            return 1.5
        return 1.0

    def _check_combo(self, atk: Element, el1: Element, el2: Element) -> bool:
        if atk == el1:
            return any(a.element == el2 for a in self.auras)
        if atk == el2:
            return any(a.element == el1 for a in self.auras)
        return False
