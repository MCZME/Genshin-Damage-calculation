from typing import Any, Tuple, List
from core.entities.base_entity import CombatEntity, Faction
from core.action.damage import Damage, DamageType
from core.action.action_data import AttackConfig, HitboxConfig, AOEShape
from core.mechanics.aura import Element
from core.logger import get_emulation_logger

class DendroCoreEntity(CombatEntity):
    """
    草原核实体 (Dendro Core)。
    - 属于中立阵营 (NEUTRAL)。
    - 受到火元素伤害触发烈绽放 (Burgeon)。
    - 受到雷元素伤害触发超绽放 (Hyperbloom)。
    - 存续时间 6s 或超过 5 个后自动爆发。
    """
    active_cores: List['DendroCoreEntity'] = []
    MAX_CORES = 5

    def __init__(self, source: Any, pos: Tuple[float, float, float]):
        super().__init__(
            name="草原核",
            faction=Faction.NEUTRAL,
            pos=pos,
            hitbox=(0.3, 0.3), # 草原核体积较小
            life_frame=360    # 6秒寿命
        )
        self.source = source # 触发绽放的角色
        
        # 记录到全局列表以管理数量
        DendroCoreEntity.active_cores.append(self)
        if len(DendroCoreEntity.active_cores) > self.MAX_CORES:
            oldest = DendroCoreEntity.active_cores.pop(0)
            oldest.state = oldest.state.FINISHING # 触发自然爆发

    def handle_damage(self, damage: Damage) -> None:
        """草原核对外界伤害的响应"""
        element = damage.element[0]
        
        if element == Element.PYRO:
            self._trigger_burgeon()
        elif element == Element.ELECTRO:
            self._trigger_hyperbloom()

    def _trigger_burgeon(self):
        """烈绽放：大范围草元素伤害"""
        get_emulation_logger().log_effect("💥 触发烈绽放！")
        self._explode(is_burgeon=True)
        self.finish()

    def _trigger_hyperbloom(self):
        """超绽放：追踪弹草元素伤害 (此处简化为小范围 AOE)"""
        get_emulation_logger().log_effect("⚡ 触发超绽放！")
        self._explode(is_hyperbloom=True)
        self.finish()

    def on_finish(self) -> None:
        """自然结束时的爆发逻辑 (普通绽放爆发)"""
        if self in DendroCoreEntity.active_cores:
            DendroCoreEntity.active_cores.remove(self)
        
        # 如果不是因为触发烈/超绽放而结束，则执行普通爆发
        if self.state != self.state.FINISHING:
            self._explode(is_burgeon=False, is_hyperbloom=False)

    def _explode(self, is_burgeon=False, is_hyperbloom=False):
        """执行最终伤害广播"""
        # 计算剧变反应伤害 (此处简化倍率逻辑，实际应根据 source 等级计算)
        # 烈绽放 3.0, 超绽放 3.0, 绽放 2.0
        base_multiplier = 3.0 if (is_burgeon or is_hyperbloom) else 2.0
        
        config = AttackConfig(
            element_u=0.0, # 剧变反应通常不附着或有特殊附着
            hitbox=HitboxConfig(
                shape=AOEShape.CYLINDER,
                radius=5.0 if is_burgeon else 1.0 # 烈绽放范围大
            )
        )
        
        dmg = Damage(
            damage_multiplier=base_multiplier,
            element=(Element.DENDRO, 0.0),
            damage_type=DamageType.REACTION,
            name="烈绽放" if is_burgeon else ("超绽放" if is_hyperbloom else "绽放爆发"),
            config=config
        )
        dmg.set_source(self.source)
        
        if self.ctx and self.ctx.space:
            self.ctx.space.broadcast_damage(self, dmg)

class LightningBladeObject(CombatEntity):
    """(保留原有逻辑并升级为 CombatEntity)"""
    def __init__(self, pos=(0,0,0)):
        super().__init__("强能之雷", Faction.NEUTRAL, pos=pos)
        # ... 保持原有雷共鸣逻辑
