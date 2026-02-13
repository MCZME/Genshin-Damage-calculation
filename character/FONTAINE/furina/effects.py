from typing import Any

from core.effect.base import BaseEffect, StackingRule
from core.event import EventType, GameEvent
from core.logger import get_emulation_logger
from core.systems.utils import AttributeCalculator
from character.FONTAINE.furina.data import (
    ELEMENTAL_BURST_DATA
)


class FurinaFanfareEffect(BaseEffect):
    """
    芙宁娜核心效果：普世欢腾 (Fanfare)。
    负责全队血量监控、气氛值叠层及属性转化。
    """

    def __init__(self, owner: Any, duration: int):
        # owner 是芙宁娜实例
        super().__init__(owner, "普世欢腾", duration=duration, stacking_rule=StackingRule.REFRESH)
        
        self.points: float = 0.0
        self.max_points: float = 300.0  # 默认上限
        self.efficiency: float = 1.0    # 叠层效率 (C2 修改)
        
        # 从技能倍率表中提取转化比例 (假设战技等级已同步)
        self.skill_lv = owner.skill_params[2] # 大招等级
        self.dmg_ratio = ELEMENTAL_BURST_DATA["气氛值转化提升伤害比例"][1][self.skill_lv-1] / 100.0
        self.heal_ratio = ELEMENTAL_BURST_DATA["气氛值转化受治疗加成比例"][1][self.skill_lv-1] / 100.0

        # C1 处理
        if owner.constellation_level >= 1:
            self.points = 150.0
            self.max_points = 400.0

        # C2 处理
        if owner.constellation_level >= 2:
            self.efficiency = 3.5 # 提升 250% 即变为 350%

    def on_apply(self):
        """激活全队监听。"""
        self.owner.event_engine.subscribe(EventType.AFTER_HURT, self)
        self.owner.event_engine.subscribe(EventType.AFTER_HEAL, self)
        # 订阅伤害计算前置事件，用于动态注入增伤
        self.owner.event_engine.subscribe(EventType.BEFORE_CALCULATE, self)
        # 订阅治疗计算前置事件，用于动态注入受治疗加成
        self.owner.event_engine.subscribe(EventType.BEFORE_HEAL, self)

    def on_remove(self):
        """清理监听。"""
        self.owner.event_engine.unsubscribe(EventType.AFTER_HURT, self)
        self.owner.event_engine.unsubscribe(EventType.AFTER_HEAL, self)
        self.owner.event_engine.unsubscribe(EventType.BEFORE_CALCULATE, self)
        self.owner.event_engine.unsubscribe(EventType.BEFORE_HEAL, self)
        
        # 清除 C2 溢出带来的生命值加成
        if "芙宁娜C2生命加成" in self.owner.attribute_panel:
            del self.owner.attribute_panel["芙宁娜C2生命加成"]

    def handle_event(self, event: GameEvent):
        """核心事件分发中心。"""
        if event.event_type in [EventType.AFTER_HURT, EventType.AFTER_HEAL]:
            self._process_hp_change(event)
            
        elif event.event_type == EventType.BEFORE_CALCULATE:
            # 动态注入增伤 (全队有效)
            dmg_ctx = event.data.get("damage_context")
            if dmg_ctx:
                bonus = self.points * self.dmg_ratio
                # 使用审计接口注入增益
                dmg_ctx.add_modifier(source="芙宁娜-气氛值", stat="伤害加成", value=bonus)
                
        elif event.event_type == EventType.BEFORE_HEAL:
            # 动态注入受治疗加成 (全队有效)
            target = event.data.get("target")
            if target:
                bonus = self.points * self.heal_ratio
                # 此处假定 HealthSystem 会从 attribute_panel 实时读取
                # 暂时通过 data 传递给计算器，或者注入目标的临时属性
                event.data["fanfare_heal_bonus"] = bonus

    def _process_hp_change(self, event: GameEvent):
        """计算血量变动并转化为气氛值。"""
        target = event.target
        amount = 0.0
        
        if event.event_type == EventType.AFTER_HURT:
            amount = event.data.get("amount", 0.0)
        else: # AFTER_HEAL
            # 注意：只有实际回复量计入
            amount = getattr(event, "healing").final_value 

        if amount <= 0: return

        # 比例计算: (变动量 / 最大生命值) * 100
        max_hp = AttributeCalculator.get_hp(target)
        if max_hp <= 0: return
        
        change_points = (amount / max_hp) * 100.0 * self.efficiency
        
        # 更新总分
        old_points = self.points
        self.points += change_points
        
        # C2 溢出转化逻辑
        if self.owner.constellation_level >= 2:
            if self.points > self.max_points:
                overflow = self.points - self.max_points
                # 每 1 点溢出气氛值提升 0.35% HP上限, 至多 140%
                hp_bonus = min(140.0, overflow * 0.35)
                # 这里的加成应该加到 生命值% 上
                # 为了保持独立性，我们单独维护一个 key
                self.owner.attribute_panel["生命值%"] = self.owner.attribute_data["生命值%"] + hp_bonus
        
        # 气氛值自身上限钳制
        self.points = min(self.points, 1000.0 if self.owner.constellation_level >= 2 else self.max_points)

        # 仅在点数有显著变化时记录日志，避免刷屏
        if int(self.points) != int(old_points):
            get_emulation_logger().log_effect(
                self.owner, f"气氛值叠加: {old_points:.1f} -> {self.points:.1f}", action="更新"
            )

    def on_tick(self, target: Any):
        """每帧更新（如果需要处理衰减等，目前 Fanfare 持续期间不衰减）。"""
        pass
