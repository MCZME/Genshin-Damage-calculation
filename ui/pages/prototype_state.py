import json
import os
from nicegui import ui
from core.factory.assembler import create_simulator_from_config
from core.data.repository import MySQLDataRepository
from core.logger import get_emulation_logger

class PrototypeState:
    def __init__(self):
        self.repo = MySQLDataRepository()
        self.char_map = {}
        self.artifact_sets = []
        self._refresh_char_db()
        self._refresh_artifact_db()
        
        self.phase = 'strategic' # 'strategic', 'tactical', 'review'
        self.selected_entity = None
        self.selected_type = 'dashboard' 
        self.is_simulating = False
        
        # 战术编排状态
        self.actions = []
        self.selected_action_idx = None
        
        # 搜索与过滤状态
        self.char_search_query = ""
        self.char_filter_element = "全部"
        self.char_filter_weapon = "全部"
        
        self.team = []
        self.targets = [
            {"id": "target_A", "name": "遗迹守卫", "level": 90, 
             "position": {"x": 0, "z": 5}, 
             "resists": {"火": 10, "水": 10, "雷": 10, "草": 10, "冰": 10, "岩": 10, "风": 10, "物理": 10}}
        ]
        self.environment = {"location": "深境螺旋 12-3", "weather": "Clear", "buffs": []}
        
        # 批处理配置
        self.batch_mode = False
        self.batch_variables = [] # 格式: {"path": [...], "values": [...], "label": "名称"}
        self.batch_completed = 0
        self.batch_total = 0

    def _refresh_char_db(self):
        try:
            char_list = self.repo.get_all_characters()
            self.char_map = {
                c["name"]: {"id": c["id"], "element": c["element"], "type": c["type"]}
                for c in char_list
            }
        except Exception as e:
            get_emulation_logger().log_error(f"角色库加载失败: {e}")
            self.char_map = {}

    def _refresh_artifact_db(self):
        try:
            self.artifact_sets = self.repo.get_all_artifact_sets()
        except Exception as e:
            self.artifact_sets = ["炽烈的炎之魔女", "绝缘之旗印", "翠绿之影"]

    def _create_placeholder_struct(self):
        return {
            "is_placeholder": True,
            "position": {"x": 0, "z": -2},
            "character": {"id": 0, "name": "待选择角色", "element": "物理", "level": 90, "constellation": 0, "talents": [1, 1, 1], "type": "单手剑"},
            "weapon": {"name": "无锋剑", "level": 1, "refinement": 1},
            "artifacts": {
                "flower": {"slot": "生之花", "set_name": "", "main_stat": "生命值", "sub_stats": []},
                "plume": {"slot": "死之羽", "set_name": "", "main_stat": "攻击力", "sub_stats": []},
                "sands": {"slot": "时之沙", "set_name": "", "main_stat": "攻击力%", "sub_stats": []},
                "goblet": {"slot": "空之杯", "set_name": "", "main_stat": "火元素伤害加成", "sub_stats": []},
                "circlet": {"slot": "理之冠", "set_name": "", "main_stat": "暴击率", "sub_stats": []},
            }
        }

    def export_config(self) -> dict:
        """导出符合仿真引擎契约的配置 Bundle"""
        return {
            "context_config": {
                "team": [c for c in self.team if not c.get("is_placeholder")],
                "targets": self.targets,
                "environment": self.environment
            },
            "sequence_config": [
                {
                    "character_name": a["character_name"],
                    "action_key": a["action_key"],
                    "params": a["params"]
                }
                for a in self.actions
            ]
        }

    async def run_simulation(self):
        if self.is_simulating: return
        
        try:
            self.is_simulating = True
            
            if not self.batch_mode:
                # --- 模式 A: 单次模拟 (详细快照) ---
                await self._run_single_simulation()
            else:
                # --- 模式 B: 批量模拟 (并行/无快照) ---
                await self._run_batch_simulation()
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            ui.notify(f"仿真异常中断: {e}", type='negative')
        finally:
            self.is_simulating = False
            self.current_sim_frame = 0
            self.batch_completed = 0

    async def _run_single_simulation(self):
        from core.persistence.database import ResultDatabase
        db = ResultDatabase("data/last_simulation.db")
        
        self.current_sim_frame = 0
        ui.notify("初始化单次仿真...", type='info')
        await db.initialize()
        await db.start_session()
        
        try:
            async def progress_callback(frame):
                self.current_sim_frame = frame
            
            simulator = create_simulator_from_config(self.export_config(), self.repo)
            simulator.db = db
            simulator.on_progress = progress_callback
            await simulator.run()
            ui.notify(f"单次仿真完成! 总帧数: {simulator.ctx.current_frame}", type='positive')
        finally:
            await db.stop_session()

    async def _run_batch_simulation(self):
        from core.batch.runner import BatchRunner
        
        total = self.batch_total or 10
        ui.notify(f"正在准备 {total} 次并行仿真...", type='info')
        
        # 1. 准备配置 (目前使用简单的蒙特卡洛：同一份配置重复 N 次)
        base_config = self.export_config()
        configs = [base_config for _ in range(total)]
        
        # 2. 初始化运行器
        runner = BatchRunner()
        self.batch_completed = 0
        
        async def batch_progress(completed, total):
            self.batch_completed = completed
            # 此处不发通知，由 UI Timer 自动感知并刷新
            
        # 3. 执行
        summary = await runner.run_batch(configs, on_progress=batch_progress)
        ui.notify(f"批量处理完成! 平均 DPS: {summary.avg_dps:.2f}", type='positive')

    def save_to_file(self, filename: str = "simulation_draft.json"):
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.export_config(), f, ensure_ascii=False, indent=4)
            ui.notify(f"配置已保存至 {filename}", type='positive')
        except Exception as e:
            ui.notify(f"保存失败: {e}", type='negative')

    def load_from_file(self, filename: str = "simulation_draft.json"):
        if not os.path.exists(filename):
            ui.notify(f"未找到文件 {filename}", type='warning')
            return
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            ctx = data.get("context_config", {})
            if "team" in ctx: self.team = ctx["team"]
            if "targets" in ctx: self.targets = ctx["targets"]
            if "environment" in ctx: self.environment = ctx["environment"]
            self.actions = data.get("sequence_config", [])
            self.selected_entity = None
            self.selected_type = 'dashboard'
            ui.notify(f"已从 {filename} 恢复配置", type='positive')
        except Exception as e:
            ui.notify(f"加载失败: {e}", type='negative')
