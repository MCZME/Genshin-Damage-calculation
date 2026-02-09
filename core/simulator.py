from typing import List, Tuple, Any, Optional
from core.context import SimulationContext
from core.event import GameEvent, EventType
from core.logger import get_emulation_logger
from core.action.action_data import ActionCommand

class Simulator:
    """
    新一代战斗模拟引擎。
    仅负责驱动时间轴，协调动作队列，并不直接处理业务逻辑。
    """
    def __init__(self, context: SimulationContext, action_sequence: List[ActionCommand], 
                 persistence_db: Optional[Any] = None):
        self.ctx = context
        self.actions = action_sequence
        self.action_ptr = 0
        self.is_running = False
        self.db = persistence_db

    async def run(self):
        """开始异步模拟循环"""
        self.is_running = True
        get_emulation_logger().log("Simulator", "模拟开始执行")
        
        # 初始帧前准备
        self._prepare_simulation()

        while self.is_running:
            # 1. 推进全局帧
            self.ctx.advance_frame()
            
            # 2. 执行本帧逻辑
            self._update_frame()
            
            # 3. 发布帧结束事件 (驱动各个 System 更新)
            self.ctx.event_engine.publish(GameEvent(EventType.FRAME_END, self.ctx.current_frame))
            
            # 4. [NEW] 持久化快照
            if self.db:
                self.db.record_snapshot(self.ctx.take_snapshot())
            
            # 5. 检查是否所有动作已完成且角色处于 IDLE
            if self._is_finished():
                get_emulation_logger().log("Simulator", f"检测到终止条件满足 (Frame: {self.ctx.current_frame}, Ptr: {self.action_ptr})")
                self.is_running = False
                
        get_emulation_logger().log("Simulator", "模拟执行完毕")

    def _prepare_simulation(self):
        # 初始化第一个动作
        self._try_enqueue_next_action()

    def _update_frame(self):
        # 更新全队所有实体的动作状态机
        # 注意：目前我们需要在 Character 中持有 ActionManager
        if self.ctx.team:
            for char in self.ctx.team.team:
                if hasattr(char, 'action_manager'):
                    char.action_manager.on_frame_update()
            
            # 尝试压入后续动作
            self._try_enqueue_next_action()

    def _try_enqueue_next_action(self):
        if self.action_ptr >= len(self.actions):
            return

        command: ActionCommand = self.actions[self.action_ptr]
        
        # 查找到对应角色对象
        char = self.ctx.team.get_character_by_name(command.character_name)
        if not char:
            get_emulation_logger().log_error(f"无法找到角色: {command.character_name}, 跳过指令")
            self.action_ptr += 1
            return

        # 尝试通过 ActionManager 执行指令
        # 注意：这里我们使用 request_action_by_name 并传递 params 字典 (即 Intent)
        # Character.elemental_skill(intent) 内部会调用 to_action_data(intent)
        if char.action_manager.request_action_by_name(command.action_type, command.params):
            self.action_ptr += 1

    def _is_finished(self) -> bool:
        # 队列为空且所有角色 IDLE
        if self.action_ptr < len(self.actions):
            return False
            
        for char in self.ctx.team.team:
            if char.action_manager.current_action is not None:
                return False
        return True
