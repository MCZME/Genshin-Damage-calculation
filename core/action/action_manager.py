from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from core.action.action_data import ActionFrameData
from core.logger import get_emulation_logger

if TYPE_CHECKING:
    from core.context import SimulationContext


class ActionInstance:
    """正在物理运行的动作实例。"""

    def __init__(self, data: ActionFrameData) -> None:
        self.data: ActionFrameData = data
        self.elapsed_frames: int = 0
        self.hit_frames_pending: List[int] = sorted(data.hit_frames.copy())
        self.is_finished: bool = False

    def advance(self) -> bool:
        self.elapsed_frames += 1
        return self.elapsed_frames >= self.data.total_frames


class ActionManager:
    """
    动作状态机引擎 (V2.4 连招管理版)。
    """

    def __init__(self, character: Any, context: "SimulationContext") -> None:
        self.character = character
        self.ctx = context
        self.current_action: Optional[ActionInstance] = None
        
        # 连招状态管理
        self.combo_counter: int = 1
        self.max_combo: int = 5 # 默认 5 段
        self.combo_reset_frames: int = 120 # 2秒不按普攻重置
        self.idle_timer: int = 0

    def request_action(self, action_data: ActionFrameData) -> bool:
        """请求执行动作，包含连击同步与中断判定。"""
        
        # 1. 自动处理普攻段位
        if action_data.action_type == "normal_attack":
            # 如果动作本身没定段位，自动分配当前计数
            if action_data.combo_index == 0:
                action_data.combo_index = self.combo_counter
        else:
            # 执行非普攻动作（如闪避、技能），通常会重置普攻段位（取决于具体角色）
            # 这里先做简单处理：非普攻动作立即重置计数
            self._reset_combo()

        # 2. 中断判定
        if self.current_action:
            if self._can_cancel_current(action_data):
                self._terminate_current("CANCELLED")
            else:
                return False

        # 3. 启动动作并推进段位
        self._start_action(action_data)
        if action_data.action_type == "normal_attack":
            self.combo_counter = (self.combo_counter % self.max_combo) + 1
            self.idle_timer = 0
            
        return True

    def on_frame_update(self) -> None:
        if not self.current_action:
            self.idle_timer += 1
            if self.idle_timer >= self.combo_reset_frames:
                self._reset_combo()
            return

        instance = self.current_action
        
        # 1. 位移平摊
        if instance.data.horizontal_dist != 0:
            self.ctx.global_move_dist += instance.data.horizontal_dist / instance.data.total_frames

        # 2. 命中检测
        if instance.hit_frames_pending and (instance.elapsed_frames + 1) == instance.hit_frames_pending[0]:
            instance.hit_frames_pending.pop(0)
            self._trigger_hit()

        # 3. 推进
        if instance.advance():
            self._terminate_current("FINISHED")

    def _can_cancel_current(self, next_action: ActionFrameData) -> bool:
        """根据新动作类型检索中断帧。"""
        instance = self.current_action
        if not instance: return True
        
        # 优先使用 action_type 作为检索 key (如 "dash", "normal_attack")
        cancel_key = next_action.action_type
        cancel_frame = instance.data.interrupt_frames.get(cancel_key)
        
        # 兜底查找
        if cancel_frame is None:
            cancel_frame = instance.data.interrupt_frames.get("any")
            
        return cancel_frame is not None and instance.elapsed_frames >= cancel_frame

    def _start_action(self, data: ActionFrameData) -> None:
        self.current_action = ActionInstance(data)
        get_emulation_logger().log_info(
            f"{self.character.name} 执行: {data.name} (段位: {data.combo_index})", 
            sender="ASM"
        )

    def _trigger_hit(self) -> None:
        instance = self.current_action
        if instance and instance.data.origin_skill:
            hit_idx = len(instance.data.hit_frames) - len(instance.hit_frames_pending) - 1
            # 回调时透传 combo_index 以便技能层识别倍率
            instance.data.origin_skill.on_execute_hit(None, hit_idx)

    def _terminate_current(self, reason: str) -> None:
        self.current_action = None

    def _reset_combo(self) -> None:
        if self.combo_counter != 1:
            self.combo_counter = 1
            get_emulation_logger().log_debug(f"{self.character.name} 连击计数重置", sender="ASM")
