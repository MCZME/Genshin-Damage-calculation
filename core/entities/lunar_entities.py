"""
月曜反应实体类。

包含：
- ProsperousCoreEntity：丰穰之核（角色技能触发生成）
- ThunderCloudEntity：雷暴云（月感电产物）
- LunarCageEntity：月笼（月结晶产物）
"""

from __future__ import annotations
import random
from typing import Any

from core.entities.base_entity import CombatEntity, Faction, EntityState
from core.entities.elemental_entities import DendroCoreEntity
from core.event import GameEvent, EventType
from core.mechanics.aura import Element
from core.systems.contract.reaction import ElementalReactionType
from core.tool import get_current_time


class ProsperousCoreEntity(DendroCoreEntity):
    """
    丰穰之核 - 由角色技能触发生成的特殊草原核。

    注意：非月绽放反应直接产物。月绽放仅生成普通草原核和草露资源。

    与普通草原核的区别：
    - 存在时间仅 0.4 秒（24 帧）
    - 迸发范围更大（6.5 米）
    - 仍造成剧变伤害（非月曜伤害）
    """

    def __init__(
        self,
        creator: Any,
        pos: tuple[float, float, float],
        life_frame: int = 24,  # 0.4 秒
    ) -> None:
        """初始化丰穰之核。"""
        super().__init__(creator, pos, life_frame)
        self.name = "丰穰之核"
        self.explosion_radius = 6.5  # 米

    def _trigger_bloom_explosion(self) -> None:
        """触发丰穰之核爆炸（大范围草元素剧变伤害）。"""
        self._publish_aoe_damage(
            name="丰穰之核爆炸",
            reaction_type=ElementalReactionType.BLOOM,
            multiplier=2.0,
            element=Element.DENDRO,
            radius=self.explosion_radius,
        )
        self.state = EntityState.FINISHING


