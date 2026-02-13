from typing import Dict, List, Set

from core.entities.base_entity import Faction
from core.event import EventType, GameEvent
from core.systems.base_system import GameSystem
from core.context import EventEngine
from core.tool import get_current_time


class ResonanceSystem(GameSystem):
    """
    元素共鸣系统。
    负责检测队伍元素构成并应用相应的全局增益效果。
    """

    def __init__(self) -> None:
        super().__init__()
        self.active_resonances: Set[str] = set()
        
        # 内部计时器与状态追踪
        self._last_electro_particle_time: int = -9999
        self._dendro_resonance_level: int = 0  # 0: 基础, 1: 触发一级, 2: 触发二级

    def initialize(self, context) -> None:
        """初始化系统并激活共鸣效果。"""
        super().initialize(context)
        self._detect_resonances()
        self._apply_static_effects()

    def register_events(self, engine: EventEngine) -> None:
        """根据激活的共鸣类型订阅对应事件。"""
        if not self.active_resonances:
            return

        # 双冰、双岩、双雷、双草均涉及动态判定
        dynamic_resonances = {"冰", "岩", "雷", "草"}
        if any(r in self.active_resonances for r in dynamic_resonances):
            engine.subscribe(EventType.BEFORE_CALCULATE, self)
            engine.subscribe(EventType.AFTER_ELEMENTAL_REACTION, self)

    def _detect_resonances(self) -> None:
        """扫描战场上的玩家实体，确定激活的共鸣类型。"""
        player_entities = self.context.space._entities.get(Faction.PLAYER, [])
        if len(player_entities) < 4:
            return

        element_counts: Dict[str, int] = {}
        for char in player_entities:
            el = getattr(char, "element", "无")
            element_counts[el] = element_counts.get(el, 0) + 1

        # 检查双元素共鸣
        for el, count in element_counts.items():
            if count >= 2:
                self.active_resonances.add(el)

    def _apply_static_effects(self) -> None:
        """应用即时生效的属性加成 (静态注入)。"""
        chars = self.context.space._entities.get(Faction.PLAYER, [])
        
        # 1. 热诚之火 (火): 攻击力提高25%
        if "火" in self.active_resonances:
            for c in chars:
                c.attribute_panel["攻击力%"] += 25.0

        # 2. 愈疗之水 (水): 生命值上限提高25%
        if "水" in self.active_resonances:
            for c in chars:
                c.attribute_panel["生命值%"] += 25.0

        # 3. 坚定之岩 (岩): 护盾强效提升15%
        if "岩" in self.active_resonances:
            for c in chars:
                c.attribute_panel["护盾强效"] += 15.0

        # 4. 蔓生之草 (草): 元素精通提升50
        if "草" in self.active_resonances:
            for c in chars:
                c.attribute_panel["元素精通"] += 50.0

        # 5. 迅捷之风 (风): 占位符
        if "风" in self.active_resonances:
            # TODO: 实现体力消耗降低、移速提升、冷却缩短
            pass

    def handle_event(self, event: GameEvent) -> None:
        """处理动态共鸣逻辑 (如战斗中的暴击加成、掉球等)。"""
        if event.event_type == EventType.BEFORE_CALCULATE:
            self._handle_before_calculate(event)
        elif event.event_type == EventType.AFTER_ELEMENTAL_REACTION:
            self._handle_after_reaction(event)

    def _handle_before_calculate(self, event: GameEvent) -> None:
        """处理伤害计算前的动态修正。"""
        ctx = event.data.get("damage_context")
        if not ctx:
            return

        # 1. 粉碎之冰 (冰): 对处于冰元素附着或冻结状态下的敌人，暴击率提高15%
        if "冰" in self.active_resonances:
            target = ctx.target
            if target and (target.has_aura("冰") or target.has_aura("冻结")):
                ctx.stats["暴击率"] += 15.0

        # 2. 坚定之岩 (岩): 处于护盾保护下时，造成的伤害提升15%
        if "岩" in self.active_resonances:
            # 简单判定：检查 source 是否挂载了护盾对象
            if getattr(ctx.source, "shield_effects", []):
                ctx.stats["伤害加成"] += 15.0

    def _handle_after_reaction(self, event: GameEvent) -> None:
        """处理反应触发后的效果 (如双雷掉球、双草精通)。"""
        # 1. 强能之雷 (雷): 触发超导、超载、感电、原激化、超激化时，掉落雷元素微粒
        if "雷" in self.active_resonances:
            current_f = get_current_time()
            if current_f - self._last_electro_particle_time >= 300:  # 5秒CD
                from core.factory.entity_factory import EntityFactory
                # 在攻击者位置产生一个雷元素微粒 (具体数值可根据需求调整)
                EntityFactory.spawn_energy(1, event.source, ("雷", 1.0), time=40)
                self._last_electro_particle_time = current_f

        # 2. 蔓生之草 (草): 触发反应后进一步提升精通
        if "草" in self.active_resonances:
            # TODO: 实现具体的精通分段加成逻辑
            pass
