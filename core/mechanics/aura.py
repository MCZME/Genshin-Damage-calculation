from math import sqrt
from typing import Any, Dict, List, Optional, Tuple, Union

from core.action.reaction import (
    ElementalReaction,
    ElementalReactionType,
    ReactionMMap,
)
from core.event import ElementalReactionEvent, EventBus
from core.tool import GetCurrentTime


class ElementalAura:
    """
    元素附着与反应处理器。
    负责维护实体身上的元素状态（Aura）并计算元素反应的消耗与触发。
    """

    def __init__(self):
        self.aura_list: List[Dict[str, Any]] = []
        self.burning_elements: Dict[str, Any] = {}
        self.quicken_elements: Dict[str, Any] = {}

    def get_aura_list(self) -> List[Dict[str, Any]]:
        """获取当前附着的元素列表"""
        return self.aura_list

    def set_aura_list(self, aura_list: List[Dict[str, Any]]) -> None:
        """设置附着元素列表"""
        self.aura_list = aura_list

    def apply_damage_element(self, damage: Any) -> Optional[float]:
        """
        应用伤害带来的元素附着或触发反应。
        返回反应倍率（如果是增幅反应）或 None。
        """
        element_type, amount = damage.element
        if amount <= 0:
            return None

        if self._check_reactions(element_type):
            return self.process_elemental_reactions(damage)
        else:
            if element_type not in {"风", "岩"}:
                self._attach_new_element(element_type, amount)
            return None

    def process_elemental_reactions(self, damage: Any) -> Optional[float]:
        """处理复合元素反应逻辑 (冻结、感电、燃烧、激化及其叠加态)"""
        reaction_triggers: List[Optional[float]] = []

        # 1. 优先处理冻结状态下的反应
        freeze = next((x for x in self.aura_list if x["element"] == "冻" and x["current_amount"] > 0), None)
        if freeze:
            return self.handle_in_freeze_reaction(damage)

        # 2. 处理感电状态 (水雷共存)
        electro_charged = [x for x in self.aura_list if x["element"] in ["水", "雷"] and x["current_amount"] > 0]
        if electro_charged and (
            len(electro_charged) == 2
            or (
                damage.element[0] in ["水", "雷"]
                and damage.element[0] != electro_charged[0]["element"]
                and len(electro_charged) == 1
            )
        ):
            return self.handle_electro_charged_reaction(damage)

        # 3. 处理燃烧状态
        if self.burning_elements:
            return self.handle_in_burning_reaction(damage)

        # 4. 处理激化状态
        if self.quicken_elements:
            return self.handle_in_quicken_reaction(damage)

        # 5. 处理常规冻结反应触发
        freeze_check = next(
            (
                x for x in self.aura_list 
                if x["element"] in ["水", "冰"] 
                and x["current_amount"] > 0 
                and damage.element[0] != x["element"]
            ),
            None,
        )
        if freeze_check and damage.element[0] in ["水", "冰"]:
            return self.handle_freeze_reaction(damage)

        # 6. 处理常规双元素反应
        for aura in self.aura_list:
            base_element = aura["element"]
            base_amount = aura["current_amount"]
            reaction_info = ReactionMMap.get((damage.element[0], base_element))
            
            if not reaction_info:
                continue

            rtype, rmult = reaction_info
            
            if rtype == ElementalReactionType.BURNING:
                reaction_triggers.append(self.handle_burning_reaction(damage))
                continue
            elif rtype == ElementalReactionType.QUICKEN:
                reaction_triggers.append(self.handle_quicken_reaction(damage))
                continue
            elif damage.element[1] > 0:
                # 计算消耗比例
                ratio = self._get_element_ratio(damage.element[0], base_element)
                
                # 计算实际消耗
                actual_base_consumed = damage.element[1] * ratio[1] / ratio[0]
                actual_trigger_consumed = base_amount * ratio[0] / ratio[1]
                
                # 更新元素量
                aura["current_amount"] -= actual_base_consumed
                damage.element = (damage.element[0], damage.element[1] - actual_trigger_consumed)
                    
                # 触发反应事件
                e = ElementalReaction(damage)
                e.set_reaction_elements(damage.element[0], base_element if base_element != "冻" else "冰")
                EventBus.publish(ElementalReactionEvent(e, GetCurrentTime()))
                
                # 记录结果 (增幅反应返回倍率，剧变返回 None)
                if e.reaction_type[0] == "剧变反应":
                    reaction_triggers.append(None)
                else:
                    reaction_triggers.append(e.reaction_multiplier)
                
                if damage.element[1] <= 0:
                    break
                
        # 返回最高倍率 (针对增幅反应)
        valid_triggers = [x for x in reaction_triggers if x is not None]
        return max(valid_triggers) if valid_triggers else None

    def handle_electro_charged_reaction(self, damage: Any) -> Optional[float]:
        """处理感电反应 (水雷共存)"""
        reaction_triggers = []
        if damage.element[0] in ["水", "雷"]:
            base_element = next(
                (a["element"] for a in self.aura_list if a["element"] in ["水", "雷"] and a["element"] != damage.element[0]), 
                None
            )
            self._attach_new_element(damage.element[0], damage.element[1])
            e = ElementalReaction(damage)
            e.set_reaction_elements(damage.element[0], base_element)
            EventBus.publish(ElementalReactionEvent(e, GetCurrentTime()))
        else:
            # 外部元素触发感电消耗
            s = {"水": 1, "雷": 0}
            for aura in sorted(self.aura_list, key=lambda x: s.get(x["element"], 6)):
                r = ReactionMMap.get((damage.element[0], aura["element"]))
                if r:
                    ratio = self._get_element_ratio(damage.element[0], aura["element"])
                    actual_trigger_consumed = aura["current_amount"] * ratio[0] / ratio[1]
                    actual_base_consumed = damage.element[1] * ratio[1] / ratio[0]
                    
                    if aura["current_amount"] >= actual_base_consumed:
                        aura["current_amount"] -= actual_base_consumed
                        damage.element = (damage.element[0], 0.0)
                    else:
                        aura["current_amount"] = 0.0
                        damage.element = (damage.element[0], damage.element[1] - actual_trigger_consumed)
                    
                    e = ElementalReaction(damage)
                    e.set_reaction_elements(damage.element[0], aura["element"])
                    EventBus.publish(ElementalReactionEvent(e, GetCurrentTime()))

                    if e.reaction_type[0] != "剧变反应":
                        reaction_triggers.append(e.reaction_multiplier)
                
                if damage.element[1] <= 0 or damage.element[0] == "岩":
                    break
                    
        return max(reaction_triggers) if reaction_triggers else None

    def handle_in_freeze_reaction(self, damage: Any) -> Optional[float]:
        """处理冻结状态下的反应 (破冰、反应叠加)"""
        freeze_aura = next((a for a in self.aura_list if a["element"] == "冻"), None)
        if not freeze_aura:
            return None
            
        # 碎冰判定
        if (damage.element[0] == "岩" or getattr(damage, "hit_type", None) == "钝击") and freeze_aura["current_amount"] > 0.5:
            freeze_aura["current_amount"] -= 8.0
            e = ElementalReaction(damage)
            e.set_reaction_elements(damage.element[0], "冻")
            EventBus.publish(ElementalReactionEvent(e, GetCurrentTime()))
            
        self.update() # 推进状态
        
        if damage.element[0] == "风":
            s = {"火": 0, "雷": 1, "水": 2, "冰": 3, "冻": 6}
            return self._handle_in_freeze_special_reaction(damage, s)
        elif damage.element[0] in ["雷", "火"]:
            s = {"冻": 1, "冰": 0}
            return self._handle_in_freeze_special_reaction(damage, s)
        elif damage.element[0] in ["水", "冰"]:
            self.handle_freeze_reaction(damage)
            
        return None
    
    def _handle_in_freeze_special_reaction(self, damage: Any, sort_list: Dict[str, int]) -> Optional[float]:
        reaction_triggers = []
        for aura in sorted(self.aura_list, key=lambda x: sort_list.get(x["element"], 6)):
            r = ReactionMMap.get((damage.element[0], aura["element"]))
            if r and r[0] == ElementalReactionType.ELECTRO_CHARGED:
                continue # 冻结状态下不直接触发感电
            elif r:
                ratio = self._get_element_ratio(damage.element[0], aura["element"])
                actual_trigger_consumed = aura["current_amount"] * ratio[0] / ratio[1]
                actual_base_consumed = damage.element[1] * ratio[1] / ratio[0]
                
                if aura["current_amount"] >= actual_base_consumed:
                    aura["current_amount"] -= actual_base_consumed
                    damage.element = (damage.element[0], 0.0)
                else:
                    aura["current_amount"] = 0.0
                    damage.element = (damage.element[0], damage.element[1] - actual_trigger_consumed)
                
                e = ElementalReaction(damage)
                e.set_reaction_elements(damage.element[0], aura["element"] if aura["element"] != "冻" else "冰")
                EventBus.publish(ElementalReactionEvent(e, GetCurrentTime()))
                
                if e.reaction_type[0] != "剧变反应":
                    reaction_triggers.append(e.reaction_multiplier)
                if damage.element[1] <= 0:
                    break
        return max(reaction_triggers) if reaction_triggers else None

    def handle_freeze_reaction(self, damage: Any) -> None:
        """触发冻结"""
        base_element = next((a for a in self.aura_list if a["element"] in ["水", "冰"] and a["element"] != damage.element[0]), None)
        if base_element:
            amount = min(damage.element[1], base_element["current_amount"])
            base_element["current_amount"] -= amount
            if base_element["current_amount"] < 0.001: base_element["current_amount"] = 0
            
            self._attach_freeze_element("冻", 2 * amount)
            e = ElementalReaction(damage)
            e.set_reaction_elements(damage.element[0], base_element["element"])
            EventBus.publish(ElementalReactionEvent(e, GetCurrentTime()))
        else:
            self._attach_new_element(damage.element[0], damage.element[1])

    def handle_burning_reaction(self, damage: Any) -> None:
        """触发燃烧"""
        base_aura = next((a for a in self.aura_list if a["element"] in ["火", "草"] and a["element"] != damage.element[0]), None)
        if base_aura or (self.quicken_elements and damage.element[0] == "火"):
            self._attach_burning_element(damage.element[0], damage.element[1])
            self.burning_elements = {
                "element": "燃",
                "initial_amount": 2.0,
                "current_amount": 2.0,
                "decay_rate": 0.0
            }
            e = ElementalReaction(damage)
            e.set_reaction_elements(damage.element[0], base_aura["element"] if base_aura else "激")
            EventBus.publish(ElementalReactionEvent(e, GetCurrentTime()))
            
            # 燃烧导致的草元素快速衰减
            if damage.element[0] == "火":
                if self.quicken_elements:
                    self.quicken_elements["decay_rate"] *= 4
                else:
                    grass = next((a for a in self.aura_list if a["element"] == "草"), None)
                    if grass: grass["decay_rate"] *= 4
        else:
            self._attach_new_element(damage.element[0], damage.element[1])

    def handle_in_burning_reaction(self, damage: Any) -> Optional[float]:
        """燃烧状态下的后续反应"""
        reaction_triggers = []
        if damage.element[0] not in ["火", "草"]:
            s = {"火": 0, "草": 1}
            for aura in sorted(self.aura_list, key=lambda x: s.get(x["element"], 6)):
                r = ReactionMMap.get((damage.element[0], aura["element"]))
                if r:
                    ratio = self._get_element_ratio(damage.element[0], aura["element"])
                    base_amount = max(self.burning_elements["current_amount"], damage.element[1]) if aura["element"] == "火" else aura["current_amount"]
                    
                    actual_base_consumed = damage.element[1] * ratio[1] / ratio[0]
                    actual_trigger_consumed = base_amount * ratio[0] / ratio[1]
                    
                    if aura["current_amount"] >= actual_base_consumed:
                        aura["current_amount"] -= actual_base_consumed
                        damage.element = (damage.element[0], 0.0)
                    else:
                        aura["current_amount"] = 0.0
                        damage.element = (damage.element[0], damage.element[1] - actual_trigger_consumed)
                    
                    if aura["element"] == "火":
                        self.burning_elements["current_amount"] -= actual_base_consumed
                        
                    e = ElementalReaction(damage)
                    e.set_reaction_elements(damage.element[0], aura["element"])
                    EventBus.publish(ElementalReactionEvent(e, GetCurrentTime()))
                    
                    if e.reaction_type[0] != "剧变反应":
                        reaction_triggers.append(e.reaction_multiplier)
                    if damage.element[1] <= 0:
                        break
        else:
            self._attach_burning_element(damage.element[0], damage.element[1])

        return max(reaction_triggers) if reaction_triggers else None

    def handle_quicken_reaction(self, damage: Any) -> None:
        """触发原激化"""
        base_aura = next((a for a in self.aura_list if a["element"] in ["雷", "草"] and a["element"] != damage.element[0]), None)
        if base_aura:
            amount = min(damage.element[1], base_aura["current_amount"])
            base_aura["current_amount"] -= amount
            self._attach_quicken_element(amount)
            
            e = ElementalReaction(damage)
            e.set_reaction_elements(damage.element[0], base_aura["element"])
            EventBus.publish(ElementalReactionEvent(e, GetCurrentTime()))
        else:
            self._attach_new_element(damage.element[0], damage.element[1])

    def handle_in_quicken_reaction(self, damage: Any) -> Optional[float]:
        """激化状态下的后续反应"""
        reaction_triggers = []
        s = {"雷": 3, "草": 4, "水": 1, "冰": 2, "火": 0}
        for aura in sorted(self.aura_list, key=lambda x: s.get(x["element"], 6)):
            r = ReactionMMap.get((damage.element[0], aura["element"]))
            if r:
                ratio = self._get_element_ratio(damage.element[0], aura["element"])
                if aura["element"] == "草":
                    self.quicken_elements["current_amount"] -= damage.element[1] * ratio[1] / ratio[0]
                
                if aura["current_amount"] >= damage.element[1] * ratio[1] / ratio[0]:
                    aura["current_amount"] -= damage.element[1] * ratio[1] / ratio[0]
                    damage.element = (damage.element[0], 0.0)
                else:
                    damage.element = (damage.element[0], damage.element[1] - aura["current_amount"] * ratio[0] / ratio[1])
                    aura["current_amount"] = 0.0

                e = ElementalReaction(damage)
                e.set_reaction_elements(damage.element[0], aura["element"])
                EventBus.publish(ElementalReactionEvent(e, GetCurrentTime()))

                if e.reaction_type[0] != "剧变反应":
                    reaction_triggers.append(e.reaction_multiplier)
                if damage.element[1] <= 0:
                    break
        
        # 激化元素本身的后续判定
        if self.quicken_elements.get("current_amount", 0) > 0:
            r = ReactionMMap.get((damage.element[0], "激"))
            if r:
                if r[0] == ElementalReactionType.BURNING:
                    self.handle_burning_reaction(damage)
                elif r[0] in [ElementalReactionType.AGGRAVATE, ElementalReactionType.SPREAD]:
                    self._attach_new_element(damage.element[0], damage.element[1])
                else:
                    ratio = self._get_element_ratio(damage.element[0], "激")
                    if self.quicken_elements["current_amount"] >= damage.element[1] * ratio[1] / ratio[0]:
                        self.quicken_elements["current_amount"] -= damage.element[1] * ratio[1] / ratio[0]
                        damage.element = (damage.element[0], 0.0)
                    else:
                        damage.element = (damage.element[0], damage.element[1] - self.quicken_elements["current_amount"] * ratio[0] / ratio[1])
                        self.quicken_elements["current_amount"] = 0.0
                
                e = ElementalReaction(damage)
                e.set_reaction_elements(damage.element[0], "激")
                EventBus.publish(ElementalReactionEvent(e, GetCurrentTime()))
                if e.reaction_type[0] != "剧变反应":
                    reaction_triggers.append(e.reaction_multiplier)

        return max(reaction_triggers) if reaction_triggers else None

    def _get_element_ratio(self, trigger: str, base: str) -> Tuple[float, float]:
        """获取元素消耗比例 (trigger:base)"""
        if (trigger, base) in [("水", "火"), ("火", "冰"), ("火", "冻"), ("草", "水")]:
            return (1.0, 2.0)
        if (trigger, base) in [("火", "水"), ("冰", "火"), ("水", "草")]:
            return (2.0, 1.0)
        if trigger in {"风", "岩"} and base in {"水", "雷", "冰", "火", "冻"}:
            return (2.0, 1.0)
        return (1.0, 1.0)

    def _attach_new_element(self, element_type: str, applied_amount: float) -> None:
        """处理新元素附着"""
        existing = next((a for a in self.aura_list if a["element"] == element_type), None)
        duration = 7.0 + applied_amount * 2.5

        if existing:
            new_amount = applied_amount * 0.8
            if new_amount > existing["current_amount"]:
                existing.update({"initial_amount": new_amount, "current_amount": new_amount})
        else:
            amount = applied_amount * 0.8
            self.aura_list.append({
                "element": element_type,
                "initial_amount": amount,
                "current_amount": amount,
                "decay_rate": amount / duration
            })

    def _attach_freeze_element(self, element_type: str, applied_amount: float) -> None:
        """处理冻元素附着 (特殊时长公式)"""
        existing = next((a for a in self.aura_list if a["element"] == element_type), None)
        duration = 2 * sqrt(5 * applied_amount + 4) - 4

        if existing:
            duration = duration * 0.7 + existing["current_amount"] / existing["decay_rate"]
            amount = max(applied_amount, existing["current_amount"])
            existing.update({"initial_amount": amount, "current_amount": amount, "decay_rate": amount / duration})
        else:
            self.aura_list.append({
                "element": element_type,
                "initial_amount": applied_amount,
                "current_amount": applied_amount,
                "decay_rate": applied_amount / duration
            })

    def _attach_burning_element(self, element_type: str, applied_amount: float) -> None:
        """处理燃烧反应元素附着"""
        existing = next((a for a in self.aura_list if a["element"] == element_type), None)
        duration = 7.0 + applied_amount * 2.5

        if existing:
            new_amount = applied_amount * 0.8
            if new_amount > existing["current_amount"]:
                existing.update({"initial_amount": new_amount, "current_amount": new_amount})
        else:
            amount = applied_amount * 0.8
            decay_rate = amount / duration if element_type != "草" else 4 * amount / duration
            self.aura_list.append({
                "element": element_type,
                "initial_amount": amount,
                "current_amount": amount,
                "decay_rate": decay_rate
            })

    def _attach_quicken_element(self, applied_amount: float) -> None:
        """处理原激化反应元素附着"""
        duration = 5 * applied_amount + 6
        self.quicken_elements = {
            "element": "激",
            "initial_amount": applied_amount,
            "current_amount": applied_amount,
            "decay_rate": applied_amount / duration
        }

    def _check_reactions(self, element: str) -> bool:
        """快速检查是否可能触发反应"""
        for e in self.aura_list:
            if ReactionMMap.get((element, e["element"])): return True
        if self.quicken_elements and ReactionMMap.get((element, "激")): return True
        if self.burning_elements and ReactionMMap.get((element, "火")): return True
        return False

    def update(self) -> None:
        """推进时间轴：更新元素衰减状态"""
        removed = []
        for aura in self.aura_list:
            aura["current_amount"] -= aura["decay_rate"] / 60
            if aura["current_amount"] <= 0:
                removed.append(aura)
        
        if self.quicken_elements:
            self.quicken_elements["current_amount"] -= self.quicken_elements["decay_rate"] / 60
            if self.quicken_elements["current_amount"] <= 0:
                self.quicken_elements = {}
                
        for aura in removed:
            self.aura_list.remove(aura)

    def clear(self) -> None:
        """清理所有附着元素"""
        self.aura_list.clear()
        self.burning_elements.clear()
        self.quicken_elements.clear()
