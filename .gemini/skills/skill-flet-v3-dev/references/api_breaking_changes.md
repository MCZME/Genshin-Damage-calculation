# Flet 0.80+ 破坏性更新对照表 (V3.0 适配)

> **核心参考源**:
> *   [Flet 官方文档 (docs.flet.dev)](https://docs.flet.dev/)
> *   [Flet GitHub Issue #5238](https://github.com/flet-dev/flet/issues/5238#issue-3018494952)

## 1. 全局配置与入口
*   **入口函数**: `ft.app(target=main)` -> **推荐**: `ft.run(main)` 或 `ft.run(main=main)`。
*   **客户端存储**: `page.client_storage` 变更为 `page.shared_preferences`。
*   **窗口调整**: `page.on_resized` 变更为 `page.on_resize`。

## 2. 文本与样式 (Text & Style)
*   **字间距**: `ft.Text` 不再直接支持 `letter_spacing` 属性。
*   **内边距**: `ft.Text` 不支持 `padding`。必须包裹在 `ft.Container` 中。
*   **对齐方式**: 强制使用大写常量，如 `ft.Alignment.CENTER` 代替小写的 `ft.alignment.center`。
*   **动画**: 使用 `ft.Animation` 代替小写的 `ft.animation.Animation`。
*   **影子**: `BoxDecoration.shadow` 变更为 `BoxDecoration.shadows`。

## 3. 核心布局组件 (Layouts)
*   **Tabs**: 
    *   构造函数可能不支持 `tabs` 列表，推荐实例化后 `append`。
    *   `Tab` 属性: `text` (String) 和 `tab_content` (Control) 统一由 `label` (StrOrControl) 替代。
    *   `is_secondary` 变更为 `secondary`。
*   **Card**: `color` 变更为 `bgcolor`；`is_semantic_container` 变更为 `semantic_container`。
*   **Badge**: 使用 `label` 代替 `text`。
*   **SafeArea**: 属性名变更为 `avoid_intrusions_left/top/right/bottom`。

## 4. 按钮与交互 (Buttons & Interaction)
*   **通用属性**: 多数按钮不再支持 `text` 属性，请使用 `content` 替代。
*   **对话框**: 使用 `page.show_dialog(dialog_name)` 开启，`page.pop_dialog()` 关闭。不再使用 `page.open(dialog_name)`。
*   **导航栏**: `NavigationDrawer` 使用 `position` 属性定义，不再直接通过 `page.drawer` 赋值。
*   **文件选择**: `FilePicker` 变为 Service，需添加至 `page.services`。提供异步方法，不再使用 `on_result` 事件。

## 5. 间距定义 (Padding & Margin)
*   **命名参数强制化**: 必须使用命名参数。
    *   **错误**: `ft.Padding.symmetric(0, 10)`
    *   **正确**: `ft.Padding(vertical=0, horizontal=10)` 或 `ft.Padding(0, 10, 0, 10)`。

## 6. 其他常用属性变更
*   **Icon**: `name` 变更为 `icon`。
*   **Checkbox**: `is_error` 变更为 `error`。
*   **Chip**: `click_elevation` 变更为 `press_elevation`。
*   **Canvas Text**: `text` 变更为 `value`。
*   **方法重命名**: 移除所有方法的 `_async` 后缀。

## 7. 拖拽逻辑 (Drag & Drop)
*   **DragTarget**: `on_will_accept` 使用 `e.accept` 代替 `e.data`；`on_leave` 使用 `e.src_id` 代替 `e.data`。
