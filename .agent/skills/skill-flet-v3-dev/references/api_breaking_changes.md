# Flet 0.80+ 破坏性更新对照表 (V3.0 适配)

> **核心参考源**:
> *   [Flet 官方文档 (docs.flet.dev)](https://docs.flet.dev/)
> *   [Flet GitHub Issue #5238](https://github.com/flet-dev/flet/issues/5238#issue-3018494952)

---

## ⚡ 核心实战总结 (项目避坑指南)

### 1. Tabs 架构重组 (必读)
*   **控制器化**: `ft.Tabs` 现在强制要求 `content` 和 `length` 参数。它不再是一个简单的容器，而是一个控制器。
*   **结构**: 必须使用 `ft.Tabs(length=N, content=ft.Column([ft.TabBar(...), ft.TabBarView([...])]))`。
*   **标签属性**: `ft.Tab` 必须使用 `label` 参数，使用 `text` 会触发 `TypeError`。
*   **事件**: `on_change` 必须绑定在最外层的 `ft.Tabs` 上，`TabBar` 不再持有该事件。

### 2. 常量大写化
*   所有 `ft.alignment.center`、`ft.colors.blue`、`ft.icons.add` 必须改为大写：`ft.Alignment.CENTER`、`ft.Colors.BLUE`、`ft.Icons.ADD`。

### 3. 组件限制
*   `ft.Text` 不再支持 `letter_spacing` 和 `padding`。
*   `ft.Padding` 必须使用命名参数或类构造，如 `ft.Padding(horizontal=10, vertical=5)`。

---

## 📜 原始更新说明 (GitHub 完整记录)

- **Alignment**: 使用 `ft.Alignment.CENTER` (及其他大写常量) 代替 `ft.alignment.center`。
- **scroll_to()**: `key` 重命名为 `scroll_key`；在控件中应使用 `key=ft.ScrollKey(<value>)`。
- **ScrollableControl**: `on_scroll_interval` 重命名为 `scroll_interval`。
- **Animation**: 使用 `ft.Animation` 代替 `ft.animation.Animation`。
- **Tabs**: 使用 `label: Optional[StrOrControl]` 代替 `text` 和 `tab_content`。
- **Pagelet**: `bottom_app_bar` 重命名为 `bottom_appbar`。
- **page.client_storage**: 变更为 `page.shared_preferences`。
- **Dialogs**: 使用 `page.show_dialog(dialog_name)` 开启，`page.close(dialog_name)` 关闭（注：实测也可使用 `page.open()` / `page.close()`）。
- **NavigationDrawer**: 使用 `position` 属性定义，不再通过 `page.drawer` 赋值。
- **All buttons**: 不再持有 `text` 属性，请使用 `content` 替代。
- **NavigationRailDesctination**: `label_content` 变更为 `label`。
- **SafeArea**: 属性名变更为 `avoid_intrusions_left/top/right/bottom`。
- **Badge**: 使用 `label` 代替 `text`。
- **Padding, Margin**: 强制使用命名参数。例如：`ft.Padding(vertical=0, horizontal=10)`。
- **SegmentedButton**: `selected` 类型从 `Set` 变为 `List[str]`。
- **ft.app(target=main)**: 变更为 `ft.run(main)`。
- **FilePicker**: 现在是 Service，需添加至 `page.services`。仅提供异步方法，不再使用 `on_result` 事件。
- **DragTarget**: `on_will_accept` 使用 `e.accept`；`on_leave` 使用 `e.src_id`。
- **Page.on_resized**: 重命名为 `Page.on_resize`。
- **Card**: `color` -> `bgcolor`, `is_semantic_container` -> `semantic_container`。
- **Checkbox**: `is_error` -> `error`。
- **Chip**: `click_elevation` -> `press_elevation`。
- **Markdown**: `img_error_content` -> `image_error_content`。
- **Switch**: `label_style` -> `label_text_style`。
- **Tabs.is_secondary**: -> `Tabs.secondary`。
- **BoxDecoration**: `shadow` -> `shadows`。
- **canvas.Text**: `text` -> `value`。
- **方法命名**: 移除所有方法的 `_async` 后缀。
- **Icon**: `name` -> `icon`。
- **Dropdown**: `on_change` 仅在编辑模式输入时触发；选择项触发 `on_select`。
- **Theme**: 移除 `primary_swatch`, `primary_color`, `shadow_color`, `divider_color` 等，改用 `color_scheme_seed` 或 `ColorScheme` 属性。
