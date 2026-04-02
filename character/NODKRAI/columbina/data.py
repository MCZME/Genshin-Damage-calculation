"""哥伦比娅 的自动化提取数据 (V2.3.1)。"""

from typing import TypedDict


class FrameDataDict(TypedDict):
    """动作帧数据结构。"""
    hit_frames: list[int]
    total_frames: int
    interrupt_frames: dict[str, int]


class AttackDataDict(TypedDict, total=False):
    """攻击数据结构。所有字段都是可选的。"""
    attack_tag: str
    extra_attack_tags: list[str]
    element_u: float
    is_ranged: bool
    icd_tag: str
    icd_group: str
    shape: str
    radius: float
    height: float
    width: float
    length: float
    offset: tuple[float, float, float]
    strike_type: str


class SkillDataDict(TypedDict):
    """技能数据结构。"""
    name: str
    values: list[float]


class MultiplierDataDict(TypedDict):
    """倍率数据结构。"""
    stat: str
    values: list[float] | list[list[float]]


# --- 角色基础信息 ---
NAME: str = "哥伦比娅"
ID: int = 103
RARITY: int = 5
ELEMENT: str = "水"
WEAPON_TYPE: str = "法器"
BREAKTHROUGH_PROP: str = "暴击率"

# --- 属性成长表 (1-100级) ---
BASE_STATS = {
    1: {'生命值': 1143.98, '攻击力': 7.45, '防御力': 40.09, '暴击率': 0.0},
    20: {'生命值': 3948.36, '攻击力': 25.71, '防御力': 138.35, '暴击率': 0.0},
    40: {'生命值': 6604.93, '攻击力': 43.0, '防御力': 231.44, '暴击率': 4.8},
    50: {'生命值': 8528.29, '攻击力': 55.52, '防御力': 298.84, '暴击率': 9.6},
    60: {'生命值': 10229.64, '攻击力': 66.6, '防御力': 358.46, '暴击率': 9.6},
    70: {'生命值': 11940.14, '攻击力': 77.74, '防御力': 418.4, '暴击率': 14.4},
    80: {'生命值': 13662.08, '攻击力': 88.95, '防御力': 478.73, '暴击率': 19.2},
    90: {'生命值': 14695.09, '攻击力': 95.67, '防御力': 514.93, '暴击率': 19.2},
    95: {'生命值': 15216.75, '攻击力': 106.43, '防御力': 533.21, '暴击率': 19.2},
    100: {'生命值': 15739.55, '攻击力': 117.2, '防御力': 551.53, '暴击率': 19.2},
}

# --- 月露泼降 (normal) ---
NORMAL_ATTACK_DATA: dict[str, tuple[str, list[float] | list[int] | list[list[float]]]] = {
    "一段伤害": ("攻击力", [46.792, 50.3014, 53.8108, 58.49, 61.9994, 65.5088, 70.188, 74.8672, 79.5464, 84.2256, 88.9048, 93.584, 99.433, 105.282, 111.131]),
    "二段伤害": ("攻击力", [36.6256, 39.3725, 42.1194, 45.782, 48.5289, 51.2758, 54.9384, 58.601, 62.2635, 65.9261, 69.5886, 73.2512, 77.8294, 82.4076, 86.9858]),
    "三段伤害": ("攻击力", [58.484, 62.8703, 67.2566, 73.105, 77.4913, 81.8776, 87.726, 93.5744, 99.4228, 105.2712, 111.1196, 116.968, 124.2785, 131.589, 138.8995]),
    "重击伤害": ("攻击力", [116.08, 124.786, 133.492, 145.1, 153.806, 162.512, 174.12, 185.728, 197.336, 208.944, 220.552, 232.16, 246.67, 261.18, 275.69]),
    "重击体力消耗": ("攻击力", [50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50]),
    "月露涤荡伤害": ("生命值", [1.5112, 1.6245, 1.7379, 1.889, 2.0023, 2.1157, 2.2668, 2.4179, 2.569, 2.7202, 2.8713, 3.0224, 3.2113, 3.4002, 3.5891]),
    "下坠期间伤害": ("攻击力", [56.8288, 61.4544, 66.08, 72.688, 77.3136, 82.6, 89.8688, 97.1376, 104.4064, 112.336, 120.2656, 128.1952, 136.1248, 144.0544, 151.984]),
    "低空/高空坠地冲击伤害": ("攻击力", [[113.6335, 141.9344], [122.8828, 153.4872], [132.132, 165.04], [145.3452, 181.544], [154.5944, 193.0968], [165.165, 206.3], [179.6995, 224.4544], [194.234, 242.6088], [208.7686, 260.7632], [224.6244, 280.568], [240.4802, 300.3728], [256.3361, 320.1776], [272.1919, 339.9824], [288.0478, 359.7872], [303.9036, 379.592]]),
}

