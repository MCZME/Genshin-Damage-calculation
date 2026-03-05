from typing import List, Dict, Any, Optional
import math

class AuditProcessor:
    """
    [V7.2 Pro] 伤害审计处理器 (增量向量版)。
    负责将离散的审计记录聚合为标准的 7 乘区模型，适配全 ADD 增量逻辑。
    """
    
    # 核心映射表：从中文字段映射到 7 个 UI 审计桶
    BUCKET_MAP = {
        "BASE": ["攻击力", "生命值", "防御力", "元素精通"],
        "MULTIPLIER": ["倍率", "固定伤害值加成"], # 包含动态匹配末尾为"倍率"的项
        "BONUS": ["伤害加成", "动作类型增伤"],
        "CRIT": ["暴击率", "暴击伤害"],
        "REACTION": ["反应基础倍率", "反应加成系数", "剧变反应基础", "最终伤害"],
        "DEFENSE": ["防御区系数"],
        "RESISTANCE": ["抗性区系数"]
    }

    @staticmethod
    def process_detail(raw_trail: List[Dict[str, Any]], is_crit: bool = False) -> Dict[str, Any]:
        """
        [核心] 聚合原始审计链为 7 大乘区大类。
        """
        buckets = {
            "base": {"total": 0.0, "steps": []},
            "multiplier": {"multiplier": 1.0, "flat": 0.0, "steps": []},
            "bonus": {"multiplier": 1.0, "steps": []},
            "crit": {"multiplier": 1.0, "steps": []},
            "reaction": {"multiplier": 1.0, "steps": []},
            "defense": {"multiplier": 1.0, "steps": []},
            "resistance": {"multiplier": 1.0, "steps": []}
        }

        # 1. 遍历审计链进行归类
        for entry in raw_trail:
            stat = entry.get("stat", "")
            val = entry.get("value", 0.0)
            op = entry.get("op", "ADD")
            source = entry.get("source", "Unknown")
            
            # 找到所属桶
            target_key = None
            for b_key, stats in AuditProcessor.BUCKET_MAP.items():
                if stat in stats or stat.endswith("倍率"):
                    target_key = b_key.lower()
                    break
            
            if not target_key:
                continue

            buckets[target_key]["steps"].append({
                "stat": stat,
                "value": val,
                "op": op,
                "source": source
            })

        # 2. 内部合算逻辑 (适配全 ADD 驱动)
        
        # [Base] 基础属性：直接累加
        for s in buckets["base"]["steps"]:
            buckets["base"]["total"] += s["value"]

        # [Multiplier] 倍率区
        for s in buckets["multiplier"]["steps"]:
            if "倍率" in s["stat"]:
                # 记录最新的倍率分量
                buckets["multiplier"]["multiplier"] = s["value"] / 100 if s["value"] > 5 else s["value"]
            elif s["stat"] == "固定伤害值加成":
                buckets["multiplier"]["flat"] += s["value"]

        # [Bonus] 增伤区
        b_sum = 0.0
        for s in buckets["bonus"]["steps"]:
            b_sum += s["value"]
        buckets["bonus"]["multiplier"] = 1.0 + (b_sum / 100.0)

        # [Crit] 暴击区
        if is_crit:
            c_val = 100.0
            for s in buckets["crit"]["steps"]:
                if s["stat"] == "暴击伤害": c_val = s["value"]
            buckets["crit"]["multiplier"] = c_val / 100.0
        else:
            buckets["crit"]["multiplier"] = 1.0

        # [Reaction] 反应区
        r_base = 1.0
        r_bonus = 0.0
        for s in buckets["reaction"]["steps"]:
            if s["stat"] == "反应基础倍率": r_base = s["value"]
            elif s["stat"] == "反应加成系数": r_bonus += s["value"]
        buckets["reaction"]["multiplier"] = r_base * (1.0 + r_bonus) if r_base > 0 else 1.0

        # [Defense] 防御区
        d_coeff = 0.0
        for s in buckets["defense"]["steps"]:
            d_coeff += s["value"]
        buckets["defense"]["multiplier"] = d_coeff if d_coeff > 0 else 1.0

        # [Resistance] 抗性区
        res_coeff = 0.0
        for s in buckets["resistance"]["steps"]:
            res_coeff += s["value"]
        buckets["resistance"]["multiplier"] = res_coeff if res_coeff > 0 else 1.0

        return buckets

