from __future__ import annotations

from core.context import create_context
from core.factory.team_factory import TeamFactory
from core.target import Target
from core.simulator import Simulator
from core.factory.action_parser import ActionParser
from core.data.repository import DataRepository


class SimulationAssembler:
    """
    仿真总装器 (Total Assembly Layer)。
    负责解析 SimulationConfig JSON 并构建完整的仿真环境。
    """

    def __init__(self, repository: DataRepository):
        self.repository = repository
        self.team_factory = TeamFactory(repository)

    def assemble(
        self, config: dict[str, Any], persistence_db: Any | None = None
    ) -> tuple[Simulator, list[dict[str, Any]]]:
        """
        从配置包组装仿真实例。

        Args:
            config: 包含 context_config 和 sequence_config 的字典。
            persistence_db: 可选的持久化数据库接口。

        Returns:
            tuple[Simulator, list[dict]]:
                - Simulator: 已挂载完整 Context 和动作序列的模拟器实例。
                - list[dict]: 静态修饰符数据列表，格式为 [{entity_id, modifiers}]，
                  需要在异步环境中调用 persistence_db.record_static_modifiers()。
        """
        # 1. 初始化上下文环境 (自动激活系统与物理空间)
        ctx = create_context()

        # 2. 组装队伍
        context_cfg = config.get("context_config", {})
        team_list_cfg = context_cfg.get("team", [])

        # 2.1 创建角色对象
        team = self.team_factory.create_team(team_list_cfg)
        team.ctx = ctx  # 显式关联 Context 以便发布事件

        # [NEW] 将 Team 注入 CombatSpace，开启物理同步与事件监听
        if ctx.space:
            ctx.space.set_team(team)

        # 3. 组装受击目标 (Enemy)
        target_cfg_list = context_cfg.get("targets", [])
        for t_cfg in target_cfg_list:
            target = Target(t_cfg)
            # 设置目标初始坐标
            pos = t_cfg.get("position", {"x": 0, "y": 0, "z": 0})
            target.set_position(pos.get("x", 0), pos.get("z", 0))

            # 手动注入到空间 (Target 默认是 Faction.ENEMY)
            ctx.space.register(target)

        # 4. 解析动作序列
        sequence_cfg = config.get("sequence_config", [])
        parser = ActionParser()
        action_sequence = parser.parse_sequence(sequence_cfg)

        # 5. 构建模拟器 (注入持久化接口)
        simulator = Simulator(ctx, action_sequence, persistence_db=persistence_db)

        # 6. 收集静态修饰符数据 (用于后续异步持久化)
        static_modifiers_data: list[dict[str, Any]] = []
        if persistence_db and hasattr(persistence_db, "record_static_modifiers"):
            for char in team.get_members():
                if hasattr(char, "dynamic_modifiers") and char.dynamic_modifiers:
                    static_modifiers_data.append({
                        "entity_id": char.entity_id,
                        "modifiers": char.dynamic_modifiers.copy()
                    })

        return simulator, static_modifiers_data


def create_simulator_from_config(
    config: dict[str, Any],
    repository: DataRepository,
    persistence_db: Any | None = None
) -> Simulator:
    """快捷工厂函数（向后兼容，不返回静态修饰符数据）"""
    assembler = SimulationAssembler(repository)
    simulator, _ = assembler.assemble(config, persistence_db=persistence_db)
    return simulator


from typing import Any
