from typing import Any, List, Optional, Tuple

from core.systems.contract.damage import Damage
from core.systems.contract.reaction import ElementalReactionType
from core.context import get_context
from core.entities.base_entity import CombatEntity, Faction
from core.event import DamageEvent, EventType
from core.mechanics.aura import Element
from core.tool import get_current_time, get_reaction_multiplier


class DendroCoreEntity(CombatEntity):
    """
    草原核实体 (绽放产物)。
    
    具备自动爆炸、受火/雷攻击触发烈/超绽放的特性。
    """
    active_cores: List["DendroCoreEntity"] = []

    def __init__(
        self, 
        creator: Any, 
        pos: Tuple[float, float, float],
        life_frame: int = 360 # 默认 6 秒
    ) -> None:
        """初始化草原核。"""
        super().__init__(
            name="草原核", 
            faction=Faction.NEUTRAL, # 中立实体，不主动攻击
            pos=pos,
            hitbox=(0.5, 0.5), # 较小的碰撞体
            life_frame=life_frame
        )
        self.creator = creator
        # 记录创建时的等级系数
        self.level_mult = get_reaction_multiplier(creator.level)
        
        # 上限管理
        DendroCoreEntity.active_cores.append(self)
        if len(DendroCoreEntity.active_cores) > 5:
            oldest = DendroCoreEntity.active_cores.pop(0)
            oldest.finish()

    def handle_damage(self, damage: "Damage") -> None:
        """
        处理打击逻辑：检测火/雷元素以触发二级反应。
        """
        el = damage.element[0]
        
        if el == Element.PYRO:
            self._trigger_burgeon()
        elif el == Element.ELECTRO:
            self._trigger_hyperbloom()

    def on_finish(self) -> None:
        """生命周期结束逻辑：如果是自然过期或被顶替，触发默认爆炸。"""
        if self in DendroCoreEntity.active_cores:
            DendroCoreEntity.active_cores.remove(self)
            
        if self.state != "DESTROYED":
            self._trigger_bloom_explosion()

    def _trigger_bloom_explosion(self) -> None:
        """触发基础绽放爆炸 (草元素范围伤害)。"""
        self._publish_aoe_damage(
            name="绽放爆炸",
            reaction_type=ElementalReactionType.BLOOM,
            multiplier=2.0,
            element=Element.DENDRO
        )
        self.state = "FINISHING"

    def _trigger_burgeon(self) -> None:
        """触发烈绽放 (大范围草元素伤害)。"""
        self._publish_aoe_damage(
            name="烈绽放",
            reaction_type=ElementalReactionType.BURGEON,
            multiplier=3.0,
            element=Element.DENDRO,
            radius=5.0
        )
        self.state = "FINISHING"

    def _trigger_hyperbloom(self) -> None:
        """触发超绽放 (单体追踪草元素伤害)。"""
        # 超绽放寻找最近的敌人
        target = self.ctx.space._find_closest(
            origin=(self.pos[0], self.pos[1]), 
            faction=Faction.ENEMY
        )
        
        if target:
            dmg = self._create_react_damage("超绽放", 3.0, Element.DENDRO)
            self.event_engine.publish(DamageEvent(
                event_type=EventType.BEFORE_DAMAGE,
                frame=get_current_time(),
                source=self.creator,
                target=target,
                damage=dmg
            ))
        self.state = "FINISHING"

    def _publish_aoe_damage(
        self, 
        name: str, 
        reaction_type: ElementalReactionType, 
        multiplier: float, 
        element: Element,
        radius: float = 3.0
    ) -> None:
        """发布范围伤害事件。"""
        dmg = self._create_react_damage(name, multiplier, element)
        # 手动执行一次 AOE 广播
        from core.systems.contract.attack import AttackConfig, HitboxConfig, AOEShape
        dmg.config = AttackConfig(
            hitbox=HitboxConfig(shape=AOEShape.SPHERE, radius=radius),
            attack_tag="剧变反应"
        )
        
        # 产生伤害 (源仍记为草原核的创建者)
        self.ctx.space.broadcast_damage(self.creator, dmg)

    def _create_react_damage(self, name: str, mult: float, element: Element) -> Damage:
        """快捷创建剧变伤害对象。"""
        from core.systems.contract.attack import AttackConfig
        dmg = Damage(
            damage_multiplier=0,
            element=(element, 0.0),
            config=AttackConfig(attack_tag="剧变反应"),
            name=name
        )
        dmg.add_data("等级系数", self.level_mult)
        dmg.add_data("反应系数", mult)
        return dmg


class CrystalShardEntity(CombatEntity):
    """
    结晶反应产生的晶片实体。
    
    存在于场景中，当玩家靠近时自动拾取并转化为结晶盾。
    """

    def __init__(
        self, 
        creator: Any, 
        element: Element,
        pos: Tuple[float, float, float],
        base_shield_hp: float,
        life_frame: int = 900 # 晶片通常存在 15 秒
    ) -> None:
        """初始化结晶晶片。"""
        super().__init__(
            name=f"结晶晶片({element.value})",
            faction=Faction.NEUTRAL,
            pos=pos,
            hitbox=(1.0, 1.0), # 较大的拾取范围
            life_frame=life_frame
        )
        self.creator = creator
        self.shield_element = element
        self.base_shield_hp = base_shield_hp

    def on_frame_update(self) -> None:
        """每帧检测周围玩家以实现自动拾取。"""
        super().on_frame_update()
        
        # 检索 1.5 米内的玩家实体
        nearby_players = self.ctx.space.get_entities_in_range(
            origin=(self.pos[0], self.pos[1]),
            radius=1.5,
            faction=Faction.PLAYER
        )
        
        if nearby_players:
            self._on_picked_up(nearby_players[0])

    def _on_picked_up(self, player: Any) -> None:
        """被玩家拾取时的逻辑。"""
        from core.systems.shield_system import ShieldSystem
        from core.systems.contract.shield import ShieldConfig
        
        shield_sys = self.ctx.get_system(ShieldSystem)
        if shield_sys:
            config = ShieldConfig(
                base_hp=self.base_shield_hp,
                element=self.shield_element,
                duration=15 * 60,
                name=f"结晶盾 ({self.shield_element.value})",
                creator=self.creator
            )
            shield_sys.add_shield(player, config)
            
        # 销毁自己
        self.finish()
