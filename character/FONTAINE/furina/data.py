"""芙宁娜 的自动化提取数据 (V2.3.1) + 实测原生数据 (V2.4)。"""

# --- 角色基础信息 ---
NAME = "芙宁娜"
ID = 75
RARITY = 5
ELEMENT = "水"
WEAPON_TYPE = "单手剑"
BREAKTHROUGH_PROP = "暴击率"

# --- 技能倍率 (高精度) ---
# NORMAL_ATTACK_DATA 格式: [属性名, [Lv1..Lv15]]
NORMAL_ATTACK_DATA = {
    "一段伤害": ["攻击力", [48.3862, 52.3246, 56.263, 61.8893, 65.8277, 70.3287, 76.5177, 82.7066, 88.8955, 95.6471, 102.3987, 109.1502, 115.9018, 122.6533, 129.4049]],
    "二段伤害": ["攻击力", [43.7293, 47.2886, 50.848, 55.9328, 59.4922, 63.56, 69.1533, 74.7466, 80.3398, 86.4416, 92.5434, 98.6451, 104.7469, 110.8486, 116.9504]],
    "三段伤害": ["攻击力", [55.12, 59.6065, 64.093, 70.5023, 74.9888, 80.1162, 87.1665, 94.2167, 101.2669, 108.9581, 116.6493, 124.3404, 132.0316, 139.7227, 147.4139]],
    "四段伤害": ["攻击力", [73.2978, 79.2639, 85.23, 93.753, 99.7191, 106.5375, 115.9128, 125.2881, 134.6634, 144.891, 155.1186, 165.3462, 175.5738, 185.8014, 196.029]],
    "重击伤害": ["攻击力", [74.218, 80.259, 86.3, 94.93, 100.971, 107.875, 117.368, 126.861, 136.354, 146.71, 157.066, 167.422, 177.778, 188.134, 198.49]],
}

ELEMENTAL_SKILL_DATA = {
    "荒性泡沫伤害": ["生命值", [7.864, 8.4538, 9.0436, 9.83, 10.4198, 11.0096, 11.796, 12.5824, 13.3688, 14.1552, 14.9416, 15.728, 16.711, 17.694, 18.677]],
    "乌瑟勋爵伤害": ["生命值", [5.96, 6.407, 6.854, 7.45, 7.897, 8.344, 8.94, 9.536, 10.132, 10.728, 11.324, 11.92, 12.665, 13.41, 14.155]],
    "海薇玛夫人伤害": ["生命值", [3.232, 3.4744, 3.7168, 4.04, 4.2824, 4.5248, 4.848, 5.1712, 5.4944, 5.8176, 6.1408, 6.464, 6.868, 7.272, 7.676]],
    "谢贝蕾妲小姐伤害": ["生命值", [8.288, 8.9096, 9.5312, 10.36, 10.9816, 11.6032, 12.432, 13.2608, 14.0896, 14.9184, 15.7472, 16.576, 17.612, 18.648, 19.684]],
    "乌瑟勋爵消耗生命值": ["生命值", [2.4]*15],
    "海薇玛夫人消耗生命值": ["生命值", [1.6]*15],
    "谢贝蕾妲小姐消耗生命值": ["生命值", [3.6]*15],
    "众水的歌者治疗量": ["生命值", [[4.8, 462.2253], [5.16, 508.4543], [5.52, 558.5355], [6.0, 612.4694], [6.36, 670.2556], [6.72, 731.8942], [7.2, 797.3852], [7.68, 866.7286], [8.16, 939.9245], [8.64, 1016.9728], [9.12, 1097.8734], [9.6, 1182.6265], [10.2, 1271.232], [10.8, 1363.69], [11.4, 1460.0002]]],
}

ELEMENTAL_BURST_DATA = {
    "技能伤害": ["生命值", [11.4064, 12.2619, 13.1174, 14.258, 15.1135, 15.969, 17.1096, 18.2502, 19.3909, 20.5315, 21.6722, 22.8128, 24.2386, 25.6644, 27.0902]],
    "气氛值转化提升伤害比例": ["数值", [0.07, 0.09, 0.11, 0.13, 0.15, 0.17, 0.19, 0.21, 0.23, 0.25, 0.27, 0.29, 0.31, 0.33, 0.35]],
    "气氛值转化受治疗加成比例": ["数值", [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.11, 0.12, 0.13, 0.14, 0.15]],
    "气氛值叠层上限": ["数值", [300]*15]
}

# --- 核心机制常量 (Mechanism Parameters) ---
MECHANISM_CONFIG = {
    "ARKHE_SWITCH_FRAME": 34,
    "BURST_FANFARE_WINDOW": (95, 1093),
    "SKILL_FIRST_HEAL_FRAME": 87,
    "SKILL_HEAL_INTERVAL": 124,
    "SKILL_USHER_INTERVAL": 200,
    "SKILL_CHEVALMARIN_INTERVAL": 97,
    "SKILL_CRABALETTA_INTERVAL": 314,
}

