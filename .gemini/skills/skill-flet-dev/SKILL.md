---
name: skill-flet-dev
description: 专门用于 Flet 0.80.x+ 版本的开发、重构与 Bug 修复。当需要处理 Flet UI 逻辑、适配破坏性更新或解决组件挂载问题时激活。
---

# Flet 开发指南 (Genshin Damage calculation)

本技能旨在强制执行 Flet 0.81.0+ 版本的最新 API 规范与声明式编程范式，确保 UI 代码的高性能、无障碍与可维护性。

## 核心原则 (Modern Flet Standards)

1. **范式迁移 (Declarative First)**: 优先采用声明式编程。使用 `@ft.observable` 定义数据模型，使用 `@ft.component` 封装组件，利用 `ft.use_state` 管理局部状态。严禁在业务逻辑中滥用命令式的 `.visible = True` 和 `page.update()`。
2. **性能优化 (Efficiency)**: 处理海量列表（超过 100 条）时，**必须**使用 `ft.ListView` 或 `ft.GridView` 并配合 `item_extent` 或分批更新 (`Batch Updates`)。任何高频更新（如游标移动）必须实现节流机制。
3. **无障碍设计 (Accessibility)**: 强制要求图标按钮提供 `tooltip`，表单控件提供 `label`。关键数值展示应使用 `semantics_label` 进行语义补充。
4. **组件解耦 (Custom Controls)**: 复杂 UI 逻辑必须封装为自定义控件 (`@ft.control`)。在内部调用 `self.update()` 的控件应设置 `is_isolated=True` 以优化渲染性能。
5. **异步原生 (Async Native)**: 耗时操作（I/O, 仿真计算）必须异步化。严禁使用 `time.sleep()`，必须使用 `await asyncio.sleep()`。利用 `did_mount` 和 `will_unmount` 管理后台任务。
6. **安全更新**: 任何 `.update()` 必须包裹在 `try-except` 中，防止组件未挂载时的 `RuntimeError`。
7. **规范命名**: 常量必须使用枚举（如 `ft.Alignment.CENTER`, `ft.Colors.BLUE`）。控件引用优先使用 `ft.Ref[T]()`。
8. **文档先行**: 进行开发前需要查看Reference下的对应文档，不能直接开始。

## 常用适配速查

| 需求 | 正确做法 |
| :--- | :--- |
| **数据响应** | 使用 `@ft.observable` 装饰模型类。 |
| **局部重绘** | 使用 `ft.use_state` 钩子。 |
| **动画效果** | 优先使用 `animate_*` 隐式动画配合 `ft.AnimationCurve`。 |
| **拖放交互** | 必须提供 `content_when_dragging` 和 `on_will_accept` 视觉反馈。 |
| **布局填充** | 合理使用 `expand` (比例) 与 `expand_loose` (自适应)。 |
| **开启对话框** | 使用 `page.show_dialog(control)`。 |
| **手势坐标** | `dx = getattr(e, 'delta_x', getattr(e, 'dx', 0))` |

## 参考文档体系 (References)

- **[声明式范式 (declarative_programming.md)](references/declarative_programming.md)**: UI = f(state) 核心准则。
- **[异步应用规范 (async_apps.md)](references/async_apps.md)**: 协程与非阻塞任务管理。
- **[动画系统规范 (animations.md)](references/animations.md)**: 隐式动画与曲线应用。
- **[辅助功能规范 (accessibility.md)](references/accessibility.md)**: 语义化与屏幕阅读器适配。
- **[海量列表优化 (large_lists.md)](references/large_lists.md)**: 虚拟化容器与分批更新。
- **[自定义组件 (custom_controls.md)](references/custom_controls.md)**: 生命周期与渲染隔离。
- **[布局扩展规范 (expanding_controls.md)](references/expanding_controls.md)**: 弹性布局策略。
- **[控件引用标准 (control_refs.md)](references/control_refs.md)**: 类型安全的对象访问。
- **[拖放交互规范 (drag_and_drop.md)](references/drag_and_drop.md)**: 交互反馈与数据交换。