class ThunderCloudEntity(CombatEntity):
    """
    雷暴云 - 月感电产物。

    特性：
    - 索敌范围 8 米半径 × 8 米高
    - 每 2 秒攻击一次（首次延迟 0.25 秒）
    - 攻击目标需有来自角色的附着
    - 造成月曜伤害，基于所有附着来源角色加权求和
    - 移动范围不超过生成位置 5 米
    """

    active_clouds: list["ThunderCloudEntity"] = []

    def __init__(
        self,
        creator: Any,
        pos: tuple[float, float, float],
        source_characters: list[Any] | None = None,
        life_frame: int = 540,  # 9 秒
    ) -> None:
        """初始化雷暴云。"""
        super().__init__(
            name="雷暴云",
            faction=Faction.PLAYER,
            pos=pos,
            hitbox=(8.0, 8.0),  # 索敌范围
            life_frame=life_frame,
        )
        self.is_targetable = False  # 雷暴云不可被选为攻击目标
        self.creator = creator
        self.spawn_pos = list(pos)  # 生成位置（用于移动限制）
        self.max_move_distance = 5.0  # 最大移动距离

        # 附着来源角色
        self.source_characters: list[Any] = source_characters or []

        # 攻击计时
        self.attack_timer: float = 0.0
        self.attack_interval: float = 2.0  # 秒
        self.initial_delay: float = 0.25  # 首次攻击延迟
        self.has_initial_attacked: bool = False

        # 上限管理
        ThunderCloudEntity.active_clouds.append(self)
        self._check_cloud_limit()

    def _check_cloud_limit(self) -> None:
        """检查雷暴云数量限制，距离过近时销毁一朵。"""
        if len(ThunderCloudEntity.active_clouds) <= 1:
            return

        for other in ThunderCloudEntity.active_clouds[:-1]:
            if other is self:
                continue
            dist = self._distance_to(other)
            if dist < 2.0:  # 距离过近
                other.finish()
                break

    def _distance_to(self, other: CombatEntity) -> float:
        """计算与另一实体的距离。"""
        dx = self.pos[0] - other.pos[0]
        dz = self.pos[1] - other.pos[1]
        return (dx * dx + dz * dz) ** 0.5

    def add_source_character(self, character: Any) -> None:
        """添加附着来源角色。"""
        if character not in self.source_characters:
            self.source_characters.append(character)

    def refresh(self) -> None:
        """刷新存在时间。"""
        self.current_frame = 0

    def _perform_tick(self) -> None:
        """每帧逻辑：攻击计时与移动。"""
        super()._perform_tick()

        # 攻击计时
        self.attack_timer += 1 / 60

        # 首次攻击延迟
        if not self.has_initial_attacked:
            if self.attack_timer >= self.initial_delay:
                self._try_attack()
                self.has_initial_attacked = True
                self.attack_timer = 0.0
        else:
            # 后续攻击
            if self.attack_timer >= self.attack_interval:
                self._try_attack()
                self.attack_timer = 0.0

        # 尝试跟随角色移动
        self._try_move_towards_creator()

    def _try_move_towards_creator(self) -> None:
        """尝试向创建者方向移动。"""
        if not self.creator:
            return

        # 计算与生成位置的距离
        dx = self.creator.pos[0] - self.spawn_pos[0]
        dz = self.creator.pos[1] - self.spawn_pos[1]
        dist = (dx * dx + dz * dz) ** 0.5

        # 如果创建者在移动范围内，向其靠近
        if dist <= self.max_move_distance:
            target_x = self.creator.pos[0]
            target_z = self.creator.pos[1]
        else:
            # 限制在最大距离内
            ratio = self.max_move_distance / dist
            target_x = self.spawn_pos[0] + dx * ratio
            target_z = self.spawn_pos[1] + dz * ratio

        # 平滑移动
        move_speed = 0.1  # 每帧移动距离
        self.pos[0] += (target_x - self.pos[0]) * move_speed
        self.pos[1] += (target_z - self.pos[1]) * move_speed

    def _try_attack(self) -> None:
        """尝试攻击目标。"""
        if not self.ctx or not self.ctx.space:
            return

        # 查找索敌范围内的目标
        targets = self.ctx.space.get_entities_in_range(
            origin=(self.pos[0], self.pos[1]),
            radius=8.0,
            faction=Faction.ENEMY,
        )

        for target in targets:
            # 检查目标是否有来自角色的附着
            if self._has_character_aura(target):
                self._perform_attack(target)
                return

    def _has_character_aura(self, target: Any) -> bool:
        """检查目标的雷水共存是否至少其一来自角色。

        月感电攻击条件：
        - 目标必须有雷水共存状态
        - 雷水共存中至少有一个附着来自角色
        """
        if not hasattr(target, "aura"):
            return False

        hydro_aura = None
        electro_aura = None

        for aura in target.aura.auras:
            if aura.element == Element.HYDRO:
                hydro_aura = aura
            elif aura.element == Element.ELECTRO:
                electro_aura = aura

        # 必须有雷水共存
        if hydro_aura is None and electro_aura is None:
            return False

        # 至少其一来自角色
        has_hydro_from_char = hydro_aura is not None and hydro_aura.source_character is not None
        has_electro_from_char = (
            electro_aura is not None and electro_aura.source_character is not None
        )

        return bool(has_hydro_from_char or has_electro_from_char)

    def _perform_attack(self, target: Any) -> None:
        """执行攻击，发布事件供 ReactionSystem 处理。"""
        # 收集参与伤害计算的角色
        contributing_chars = self._get_contributing_characters(target)

        if self.event_engine:
            self.event_engine.publish(GameEvent(
                event_type=EventType.LUNAR_CHARGED_TICK,
                frame=get_current_time(),
                source=self,
                data={
                    "cloud": self,
                    "target": target,
                    "source_characters": contributing_chars,
                }
            ))

    def _get_contributing_characters(self, target: Any) -> list[Any]:
        """获取参与伤害计算的角色列表。"""
        characters = set()

        # 从目标附着中收集来源角色
        for aura in target.aura.auras:
            if aura.source_character:
                characters.add(aura.source_character)

        # 合并雷暴云记录的来源角色
        for char in self.source_characters:
            characters.add(char)

        return list(characters)

    def on_finish(self) -> None:
        """销毁时从列表移除。"""
        if self in ThunderCloudEntity.active_clouds:
            ThunderCloudEntity.active_clouds.remove(self)