# --- 动作时序数据 (Action Timing) ---
ACTION_FRAME_DATA = {
    "NORMAL_1": {"hit_frames": [15], "total_frames": 34, "interrupt_frames": {"normal_attack": 31, "any": 34}},
    "NORMAL_2": {"hit_frames": [12], "total_frames": 28, "interrupt_frames": {"normal_attack": 23, "any": 28}},
    "NORMAL_3": {"hit_frames": [21], "total_frames": 48, "interrupt_frames": {"normal_attack": 36, "any": 48}},
    "NORMAL_4": {"hit_frames": [27], "total_frames": 58, "interrupt_frames": {"normal_attack": 53, "any": 58}},
    "CHARGED": {"hit_frames": [32], "total_frames": 253, "interrupt_frames": {"elemental_skill": 3, "elemental_burst": 3, "dash": 7, "any": 253}},
    "SKILL_OUSIA": {"hit_frames": [18], "total_frames": 54, "interrupt_frames": {"dash": 18, "any": 54}},
    "SKILL_PNEUMA": {"hit_frames": [], "total_frames": 57, "interrupt_frames": {"dash": 16, "any": 57}},
    "ELEMENTAL_BURST": {"hit_frames": [98], "total_frames": 121, "interrupt_frames": {"dash": 115, "any": 121}},
}

# --- 攻击数据 (Attack Data) ---
ATTACK_DATA = {
    "普通攻击1": {
        "attack_tag": "普通攻击1",
        "element_u": 1.0,
        "is_ranged": False,
        "icd_tag": "Default",
        "icd_group": "NormalAttack",
        "shape": "长方体", "width": 1.5, "height": 1.5, "length": 2.8,
        "offset": (0.0, 0.7, -0.1), "strike_type": "突刺"
    },
    "普通攻击2": {
        "attack_tag": "普通攻击2",
        "element_u": 1.0,
        "is_ranged": False,
        "icd_tag": "Default",
        "icd_group": "NormalAttack",
        "shape": "圆柱", "radius": 1.7, "height": 1.5,
        "offset": (0.0, -0.1, 0.1), "strike_type": "切割"
    },
    "普通攻击3": {
        "attack_tag": "普通攻击3",
        "element_u": 1.0,
        "is_ranged": False,
        "icd_tag": "Default",
        "icd_group": "NormalAttack",
        "shape": "圆柱", "radius": 1.9, "height": 1.5,
        "offset": (0.0, -0.1, 0.5), "strike_type": "切割"
    },
    "普通攻击4": {
        "attack_tag": "普通攻击4",
        "element_u": 1.0,
        "is_ranged": False,
        "icd_tag": "Default",
        "icd_group": "NormalAttack",
        "shape": "长方体", "width": 5.0, "height": 2.5, "length": 6.0,
        "offset": (0.0, 1.2, -2.5), "strike_type": "切割"
    },
    "重击": {
        "attack_tag": "重击",
        "element_u": 1.0,
        "is_ranged": False,
        "icd_tag": "Default",
        "icd_group": "ChargedAttack",
        "shape": "球", "radius": 2.6,
        "offset": (0.0, 1.0, 0.0), "strike_type": "切割"
    },
    "元素战技": {
        "attack_tag": "元素战技",
        "element_u": 1.0,
        "is_ranged": False,
        "icd_tag": "None",
        "icd_group": "None",
        "shape": "球", "radius": 5.0,
        "strike_type": "默认"
    },
    "乌瑟勋爵伤害": {
        "attack_tag": "乌瑟勋爵伤害",
        "extra_attack_tags": ["元素战技"],
        "element_u": 1.0,
        "is_ranged": True,
        "icd_tag": "FurinaElementalSkill",
        "icd_group": "FurinaSalonShared",
        "shape": "球", "radius": 2.5,
        "strike_type": "默认"
    },
    "海薇玛夫人伤害": {
        "attack_tag": "海薇玛夫人伤害",
        "extra_attack_tags": ["元素战技"],
        "element_u": 1.0,
        "is_ranged": True,
        "icd_tag": "FurinaElementalSkill",
        "icd_group": "FurinaSalonShared",
        "shape": "球", "radius": 0.5,
        "strike_type": "默认"
    },
    "谢贝蕾妲小姐伤害": {
        "attack_tag": "谢贝蕾妲小姐伤害",
        "extra_attack_tags": ["元素战技"],
        "element_u": 1.0,
        "is_ranged": True,
        "icd_tag": "None",
        "icd_group": "None",
        "shape": "球", "radius": 3.5,
        "strike_type": "默认"
    },
    "元素爆发": {
        "attack_tag": "元素爆发",
        "element_u": 1.0,
        "is_ranged": False,
        "icd_tag": "None",
        "icd_group": "None",
        "shape": "球", "radius": 5.0,
        "strike_type": "默认"
    }
}

# --- 6命增强补丁 ---
C6_PHYSICS_PATCH = {
    "普通攻击1": {"length": 3.0},
    "普通攻击2": {"radius": 2.3},
    "普通攻击3": {"radius": 2.2, "offset": (0.0, -0.1, 0.8)},
    "普通攻击4": {"width": 6.0, "length": 7.0},
}
