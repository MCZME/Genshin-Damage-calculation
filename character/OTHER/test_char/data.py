"""测试角色 (ID 1) 的模拟数据 (V2.5 审计验证版)。"""

# --- 角色基础信息 ---
NAME = "测试角色"
ID = 1
RARITY = 4
ELEMENT = "风"
WEAPON_TYPE = "单手剑"
BREAKTHROUGH_PROP = "攻击力"

# --- 角色基础属性 (Level: Stats) ---
# 补充了 V2.5 审计所需的各种细分字段
BASE_STATS = {
    1: {
        "hp": 1000.0, "atk": 100.0, "def": 50.0, 
        "crit_rate": 5.0, "crit_dmg": 50.0, "元素精通": 0.0,
        "攻击力%": 0.0, "固定攻击力": 0.0
    },
    90: {
        "hp": 10000.0, "atk": 300.0, "def": 600.0, 
        "crit_rate": 5.0, "crit_dmg": 50.0, "元素精通": 100.0,
        "攻击力%": 20.0, "固定攻击力": 50.0 # 模拟面板绿字
    },
}

# --- 技能倍率 (格式: [属性名, [Lv1..Lv15]]) ---
NORMAL_ATTACK_DATA = {
    "一段伤害": ["攻击力", [50.0] * 15],
    "二段伤害": ["攻击力", [60.0] * 15],
    "三段伤害": ["攻击力", [80.0] * 15],
    "重击伤害": ["攻击力", [120.0] * 15],
    "下落期间伤害": ["攻击力", [80.0] * 15],
    "低空坠地冲击伤害": ["攻击力", [150.0] * 15],
    "高空坠地冲击伤害": ["攻击力", [200.0] * 15],
}

ELEMENTAL_SKILL_DATA = {
    "技能伤害": ["攻击力", [250.0] * 15],
}

ELEMENTAL_BURST_DATA = {
    "技能伤害": ["攻击力", [600.0] * 15],
}

# --- 核心机制常量 ---
MECHANISM_CONFIG = {
    "id": 1,
    "name": "test_char",
    "element": "风",
    "weapon": "单手剑",
    "region": "OTHER"
}

# --- 动作时序数据 (Action Timing) ---
ACTION_FRAME_DATA = {
    "普通攻击1": {
        "hit_frames": [10], "total_frames": 20,
        "interrupt_frames": {"normal_attack": 15, "any": 20},
    },
    "普通攻击2": {
        "hit_frames": [11], "total_frames": 22,
        "interrupt_frames": {"normal_attack": 16, "any": 22},
    },
    "普通攻击3": {
        "hit_frames": [12], "total_frames": 25,
        "interrupt_frames": {"normal_attack": 18, "any": 25},
    },
    "重击": {
        "hit_frames": [15], "total_frames": 30,
        "interrupt_frames": {"dash": 25, "any": 30},
    },
    "元素战技": {
        "hit_frames": [20], "total_frames": 40,
        "interrupt_frames": {"dash": 30, "any": 40},
    },
    "元素爆发": {
        "hit_frames": [45], "total_frames": 60,
        "interrupt_frames": {"dash": 50, "any": 60},
    },
}

# --- 攻击数据 (Attack Data) ---
ATTACK_DATA = {
    "普通攻击1": {
        "attack_tag": "普通攻击1", "element_u": 1.0, "is_ranged": False,
        "icd_tag": "Default", "icd_group": "NormalAttack",
        "shape": "圆柱", "radius": 1.5, "height": 1.0, "strike_type": "切割",
    },
    "普通攻击2": {
        "attack_tag": "普通攻击2", "element_u": 1.0, "is_ranged": False,
        "icd_tag": "Default", "icd_group": "NormalAttack",
        "shape": "圆柱", "radius": 1.5, "height": 1.0, "strike_type": "切割",
    },
    "普通攻击3": {
        "attack_tag": "普通攻击3", "element_u": 1.0, "is_ranged": False,
        "icd_tag": "Default", "icd_group": "NormalAttack",
        "shape": "长方体", "width": 2.0, "height": 1.5, "length": 3.0, "strike_type": "切割",
    },
    "重击": {
        "attack_tag": "重击", "element_u": 1.0, "is_ranged": False,
        "icd_tag": "Default", "icd_group": "ChargedAttack",
        "shape": "球", "radius": 2.0, "strike_type": "切割",
    },
    "元素战技": {
        "attack_tag": "元素战技", "element_u": 1.0, "is_ranged": False,
        "icd_tag": "None", "icd_group": "None",
        "shape": "球", "radius": 5.0, "strike_type": "默认",
    },
    "混合缩放测试": {
        "attack_tag": "元素战技", "element_u": 1.0, "is_ranged": False,
        "icd_tag": "None", "icd_group": "None",
        "shape": "球", "radius": 5.0, "strike_type": "默认",
    },
    "剧变反应测试": {
        "attack_tag": "元素爆发", "element_u": 1.0, "is_ranged": False,
        "icd_tag": "None", "icd_group": "None",
        "shape": "球", "radius": 6.0, "strike_type": "默认",
    },
    "元素爆发": {
        "attack_tag": "元素爆发", "element_u": 1.0, "is_ranged": False,
        "icd_tag": "None", "icd_group": "None",
        "shape": "球", "radius": 10.0, "strike_type": "默认",
    },
}
