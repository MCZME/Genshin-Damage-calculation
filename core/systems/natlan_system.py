from core.systems.base_system import GameSystem
from core.context import EventEngine
from core.event import EventType, GameEvent
from core.logger import get_emulation_logger
from core.entities.base_entity import Faction

class NatlanSystem(GameSystem):
    """
    纳塔地区特性系统，处理夜魂迸发等机制。
    """
    def __init__(self):
        super().__init__()
        self.last_nightsoul_burst_time = -9999

    def register_events(self, engine: EventEngine):
        # 监听伤害后置事件以触发夜魂迸发
        engine.subscribe(EventType.AFTER_DAMAGE, self)

    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.AFTER_DAMAGE:
            self._check_nightsoul_burst(event)

    def _check_nightsoul_burst(self, event: GameEvent):
        damage = event.data.get('damage')
        if not damage or damage.element[0] == '物理':
            return

        ctx = self.context
        if not ctx or not ctx.space:
            return

        # 计算队伍中纳塔角色的数量 (从 CombatSpace 中获取玩家阵营实体)
        natlan_character_count = 0
        player_entities = ctx.space._entities.get(Faction.PLAYER, [])
        for char in player_entities:
            # 假设角色属性中存有 association 字段
            if getattr(char, 'association', '') == '纳塔':
                natlan_character_count += 1

        if natlan_character_count > 0:
            # 根据纳塔角色数量确定触发间隔 (18s, 12s, 9s)
            trigger_interval = [18, 12, 9][min(natlan_character_count, 3) - 1] * 60
            
            if event.frame - self.last_nightsoul_burst_time > trigger_interval:
                self.last_nightsoul_burst_time = event.frame
                get_emulation_logger().log_effect('触发夜魂迸发')
                
                # 发布夜魂迸发事件
                burst_event = GameEvent(EventType.NIGHTSOUL_BURST, event.frame, source=event.data.get('character'))
                self.engine.publish(burst_event)
