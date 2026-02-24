from typing import List, Dict, Any, Tuple
import json

class AnalysisDataProcessor:
    """
    [V4.0 数据加工层] 纯逻辑处理层。
    负责将 Repository 返回的原始行数据转换为 UI 友好的聚合模型。
    """
    
    @staticmethod
    def process_dps_series(raw_events: List[Dict[str, Any]], name_map: Dict[int, str], total_frames: int, window_size: int = 180) -> Dict[str, List[Dict[str, Any]]]:
        """
        [核心] 计算分角色平滑 DPS 序列。
        采用滑动平均算法，将离散伤害脉冲转化为连续面积图数据。
        """
        # 1. 初始化各角色在全时间轴上的伤害桶 (每帧一个桶)
        series_buckets: Dict[str, List[float]] = {}
        for name in name_map.values():
            series_buckets[name] = [0.0] * (total_frames + 1)
        
        # 2. 将原始伤害填入桶中
        for ev in raw_events:
            name = name_map.get(ev['source_id'], f"Unknown_{ev['source_id']}")
            if name not in series_buckets: series_buckets[name] = [0.0] * (total_frames + 1)
            series_buckets[name][ev['frame']] += ev['dmg']
            
        # 3. 滑动平均处理 (SMA)
        processed_series: Dict[str, List[Dict[str, Any]]] = {}
        for name, buckets in series_buckets.items():
            # 这里的计算可以优化，目前采用简单的窗口求和
            smoothed = []
            current_window_sum = 0.0
            
            for f in range(total_frames + 1):
                # 进窗
                current_window_sum += buckets[f]
                # 出窗
                if f >= window_size:
                    current_window_sum -= buckets[f - window_size]
                
                # 计算当前帧的平滑 DPS (总和 / 窗口时长)
                # 窗口时长(秒) = window_size / 60
                val = current_window_sum / (window_size / 60.0)
                
                # 降低采样密度：每 30 帧 (0.5秒) 采样一次，大幅提升渲染性能
                if f % 30 == 0 or f == total_frames: 
                    smoothed.append({"frame": f, "value": val})
            
            processed_series[name] = smoothed
            
        return processed_series

    @staticmethod
    def process_action_segments(raw_pulses: List[Dict[str, Any]], name_map: Dict[int, str]) -> Dict[str, List[Dict[str, Any]]]:
        """将逐帧的脉冲点聚合为具有起始、结束帧的动作片段"""
        tracks: Dict[str, List[Dict[str, Any]]] = {}
        
        # 内部临时存储：eid -> {current_action, start_frame}
        state = {}
        
        for p in raw_pulses:
            eid = p['eid']
            fid = p['f']
            aid = p['action']
            name = name_map.get(eid, f"Char_{eid}")
            
            if name not in tracks: tracks[name] = []
            
            if eid not in state:
                state[eid] = {"action": aid, "start": fid}
            elif state[eid]["action"] != aid:
                # 结束旧片段
                tracks[name].append({
                    "start": state[eid]["start"],
                    "end": fid - 1,
                    "action": state[eid]["action"]
                })
                # 开始新片段
                state[eid] = {"action": aid, "start": fid}
                
        # 处理结尾
        for eid, s in state.items():
            name = name_map.get(eid, f"Char_{eid}")
            tracks[name].append({
                "start": s["start"],
                "end": s["start"] + 1, # 占位，实际中可以取最后一帧
                "action": s["action"]
            })
            
        return tracks

    @staticmethod
    def process_trajectories(raw_pulses: List[Dict[str, Any]], name_map: Dict[int, str]) -> Dict[str, List[Dict[str, Any]]]:
        """转换物理轨迹格式"""
        trajectories = {}
        for p in raw_pulses:
            name = name_map.get(p['eid'], f"Entity_{p['eid']}")
            if name not in trajectories: trajectories[name] = []
            trajectories[name].append({"f": p['f'], "pos": (p['x'], p['z']), "on": bool(p['on'])})
        return trajectories

    @staticmethod
    def process_reaction_stats(raw_payloads: List[str]) -> Dict[str, int]:
        stats = {}
        for payload_str in raw_payloads:
            try:
                payload = json.loads(payload_str)
                reaction = payload.get("elemental_reaction", {})
                rtype = reaction.get("reaction_type")
                if rtype:
                    stats[rtype] = stats.get(rtype, 0) + 1
            except:
                continue
        return stats

    @staticmethod
    def process_mechanism_trajectories(raw_metrics: List[Dict[str, Any]], name_map: Dict[int, str]) -> Dict[str, List[Tuple[int, float]]]:
        trajectories = {}
        for m in raw_metrics:
            e_name = name_map.get(m['eid'], f"ID:{m['eid']}")
            m_key = f"{e_name}-{m['key']}"
            if m_key not in trajectories:
                trajectories[m_key] = []
            trajectories[m_key].append((m['f'], m['val']))
        return trajectories
