# Flet 动画系统 (Animations) 开发规范

Flet 提供了强大的隐式动画和显式动画支持。在本项目中，应优先使用隐式动画以保持代码简洁。

## 1. 隐式动画 (Implicit Animations)
通过设置 `animate_*` 属性，当目标值改变时，控件会自动平滑过渡。

### 常用属性
- `animate_opacity`: 对应 `opacity`
- `animate_rotation`: 对应 `rotate`
- `animate_scale`: 对应 `scale`
- `animate_offset`: 对应 `offset` (用于滑动效果)
- `animate_position`: 对应 `left`, `right`, `top`, `bottom`
- `animate` (仅限 Container): 对应 size, bgcolor, border, gradient 等

### 配置方式 (推荐优先级)
1. **推荐**：使用 `ft.Animation(duration, curve)` 进行精细控制。
   ```python
   animate_scale = ft.Animation(600, ft.AnimationCurve.BOUNCE_OUT)
   ```
2. **次选**：使用 `int` (毫秒数)，默认为线性曲线。
3. **禁用**：直接使用 `bool` (默认 1000ms)，除非是极其简单的场景。

## 2. 布局约束
- **`animate_position`**：仅当控件位于 `ft.Stack` 中或 `page.overlay` 列表中时才生效。

## 3. 组件切换 (AnimatedSwitcher)
用于两个组件（新旧内容）之间的平滑过渡。
```python
sw = ft.AnimatedSwitcher(
    content=initial_content,
    transition=ft.AnimatedSwitcherTransition.SCALE,
    duration=500,
    switch_in_curve=ft.AnimationCurve.EASE_OUT,
)
```

## 4. 动画回调 (on_animation_end)
通过 `on_animation_end` 事件可以链式触发多个动画或执行清理工作。
- 事件数据 `e.data` 包含触发动画的属性名称（如 "opacity", "scale"）。

## 5. 最佳实践
- **避免过度动画**：在分析类界面（如 DPS 曲线图）中，游标移动应保持高性能，避免使用过长的 `BOUNCE` 类曲线。
- **性能优化**：对于频繁变动的位置属性，确保使用了正确的节流机制。

---
*来源：Flet 官方文档 - Animations*
