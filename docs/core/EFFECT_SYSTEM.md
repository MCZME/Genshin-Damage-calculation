# Core - 效果系统 (Effect System)

效果系统（Buff/Debuff）负责处理所有属性加成、持续伤害和特殊状态。

## 目录结构 (物理隔离)
为了解决文件膨胀问题，效果逻辑已实现完全分离：
- `core/effect/base.py`: 定义基类。
- `core/effect/weapon/`: 武器效果 (一武器一文件)。
- `core/effect/artifact/`: 圣遗物效果 (一套装一文件)。

## 核心基类 (`BaseEffect`)
支持完整的生命周期钩子：
- `on_apply()`: 获得效果瞬间触发。
- `on_tick()`: 每一帧触发（用于感电、燃烧）。
- `on_remove()`: 效果消失瞬间触发（还原属性）。
- `on_stack_added()`: 当效果重复获得时的堆叠处理。

## 通用属性加成 (`StatModifierEffect`)
对于简单的数值加成，不再需要编写 Python 类，直接使用 `StatModifierEffect` 配合属性字典即可：

```python
# 增加 20% 攻击力和 10% 暴击
buff = StatModifierEffect(owner, "我的Buff", {"攻击力%": 20, "暴击率": 10}, duration=600)
buff.apply()
```

## 堆叠规则 (`StackingRule`)
- **`REFRESH`**: 刷新持续时间。
- **`ADD`**: 增加层数。
- **`INDEPENDENT`**: 独立并存。
