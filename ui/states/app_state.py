import json
import os
import asyncio
import flet as ft
from typing import List, Dict, Any, Optional
from core.data.repository import MySQLDataRepository
from core.logger import get_ui_logger
from core.registry import CharacterClassMap, WeaponClassMap, ArtifactSetMap
from core.batch.models import SimulationNode, SimulationMetrics, ModifierRule
from core.factory.assembler import create_simulator_from_config
from core.batch.generator import ConfigGenerator
from ui.services.event_bus import UIEventBus


class AppState:
    """
    工作台全量状态管理器 (V3.1 - 规则派生架构)。
    """

    def __init__(self):
        self.page = None
        self.main_to_branch = None
        self.branch_to_main = None
        self.repo = MySQLDataRepository()
        
        # 0. UI 事件总线 (解耦后的事件管理)
        self.events = UIEventBus()

        # 1. 基础元数据
        self.char_map = {}
        self.weapon_map: Dict[str, List[Dict[str, Any]]] = {}
        self.target_map = {}
        self.artifact_sets = []
        
        # 已实装名单 (代码层面已注册)
        self.implemented_chars = set()
        self.implemented_weapons = set()
        self.implemented_artifacts = set()
        
        self._load_metadata()

        # 2. UI 流程状态
        self.sidebar_collapsed = False
        self.visual_collapsed = False
        self.selection: Optional[Dict] = None

        from ui.states.strategic_state import StrategicState
        from ui.states.tactical_state import TacticalState
        from ui.states.universe_state import UniverseState
        self.strategic_state = StrategicState()
        self.tactical_state = TacticalState()
        self.tactical_state.sequence.clear() # 清空 Mock 动作

        # 4. 分支宇宙状态
        self.universe_state = UniverseState(self.events)

        # 5. 仿真运行状态
        self.is_simulating = False
        self.sim_progress = 0.0
        self.sim_status = "IDLE"
        self.last_metrics: Optional[SimulationMetrics] = None
        self.last_session_id: Optional[int] = None

    def register_page(self, page: ft.Page):
        self.page = page

    def refresh(self):
        """传统的全局刷新快捷方式"""
        self.events.notify("global")
        if self.page:
            try:
                self.page.update()
            except Exception:
                pass

    def _load_metadata(self):
        try:
            char_list = self.repo.get_all_characters()
            self.char_map = {
                c["name"]: {"id": c["id"], "element": c["element"], "type": c["type"], "rarity": c.get("rarity", 5)}
                for c in char_list
            }
            
            # 预加载所有武器并缓存
            weapon_types = ["单手剑", "双手剑", "长柄武器", "法器", "弓"]
            for wt in weapon_types:
                self.weapon_map[wt] = self.repo.get_weapons_by_type(wt)
                
            self.artifact_sets = self.repo.get_all_artifact_sets()

            # 刷新已实装列表
            self.implemented_chars = set(CharacterClassMap.keys())
            self.implemented_weapons = set(WeaponClassMap.keys())
            self.implemented_artifacts = set(ArtifactSetMap.keys())
            
            get_ui_logger().log_info(f"Implemented assets: {len(self.implemented_chars)} chars, {len(self.implemented_weapons)} weapons")
            self.target_map = {
                "遗迹守卫": {
                    "level": 90,
                    "resists": {k: 10 for k in ["火", "水", "雷", "草", "冰", "岩", "风", "物理"]},
                },
                "丘丘人": {
                    "level": 90,
                    "resists": {k: 10 for k in ["火", "水", "雷", "草", "冰", "岩", "风", "物理"]},
                },
                "古岩龙蜥": {
                    "level": 90,
                    "resists": {k: 10 for k in ["火", "水", "雷", "草", "冰", "岩", "风", "物理"]},
                },
            }
        except Exception as e:
            get_ui_logger().log_error(f"AppState: Metadata load failed: {e}")

    # --- 变异树操作 (通过 UniverseState 代理) ---

    @property
    def universe_root(self): return self.universe_state.universe_root
    
    @property
    def selected_node(self): return self.universe_state.selected_node

    def select_node(self, node): self.universe_state.select_node(node)
    def add_branch(self, parent, name="新分支"): self.universe_state.add_branch(parent, name)
    def apply_range_to_node(self, node, path, s, e, step, label): self.universe_state.apply_range_to_node(node, path, s, e, step, label)
    def remove_node(self, nid): self.universe_state.remove_node(nid)
    def update_node(self, nid, name=None, rule=None): self.universe_state.update_node(nid, name, rule)
    def get_selected_node_config(self): return self.universe_state.get_selected_node_config()

    # --- 跨进程通信 ---

    def launch_commander(self):
        if self.main_to_branch:
            config = self.export_config()
            # 导出配置中已包含 sequence_config，不再需要 raw 引用
            # 将初始化配置存为子进程的 root_config
            msg = {"type": "INIT_UNIVERSE", "config": config}

            self.main_to_branch.put(msg)

    async def apply_external_config(self, config: Dict):
        ctx = config.get("context_config", {})
        
        # 恢复 team_data
        loaded_team = ctx.get("team", [])
        for i in range(4):
            if i < len(loaded_team) and loaded_team[i] is not None:
                member_cfg = loaded_team[i]
                # 解析字典重组为 strategic_state.team_data 期望的格式
                base_member = self.strategic_state._create_empty_member()
                base_member.update({
                    "id": member_cfg["character"]["id"],
                    "name": member_cfg["character"]["name"],
                    "element": member_cfg["character"]["element"],
                    "level": str(member_cfg["character"].get("level", 90)),
                    "type": member_cfg["character"].get("type", "Unknown")
                })
                base_member["weapon"].update({
                    "id": member_cfg["weapon"].get("name"),
                    "level": str(member_cfg["weapon"].get("level", 90)),
                    "refinement": str(member_cfg["weapon"].get("refinement", 1))
                })
                # 解析圣遗物
                for art in member_cfg.get("artifacts", []):
                    slot = art["slot"].capitalize()
                    if slot in base_member["artifacts"]:
                        base_member["artifacts"][slot]["name"] = art["set_name"]
                        base_member["artifacts"][slot]["main"] = art["main_stat"]
                        base_member["artifacts"][slot]["main_val"] = str(art["value"])
                        base_member["artifacts"][slot]["subs"] = [[s["key"], str(s["value"])] for s in art.get("sub_stats", [])]
                
                self.strategic_state.team_data[i] = base_member
            else:
                self.strategic_state.team_data[i] = self.strategic_state._create_empty_member()

        # 恢复 targets 与 spatial_data
        loaded_targets = ctx.get("targets", [])
        self.strategic_state.targets.clear()
        self.strategic_state.spatial_data["target_positions"].clear()

        if loaded_targets:
            for t_cfg in loaded_targets:
                # 重新映射至 StrategicState 的内部格式 (resists 为字符串)
                target = {
                    "id": t_cfg["id"],
                    "name": t_cfg["name"],
                    "level": str(t_cfg.get("level", 90)),
                    "resists": {k: str(v) for k, v in t_cfg.get("resists", {}).items()}
                }
                self.strategic_state.targets.append(target)
                
                # 恢复位置信息
                pos = t_cfg.get("position", {"x": 0.0, "z": 5.0})
                self.strategic_state.spatial_data["target_positions"][target["id"]] = pos
            
            self.strategic_state.selected_target_index = 0
        else:
            self.strategic_state.targets = [self.strategic_state._create_target_instance("target_A", "遗迹守卫")]
            self.strategic_state.selected_target_index = 0

        # 恢复 scene_data
        if "environment" in ctx:
            self.strategic_state.scene_data = ctx["environment"]

        # 恢复 tactical 序列
        loaded_seq = config.get("sequence_config", [])
        self.tactical_state.sequence.clear()
        
        for act in loaded_seq:
            from ui.states.tactical_state import ActionUnit
            
            # reverse mapping for char_name to char_id
            char_id = "unknown"
            for m in self.strategic_state.team_data:
                if m.get("name") == act["character_name"]:
                    char_id = m.get("id")
                    break
                    
            unit = ActionUnit(
                char_id=char_id,
                action_type=act["action_key"]
            )
            unit.params = act.get("params", {})
            self.tactical_state.add_action(unit)

        self.selection = None
        self.events.notify("strategic")
        self.events.notify("tactical")
        self.events.notify("scene")
        get_ui_logger().log_info("External configuration applied to Reboot Workbench.")

    # --- 运行逻辑 ---

    def export_config(self) -> Dict[str, Any]:
        team_cfg = []
        for member in self.strategic_state.team_data:
            if member.get("id") is None:
                continue
            arts_list = []
            for slot, data in member["artifacts"].items():
                if data["name"] and data["name"] != "未装备":
                    arts_list.append(
                        {
                            "slot": slot.lower(),
                            "set_name": data["name"],
                            "main_stat": data["main"],
                            "value": float(data.get("main_val", 0)),
                            "sub_stats": [{"key": s[0], "value": float(s[1])} for s in data.get("subs", []) if len(s) >= 2],
                        }
                    )

            team_cfg.append(
                {
                    "character": {
                        "id": member["id"],
                        "name": member["name"],
                        "element": member["element"],
                        "level": int(member["level"]),
                        "constellation": int(member.get("constellation", 0)),
                        "talents": [int(member['talents']['na']), int(member['talents']['e']), int(member['talents']['q'])],
                        "type": member.get("type", "Unknown")
                    },
                    "weapon": {
                        "name": member["weapon"]["id"] if member["weapon"]["id"] else "未装备",
                        "level": int(member["weapon"].get("level", 90)),
                        "refinement": int(member["weapon"].get("refinement", 1))
                    },
                    "artifacts": arts_list,
                    "position": {"x": 0, "z": 0},
                }
            )

        target_cfg = []
        for t in self.strategic_state.targets:
            pos = self.strategic_state.spatial_data["target_positions"].get(t["id"], {"x": 0.0, "z": 5.0})
            target_cfg.append({
                "id": t["id"],
                "name": t["name"],
                "level": int(t.get("level", 90)),
                "position": pos,
                "resists": {k: float(v) for k, v in t["resists"].items()},
            })

        seq_cfg = []
        for act in self.tactical_state.sequence:
            # 解析对应角色的名字
            char_name = act.char_id
            for member in self.strategic_state.team_data:
                if member.get("id") == act.char_id:
                    char_name = member["name"]
                    break
            
            seq_cfg.append(
                {
                    "character_name": char_name,
                    "action_key": act.action_type,
                    "params": act.params
                }
            )
            
        return {
            "context_config": {"team": team_cfg, "targets": target_cfg, "environment": self.strategic_state.scene_data},
            "sequence_config": seq_cfg,
        }

    async def run_simulation(self):
        if self.is_simulating:
            return
        self.is_simulating = True
        self.sim_status = "RUNNING..."
        self.events.notify("simulation")
        
        from core.persistence.database import ResultDatabase
        import time
        db = ResultDatabase()
        
        try:
            # 1. 持久化层准备
            await db.initialize()
            # 创建会话并捕获 ID
            config_name = f"仿真_{int(time.time())}"
            self.last_session_id = await db.create_session(config_name, config_snapshot=self.export_config())
            get_ui_logger().log_info(f"AppState: Simulation session created. ID: {self.last_session_id}")
            await db.start_session()
            
            # 2. 仿真引擎实例化与运行
            config = self.export_config()
            # 将持久化接口注入模拟器
            simulator = create_simulator_from_config(config, self.repo, persistence_db=db)
            await simulator.run()
            
            # 3. 数据收尾：确保所有帧数据刷入磁盘
            await db.stop_session()
            
            total_dmg = db.projector.total_damage if db.projector else 0.0
            duration = simulator.ctx.current_frame
            dps = (total_dmg / duration * 60) if duration > 0 else 0.0
            get_ui_logger().log_info(f"AppState: Simulation finished. Frame: {duration}, Total DMG: {total_dmg}")
            self.last_metrics = SimulationMetrics(total_damage=total_dmg, dps=dps, simulation_duration=duration)
            self.sim_status = f"FINISHED | DPS: {int(dps)}"
            self.sim_progress = 1.0
        except Exception as e:
            import traceback
            # 异常发生时也尝试停止 db 以防文件锁死
            try: await db.stop_session()
            except: pass
            
            self.sim_status = f"FAILED: {str(e)[:25]}"
            get_ui_logger().log_error(f"Single Simulation Error: {e}\n{traceback.format_exc()}")
        finally:
            self.is_simulating = False
            self.events.notify("simulation")

    @property
    def root_config(self): return self.universe_state.root_config
    
    @root_config.setter
    def root_config(self, value): self.universe_state.root_config = value

    async def run_batch_simulation(self):
        if self.is_simulating:
            return
        if not self.universe_state.root_config:
            return

        self.is_simulating = True
        self.sim_status = "BATCH PREPARING..."
        self.events.notify("simulation")
        try:
            from core.batch.runner import BatchRunner

            configs = list(ConfigGenerator.generate_from_tree(self.universe_state.root_config, self.universe_state.universe_root))
            if not configs:
                return
            runner = BatchRunner()

            def update_progress(c, t):
                self.sim_progress = c / t
                self.sim_status = f"BATCH RUNNING ({c}/{t})..."
                self.events.notify("simulation")

            summary = await runner.run_batch(configs, on_progress=update_progress)
            self.sim_status = f"BATCH FINISHED | AVG: {int(summary.avg_dps)}"
            self.sim_progress = 1.0
            return summary
        except Exception as e:
            import traceback

            self.sim_status = f"BATCH FAILED: {str(e)[:20]}"
            get_ui_logger().log_error(f"Batch Simulation Error: {e}\n{traceback.format_exc()}")
        finally:
            self.is_simulating = False
            self.events.notify("simulation")

    def save_config(self, filename: str, data: Dict = None):
        """保存配置到文件。如果未提供 data，则导出当前全量配置。"""
        if not filename.endswith(".json"):
            filename += ".json"
        
        # 如果是绝对路径则直接使用，否则存入默认目录
        if os.path.isabs(filename):
            save_path = filename
        else:
            os.makedirs("data/configs", exist_ok=True)
            save_path = os.path.join("data/configs", filename)
            
        config_data = data if data is not None else self.export_config()
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
        get_ui_logger().log_info(f"Config saved to {save_path}")

    def export_character_template(self, index: int) -> Dict[str, Any]:
        """将指定槽位的角色完整数据导出为模版"""
        member = self.strategic_state.team_data[index]
        if member.get("id") is None:
            return {}
            
        return {
            "version": "V2.4",
            "type": "character_template",
            "name": member.get("name"),
            "data": {
                "base": {
                    "id": member.get("id"),
                    "name": member.get("name"),
                    "level": member.get("level"),
                    "constellation": member.get("constellation"),
                    "talents": member.get("talents"),
                    "element": member.get("element"),
                    "type": member.get("type")
                },
                "weapon": member.get("weapon"),
                "artifacts": member.get("artifacts")
            }
        }

    def apply_character_template(self, index: int, template: Dict[str, Any]):
        """从模版应用角色配置到指定槽位"""
        if template.get("type") != "character_template":
            return
            
        data = template.get("data", {})
        base = data.get("base", {})
        
        # 获取目标槽位并覆盖数据
        target = self.strategic_state.team_data[index]
        target.update(base)
        target["weapon"] = data.get("weapon", {"id": None, "level": "90", "refinement": "1"})
        target["artifacts"] = data.get("artifacts", {s: {"id": None, "main_stat": None, "sub_stats": []} for s in ["Flower", "Plume", "Sands", "Goblet", "Circlet"]})
        
        # 触发 UI 同步更新可通过 refresh 逻辑
        get_ui_logger().log_info(f"Template applied to slot {index}: {base.get('name')}")

    def export_artifact_set(self, index: int) -> Dict[str, Any]:
        """导出指定槽位的圣遗物五件套"""
        member = self.strategic_state.team_data[index]
        return {
            "version": "V2.4",
            "type": "artifact_set",
            "char_name": member.get("name"),
            "artifacts": member.get("artifacts")
        }

    def apply_artifact_set(self, index: int, template: Dict[str, Any]):
        """应用圣遗物五件套"""
        if template.get("type") != "artifact_set":
            return
            
        target = self.strategic_state.team_data[index]
        target["artifacts"] = template.get("artifacts", {})
        get_ui_logger().log_info(f"Artifact set applied to slot {index}")

    async def load_config(self, filename: str):
        path = os.path.join("data/configs", filename)
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        await self.apply_external_config(data)
        get_ui_logger().log_info(f"Config loaded from {filename}")

    # --- 批处理 tree 持久化 (通过 UniverseState 代理) ---
    def save_universe(self, filename): 
        self.universe_state.save_universe(filename)

    def load_universe(self, filename): 
        self.universe_state.load_universe(filename)

    def list_universes(self): 
        return self.universe_state.list_universes()
