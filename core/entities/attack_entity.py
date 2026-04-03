"""
攻击实体基类。

攻击实体是一种可以承载一次攻击的实体，在满足触发条件时释放攻击。
支持多种触发模式：生命周期结束、命中帧、追踪碰撞等。
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Any, TYPE_CHECKING

from core.entities.base_entity import BaseEntity, Faction
from core.event import GameEvent, EventType
from core.tool import get_current_time

if TYPE_CHECKING:
    from core.context import SimulationContext
    from core.systems.contract.damage import Damage


class AttackTriggerType(Enum):
    """攻击触发类型。"""

    ON_FINISH = auto()  # 生命周期结束时触发
    ON_HIT_FRAME = auto()  # 到达指定命中帧时触发
    ON_PROXIMITY = auto()  # 靠近目标时触发
    TRACKING = auto()  # 追踪模式（移动追踪目标，碰撞时触发）


class TargetingMode(Enum):
    """目标选择模式。"""

    CLOSEST = auto()  # 最近目标
    RANDOM = auto()  # 随机目标
    FIXED = auto()  # 固定目标（需要预设）


class AttackEntity(BaseEntity):
    """
    攻击实体基类。

    承载一次攻击，在满足触发条件时释放。
    支持：延迟攻击、追踪攻击、条件触发等多种模式。
    """

    def __init__(
        self,
        name: str,
        damage: "Damage",
        source: Any,
        pos: tuple[float, float, float] = (0.0, 0.0, 0.0),
        facing: float = 0.0,
        hitbox: tuple[float, float] = (0.5, 0.5),
        faction: Faction = Faction.PLAYER,
        life_frame: float = 60,
        trigger_type: AttackTriggerType = AttackTriggerType.ON_FINISH,
        targeting_mode: TargetingMode = TargetingMode.CLOSEST,
        tracking_speed: float = 0.0,
        tracking_target: Any = None,
        context: "SimulationContext | None" = None,
    ) -> None:
        """初始化攻击实体。

        Args:
            name: 实体名称。
            damage: 伤害对象。
            source: 伤害来源角色。
            pos: 位置坐标。
            facing: 朝向角度。
            hitbox: 碰撞盒尺寸。
            faction: 阵营。
            life_frame: 生存帧数。
            trigger_type: 触发类型。
            targeting_mode: 索敌模式。
            tracking_speed: 追踪速度（仅 TRACKING 模式有效）。
            tracking_target: 追踪目标（仅 TRACKING/ON_PROXIMITY 模式有效）。
            context: 仿真上下文。
        """
        super().__init__(name, life_frame, pos, facing, hitbox, faction, context)

        self.damage = damage
        self.source = source
        self.trigger_type = trigger_type
        self.targeting_mode = targeting_mode
        self.tracking_speed = tracking_speed
        self.tracking_target = tracking_target

        self.has_attacked = False  # 是否已释放攻击

        # 命中帧模式
        self.hit_frames: list[int] = []
        self.hit_index = 0

    def set_hit_frames(self, frames: list[int]) -> None:
        """设置命中帧（用于多段攻击）。"""
        self.hit_frames = sorted(frames)
        self.trigger_type = AttackTriggerType.ON_HIT_FRAME

    def _perform_tick(self) -> None:
        """每帧逻辑：处理追踪、命中帧判定。"""
        super()._perform_tick()

        if self.has_attacked:
            return

        if self.trigger_type == AttackTriggerType.ON_HIT_FRAME:
            self._check_hit_frame()
        elif self.trigger_type == AttackTriggerType.ON_PROXIMITY:
            self._check_proximity()
        elif self.trigger_type == AttackTriggerType.TRACKING:
            self._perform_tracking()

    def _check_hit_frame(self) -> None:
        """检查是否到达命中帧。"""
        if self.hit_index < len(self.hit_frames):
            if self.current_frame >= self.hit_frames[self.hit_index]:
                self._execute_attack()
                self.hit_index += 1

    def _check_proximity(self) -> None:
        """检查是否靠近目标。"""
        target = self.tracking_target
        if not target:
            return

        dx = target.pos[0] - self.pos[0]
        dz = target.pos[1] - self.pos[1]
        dist = (dx * dx + dz * dz) ** 0.5

        if dist <= self.hitbox[0] + target.hitbox[0]:
            self._execute_attack()

    def _perform_tracking(self) -> None:
        """执行追踪移动。"""
        target = self.tracking_target
        if not target:
            return

        dx = target.pos[0] - self.pos[0]
        dz = target.pos[1] - self.pos[1]
        dist = (dx * dx + dz * dz) ** 0.5

        if dist > 0:
            speed = self.tracking_speed
            self.pos[0] += (dx / dist) * speed
            self.pos[1] += (dz / dist) * speed

        if dist <= self.hitbox[0] + target.hitbox[0]:
            self._execute_attack()

    def on_finish(self) -> None:
        """生命周期结束时触发攻击（如果尚未攻击且触发类型为 ON_FINISH）。"""
        if not self.has_attacked:
            if self.trigger_type == AttackTriggerType.ON_FINISH:
                self._execute_attack()
        super().on_finish()

    def _execute_attack(self) -> None:
        """执行攻击：发布 BEFORE_DAMAGE 事件。"""
        if self.has_attacked:
            return

        self.has_attacked = True
        dmg = self.damage
        dmg.set_source(self.source)

        # 自动索敌
        if not dmg.target and self.ctx and self.ctx.space:
            target = self._find_target()
            if target:
                dmg.set_target(target)

        # 发布伤害事件
        if self.event_engine:
            self.event_engine.publish(
                GameEvent(
                    event_type=EventType.BEFORE_DAMAGE,
                    frame=get_current_time(),
                    source=self.source,
                    data={
                        "character": self.source,
                        "damage": dmg,
                        "attack_entity": self,
                    },
                )
            )

    def _find_target(self) -> BaseEntity | None:
        """根据索敌模式寻找目标。"""
        if not self.ctx or not self.ctx.space:
            return None

        target_faction = Faction.ENEMY if self.faction == Faction.PLAYER else Faction.PLAYER
        candidates = self.ctx.space.get_entities_in_range(
            origin=(self.pos[0], self.pos[1]),
            radius=50.0,
            faction=target_faction,
        )

        if not candidates:
            return None

        if self.targeting_mode == TargetingMode.CLOSEST:
            candidates.sort(
                key=lambda e: (e.pos[0] - self.pos[0]) ** 2 + (e.pos[1] - self.pos[1]) ** 2
            )
            return candidates[0]
        elif self.targeting_mode == TargetingMode.RANDOM:
            import random

            return random.choice(candidates)
        elif self.targeting_mode == TargetingMode.FIXED:
            return self.tracking_target if self.tracking_target in candidates else candidates[0]

        return candidates[0]

    def export_state(self) -> dict[str, Any]:
        """导出状态快照。"""
        base = super().export_state()
        base.update(
            {
                "has_attacked": self.has_attacked,
                "trigger_type": self.trigger_type.name,
                "targeting_mode": self.targeting_mode.name,
            }
        )
        return base

    def export_static_data(self) -> dict[str, Any]:
        """导出攻击实体的静态配置数据。"""
        data = super().export_static_data()
        data["entity_type"] = "ATTACK_ENTITY"
        # 记录来源 ID
        if self.source is not None:
            data["owner_id"] = getattr(self.source, "entity_id", None)
        # 攻击实体特有属性（用于复盘分析）
        data["trigger_type"] = self.trigger_type.name
        data["targeting_mode"] = self.targeting_mode.name
        return data
