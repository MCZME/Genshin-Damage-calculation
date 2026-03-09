from typing import List, Dict, Any

class DamageDistProcessor:
    """
    [V6.9 Pro] 三阶伤害处理器。
    支持：1. 梯度断层识别 2. 贡献度底噪过滤 3. '元素:量' 格式解析。
    """

    @staticmethod
    def _clean_element(raw_val: Any) -> str:
        """
        [V7.0] 标准化元素解析器。
        严格遵循 '元素:量' 格式 (如 '火:1.0')。
        """
        raw_str = str(raw_val)
        if ":" in raw_str:
            return raw_str.split(":")[0]
        return raw_str if raw_str and raw_str != "None" else "Neutral"

    @staticmethod
    def process(raw_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        核心加工逻辑：聚合 -> 统计频率 -> 梯度识别分段。
        """
        frame_map = {}
        global_peak = 0.0
        max_hit_count = 0
        
        # 1. 基础帧聚合
        for ev in raw_events:
            f = ev['frame']
            if f not in frame_map:
                frame_map[f] = {"events": [], "total": 0.0, "hit_count": 0}
            
            # 使用强力清洗器获取纯净的元素名称
            elem_str = DamageDistProcessor._clean_element(ev.get('element', 'Neutral'))

            frame_map[f]["events"].append({
                "dmg": ev['value'],
                "element": elem_str,
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
        
        # 2. 统计特征提取
        frame_totals = sorted([d["total"] for d in frame_map.values() if d["total"] > 0])
        if not frame_totals:
            return DamageDistProcessor._empty_result()

        total_sum = sum(frame_totals)
        
        # 3. 三阶阈值决策
        # A. 确定噪音阈值 (5% 贡献度)
        acc_sum = 0
        noise_threshold = frame_totals[0]
        for v in frame_totals:
            acc_sum += v
            if acc_sum > total_sum * 0.05:
                noise_threshold = v
                break
        
        # B. 确定分段阈值 (梯度跃迁)
        effective_totals = [v for v in frame_totals if v >= noise_threshold]
        if len(effective_totals) > 1:
            gaps = [effective_totals[i+1] - effective_totals[i] for i in range(len(effective_totals)-1)]
            max_gap_idx = gaps.index(max(gaps))
            v_before = effective_totals[max_gap_idx]
            v_after = effective_totals[max_gap_idx + 1]
            
            candidate_split = max(v_before * 1.5, global_peak / 3.0)
            split_threshold = min(candidate_split, v_after)
            is_split = global_peak > split_threshold * 1.2
        else:
            split_threshold = global_peak
            is_split = False

        return {
            "frame_map": frame_map,
            "sorted_frames": sorted(frame_map.keys()),
            "global_peak": max(global_peak, 1.0),
            "noise_threshold": noise_threshold,
            "split_threshold": max(split_threshold, 1.0),
            "max_hit_count": max(max_hit_count, 1),
            "is_split_axis": is_split
        }

    @staticmethod
    def _empty_result():
        return {
            "frame_map": {}, "sorted_frames": [], "global_peak": 1.0,
            "noise_threshold": 0, "split_threshold": 1.0,
            "max_hit_count": 1, "is_split_axis": False
        }
