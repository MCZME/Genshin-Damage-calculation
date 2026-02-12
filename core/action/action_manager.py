from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from core.action.action_data import ActionFrameData
from core.logger import get_emulation_logger

if TYPE_CHECKING:
    from core.context import SimulationContext


class ActionInstance:
    """正在物理运行的动作实例。
    
    持有当前动作的实时帧计数和待触发的命中点序列。
    """

    def __init__(self, data: ActionFrameData) -> None:
        """初始化动作实例。

        Args:
            data: 该动作的元数据定义。
        """
        self.data: ActionFrameData = data
        self.elapsed_frames: int = 0
        self.hit_frames_pending: List[int] = sorted(data.hit_frames.copy())
        self.is_finished: bool = False

    def advance(self) -> bool:
        """递增动作进度并检查是否已到达自然终点。"""
        self.elapsed_frames += 1
        if self.elapsed_frames >= self.data.total_frames:
            self.is_finished = True
        return self.is_finished


class ActionManager:
    """
    动作状态机引擎 (ASM Engine)。
    
    负责管理单个实体的动作生命周期、执行精细化的动作取消 (Cancel) 逻辑，
    并协调物理位移与事件触发。
    """

    def __init__(self, character: Any, context: "SimulationContext") -> None:
        """初始化动作管理器。

        Args:
            character: 管理的目标实体 (通常为角色)。
            context: 当前仿真的上下文。
        """
        self.character = character
        self.ctx = context
        self.current_action: Optional[ActionInstance] = None

    def request_action(self, action_data: ActionFrameData) -> bool:
        """
        请求执行一个新动作。
        
        如果当前正在执行动作，系统会根据 `interrupt_frames` 判定是否允许立即中断。

        Args:
            action_data: 待执行的新动作物理元数据。

        Returns:
            bool: 动作请求是否被受理。
        """
        if self.current_action:
            # 尝试中断当前动作
            if self._can_cancel_current(action_data):
                self._terminate_current("CANCELLED")
            else:
                # 处于不可中断期，拒绝请求
                return False

        self._start_action(action_data)
        return True

    def request_action_by_name(self, method_name: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """
        [系统级接口] 通过方法名请求动作。
        通常由 Simulator 调用以驱动角色逻辑。

        Args:
            method_name: 角色类对应的方法名。
            params: 意图参数。

        Returns:
            bool: 动作是否受理。
        """
        if hasattr(self.character, method_name):
            method = getattr(self.character, method_name)
            try:
                # 调用角色方法，由方法内部通过 to_action_data 最终调用 request_action
                if params is not None:
                    return method(params)
                return method()
            except Exception as e:
                get_emulation_logger().log_error(
                    f"动作请求异常 [{method_name}]: {str(e)}", sender="ASM"
                )
                return False
        return False

    def on_frame_update(self) -> None:
        """每帧驱动逻辑。处理位移累加、命中点检测及自然结束判定。"""
        if not self.current_action:
            return

        instance = self.current_action
        
        # 1. 物理位移平摊处理 (XZ平面)
        if instance.data.horizontal_dist != 0:
            dist_per_frame = instance.data.horizontal_dist / instance.data.total_frames
            # 此处应配合实体朝向计算坐标增量，暂由上下文全局统计
            self.ctx.global_move_dist += dist_per_frame

        # 2. 命中点检测 (Hit-frame detection)
        # 注意：先判断是否命中，再递增帧，以符合 1-based 的测量直觉
        if instance.hit_frames_pending and (instance.elapsed_frames + 1) == instance.hit_frames_pending[0]:
            instance.hit_frames_pending.pop(0)
            self._trigger_hit()

        # 3. 进度推进与自然结束检查
        if instance.advance():
            self._terminate_current("FINISHED")

    def _start_action(self, data: ActionFrameData) -> None:
        """初始化并启动一个动作实例。"""
        self.current_action = ActionInstance(data)
        get_emulation_logger().log_info(
            f"{self.character.name} 执行: {data.name} (时长: {data.total_frames})", 
            sender="ASM"
        )

    def _trigger_hit(self) -> None:
        """触发命中点逻辑，回调技能层的 on_execute_hit。"""
        instance = self.current_action
        if instance and instance.data.origin_skill:
            skill = instance.data.origin_skill
            # 计算当前是第几段命中
            hit_idx = len(instance.data.hit_frames) - len(instance.hit_frames_pending) - 1
            if hasattr(skill, "on_execute_hit"):
                skill.on_execute_hit(None, hit_idx)

    def _can_cancel_current(self, next_action: ActionFrameData) -> bool:
        """核心判定：当前动作是否能被新动作取消。"""
        if not self.current_action:
            return True
            
        instance = self.current_action
        # 从元数据中检索针对目标动作类型的取消帧
        # 我们假设 data.name 或某些 tag 用于匹配
        # 这里的 key 应该对齐 ActionCommand 的命名，如 "dash", "elemental_skill"
        
        # 获取新动作的映射标识 (优先使用新动作定义的标签，如 'dash')
        # 简化处理：假设 next_action.name 包含了类型信息，或通过外部逻辑注入类型
        cancel_key = next_action.name.lower()
        
        # 查找取消窗口
        cancel_frame = instance.data.interrupt_frames.get(cancel_key)
        
        # 备选查找：通配符 'any'
        if cancel_frame is None:
            cancel_frame = instance.data.interrupt_frames.get("any")
            
        if cancel_frame is not None and instance.elapsed_frames >= cancel_frame:
            return True
            
        return False

    def _terminate_current(self, reason: str) -> None:
        """终结当前动作。"""
        if self.current_action:
            get_emulation_logger().log_info(
                f"{self.character.name} 动作中断 [{reason}]: {self.current_action.data.name}", 
                sender="ASM"
            )
            self.current_action = None