# --- 万古潮汐 (skill) ---
ELEMENTAL_SKILL_DATA: dict[str, tuple[str, list[float]]] = {
    "技能伤害": ("生命值", [16.72, 17.974, 19.228, 20.9, 22.154, 23.408, 25.08, 26.752, 28.424, 30.096, 31.768, 33.44, 35.53, 37.62, 39.71]),
    "引力涟漪·持续伤害": ("生命值", [9.36, 10.062, 10.764, 11.7, 12.402, 13.104, 14.04, 14.976, 15.912, 16.848, 17.784, 18.72, 19.89, 21.06, 22.23]),
    "引力干涉·月感电伤害": ("生命值", [4.704, 5.0568, 5.4096, 5.88, 6.2328, 6.5856, 7.056, 7.5264, 7.9968, 8.4672, 8.9376, 9.408, 9.996, 10.584, 11.172]),
    "引力干涉·月绽放伤害": ("生命值", [1.408, 1.5136, 1.6192, 1.76, 1.8656, 1.9712, 2.112, 2.2528, 2.3936, 2.5344, 2.6752, 2.816, 2.992, 3.168, 3.344]),
    "引力干涉·月结晶伤害": ("生命值", [8.824, 9.4858, 10.1476, 11.03, 11.6918, 12.3536, 13.236, 14.1184, 15.0008, 15.8832, 16.7656, 17.648, 18.751, 19.854, 20.957]),
    "引力值上限": ("攻击力", [60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60]),
    "引力涟漪持续时间": ("攻击力", [25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25]),
    "冷却时间": ("攻击力", [17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17]),
}

# --- 她的乡愁 (burst) ---
ELEMENTAL_BURST_DATA: dict[str, tuple[str, list[float]]] = {
    "技能伤害": ("生命值", [32.24, 34.658, 37.076, 40.3, 42.718, 45.136, 48.36, 51.584, 54.808, 58.032, 61.256, 64.48, 68.51, 72.54, 76.57]),
    "月曜反应伤害提升": ("攻击力", [13.0, 16.0, 19.0, 22.0, 25.0, 28.0, 31.0, 34.0, 37.0, 40.0, 43.0, 46.0, 49.0, 52.0, 55.0]),
    "月之领域持续时间": ("攻击力", [20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20]),
    "冷却时间": ("攻击力", [15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15]),
    "元素能量": ("攻击力", [60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60]),
}

# --- 动作时序数据 (实测) ---
ACTION_FRAME_DATA: dict[str, FrameDataDict] = {
    "普通攻击1": {
        "hit_frames": [36],
        "total_frames": 61,
        "interrupt_frames": {"normal_attack": 55, "dash": 61, "any": 61},
    },
    "普通攻击2": {
        "hit_frames": [31],
        "total_frames": 68,
        "interrupt_frames": {"normal_attack": 62, "dash": 68, "any": 68},
    },
    "普通攻击3": {
        "hit_frames": [42],
        "total_frames": 119,
        "interrupt_frames": {"normal_attack": 108, "dash": 119, "any": 119},
    },
    "重击": {
        "hit_frames": [53],
        "total_frames": 102,
        "interrupt_frames": {"dash": 102, "any": 102},
    },
    "月露涤荡": {
        # 特殊重击：命中帧为69，9，17，总共151帧
        "hit_frames": [69, 78, 86],
        "total_frames": 151,
        "interrupt_frames": {"dash": 151, "any": 151},
    },
    "元素战技": {
        "hit_frames": [55],
        "total_frames": 63,
        "interrupt_frames": {"dash": 63, "any": 63},
    },
    "引力干涉·月感电": {
        # 单次雷元素范围伤害
        "hit_frames": [41],
        "total_frames": 74,
        "interrupt_frames": {"any": 74},
    },
    "引力干涉·月绽放": {
        # 发射5枚月露之印
        "hit_frames": [40, 45, 50, 55, 60],
        "total_frames": 74,
        "interrupt_frames": {"any": 74},
    },
    "引力干涉·月结晶": {
        # 单次岩元素范围伤害
        "hit_frames": [41],
        "total_frames": 74,
        "interrupt_frames": {"any": 74},
    },
    "元素爆发": {
        "hit_frames": [147],
        "total_frames": 238,
        "interrupt_frames": {"dash": 238, "any": 238},
    },
}

