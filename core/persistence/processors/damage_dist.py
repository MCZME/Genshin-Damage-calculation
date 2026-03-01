from typing import List, Dict, Any
import math

class DamageDistProcessor:
    """
    [V6.6 Pro] 伤害分布专项处理器。
    负责将原始伤害事件流转换为支持双段线性坐标系与频率热力图的 ViewModel。
    """

    @staticmethod
    def process(raw_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        核心加工逻辑：聚合 -> 统计频率 -> 计算分位数 -> 生成映射元数据。
        """
        frame_map = {}
        global_peak = 0.0
        max_hit_count = 0
        
        # 1. 基础帧聚合与频率统计
        for ev in raw_events:
            f = ev['frame']
            if f not in frame_map:
                frame_map[f] = {"events": [], "total": 0.0, "hit_count": 0}
            
            frame_map[f]["events"].append({
                "dmg": ev['value'],
                "element": ev['element'],
                "is_crit": "!" in ev.get('action', ''),
                "event_id": ev['event_id'],
                "source": ev['source']
            })
            frame_map[f]["total"] += ev['value']
            frame_map[f]["hit_count"] += 1
            
            if frame_map[f]["total"] > global_peak:
                global_peak = frame_map[f]["total"]
            if frame_map[f]["hit_count"] > max_hit_count:
                max_hit_count = frame_map[f]["hit_count"]
        
        # 2. P98 动态分段阈值计算
        # 提取所有有效伤害帧（排除极低底噪）
        frame_totals = [d["total"] for d in frame_map.values() if d["total"] > 1.0]
        frame_totals.sort()
        
        p98_threshold = global_peak # 默认不分段
        if frame_totals:
            idx = int(len(frame_totals) * 0.98)
            if idx >= len(frame_totals): idx = len(frame_totals) - 1
            p98_threshold = frame_totals[idx]
        
        # 3. 确定显示上限与分段策略
        # 规则：如果 GlobalMax 远高于 P98（>1.5倍），则激活双段显示
        is_split = global_peak > p98_threshold * 1.5
        display_ceiling = global_peak if not is_split else p98_threshold * 1.5
        
        # 4. ViewModel 构建
        return {
            "frame_map": frame_map,
            "sorted_frames": sorted(frame_map.keys()),
            "global_peak": max(global_peak, 1.0),
            "p98_threshold": max(p98_threshold, 1.0),
            "display_ceiling": max(display_ceiling, 1.0),
            "max_hit_count": max(max_hit_count, 1),
            "is_split_axis": is_split
        }
