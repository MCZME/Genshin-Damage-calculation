# Flet V3 (0.80+) 核心组件参数详表 (Component Specs)

> 本文档存储经由官方文档 (`docs.flet.dev`) 深度抓取并核实的常用组件详细参数。

---

## 1. Tabs 体系 (Navigation)

### ft.Tabs
*   **必填构造参数**:
    *   `length` (int): Tab 总数。
    *   `content` (Control): 嵌套容器（包含 TabBar 和 TabBarView）。
*   **状态管理**:
    *   `selected_index` (int): 当前选中索引。
    *   `on_change`: 索引改变时的唯一回调。

### ft.TabBar
*   **必填构造参数**:
    *   `tabs` (list[ft.Tab]): 标签单元列表。
*   **交互事件**:
    *   `on_click`: 点击标签事件。
    *   `on_hover`: 鼠标悬停事件。

### ft.Tab
*   **核心属性**:
    *   `label` (str | Control): **唯一合法标签属性**（替代了旧版的 `text`）。
    *   `icon` (ft.Icons): 标签图标。

---

## 2. 布局容器 (Layout)

### ft.Container
*   **装饰属性**:
    *   `bgcolor` (ColorValue): 背景色。
    *   `border` (ft.Border): 边框。
    *   `border_radius` (BorderRadiusValue): 圆角。
    *   `shadow` (BoxShadowValue | list): 投影。
*   **定位属性**:
    *   `padding` (PaddingValue): 内边距。必须使用命名参数 `ft.Padding(horizontal=X, vertical=Y)`。
    *   `alignment` (ft.Alignment): 内容对齐方式。
*   **注意**: **未列出 `margin` 属性**。

---

## 3. 文本展示 (Display)

### ft.Text
*   **支持属性**:
    *   `value` (str): 文本内容。
    *   `size` (int): 字体大小。
    *   `weight` (ft.FontWeight): 字重。
    *   `color` (ColorValue): 字体颜色。
    *   `selectable` (bool): 是否允许用户选择。
*   **已移除属性**: `letter_spacing`, `padding`, `margin`。

---

## 4. 交互手势 (Interaction)

### ft.GestureDetector
*   **DragUpdateEvent (Pan)**:
    *   `delta_x` / `delta_y`: 坐标增量。
    *   `local_delta`: 包含 x, y 的 Offset 对象（推荐）。
*   **缩放支持**: `on_scale_start/update/end`。
