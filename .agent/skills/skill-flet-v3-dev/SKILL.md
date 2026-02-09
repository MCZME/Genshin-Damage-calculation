---
name: skill-flet-v3-dev
description: 专门用于 Flet 0.80.x+ (V3.0) 版本的开发、重构与 Bug 修复。当需要处理 Flet UI 逻辑、适配破坏性更新或解决组件挂载问题时激活。
---

# Flet V3 开发指南

本技能旨在强制执行 Flet 0.80+ 版本的最新 API 规范，确保 UI 代码的高性能与稳定性。

## 核心原则 (Modern Flet)

1. **构造函数解耦**: 严禁在大型组件（如 `ft.Tabs`, `ft.Column`）的构造函数中传入大量嵌套的 `controls` 或 `tabs`。推荐先实例化，再使用 `append()`。
2. **大写规范**: 所有的 `ft.icons`、`ft.colors` 必须使用 PascalCase (如 `ft.Icons.ADD`, `ft.Colors.BLUE`)。
3. **安全更新**: 任何在异步或初始化期间调用的 `.update()` 必须包裹在 `try-except` 中，以防止组件未挂载时的 `RuntimeError`。
4. **属性适配**: 牢记 `ft.Text` 不支持 `padding` 和 `letter_spacing`。

## 常见适配指南

| 旧版属性/方法 | 新版推荐方案 |
| :--- | :--- |
| `ft.Tabs(tabs=[...])` | `t = ft.Tabs(); t.tabs.append(...)` |
| `ft.Tab(label="...")` | `ft.Tab(text="...")` (注：部分次版本号有波动，优先通过实例化后赋值测试) |
| `ft.Text(padding=X)` | `ft.Container(content=ft.Text(...), padding=X) ` |
| `ft.app(target=main)` | `ft.run(main)` |
| `e.delta_x` | `getattr(e, 'delta_x', getattr(e, 'dx', 0))` |

## 参考文档



- **[Flet 官方文档 (docs.flet.dev)](https://docs.flet.dev/)**: 基于代码库生成的最新 MkDocs 文档（V3.0 权威来源）。

- **[API 破坏性更新对照](references/api_breaking_changes.md)**: 详细的字段级变更。

- **[V3.0 组件范式](references/best_practices.md)**: 推荐的 UI 类结构。