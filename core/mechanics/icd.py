from typing import Dict, Any, Optional
from dataclasses import dataclass
from core.tool import GetCurrentTime

@dataclass
class ICDRule:
    """ICD 规则定义"""
    interval: int = 150 # 默认 2.5s (150帧 @ 60fps)
    hit_limit: int = 3   # 默认 3次打击

# 全局预定义规则
ICD_RULES: Dict[str, ICDRule] = {
    "Default": ICDRule(150, 3),
    "None": ICDRule(0, 1),       # 独立附着 (每一段都附着)
    "Independent": ICDRule(0, 1)  # 同上
}

class ICDManager:
    """
    ICD 管理器。
    负责追踪单个实体的元素附着冷却状态。
    """
    def __init__(self, owner):
        self.owner = owner
        # 记录每个标签的状态: [当前打击计数, 上次附着帧数]
        self.records: Dict[str, list] = {}

    def check_attachment(self, tag: str) -> bool:
        """
        根据标签判定本次攻击是否允许附着元素。
        """
        # 1. 独立附着判断
        if tag in ["None", "Independent", None]:
            return True
            
        current_frame = GetCurrentTime()
        rule = ICD_RULES.get(tag, ICD_RULES["Default"])
        
        if tag not in self.records:
            # 首次攻击，允许附着
            self.records[tag] = [1, current_frame]
            return True
        
        record = self.records[tag]
        hit_count = record[0]
        last_attach_frame = record[1]
        
        # 2. 判定时间冷却
        if current_frame - last_attach_frame >= rule.interval:
            record[0] = 1
            record[1] = current_frame
            return True
            
        # 3. 判定打击次数
        if hit_count >= rule.hit_limit:
            record[0] = 1
            record[1] = current_frame
            return True
            
        # 4. 不满足条件，仅增加计数
        record[0] += 1
        return False

    def reset(self, tag: Optional[str] = None):
        if tag:
            if tag in self.records: del self.records[tag]
        else:
            self.records.clear()