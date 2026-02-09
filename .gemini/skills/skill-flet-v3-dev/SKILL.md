---
name: skill-flet-v3-dev
description: 专门用于 Flet 0.80.x+ (V3.0) 版本的开发、重构与 Bug 修复。当需要处理 Flet UI 逻辑、适配破坏性更新或解决组件挂载问题时激活。
---

# Flet V3 开发指南

本技能旨在强制执行 Flet 0.80+ 版本的最新 API 规范，确保 UI 代码的高性能与稳定性。

## 核心原则 (Modern Flet)

1. **架构先行**: 必须严格遵循 `ft.Tabs` 控制器架构，嵌套使用 `ft.TabBar` 和 `ft.TabBarView`。
2. **文档驱动**: 开发前必须查阅 `references/component_specs.md` 获取组件参数，或通过 `references/verified_api.md` 访问官方文档。
3. **安全更新**: 任何 `.update()` 必须包裹在 `try-except` 中，防止组件未挂载时的 `RuntimeError`。
4. **大写规范**: 常量必须大写（如 `ft.Alignment.CENTER`, `ft.Colors.BLUE`）。

## 参考文档体系

- **[官方文档索引 (verified_api.md)](references/verified_api.md)**: 包含官方文档全量分类链接，用于搜索不确定的组件路径。
- **[核心组件详表 (component_specs.md)](references/component_specs.md)**: 存储经抓取核实的常用组件（Tabs, Container, Text, GestureDetector）参数详情。
- **[API 破坏性更新对照](references/api_breaking_changes.md)**: 记录从 0.28.x 到 0.80.x 的历史变更。
- **[V3.0 组件开发范式](references/best_practices.md)**: 推荐的 UI 类继承与数据填充结构。

## 常用适配速查

| 需求 | 正确做法 |
| :--- | :--- |
| **Tab 标签** | 必须使用 `label="名称"`，严禁使用 `text`。 |
| **Tabs 切换** | `on_change` 事件必须绑定在 `ft.Tabs` 顶层。 |
| **文本边距** | `ft.Container(content=ft.Text(...), padding=10)` |
| **手势坐标** | `dx = getattr(e, 'delta_x', getattr(e, 'dx', 0))` |
