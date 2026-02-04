from artifact.artifact import Artifact, ArtifactManager, ArtifactPiece
from character.character import CharacterState
from core.context import create_context, get_context
from core.dataHandler.DataHandler import clear_data, save_report
from core.event import EventBus, FrameEndEvent
from core.logger import get_emulation_logger
from core.map import CharacterClassMap, WeaponClassMap
from core.target import Target
from core.team import Team
import threading

class Emulation():
    
    # 游戏参数设计
    fps = 60  # 帧率
    target = None
    current_frame = 0
    team = None

    def __init__(self, team_data, action_sequence, target_data):
        super().__init__()
        # 初始化上下文
        self.ctx = create_context()
        
        self.team_data = team_data
        self.action_sequence = action_sequence
        Emulation.target = Target(target_data)
        # 将 target 注入 context
        self.ctx.target = Emulation.target

    def set_log_file(self, file=None):
        if file is None:
            get_emulation_logger().new_log_file()
        else:
            get_emulation_logger().new_log_file(file)

    def set_quueue(self,queue):
        self.progress_queue = queue

    def thread(self):
        return threading.Thread(target=self.simulate, args=())

    def simulate(self):
        """
        模拟执行一系列动作。
        """
        # 获取当前上下文
        ctx = get_context()

        self.n = 0
        self.set_data()
        
        # 将 team 注入 context
        ctx.team = Emulation.team
        
        action = iter(self._actions)
        self.next_character = next(action)
        Emulation.team.swap(self.next_character)
        
        Team.current_frame = 0 # 初始化当前帧数
        ctx.current_frame = 0
        
        if hasattr(self, 'progress_queue') and self.progress_queue:
            try:
                self.progress_queue.put({
                    "start": {
                        "length": len(self._actions),
                        "current": self.n + 1,
                        "msg": f"{Emulation.team.current_character.name} 执行 {self.next_character}"
                    }
                })
            except Exception as e:
                get_emulation_logger().log_error(f"发送进度失败: {str(e)}")
        self.n += 1
        try:
            self.next_character = next(action)
        except StopIteration:
            self.next_character = None
            get_emulation_logger().log("Team","最后一个动作开始执行")

        while True:
            # 推进帧
            ctx.advance_frame()
            # 同步旧的静态变量以兼容
            Emulation.current_frame = ctx.current_frame
            
            if self._update(self.target,action):
                if hasattr(self, 'progress_queue') and self.progress_queue:
                    self.progress_queue.put(None)
                break

    def _update(self, target, action):
        Emulation.team.update(target)
        Emulation.target.update()

        ctx = get_context()
        event = FrameEndEvent(ctx.current_frame)
        # 直接使用 context 的 engine 发布
        ctx.event_engine.publish(event)

        if self.next_character is not None and Emulation.team.swap(self.next_character):
            get_emulation_logger().log("Team","切换成功")
            if hasattr(self, 'progress_queue') and self.progress_queue:
                try:
                    self.progress_queue.put({
                        "update": {
                            "current": self.n + 1,
                            "length": len(Emulation._actions),
                            "msg": f"{Emulation.team.current_character.name} 执行 {self.next_character[1]}"
                        }
                    })
                except Exception as e:
                    get_emulation_logger().log_error(f"发送进度更新失败: {str(e)}")
            self.n += 1
            try:
                self.next_character = next(action)
            except StopIteration:
                self.next_character = None
                get_emulation_logger().log("Team","最后一个动作开始执行")

        if self.next_character is None and self.team.current_character.state[0] == CharacterState.IDLE:
            get_emulation_logger().log("Team","动作执行完毕")
            return True
        return False

    @classmethod
    def emulation_init(cls):
        # 静态初始化时也需要创建上下文
        create_context()
        Emulation.current_frame = 0
        Team.clear()
        EventBus.clear()
        clear_data()

    def set_data(self):
        from core.data.repository import MySQLDataRepository
        from core.factory.team_factory import TeamFactory
        from core.factory.action_parser import ActionParser
        
        # 1. 初始化数据仓库和工厂
        repository = MySQLDataRepository()
        team_factory = TeamFactory(repository)
        action_parser = ActionParser()
        
        # 2. 构建队伍并存入上下文
        self.team = team_factory.create_team(self.team_data)
        self.ctx.team = self.team
        # 兼容旧代码对类属性的引用（逐步废弃）
        Emulation.team = self.team
        
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
