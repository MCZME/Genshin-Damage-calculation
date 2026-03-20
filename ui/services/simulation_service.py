import time
from typing import Dict, Any, Optional, Callable
from core.factory.assembler import SimulationAssembler
from core.persistence.database import ResultDatabase
from core.batch.models import SimulationMetrics
from core.logger import get_ui_logger

class SimulationService:
    """
    仿真服务：负责驱动单次和批量仿真任务。
    """
    def __init__(self, metadata_repo):
        self._repo = metadata_repo
        self.is_simulating = False

    async def run_single(
        self,
        config: Dict[str, Any],
        on_progress: Callable[[str, float], None]
    ) -> Optional[SimulationMetrics]:
        """执行单次仿真任务"""
        if self.is_simulating:
            return None

        self.is_simulating = True
        db = ResultDatabase()

        try:
            on_progress("INITIALIZING DB...", 0.1)
            await db.initialize()

            # 1. 创建会话
            config_name = f"仿真_{int(time.time())}"
            await db.create_session(config_name, config_snapshot=config)
            await db.start_session()

            on_progress("BUILDING SIMULATION...", 0.2)
            # 2. 组装仿真器（使用完整版以获取静态修饰符数据）
            assembler = SimulationAssembler(self._repo)
            simulator, static_modifiers_data = assembler.assemble(config, persistence_db=db)

            # 2.1 持久化静态修饰符（武器/圣遗物）
            for data in static_modifiers_data:
                await db.record_static_modifiers(
                    data["entity_id"],
                    data["modifiers"]
                )

            on_progress("RUNNING SIMULATION...", 0.3)
            # 3. 运行仿真
            await simulator.run()

            on_progress("FINALIZING DATA...", 0.9)
            await db.stop_session()

            # 4. 合算结果
            total_dmg = db.projector.total_damage if db.projector else 0.0
            duration = simulator.ctx.current_frame
            dps = (total_dmg / duration * 60) if duration > 0 else 0.0

            metrics = SimulationMetrics(total_damage=total_dmg, dps=dps, simulation_duration=duration)
            on_progress(f"FINISHED | DPS: {int(dps)}", 1.0)
            return metrics

        except Exception as e:
            get_ui_logger().log_error(f"SimulationService: Single run failed: {e}")
            on_progress(f"FAILED: {str(e)[:20]}", 0.0)
            try:
                await db.stop_session()
            except Exception:
                pass
            raise e
        finally:
            self.is_simulating = False
