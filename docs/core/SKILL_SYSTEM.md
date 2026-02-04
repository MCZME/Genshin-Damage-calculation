# Core - 技能系统 (Skill System)

技能系统负责定义角色具体的战斗行为逻辑。

## 核心基类 (`SkillBase`)
技能不再负责“计时”，而是负责“逻辑回调”。
- **`to_action_data()`**: 将技能参数导出为 ASM 引擎可识别的帧数据。
- **`on_execute_hit()`**: 当 ASM 运行到命中帧时，由引擎回传信号并触发伤害。

## 数据驱动技能 (`GenericSkill`)
对于逻辑简单的技能，可以直接通过配置文件（Dict）实例化，无需写代码：
```python
config = {
    "hit_frames": [15, 30],
    "multipliers": [[100, 110...], [200, 220...]],
    "element": ("火", 1)
}
skill = GenericSkill("我的技能", config, lv=10)
```

## 动作映射
每个角色实例通过持有 `NormalAttack`、`Skill`、`Burst` 等成员变量来对接 ASM。基类 `Character` 会自动通过反射机制寻找这些成员。
