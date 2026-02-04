from typing import List, Tuple, Any, Optional
from core.context import SimulationContext, get_context
from core.Event import FrameEndEvent
from core.Logger import get_emulation_logger

class Simulator:
    """
    新一代战斗模拟引擎。
    仅负责驱动时间轴，协调动作队列，并不直接处理业务逻辑。
    """
    def __init__(self, context: SimulationContext, action_sequence: List[Tuple[str, str, Any]]):
        self.ctx = context
        self.actions = action_sequence
        self.action_ptr = 0
        self.is_running = False

    def run(self):
        """开始模拟循环"""
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
            self.ctx.event_engine.publish(FrameEndEvent(self.ctx.current_frame))
            
            # 4. 检查是否所有动作已完成且角色处于 IDLE
            if self._is_finished():
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
                    char.action_manager.update()
            
            # 尝试压入后续动作
            self._try_enqueue_next_action()

    def _try_enqueue_next_action(self):
        if self.action_ptr >= len(self.actions):
            return

        # 检查当前场上角色是否准备好接受下一个动作
        # 这里涉及复杂的换人逻辑和 ASM 取消逻辑
        # 简化版：如果当前动作 ptr 指向的角色是场上角色，且他可以接受新动作，则执行
        target_char_name, method_name, params = self.actions[self.action_ptr]
        
        # 查找到对应角色对象 (这里假设 Team 能通过名字查找)
        char = self.ctx.team.get_character_by_name(target_char_name)
        if not char:
            self.action_ptr += 1
            return

        # 如果角色处于 IDLE 或已进入取消窗口
        if char.action_manager.request_action_by_name(method_name, params):
            self.action_ptr += 1

    def _is_finished(self) -> bool:
        # 队列为空且所有角色 IDLE
        if self.action_ptr < len(self.actions):
            return False
            
        for char in self.ctx.team.team:
            if char.action_manager.current_action is not None:
                return False
        return True
