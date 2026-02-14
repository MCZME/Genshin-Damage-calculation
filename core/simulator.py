from typing import Any, Callable, List, Optional
import traceback

from core.action.action_data import ActionCommand
from core.context import SimulationContext
from core.event import GameEvent, EventType
from core.logger import get_emulation_logger


class Simulator:
    """
    新一代战斗模拟引擎。
    负责驱动时间轴、协调动作指令序列以及同步各系统状态。
    """

    def __init__(
        self,
        context: SimulationContext,
        action_sequence: List[ActionCommand],
        persistence_db: Optional[Any] = None,
        on_progress: Optional[Callable[[int], Any]] = None,
    ):
        """初始化模拟器。

        Args:
            context: 模拟上下文实例。
            action_sequence: 待执行的动作指令序列。
            persistence_db: 可选的持久化数据库接口。
            on_progress: 进度回调函数，接收当前帧数作为参数。
        """
        self.ctx = context
        self.actions = action_sequence
        self.action_ptr = 0
        self.is_running = False
        self.db = persistence_db
        self.on_progress = on_progress
        self.max_frames = 18000  # 5分钟硬限制 (60fps * 300s)

    async def run(self) -> None:
        """开始异步模拟循环。

        驱动每一帧的物理更新、指令下发、事件发布以及状态持久化。
        """
        self.is_running = True
        get_emulation_logger().log_info("模拟开始执行", sender="Simulator")

        try:
            # 初始帧前准备
            self._prepare_simulation()

            while self.is_running:
                # 1. 推进全局帧 (此方法内部会驱动 ctx.space.on_frame_update, 进而驱动 team)
                self.ctx.advance_frame()

                # 安全限制
                if self.ctx.current_frame > self.max_frames:
                    get_emulation_logger().log_error("仿真超时，强制终止")
                    break

                # 2. 尝试下发指令
                self._try_enqueue_next_action()

                # 3. 发布帧结束事件 (驱动各 System 结算)
                self.ctx.event_engine.publish(
                    GameEvent(EventType.FRAME_END, self.ctx.current_frame)
                )

                # 4. 持久化快照
                if self.db:
                    self.db.record_snapshot(self.ctx.take_snapshot())

                # 5. UI 进度通知 (每 10 帧同步一次)
                if self.on_progress and self.ctx.current_frame % 10 == 0:
                    await self.on_progress(self.ctx.current_frame)

                # 6. 检查是否所有动作已完成且角色处于空闲态
                if self._is_finished():
                    get_emulation_logger().log_info(
                        f"检测到终止条件满足 (Frame: {self.ctx.current_frame}, Ptr: {self.action_ptr})",
                        sender="Simulator",
                    )
                    self.is_running = False

        except Exception as e:
            error_msg = f"仿真运行异常中断: {str(e)}\n{traceback.format_exc()}"
            get_emulation_logger().log_error(error_msg)
            raise
        finally:
            self.is_running = False

        # 仿真结束后确保最后一次进度同步
        if self.on_progress:
            await self.on_progress(self.ctx.current_frame)

        get_emulation_logger().log_info("模拟执行完毕", sender="Simulator")

    def _prepare_simulation(self) -> None:
        """模拟启动前的预处理逻辑。"""
        self._try_enqueue_next_action()

    def _try_enqueue_next_action(self) -> None:
        """尝试从指令序列中提取下一个指令并请求角色执行。"""
        if self.action_ptr >= len(self.actions):
            return

        command: ActionCommand = self.actions[self.action_ptr]

        # 优先从 Team 实例中查找角色 (通过 Space 访问)
        char = None
        if self.ctx.space and self.ctx.space.team:
            char = self.ctx.space.team.get_character_by_name(command.character_name)

        if not char:
            get_emulation_logger().log_error(
                f"无法找到角色: {command.character_name}, 跳过指令", sender="Simulator"
            )
            self.action_ptr += 1
            return

        # 尝试通过角色提供的统一动作分发接口执行指令
        if char.perform_action(command.action_type, command.params):
            self.action_ptr += 1

    def _is_finished(self) -> bool:
        """检查模拟是否达到终止条件。

        终止条件：指令序列已全部下发，且当前场上所有角色均处于 IDLE 状态。
        """
        if self.action_ptr < len(self.actions):
            return False

        # 检查所有玩家实体的动作状态
        if self.ctx.space and self.ctx.space.team:
            for char in self.ctx.space.team.get_members():
                # 兼容性检查：如果 ActionManager 持有正在执行的任务，则认为没结束
                if (
                    getattr(char.action_manager, "current_character_action", None)
                    is not None
                ):
                    return False
                if getattr(char.action_manager, "current_action", None) is not None:
                    return False
        return True
