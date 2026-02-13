from typing import Dict, Any, List, Optional
from core.context import create_context, SimulationContext
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

    def assemble(self, config: Dict[str, Any]) -> Simulator:
        """
        从配置包组装仿真实例。
        
        Args:
            config: 包含 context_config 和 sequence_config 的字典。
            
        Returns:
            Simulator: 已挂载完整 Context 和动作序列的模拟器实例。
        """
        # 1. 初始化上下文环境 (自动激活系统与物理空间)
        ctx = create_context()
        
        # 2. 组装队伍 (TeamFactory 内部会自动将角色注册到 ctx.space)
        context_cfg = config.get("context_config", {})
        team_list_cfg = context_cfg.get("team", [])
        
        # 2.1 创建角色对象
        team = self.team_factory.create_team(team_list_cfg)
        ctx.team = team

        # 3. 组装受击目标 (Enemy)
        target_cfg_list = context_cfg.get("targets", [])
        for t_cfg in target_cfg_list:
            target = Target(t_cfg)
            # [NEW] 设置目标初始坐标
            pos = t_cfg.get("position", {"x": 0, "y": 0, "z": 0})
            target.set_position(pos.get("x", 0), pos.get("z", 0))
            
            # 手动注入到空间 (Target 默认是 Faction.ENEMY)
            ctx.space.register(target)
            
        # 4. 解析动作序列
        sequence_cfg = config.get("sequence_config", [])
        parser = ActionParser()
        action_sequence = parser.parse_sequence(sequence_cfg)
        
        # 5. 构建模拟器
        simulator = Simulator(ctx, action_sequence)
        
        return simulator

def create_simulator_from_config(config: Dict[str, Any], repository: DataRepository) -> Simulator:
    """快捷工厂函数"""
    assembler = SimulationAssembler(repository)
    return assembler.assemble(config)
