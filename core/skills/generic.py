from typing import Any, Dict, List, Union
from core.skills.base import SkillBase
from core.action.action_data import ActionFrameData
from core.action.damage import Damage, DamageType
from core.event import DamageEvent
from core.tool import GetCurrentTime

class GenericSkill(SkillBase):
    """
    通用技能类。
    能够通过配置数据动态定义技能行为，支持多段伤害和 ASM 对接。
    """
    def __init__(self, name: str, config: Dict[str, Any], lv: int, caster: Any = None):
        """
        :param name: 技能名称
        :param config: 包含帧数和倍率的配置字典
        :param lv: 技能等级 (1-15)
        :param caster: 施法者对象
        """
        super().__init__(
            name=name,
            total_frames=config.get("total_frames", 60),
            cd=config.get("cd", 0),
            lv=lv,
            element=config.get("element", ("物理", 0)),
            caster=caster
        )
        # 伤害判定帧列表 [frame1, frame2, ...]
        self.hit_frames: List[int] = config.get("hit_frames", [])
        
        # 倍率配置列表，支持单段 [lv1..15] 或多段 [[lv1..15], [lv1..15]]
        self.multipliers: List[Union[float, List[float]]] = config.get("multipliers", [])
        
        # 伤害类型 (NORMAL, SKILL, BURST 等)
        self.damage_type: DamageType = config.get("damage_type", DamageType.SKILL)
        
        # 取消窗口配置 {"jump": 12, "dash": 15}
        self.cancel_windows: Dict[str, int] = config.get("cancel_windows", {})

    def to_action_data(self, params: Any = None) -> ActionFrameData:
        """生成供 ASM 调用的动作数据"""
        data = ActionFrameData(
            name=self.name,
            total_frames=self.total_frames,
            hit_frames=self.hit_frames,
            cancel_windows=self.cancel_windows
        )
        # 挂载运行时对象，以便 ActionManager 每一帧回调 on_frame_update
        data.origin_skill = self
        return data

    def on_frame_update(self, target: Any):
        """
        ASM 每一帧的回调逻辑。
        目前通用逻辑已由 ASM 处理命中检查，此处可留空或处理持续性效果。
        """
        pass

    def on_execute_hit(self, target: Any, hit_index: int):
        """
        当 ASM 命中点触发时的标准回调。
        """
        self._apply_damage(target, hit_index)

    def _apply_damage(self, target: Any, hit_index: int):
        """执行具体的伤害发布逻辑"""
        if not self.caster or hit_index >= len(self.multipliers):
            return

        # 获取当前等级对应的倍率数值
        m_data = self.multipliers[hit_index]
        if isinstance(m_data, list):
            # 处理多级倍率表
            multiplier = m_data[self.lv - 1] if self.lv <= len(m_data) else m_data[-1]
        else:
            # 兼容单固定倍率
            multiplier = m_data

        damage = Damage(
            damage_multiplier=multiplier,
            element=self.element,
            damage_type=self.damage_type,
            name=f"{self.name} 第{hit_index + 1}段"
        )
        
        # 通过实体的局部引擎发布伤害事件 (自动冒泡至全局计算系统)
        self.caster.event_engine.publish(
            DamageEvent(self.caster, target, damage, GetCurrentTime())
        )
