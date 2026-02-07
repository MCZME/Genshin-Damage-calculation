from enum import Enum, auto
from typing import Any, Optional, Tuple, List
from core.context import get_context
from core.mechanics.aura import AuraManager, Element
from core.mechanics.icd import ICDManager

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
        if self.state == EntityState.FINISHING:
            self.finish()
            return
            
        if self.state != EntityState.ACTIVE:
            return
        
        self.current_frame += 1
        if self.current_frame >= self.life_frame:
            self.finish()
            return
            
        self.on_frame_update()

    def finish(self) -> None:
        if self.state not in [EntityState.ACTIVE, EntityState.FINISHING]:
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
    """
    def __init__(self, 
                 name: str, 
                 faction: Faction = Faction.ENEMY,
                 pos: Tuple[float, float, float] = (0.0, 0.0, 0.0),
                 facing: float = 0.0,
                 hitbox: Tuple[float, float] = (0.5, 2.0),
                 life_frame: float = float("inf"), 
                 context: Optional[Any] = None):
        super().__init__(name, life_frame, context)
        
        self.faction = faction
        self.pos = list(pos)
        self.facing = facing
        self.hitbox = hitbox
        
        # 物理模拟组件
        self.aura = AuraManager()
        self.active_effects = []
        
        # ICD 管理器 (用于追踪该实体受到的附着冷却)
        self.icd_manager = ICDManager(self)

    def set_position(self, x: float, z: float, y: Optional[float] = None):
        self.pos[0] = x
        self.pos[1] = z
        if y is not None:
            self.pos[2] = y

    def handle_damage(self, damage: Any) -> None:
        raise NotImplementedError("CombatEntity 子类必须实现 handle_damage")

    def apply_elemental_aura(self, damage: Any) -> List[Any]:
        """
        接收元素附着的统一入口，增加了高精度 ICD 判定。
        """
        # 1. 检查 ICD (传入攻击源以实现独立计算)
        tag = getattr(damage.config, 'icd_tag', 'Default')
        multiplier = self.icd_manager.check_attachment(damage.source, tag)
        
        if multiplier <= 0:
            # 系数为0，不产生附着与反应
            return []
            
        # 2. 根据系数调整元素量 (Gauge)
        # 注意: 这里的 element_u 是攻击配置的初始量
        final_u = damage.config.element_u * multiplier
        
        # 3. 调用 AuraManager 处理实际附着
        results = self.aura.apply_element(damage.element[0], final_u)
        
        # 4. 同步反应结果到伤害对象 (供后续流水线消费)
        if hasattr(damage, "reaction_results"):
            damage.reaction_results.extend(results)
            
        return results

    def on_frame_update(self) -> None:
        self.aura.update(1/60)
        
        for eff in self.active_effects[:]:
            if hasattr(eff, "on_frame_update"):
                eff.on_frame_update()
            elif hasattr(eff, "update"): # 兼容旧接口
                eff.update()
                
            if not getattr(eff, 'is_active', True):
                self.active_effects.remove(eff)