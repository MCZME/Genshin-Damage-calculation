"""
场景实体基类。

场景实体是一种需要在场景中长时间存在的实体，承载一些特殊的逻辑。
支持：区域检测、周期触发、与角色交互等。
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from core.entities.base_entity import BaseEntity, Faction
from core.event import GameEvent, EventType
from core.tool import get_current_time

if TYPE_CHECKING:
    from core.context import SimulationContext


class SceneEntity(BaseEntity):
    """
    场景实体基类。

    长期存在于场景中，承载特殊逻辑。
    支持：范围效果、周期性触发、与角色交互等。
    """

    # 全局场景实体管理
    active_scenes: dict[str, list["SceneEntity"]] = {}

    def __init__(
        self,
        name: str,
        pos: tuple[float, float, float] = (0.0, 0.0, 0.0),
        facing: float = 0.0,
        hitbox: tuple[float, float] = (5.0, 5.0),
        faction: Faction = Faction.NEUTRAL,
        life_frame: float = float("inf"),
        context: "SimulationContext | None" = None,
        owner: Any = None,
        tick_interval: int = 60,
        detection_radius: float | None = None,
        affect_factions: list[Faction] | None = None,
    ) -> None:
        """初始化场景实体。

        Args:
            name: 实体名称。
            pos: 位置坐标。
            facing: 朝向角度。
            hitbox: 碰撞盒尺寸。
            faction: 阵营。
            life_frame: 生存帧数。
            context: 仿真上下文。
            owner: 所属实体（如创建者角色）。
            tick_interval: 周期触发间隔（帧）。
            detection_radius: 区域检测半径，默认使用 hitbox[0]。
            affect_factions: 影响的阵营列表，默认 [ENEMY, PLAYER]。
        """
        super().__init__(name, life_frame, pos, facing, hitbox, faction, context)

        self.owner = owner
        self.tick_interval = tick_interval
        self.detection_radius = detection_radius if detection_radius is not None else hitbox[0]
        self.affect_factions = affect_factions if affect_factions else [Faction.ENEMY, Faction.PLAYER]

        self.tick_timer = 0
        self._entities_in_range: set[int] = set()  # 区域内实体 ID

        # 注册到全局管理
        self._register_scene()

    def _register_scene(self) -> None:
        """注册到全局场景管理。"""
        scene_type = self.name.split("(")[0]  # 提取基础名称
        if scene_type not in SceneEntity.active_scenes:
            SceneEntity.active_scenes[scene_type] = []
        SceneEntity.active_scenes[scene_type].append(self)

    def _unregister_scene(self) -> None:
        """从全局管理注销。"""
        scene_type = self.name.split("(")[0]
        if scene_type in SceneEntity.active_scenes:
            if self in SceneEntity.active_scenes[scene_type]:
                SceneEntity.active_scenes[scene_type].remove(self)

    def _perform_tick(self) -> None:
        """每帧逻辑。"""
        super()._perform_tick()

        # 处理区域检测
        self._check_entities_in_range()

        # 处理周期触发
        self.tick_timer += 1
        if self.tick_timer >= self.tick_interval:
            self.tick_timer = 0
            self._on_tick()

    def _check_entities_in_range(self) -> None:
        """检测区域内的实体变化。"""
        if not self.ctx or not self.ctx.space:
            return

        current_entities: set[int] = set()

        for faction in self.affect_factions:
            entities = self.ctx.space.get_entities_in_range(
                origin=(self.pos[0], self.pos[1]),
                radius=self.detection_radius,
                faction=faction,
            )
            for e in entities:
                if e.entity_id == self.entity_id:
                    continue  # 排除自身

                current_entities.add(e.entity_id)

                # 进入检测
                if e.entity_id not in self._entities_in_range:
                    self._on_entity_enter(e)

                # 持续检测（每帧）
                self._on_entity_stay(e)

        # 离开检测
        left_ids = self._entities_in_range - current_entities
        for eid in left_ids:
            entity = self._find_entity_by_id(eid)
            if entity:
                self._on_entity_exit(entity)

        self._entities_in_range = current_entities

    def _find_entity_by_id(self, entity_id: int) -> BaseEntity | None:
        """根据 ID 查找实体。"""
        if not self.ctx or not self.ctx.space:
            return None
        for e in self.ctx.space.get_all_entities():
            if e.entity_id == entity_id:
                return e
        return None

    def _on_entity_enter(self, entity: Any) -> None:
        """实体进入区域。子类可重写此方法。"""
        if self.event_engine:
            self.event_engine.publish(
                GameEvent(
                    event_type=EventType.SCENE_ENTITY_ENTER,
                    frame=get_current_time(),
                    source=self,
                    data={"scene_entity": self, "entity": entity},
                )
            )

    def _on_entity_exit(self, entity: Any) -> None:
        """实体离开区域。子类可重写此方法。"""
        if self.event_engine:
            self.event_engine.publish(
                GameEvent(
                    event_type=EventType.SCENE_ENTITY_EXIT,
                    frame=get_current_time(),
                    source=self,
                    data={"scene_entity": self, "entity": entity},
                )
            )

    def _on_entity_stay(self, entity: Any) -> None:
        """实体持续在区域内。子类可重写此方法。"""
        pass

    def _on_tick(self) -> None:
        """周期触发。子类可重写此方法。"""
        if self.event_engine:
            self.event_engine.publish(
                GameEvent(
                    event_type=EventType.SCENE_ENTITY_TICK,
                    frame=get_current_time(),
                    source=self,
                    data={"scene_entity": self},
                )
            )

    def refresh(self) -> None:
        """刷新存在时间。"""
        self.current_frame = 0

    def on_finish(self) -> None:
        """销毁时清理。"""
        self._unregister_scene()
        super().on_finish()

    @classmethod
    def get_active_scenes(cls, scene_type: str) -> list["SceneEntity"]:
        """获取指定类型的所有活跃场景实体。"""
        return cls.active_scenes.get(scene_type, [])

    @classmethod
    def count_active_scenes(cls, scene_type: str) -> int:
        """计算指定类型的活跃场景实体数量。"""
        return len(cls.active_scenes.get(scene_type, []))

    def export_state(self) -> dict[str, Any]:
        """导出状态快照。"""
        base = super().export_state()
        base.update(
            {
                "detection_radius": self.detection_radius,
                "entities_in_range": len(self._entities_in_range),
                "tick_timer": self.tick_timer,
            }
        )
        return base

    def export_static_data(self) -> dict[str, Any]:
        """导出场景实体的静态配置数据。"""
        data = super().export_static_data()
        data["entity_type"] = "SCENE_ENTITY"
        # 记录所属者 ID
        if self.owner is not None:
            data["owner_id"] = getattr(self.owner, "entity_id", None)
        # 场景实体特有属性
        data["detection_radius"] = self.detection_radius
        data["tick_interval"] = self.tick_interval
        return data
