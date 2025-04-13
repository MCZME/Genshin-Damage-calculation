# BaseClass.py 文档

BaseClass.py 定义了原神伤害计算系统中的核心基类和技能类。

## 类层次结构

### 效果基类
- `TalentEffect`: 天赋效果基类
- `ConstellationEffect`: 命座效果基类
- `ElementalEnergy`: 元素能量管理类

### 技能基类
- `SkillBase`: 所有技能的基础抽象类
  - `EnergySkill`: 需要能量的技能
  - `DashSkill`: 冲刺技能
  - `JumpSkill`: 跳跃技能
  - `NormalAttackSkill`: 普通攻击技能
  - `ChargedAttackSkill`: 重击技能
  - `PlungingAttackSkill`: 下落攻击技能

## 类详细说明

### TalentEffect
天赋效果基类

**属性:**
- `name`: 效果名称

**方法:**
- `apply(character)`: 应用效果到角色
- `update(target)`: 更新效果状态

### ConstellationEffect
命座效果基类

**属性:**
- `name`: 效果名称

**方法:**
- `apply(character)`: 应用效果到角色
- `update(target)`: 更新效果状态

### ElementalEnergy
元素能量管理类

**属性:**
- `elemental_energy`: 元素能量类型和最大值元组
- `current_energy`: 当前能量值

**方法:**
- `is_energy_full()`: 检查能量是否已满
- `clear_energy()`: 清空当前能量

### SkillBase (抽象类)
所有技能的基础抽象类

**属性:**
- `name`: 技能名称
- `total_frames`: 总帧数
- `current_frame`: 当前帧
- `cd`: 冷却时间
- `cd_timer`: 冷却计时器
- `lv`: 技能等级
- `element`: 元素类型
- `damageMultipiler`: 伤害倍率
- `interruptible`: 是否可打断
- `caster`: 施法者

**方法:**
- `start(caster)`: 启动技能
- `update(target)`: 更新技能状态
- `on_frame_update(target)` (抽象方法): 每帧更新逻辑
- `on_finish()`: 技能结束处理
- `on_interrupt()`: 技能被打断处理

### EnergySkill
需要能量的技能

继承自`SkillBase`，增加了能量检查逻辑

**方法:**
- `start(caster)`: 检查能量是否足够，足够则启动技能

### DashSkill
冲刺技能

**属性:**
- `v`: 冲刺速度

**方法:**
- `start(caster)`: 发布冲刺开始事件
- `on_frame_update(target)`: 更新角色位置
- `on_finish()`: 发布冲刺结束事件

### JumpSkill
跳跃技能

**属性:**
- `v`: 跳跃速度

**方法:**
- `start(caster)`: 发布跳跃开始事件
- `on_frame_update(target)`: 更新角色高度和位置
- `on_finish()`: 进入下落状态并发布跳跃结束事件

### NormalAttackSkill
普通攻击技能

**属性:**
- `segment_frames`: 各段攻击帧数
- `damageMultipiler`: 各段伤害倍率
- `current_segment`: 当前攻击段数

**方法:**
- `start(caster, n)`: 启动n段普通攻击
- `_on_segment_end(target)`: 处理段攻击结束
- `_apply_segment_effect(target)`: 应用段攻击效果

### ChargedAttackSkill
重击技能

**属性:**
- `hit_frame`: 命中帧

**方法:**
- `_apply_attack(target)`: 应用重击伤害

### PlungingAttackSkill
下落攻击技能

**属性:**
- `height_type`: 高度类型(低空/高空)
- `v`: 下落速度
- `damageMultipiler`: 不同类型下落伤害倍率

**方法:**
- `start(caster, is_high)`: 启动下落攻击
- `_apply_during_damage(target)`: 应用下坠期间伤害
- `_apply_impact_damage(target)`: 应用坠地冲击伤害

## 使用示例

```python
# 创建普通攻击技能
normal_attack = NormalAttackSkill(lv=1)
normal_attack.start(character, n=3)  # 启动3段攻击

# 创建下落攻击技能
plunging_attack = PlungingAttackSkill(lv=1)
plunging_attack.start(character, is_high=True)  # 高空下落攻击
```

## 事件系统

所有技能都通过`EventBus`发布事件，主要事件类型包括:
- 技能开始/结束事件
- 伤害事件
- 攻击段数事件
