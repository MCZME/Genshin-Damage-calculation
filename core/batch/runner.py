import asyncio
import concurrent.futures
import multiprocessing
import os
from datetime import datetime
from typing import List, Dict, Any, Callable
from core.batch.models import SimulationMetrics, BatchSummary
from core.factory.assembler import create_simulator_from_config
from core.data.repository import MySQLDataRepository

def simulation_worker(config: Dict[str, Any], index: int, log_dir: str = None) -> SimulationMetrics:
    """
    Worker 进程入口函数。
    """
    # 1. 独立初始化环境
    from core.registry import initialize_registry
    from core.logger import SimulationLogger, get_emulation_logger
    
    # 2. 专门为本次运行创建日志对象
    log_file = None
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"run_{index}.log")
    
    # 实例化一个独立的 Logger，它将接管本次子进程的所有仿真日志
    logger = SimulationLogger(name=f"BatchRun_{index}", log_file=log_file)
    
    # 3. 初始化注册表
    initialize_registry()
    
    # 4. 这里的 Repository 需要在子进程内实例化
    repo = MySQLDataRepository()
    
    # 5. 创建并执行仿真
    simulator = create_simulator_from_config(config, repo)
    # 将 logger 显式挂载到 context 中 (假设 Context 逻辑会使用它)
    simulator.ctx.logger = logger
    
    async def _run():
        await simulator.run()
        
    asyncio.run(_run())
    
    # 6. 提取结果摘要
    metrics = SimulationMetrics(
        total_damage=getattr(simulator.ctx, "total_damage", 0.0),
        dps=0.0, 
        simulation_duration=simulator.ctx.current_frame,
        param_snapshot=config.get("_batch_metadata", {}).get("params", {})
    )
    
    if metrics.simulation_duration > 0:
        metrics.dps = metrics.total_damage / metrics.simulation_duration * 60
        
    return metrics

class BatchRunner:
    """
    批量仿真运行器。
    """
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or multiprocessing.cpu_count()

    async def run_batch(self, configs: List[Dict[str, Any]], 
                        on_progress: Callable[[int, int], Any] = None) -> BatchSummary:
        """
        异步运行批量仿真任务列表。
        """
        loop = asyncio.get_running_loop()
        summary = BatchSummary(total_runs=len(configs))
        
        # 准备批次日志目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = os.path.join("data", "log", "Batch", f"batch_{timestamp}")
        
        # 使用 ProcessPoolExecutor
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # 修改传参：包含 index 和 log_dir
            tasks = [
                loop.run_in_executor(executor, simulation_worker, cfg, i, log_dir) 
                for i, cfg in enumerate(configs)
            ]
            
            completed = 0
            for coro in asyncio.as_completed(tasks):
                try:
                    result = await coro
                    summary.results.append(result)
                except Exception as e:
                    print(f"Worker Error: {e}")
                
                completed += 1
                if on_progress:
                    if asyncio.iscoroutinefunction(on_progress):
                        await on_progress(completed, len(configs))
                    else:
                        on_progress(completed, len(configs))
        
        self._calculate_stats(summary)
        return summary

    def _calculate_stats(self, summary: BatchSummary):
        if not summary.results: return
        
        dps_list = [r.dps for r in summary.results]
        import statistics
        summary.avg_dps = statistics.mean(dps_list) if dps_list else 0
        summary.max_dps = max(dps_list) if dps_list else 0
        summary.min_dps = min(dps_list) if dps_list else 0
        if len(dps_list) > 1:
            summary.std_dev_dps = statistics.stdev(dps_list)
        
        dps_list.sort()
        if dps_list:
            idx = min(int(len(dps_list) * 0.95), len(dps_list) - 1)
            summary.p95_dps = dps_list[idx]