# --- 攻击数据 (实测) ---
ATTACK_DATA: dict[str, AttackDataDict] = {
    "普通攻击1": {
        "attack_tag": "普通攻击1",
        "element_u": 1.0,
        "is_ranged": False,
        "icd_tag": "Default",
        "icd_group": "NormalAttack",
        "shape": "圆柱",
        "radius": 1.0,
        "height": 3.0,
        "offset": (0.0, -1.0, 0.0),
        "strike_type": "默认",
    },
    "普通攻击2": {
        "attack_tag": "普通攻击2",
        "element_u": 1.0,
        "is_ranged": False,
        "icd_tag": "Default",
        "icd_group": "NormalAttack",
        "shape": "圆柱",
        "radius": 1.0,
        "height": 3.0,
        "offset": (0.0, -1.0, 0.0),
        "strike_type": "默认",
    },
    "普通攻击3": {
        "attack_tag": "普通攻击3",
        "element_u": 1.0,
        "is_ranged": False,
        "icd_tag": "Default",
        "icd_group": "NormalAttack",
        "shape": "球",
        "radius": 2.5,
        "offset": (0.0, 0.0, 0.0),
        "strike_type": "默认",
    },
    "重击": {
        "attack_tag": "重击",
        "element_u": 1.0,
        "is_ranged": True,
        "icd_tag": "Default",
        "icd_group": "ChargedAttack",
        "shape": "圆柱",
        "radius": 3.5,
        "height": 2.5,
        "offset": (0.0, -0.7, 0.0),
        "strike_type": "默认",
    },
    "月露涤荡A": {
        "attack_tag": "月绽放",
        "element_u": 0,  # 月曜伤害无附着
        "is_ranged": True,
        "icd_tag": "None",
        "icd_group": "None",
        "shape": "圆柱",
        "radius": 3.3,
        "height": 2.5,
        "offset": (0.0, -0.7, 0.0),
        "strike_type": "默认",
    },
    "月露涤荡B": {
        "attack_tag": "月绽放",
        "element_u": 0,
        "is_ranged": True,
        "icd_tag": "None",
        "icd_group": "None",
        "shape": "圆柱",
        "radius": 3.3,
        "height": 2.5,
        "offset": (0.0, -0.7, 0.0),
        "strike_type": "默认",
    },
    "月露涤荡C": {
        "attack_tag": "月绽放",
        "element_u": 0,
        "is_ranged": True,
        "icd_tag": "None",
        "icd_group": "None",
        "shape": "圆柱",
        "radius": 3.3,
        "height": 3.0,
        "offset": (0.0, -0.7, 0.0),
        "strike_type": "默认",
    },
    "元素战技": {
        "attack_tag": "元素战技",
        "element_u": 1.0,
        "is_ranged": False,
        "icd_tag": "None",
        "icd_group": "None",
        "shape": "圆柱",
        "radius": 6.0,
        "height": 3.5,
        "offset": (0.0, -1.0, 0.0),
        "strike_type": "默认",
    },
    "引力涟漪·持续伤害": {
        "attack_tag": "元素战技",
        "element_u": 1.0,
        "is_ranged": True,
        "icd_tag": "ColumbinaRipple",
        "icd_group": "ColumbinaSkill",
        "shape": "圆柱",
        "radius": 4.0,
        "height": 3.0,
        "offset": (0.0, -1.0, 0.0),
        "strike_type": "默认",
    },
    "引力涟漪·满辉": {
        "attack_tag": "元素战技",
        "element_u": 1.0,
        "is_ranged": True,
        "icd_tag": "ColumbinaRipple",
        "icd_group": "ColumbinaSkill",
        "shape": "圆柱",
        "radius": 6.0,
        "height": 3.5,
        "offset": (0.0, -1.0, 0.0),
        "strike_type": "默认",
    },
    "引力干涉·月感电": {
        "attack_tag": "月感电",
        "element_u": 0,  # 月曜伤害无附着
        "is_ranged": True,
        "icd_tag": "None",
        "icd_group": "None",
        "shape": "圆柱",
        "radius": 6.0,
        "height": 3.5,
        "offset": (0.0, -1.0, 0.0),
        "strike_type": "默认",
    },
    "引力干涉·月绽放": {
        "attack_tag": "月绽放",
        "element_u": 0,
        "is_ranged": True,
        "icd_tag": "None",
        "icd_group": "None",
        "shape": "球",
        "radius": 0.5,
        "offset": (0.0, 0.0, 0.0),
        "strike_type": "默认",
    },
    "引力干涉·月结晶": {
        "attack_tag": "月结晶",
        "element_u": 0,
        "is_ranged": True,
        "icd_tag": "None",
        "icd_group": "None",
        "shape": "圆柱",
        "radius": 6.0,
        "height": 3.5,
        "offset": (0.0, -1.0, 0.0),
        "strike_type": "默认",
    },
    "元素爆发": {
        "attack_tag": "元素爆发",
        "element_u": 2.0,  # 大招2U
        "is_ranged": True,
        "icd_tag": "None",
        "icd_group": "None",
        "shape": "圆柱",
        "radius": 6.5,
        "height": 4.0,
        "offset": (0.0, -1.0, 0.5),
        "strike_type": "默认",
    },
}

# --- 核心机制常量 ---
MECHANISM_CONFIG = {
    # 引力值系统
    "GRAVITY_MAX": 60,  # 引力值上限
    "GRAVITY_RIPPLE_DURATION": 1500,  # 引力涟漪持续帧数 (25秒 * 60)
    # 月之领域
    "LUNAR_DOMAIN_DURATION": 1200,  # 月之领域持续帧数 (20秒 * 60)
    # 草露机制
    "GRASS_DEW_MAX": 3,  # 草露上限
    "GRASS_DEW_CONSUME": 1,  # 月露涤荡消耗草露数量
    # 能量微粒产球
    "ENERGY_PARTICLE_CD": 210,  # 产球冷却帧数 (3.5秒 * 60)
    "ENERGY_PARTICLE_RATES": (0.6666667, 0.3333333),  # 1微粒:2微粒 的概率
}