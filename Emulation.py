from artifact.artifact import Artifact, ArtifactManager, ArtifactPiece
from character.character import CharacterState
from core.context import create_context, get_context
from core.dataHandler.DataHandler import clear_data, save_report
from core.event import EventBus, FrameEndEvent
from core.logger import get_emulation_logger
from core.registry import CharacterClassMap, WeaponClassMap
from core.target import Target
from core.team import Team
import threading

class Emulation():
    
    # 游戏参数设计
    fps = 60  # 帧率

    def __init__(self, team_data, action_sequence, target_data):
        super().__init__()
        # 1. 初始化上下文
        self.ctx = create_context()
        
        self.team_data = team_data
        self.action_sequence = action_sequence
        
        # 2. 初始化目标并关联上下文
        self.target = Target(target_data)
        self.ctx.target = self.target

    def set_log_file(self, file=None):
        if file is None:
            get_emulation_logger().new_log_file()
        else:
            get_emulation_logger().new_log_file(file)

    def set_quueue(self, queue):
        self.progress_queue = queue

    def thread(self):
        return threading.Thread(target=self.simulate, args=())

    def simulate(self):
        """
        模拟执行一系列动作。
        """
        # 确保在当前上下文作用域内运行
        with self.ctx:
            self.n = 0
            self.set_data()
            
            action_iter = iter(self._actions)
            self.next_character_action = next(action_iter, None)
            
            if self.next_character_action:
                self.ctx.team.swap(self.next_character_action)
                if hasattr(self, 'progress_queue') and self.progress_queue:
                    try:
                        self.progress_queue.put({
                            "start": {
                                "length": len(self._actions),
                                "current": self.n + 1,
                                "msg": f"{self.ctx.team.current_character.name} 执行 {self.next_character_action}"
                            }
                        })
                    except Exception as e:
                        get_emulation_logger().log_error(f"发送进度失败: {str(e)}")
                self.n += 1
                self.next_character_action = next(action_iter, None)
            else:
                get_emulation_logger().log("Team", "无动作可执行")

            while True:
                # 推进帧
                self.ctx.advance_frame()
                
                if self._update(self.target, action_iter):
                    if hasattr(self, 'progress_queue') and self.progress_queue:
                        self.progress_queue.put(None)
                    break

    def _update(self, target, action_iter):
        self.ctx.team.update(target)
        self.target.update()

        event = FrameEndEvent(self.ctx.current_frame)
        self.ctx.event_engine.publish(event)

        if self.next_character_action is not None and self.ctx.team.swap(self.next_character_action):
            get_emulation_logger().log("Team", "切换成功")
            if hasattr(self, 'progress_queue') and self.progress_queue:
                try:
                    self.progress_queue.put({
                        "update": {
                            "current": self.n + 1,
                            "length": len(self._actions),
                            "msg": f"{self.ctx.team.current_character.name} 执行 {self.next_character_action[1]}"
                        }
                    })
                except Exception as e:
                    get_emulation_logger().log_error(f"发送进度更新失败: {str(e)}")
            self.n += 1
            try:
                self.next_character_action = next(action_iter)
            except StopIteration:
                self.next_character_action = None
                get_emulation_logger().log("Team", "最后一个动作开始执行")

        if self.next_character_action is None and self.ctx.team.current_character.state[0] == CharacterState.IDLE:
            get_emulation_logger().log("Team", "动作执行完毕")
            return True
        return False

    @classmethod
    def emulation_init(cls):
        """全局重置逻辑 (慎用)"""
        clear_data()

    def set_data(self):
        from core.data.repository import MySQLDataRepository
        from core.factory.team_factory import TeamFactory
        from core.factory.action_parser import ActionParser
        
        # 1. 初始化工厂
        # 注意：此处应根据实际配置选择 Repository，这里保持原样
        repository = MySQLDataRepository()
        team_factory = TeamFactory(repository)
        action_parser = ActionParser()
        
        # 2. 构建队伍并存入上下文
        self.team = team_factory.create_team(self.team_data)
        self.ctx.team = self.team
        
        # 3. 解析动作序列
        self._actions = action_parser.parse_sequence(self.action_sequence)
        
    def simulate_multi(self, sim_file_path, sim_id, uid):
        try:
            self.set_log_file(sim_file_path+uid+'/logs/'+uid+'_'+str(sim_id)+'.log')
            self.simulate()
            save_report(sim_file_path+uid+'/data/',uid+'_'+str(sim_id))
            return {
                'sim_id': sim_id,
                'uid': uid,
                'sim_file_path': sim_file_path,
                'status': 'success'
            }
        except Exception as e:
            return {
                'sim_id': sim_id,
                'uid': uid,
                'sim_file_path': sim_file_path,
                'status': 'failed',
                'error': str(e)
            }
