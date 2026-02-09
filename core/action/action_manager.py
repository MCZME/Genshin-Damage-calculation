from typing import Any, Optional
from core.action.action_data import ActionFrameData
from core.logger import get_emulation_logger

class ActionInstance:
    """正在运行的动作实例"""
    def __init__(self, data: ActionFrameData):
        self.data = data
        self.elapsed_frames = 0
        self.hit_frames_pending = data.hit_frames.copy()
        self.is_finished = False

    def advance(self) -> bool:
        if self.elapsed_frames >= self.data.total_frames:
            self.is_finished = True
        return self.is_finished

class ActionManager:
    """
    动作状态机引擎 (ASM Engine)。
    负责管理单个实体的动作生命周期、取消窗口和事件触发。
    """
    def __init__(self, character, context):
        self.character = character
        self.ctx = context
        self.current_action: Optional[ActionInstance] = None
        
    def request_action(self, action_data: ActionFrameData) -> bool:
        """
        请求执行一个新动作。
        如果当前正在执行动作，会检查取消窗口。
        """
        if self.current_action:
            # 检查当前动作是否允许被新动作取消
            if self._can_cancel_current(action_data.name):
                self._terminate_current("CANCELLED")
            else:
                return False # 无法取消，拒绝请求
        
        self._start_action(action_data)
        return True

    def request_action_by_name(self, method_name: str, params: Any = None) -> bool:
        """
        [Simulator 专用] 通过方法名请求动作。
        """
        # 如果是切换动作，Simulator 已经处理了 swap，这里只需调用对应方法
        if hasattr(self.character, method_name):
            attr = getattr(self.character, method_name)
            try:
                # 执行方法并返回其布尔结果 (受理状态)
                if params is not None:
                    return attr(params)
                else:
                    return attr()
            except Exception as e:
                get_emulation_logger().log_error(f"Action request failed for {method_name}: {e}")
                return False
        return False

    def on_frame_update(self):
        """每帧驱动逻辑"""
        if not self.current_action:
            return

        instance = self.current_action
        
        # 0. 驱动技能内部逻辑 (无需参数)
        instance.elapsed_frames += 1 # 先增加帧计数
        if instance.data.origin_skill and hasattr(instance.data.origin_skill, 'on_frame_update'):
            instance.data.origin_skill.current_frame = instance.elapsed_frames
            try:
                instance.data.origin_skill.on_frame_update()
            except Exception as e:
                get_emulation_logger().log_error(f"Skill update failed: {e}")

        # 1. 检查判定点 (Hitframes)
        # 如果当前帧是伤害帧，则触发伤害逻辑 (具体的伤害逻辑由 Character/Skill 提供回调或发布事件)
        if instance.hit_frames_pending and instance.elapsed_frames == instance.hit_frames_pending[0]:
            instance.hit_frames_pending.pop(0)
            self._trigger_hit()

        # 2. 累到位移 (Displacement)
        if instance.data.horizontal_dist > 0:
            # 平摊到每一帧，或者在起始帧一次性增加？
            # 模拟器倾向于平摊以保持“每一刻的状态”
            dist_per_frame = instance.data.horizontal_dist / instance.data.total_frames
            self.ctx.global_move_dist += dist_per_frame

        # 3. 推进帧
        if instance.advance():
            self._terminate_current("FINISHED")

    def _start_action(self, data: ActionFrameData):
        self.current_action = ActionInstance(data)
        get_emulation_logger().log_info(f"{self.character.name} 开始执行动作: {data.name} (时长: {data.total_frames} 帧)", sender="ASM")
        
        # 建立运行时绑定
        if self.current_action.data.origin_skill:
            self.current_action.data.origin_skill.caster = self.character

    def _trigger_hit(self):
        """
        触发命中点逻辑。
        """
        instance = self.current_action
        if instance.data.origin_skill and hasattr(instance.data.origin_skill, 'on_execute_hit'):
            # 计算当前命中的索引 (total - remaining)
            hit_idx = len(instance.data.hit_frames) - len(instance.hit_frames_pending) - 1
            instance.data.origin_skill.on_execute_hit(self.ctx.target, hit_idx)

    def _can_cancel_current(self, next_action_name: str) -> bool:
        if not self.current_action:
            return True
        
        # 查找取消窗口
        instance = self.current_action
        cancel_frame = instance.data.cancel_windows.get(next_action_name)
        
        # 如果没配置具体的，看有没有通用取消点 'ANY'
        if cancel_frame is None:
            cancel_frame = instance.data.cancel_windows.get('ANY')
            
        if cancel_frame is not None and instance.elapsed_frames >= cancel_frame:
            return True
            
        return False

    def _terminate_current(self, reason: str):
        if self.current_action:
            get_emulation_logger().log_info(f"{self.character.name} 动作结束 ({reason}: {self.current_action.data.name})", sender="ASM")
            self.current_action = None