class LunarCageEntity(CombatEntity):
    """
    月笼 - 月结晶产物。

    特性：
    - 索敌范围 12 米半径 × 5 米高
    - 存在时间 9 秒，无攻击则销毁
    - 每 3 次月结晶触发 3 枚月笼各攻击一次
    - 伤害范围小（0.5 米）
    - 不参与岩造物公共上限
    """

    active_cages: list["LunarCageEntity"] = []

    def __init__(
        self,
        creator: Any,
        pos: tuple[float, float, float],
        life_frame: int = 540,  # 9 秒
    ) -> None:
        """初始化月笼。"""
        super().__init__(
            name="月笼",
            faction=Faction.PLAYER,
            pos=pos,
            hitbox=(12.0, 5.0),  # 索敌范围
            life_frame=life_frame,
        )
        self.is_targetable = False  # 月笼不可被选为攻击目标
        self.creator = creator
        self.attack_cooldown: float = 0.0
        self.has_attacked: bool = False  # 是否进行过谐奏攻击
        self.time_since_last_attack: float = 0.0

        # 上限管理
        LunarCageEntity.active_cages.append(self)

    def refresh(self) -> None:
        """刷新存活时间（攻击后调用）。"""
        self.time_since_last_attack = 0.0

    def _perform_tick(self) -> None:
        """每帧逻辑：检查超时。"""
        super()._perform_tick()

        # 更新无攻击时间
        self.time_since_last_attack += 1 / 60

        # 超过 9 秒无攻击则销毁
        if self.time_since_last_attack >= 9.0:
            self.finish()

    @classmethod
    def count_nearby_cages(cls, pos: tuple[float, float, float], radius: float = 12.0) -> int:
        """计算指定位置附近的月笼数量。"""
        count = 0
        for cage in cls.active_cages:
            dx = cage.pos[0] - pos[0]
            dz = cage.pos[1] - pos[1]
            if (dx * dx + dz * dz) ** 0.5 <= radius:
                count += 1
        return count

    @classmethod
    def get_nearby_cages(cls, pos: tuple[float, float, float], radius: float = 12.0) -> list["LunarCageEntity"]:
        """获取指定位置附近的月笼列表。"""
        cages = []
        for cage in cls.active_cages:
            dx = cage.pos[0] - pos[0]
            dz = cage.pos[1] - pos[1]
            if (dx * dx + dz * dz) ** 0.5 <= radius:
                cages.append(cage)
        return cages

    @classmethod
    def trigger_attack(cls, target: Any, source_characters: list[Any]) -> None:
        """
        触发谐奏攻击。

        Args:
            target: 攻击目标
            source_characters: 参与伤害计算的角色列表
        """
        if not cls.active_cages:
            return

        # 随机选择 3 枚月笼进行攻击
        attacking_cages = random.sample(
            cls.active_cages,
            min(3, len(cls.active_cages))
        )

        for cage in attacking_cages:
            cage._perform_attack(target, source_characters)

    def _perform_attack(self, target: Any, source_characters: list[Any]) -> None:
        """执行单次谐奏攻击。"""
        if self.event_engine:
            self.event_engine.publish(GameEvent(
                event_type=EventType.LUNAR_CRYSTALLIZE_ATTACK,
                frame=get_current_time(),
                source=self,
                data={
                    "cage": self,
                    "target": target,
                    "source_characters": source_characters,
                }
            ))

        # 刷新存活时间
        self.refresh()

    def on_finish(self) -> None:
        """销毁时从列表移除。"""
        if self in LunarCageEntity.active_cages:
            LunarCageEntity.active_cages.remove(self)
