from enum import Enum, auto
from typing import Any, Optional, Tuple, List
from core.context import get_context
from core.mechanics.aura import AuraManager, Element

class EntityState(Enum):
    """实体的生命周期状态"""
    INIT = auto()      # 初始化
    ACTIVE = auto()    # 活跃中
    FINISHING = auto() # 正在结束
    DESTROYED = auto() # 已彻底销毁

class Faction(Enum):
    """实体所属阵营"""
    PLAYER = auto()    # 玩家/友方
    ENEMY = auto()     # 敌人/敌对
    NEUTRAL = auto()   # 中立/环境物

class BaseEntity:
    """
    仿真世界中的实体基类。
    负责最底层的生命周期管理。
    """
    def __init__(self, name: str, life_frame: float = float("inf"), context: Optional[Any] = None):
        self.name = name
        self.life_frame = life_frame
        self.current_frame = 0
        self.state = EntityState.ACTIVE
        
        # 上下文与事件引擎绑定
        self.ctx = context if context else get_context()
        self.event_engine = self.ctx.event_engine if self.ctx else None

    @property
    def is_active(self) -> bool:
        return self.state == EntityState.ACTIVE

    def update(self) -> None:
        """
        每帧驱动。不再强制要求传入 target。
        """
        if self.state != EntityState.ACTIVE:
            return
        
        self.current_frame += 1
        if self.current_frame >= self.life_frame:
            self.finish()
            return
            
        self.on_frame_update()

    def finish(self) -> None:
        if self.state != EntityState.ACTIVE:
            return
        self.state = EntityState.FINISHING
        self.on_finish()
        self.state = EntityState.DESTROYED

    def on_frame_update(self) -> None:
        pass

    def on_finish(self) -> None:
        pass

class CombatEntity(BaseEntity):
    """
    战斗实体类。
    所有可参与伤害计算与元素反应的物体均继承此类。
    """
    def __init__(self, 
                 name: str, 
                 faction: Faction = Faction.ENEMY,
                 pos: Tuple[float, float, float] = (0.0, 0.0, 0.0),
                 facing: float = 0.0,
                 hitbox_radius: float = 0.5, # 默认碰撞半径
                 life_frame: float = float("inf"), 
                 context: Optional[Any] = None):
        super().__init__(name, life_frame, context)
        
        self.faction = faction
        self.pos = list(pos)
        self.facing = facing
        self.hitbox_radius = hitbox_radius
        
        # 物理模拟组件
        self.aura = AuraManager()
        self.active_effects = []

    def set_position(self, x: float, z: float, y: Optional[float] = None):
        self.pos[0] = x
        self.pos[1] = z
        if y is not None:
            self.pos[2] = y

    def handle_damage(self, damage: Any) -> None:
        """
        接收伤害的统一入口。子类需实现具体的防御、抗性结算。
        """
        raise NotImplementedError("CombatEntity 子类必须实现 handle_damage")

    def apply_elemental_aura(self, damage: Any) -> List[Any]:
        """
        接收元素附着的统一入口。
        """
        # 默认调用内部的 AuraManager 处理
        return self.aura.apply_element(damage.element[0], float(damage.element[1]))

    def on_frame_update(self) -> None:
        """扩展驱动：每帧更新附着状态"""
        # 假设 60 FPS
        self.aura.update(1/60)
        
        # 更新持续性效果 (Effect)
        for eff in self.active_effects[:]:
            eff.update()
            if not getattr(eff, 'is_active', True):
                self.active_effects.remove(eff)
