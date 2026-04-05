from collections.abc import Callable
from typing import Any, TypeVar
from core.entities.base_entity import BaseEntity
from core.context import get_context

T = TypeVar("T", bound=BaseEntity)


class EntityFactory:
    """
    实体工厂。
    """

    @staticmethod
    def spawn_energy(
        num: int,
        character: Any,
        element_energy: Any,
        is_fixed: bool = False,
        is_alone: bool = False,
        time: int = 40,
    ) -> None:
        """
        统一的能量产生接口。

        Args:
            num: 产生数量（或球数）。
            character: 目标角色。
            element_energy: 元素类型与基础值，如 ("水", 2) 表示水元素微粒。
            is_fixed: 是否为固定回能。
            is_alone: 是否为独立回能。
            time: 延迟帧数。如果为 0，则立即触发回能事件。
        """
        if time != 0:
            from core.entities.energy import EnergyDropsObject

            ctx = get_context()
            # 创建单个实体，包含微粒数量信息
            entity = EnergyDropsObject(
                character=character,
                element_energy=element_energy,
                life_frame=time,
                is_fixed=is_fixed,
                is_alone=is_alone,
                count=num,
                context=ctx,
            )
            # 注册到 CombatSpace 以便帧更新
            if ctx and ctx.space:
                ctx.space.register(entity)
        else:
            from core.event import GameEvent, EventType
            from core.tool import get_current_time

            ctx = get_context()
            if ctx.event_engine:
                # 立即触发时，合并数量到 amount
                total_amount = (element_energy[0], element_energy[1] * num)
                energy_event = GameEvent(
                    event_type=EventType.BEFORE_ENERGY_CHANGE,
                    frame=get_current_time(),
                    source=character,
                    data={
                        "character": character,
                        "amount": total_amount,
                        "is_fixed": is_fixed,
                        "is_alone": is_alone,
                    },
                )
                ctx.event_engine.publish(energy_event)
