import time
from typing import Dict, Any, Optional, Callable
from core.factory.assembler import create_simulator_from_config
from core.persistence.database import ResultDatabase
from core.batch.runner import BatchRunner
from core.batch.generator import ConfigGenerator
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
            
            on_progress("RUNNING SIMULATION...", 0.3)
            # 2. 运行仿真
            simulator = create_simulator_from_config(config, self._repo, persistence_db=db)
            await simulator.run()
            
            on_progress("FINALIZING DATA...", 0.9)
            await db.stop_session()
            
            # 3. 合算结果
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

    async def run_batch(
        self, 
        root_config: Dict, 
        universe_root: Any, 
        on_progress: Callable[[str, float], None]
    ) -> Any:
        """执行批量仿真任务"""
        if self.is_simulating:
            return None
        
        self.is_simulating = True
        try:
            on_progress("BATCH PREPARING...", 0.05)
            configs = list(ConfigGenerator.generate_from_tree(root_config, universe_root))
            if not configs:
                return None
            
            runner = BatchRunner()
            
            def progress_bridge(current, total):
                on_progress(f"BATCH RUNNING ({current}/{total})...", current / total)

            summary = await runner.run_batch(configs, on_progress=progress_bridge)
            on_progress(f"BATCH FINISHED | AVG: {int(summary.avg_dps)}", 1.0)
            return summary
            
        except Exception as e:
            get_ui_logger().log_error(f"SimulationService: Batch run failed: {e}")
            on_progress("BATCH FAILED", 0.0)
            raise e
        finally:
            self.is_simulating = False
