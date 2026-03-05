# Flet 0.80+ 破坏性更新对照表 (V3.0 适配)

> **核心参考源**:
> *   [Flet 官方文档 (docs.flet.dev)](https://docs.flet.dev/)
> *   [Flet GitHub Issue #5238](https://github.com/flet-dev/flet/issues/5238)

---

## ⚡ 核心实战总结 (项目避坑指南)

### 1. 对话框交互 (Dialogs) - **重大修正**
*   **开启**: `page.show_dialog(dialog_object)`。
*   **关闭**: `page.pop_dialog()`。
*   **注意**: `page` 没有 `open` 或 `close` 方法。

### 2. 下拉菜单 (Dropdown)
*   **事件**: `on_change` 已被**移除**。
    *   `on_select`: 当用户选择某个选项时触发。

### 3. 颜色方案 (ColorScheme) - **新发现**
*   **移除**: `background` 和 `surface_variant` 属性已从 `ft.ColorScheme` 中移除。
*   **替代**: 请使用 `surface` 或其变体（如 `surface_container`）来定义底色。

### 4. 交互事件 (Events) - **新发现**
*   **DragUpdateEvent**: 移除了 `delta_x` 和 `delta_y`
*   **替代**: 请使用 **`e.local_delta.x`** 和 **`e.local_delta.y`**。

### 5. 常量规范 (Top Priority)
所有常量访问必须大写。
*   **Icons**: `ft.Icons.NAME` (大写 I)。
*   **Colors**: `ft.Colors.NAME` (大写 C)。带有数字后缀需加下划线，如 `ft.Colors.WHITE_54`。
*   **Alignment**: `ft.Alignment.NAME` (大写 A)。

### 6. 组件属性变更 (Critical)
*   **Text**: 移除了 `letter_spacing`、`padding`、`margin`。使用 **`rotate`** 进行旋转。
*   **TextField**: `placeholder` 已重命名为 **`hint_text`**。
*   **Tab**: 必须使用 `label` 属性。
*   **Chip**: 不支持 `border_color`，必须使用 **`border_side=ft.BorderSide(1, color)`**。
*   **Container**: 强制使用 `ft.padding.all()` 或 `ft.Padding()` 命名对象。**不支持 `on_resize`**。
*   **FloatingActionButton**: 不持 `color` 属性，必须使用 **`foreground_color`**。
*   **Global**: 几乎所有组件的 `id` 属性都已变更为 **`key`**。

---

## 📜 原始更新说明 (GitHub 完整记录)
- **Alignment**: 使用 `ft.Alignment.CENTER` 代替 `ft.alignment.center`。
- **scroll_to()**: `key` 重命名为 `scroll_key`；在控件中应使用 `key=ft.ScrollKey(<value>)`。
- **ScrollableControl**: `on_scroll_interval` 重命名为 `scroll_interval`。
- **Animation**: 使用 `ft.Animation` 代替 `ft.animation.Animation`。
- **Tabs**: 使用 `label: Optional[StrOrControl]` 代替 `text` 和 `tab_content`。
- **Pagelet**: `bottom_app_bar` 重命名为 `bottom_appbar`。
- **page.client_storage**: 变更为 `page.shared_preferences`。
- **NavigationDrawer**: 使用 `position` 属性定义，不再通过 `page.drawer` 赋值。
- **All buttons**: 不再持有 `text` 属性，请使用 `content` 替代（如 `FloatingActionButton`）。
- **NavigationRailDesctination**: `label_content` 变更为 `label`。
- **SafeArea**: 属性名变更为 `avoid_intrusions_left/top/right/bottom`。
- **Badge**: 使用 `label` 代替 `text`。
- **Padding, Margin**: 强制使用命名参数。`。
- **SegmentedButton**: `selected` 类型从 `Set` 变为 `List[str]`。
- **ft.run(target=main)**: Flet 0.80.x 推荐使用 **`ft.run`** 替代 `ft.app`。
- **page.push_route()**: 推荐替代 `page.go()`。
- **FilePicker**: 现在是 Service，需通过 `page.open(file_picker)` 开启。
- **DragTarget**: `on_will_accept` 使用 `e.accept`；`on_leave` 使用 `e.src_id`。
- **Page.on_resized**: 重命名为 `Page.on_resize`。
- **Card**: `color` -> `bgcolor`, `is_semantic_container` -> `semantic_container`。
- **CardVariant**: 仅支持 `ELEVATED`, `FILLED`, `OUTLINED`。不支持 `SURFACE`。
- **Checkbox**: `is_error` -> `error`。
- **Chip**: `click_elevation` -> `press_elevation`。
- **Markdown**: `img_error_content` -> `image_error_content`。
- **Switch**: `label_style` -> `label_text_style`。
- **Tabs.is_secondary**: -> `Tabs.secondary`。
- **BoxDecoration**: `shadow` -> `shadows` (复数)。
- **canvas.Text**: `text` -> `value`。
- **方法命名**: 移除所有方法的 `_async` 后缀。
*   **Icon**: `name` -> `icon`。
*   **Dropdown**: 使用 `on_select` 代替 `on_change`。
*   **Theme**: 移除 `primary_swatch`, `primary_color` 等，改用 `color_scheme_seed` 或 `ColorScheme` 属性。

---

## 🛑 渲染稳定性 (防止“一片灰”崩溃)
基于实战测试，以下配置必须严格遵守以确保 Flutter 渲染引擎不挂起：

1. **BoxShadow (阴影)**
   - `Container.shadow` 属性**必须接收一个列表**。
   - ✅ 正确：`shadow=[ft.BoxShadow(...)]`
   - ❌ 错误：`shadow=ft.BoxShadow(...)` (可能导致静默挂起)。

2. **Gradient (渐变)**
   - `colors` 列表必须包含**至少两种**颜色。
   - 推荐优先使用 **Hex 十六进制代码** (如 `#1A1A1A`)，避免在某些环境下 `rgba()` 解析失败。

3. **ft.Text 样式裁剪**
   - **已移除**: `letter_spacing`, `shadow`, `padding`, `margin`。
   - **替代方案**: 使用 `style=ft.TextStyle(letter_spacing=2, shadows=[...])`。

4. **初始化**
   - **推荐**: 使用 `ft.run(main)` 替代 `ft.app(target=main)`。
   - **Renderer 报错**: 若遇到 `No current renderer is set`，确保所有组件在 `Renderer.render`的执行流内部实例化。