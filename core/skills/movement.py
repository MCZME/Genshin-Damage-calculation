from typing import Any, TypedDict
from core.skills.base import SkillBase
from core.action.action_data import ActionFrameData


class FrameData(TypedDict, total=False):
    """帧数据结构。"""
    total_frames: int
    interrupt_frames: dict[str, int]


class DashSkill(SkillBase):
    """
    通用冲刺/闪避组件 (V2.4 动作工厂版)。
    主要用于触发位移、打断后摇以及提供动作状态。
    """

    def __init__(self, lv: int = 1, caster: Any = None):
        super().__init__(lv, caster)
        # 默认冲刺时序 (若 data.py 未定义则使用此默认值)
        self.default_frames: FrameData = {"total_frames": 20, "interrupt_frames": {"any": 20}}

    def to_action_data(
        self, intent: dict[str, Any] | None = None
    ) -> ActionFrameData:
        # 尝试从角色数据中获取实测冲刺数据
        frames: FrameData = self.default_frames
        if hasattr(self.caster, "action_frame_data"):
            raw = self.caster.action_frame_data.get("DASH", self.default_frames)
            if isinstance(raw, dict):
                frames = raw  # type: ignore[assignment]

        total = frames["total_frames"]
        interrupt_frames = frames.get("interrupt_frames", {"any": total})

        return ActionFrameData(
            name="冲刺",
            action_type="dash",
            total_frames=total,
            hit_frames=[],
            interrupt_frames=interrupt_frames,
            origin_skill=self,
        )

    def on_frame_update(self) -> None:
        """每一帧的位移逻辑。"""
        # 在此处执行物理位移累加 (暂略)
        pass


class JumpSkill(SkillBase):
    """
    通用跳跃组件 (V2.4 动作工厂版)。
    """

    def __init__(self, lv: int = 1, caster: Any = None):
        super().__init__(lv, caster)
        self.default_frames: FrameData = {"total_frames": 31, "interrupt_frames": {"any": 31}}

    def to_action_data(
        self, intent: dict[str, Any] | None = None
    ) -> ActionFrameData:
        frames: FrameData = self.default_frames
        if hasattr(self.caster, "action_frame_data"):
            raw = self.caster.action_frame_data.get("JUMP", self.default_frames)
            if isinstance(raw, dict):
                frames = raw  # type: ignore[assignment]

        total = frames["total_frames"]
        interrupt_frames = frames.get("interrupt_frames", {"any": total})

        return ActionFrameData(
            name="跳跃",
            action_type="jump",
            total_frames=total,
            hit_frames=[],
            interrupt_frames=interrupt_frames,
            origin_skill=self,
        )

    def on_frame_update(self) -> None:
        """处理垂直上升逻辑。"""
        pass
