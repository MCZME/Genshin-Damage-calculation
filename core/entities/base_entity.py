from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from core.context import get_context
from core.mechanics.aura import AuraManager
from core.mechanics.icd import ICDManager

if TYPE_CHECKING:
    from core.effect.common import ShieldEffect


class EntityState(Enum):
    """实体的生命周期状态。"""
    INIT = auto()      # 初始化
    ACTIVE = auto()    # 活跃中
    FINISHING = auto() # 正在结束
    DESTROYED = auto() # 已彻底销毁


class Faction(Enum):
    """实体所属阵营。"""
    PLAYER = auto()    # 玩家/友方
    ENEMY = auto()     # 敌人/敌对
    NEUTRAL = auto()   # 中立/环境物


class BaseEntity:
    """
    仿真世界中的实体基类。
    负责最底层的生命周期管理、上下文绑定与基础驱动。
    """

    def __init__(
        self, 
        name: str, 
        life_frame: float = float("inf"), 
        context: Optional[Any] = None
    ) -> None:
        """初始化基础实体。

        Args:
            name: 实体名称。
            life_frame: 实体的生存帧数，默认永久。
            context: 绑定的仿真上下文。
        """
        self.name: str = name
        self.life_frame: float = life_frame
        self.current_frame: int = 0
        self.state: EntityState = EntityState.ACTIVE
        
        # 上下文与事件引擎绑定
        self.ctx = context if context else get_context()
        self.event_engine = self.ctx.event_engine if self.ctx else None

    @property
    def is_active(self) -> bool:
        """判断实体是否处于活跃状态。"""
        return self.state == EntityState.ACTIVE

    def on_frame_update(self) -> None:
        """驱动实体每帧逻辑。统一入口，包含生命周期维护与业务逻辑触发。"""
        if self.state == EntityState.FINISHING:
            self.finish()
            return
            
        if self.state != EntityState.ACTIVE:
            return
        
        self.current_frame += 1
        if self.current_frame >= self.life_frame:
            self.finish()
            return
            
        # 执行具体子类的业务逻辑
        self._perform_tick()

    def _perform_tick(self) -> None:
        """[钩子] 实体的具体业务逻辑实现点。子类应重写此方法而非 on_frame_update。"""
        pass

    def finish(self) -> None:
        """终结实体生命周期，执行清理逻辑。"""
        if self.state not in [EntityState.ACTIVE, EntityState.FINISHING]:
            return
        self.state = EntityState.FINISHING
        self.on_finish()
        self.state = EntityState.DESTROYED

    def on_finish(self) -> None:
        """[钩子] 实体销毁前的清理逻辑。"""
        pass

    def on_finish(self) -> None:
        """[钩子] 实体销毁前的清理逻辑。"""
        pass

    def export_state(self) -> Dict[str, Any]:
        """导出基础状态快照。"""
        return {
            "name": self.name,
            "frame": self.current_frame,
            "state": self.state.name
        }


class CombatEntity(BaseEntity):
    """
    战斗实体类。
    增加了空间位置、阵营、元素附着、效果列表及 ICD 管理。
    """

    def __init__(
        self, 
        name: str, 
        faction: Faction = Faction.ENEMY,
        pos: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        facing: float = 0.0,
        hitbox: Tuple[float, float] = (0.5, 2.0),
        life_frame: float = float("inf"), 
        context: Optional[Any] = None
    ) -> None:
        """初始化战斗实体。"""
        super().__init__(name, life_frame, context)
        
        self.faction: Faction = faction
        self.pos: List[float] = list(pos)
        self.facing: float = facing
        self.hitbox: Tuple[float, float] = hitbox
        
        # 核心战斗组件
        self.aura: AuraManager = AuraManager()
        self.active_effects: List[Any] = []
        self.shield_effects: List["ShieldEffect"] = []
        
        # ICD 管理器 (用于追踪该实体受到的附着冷却)
        self.icd_manager: ICDManager = ICDManager(self)
        
        # [新] 属性审计链支持
        from core.systems.contract.modifier import ModifierRecord
        self.dynamic_modifiers: List[ModifierRecord] = []
        self.attribute_data: Dict[str, float] = {}

    def add_modifier(self, source: str, stat: str, value: float, op: str = "ADD") -> None:
        """向实体注入一个带来源的属性修饰符。"""
        from core.systems.contract.modifier import ModifierRecord
        self.dynamic_modifiers.append(ModifierRecord(source, stat, value, op))

    def export_state(self) -> Dict[str, Any]:
        """导出战斗状态快照。"""
        base = super().export_state()
        base.update({
            "pos": [round(x, 3) for x in self.pos],
            "facing": round(self.facing, 2),
            "faction": self.faction.name,
            "auras": self.aura.export_state(),
            "shield_count": len(self.shield_effects),
            "attributes": self.attribute_data.copy()
        })
        return base

    def set_position(self, x: float, z: float, y: Optional[float] = None) -> None:
        """设置实体在场景中的坐标。"""
        self.pos[0] = x
        self.pos[1] = z
        if y is not None:
            self.pos[2] = y

    def handle_damage(self, damage: Any) -> None:
        """处理受到的伤害。由子类实现。"""
        pass

    def heal(self, amount: float) -> None:
        """处理治疗。"""
        pass

    def hurt(self, amount: float) -> None:
        """处理受伤/扣血。"""
        pass

    def add_effect(self, effect: Any) -> None:
        """[接口] 向实体挂载一个效果。"""
        if effect not in self.active_effects:
            self.active_effects.append(effect)

    def remove_effect(self, effect: Any) -> None:
        """[接口] 从实体移除一个效果。"""
        if effect in self.active_effects:
            self.active_effects.remove(effect)

    def apply_elemental_aura(self, damage: Any) -> List[Any]:
        """接收元素附着的统一入口，包含 ICD 判定逻辑。"""
        # 1. 检查 ICD
        tag = getattr(damage.config, "icd_tag", "Default")
        group = getattr(damage.config, "icd_group", "Default")
        
        # 修正：显式判断 damage.source 是否为 None
        source_ent = getattr(damage, "source", None)
        if source_ent is None:
            source_ent = self
        
        multiplier = self.icd_manager.check_attachment(source_ent, tag, group)
        
        if multiplier <= 0:
            return []
            
        # 2. 应用元素附着
        final_u = damage.element[1] * multiplier
        results = self.aura.apply_element(damage.element[0], final_u)
        
        # 3. 反馈并发布反应事件
        from core.event import GameEvent, EventType
        from core.tool import get_current_time
        
        if hasattr(damage, "reaction_results"):
            damage.reaction_results.extend(results)
            
        for res in results:
            self.event_engine.publish(GameEvent(
                event_type=EventType.AFTER_ELEMENTAL_REACTION,
                frame=get_current_time(),
                source=source_ent,
                data={
                    "target": self,
                    "elemental_reaction": res
                }
            ))
            
        return results

    def _perform_tick(self) -> None:
        """驱动战斗实体的每帧逻辑。"""
        self.aura.update(self, 1/60)
        
        for eff in self.active_effects[:]:
            eff.on_frame_update(self)
            self.active_effects.remove(eff)
