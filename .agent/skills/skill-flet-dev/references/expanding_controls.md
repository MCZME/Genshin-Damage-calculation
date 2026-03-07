# Flet 控件布局扩展 (Expanding Controls) 开发规范

在 Flet 布局中，通过 `expand` 和 `expand_loose` 属性，可以灵活地控制子控件如何填充父容器（Row, Column, View, Page）的可用空间。

## 1. `expand` 属性
`expand` 用于强制控件填充父容器沿主轴方向的剩余空间。

### 赋值规范
- **布尔值 (`bool`)**：`True` 表示该控件应占据所有可用空间。
- **整数 (`int`)**：用于在多个设置了 `expand` 的控件之间按比例分配空间。
    - 例如：在一个 `Row` 中，`expand=1` 和 `expand=3` 的两个控件将分别占据 25% 和 75% 的剩余空间。

### 常用场景
- **自适应输入框**：在 `Row` 中放置一个按钮和一个 `TextField`，给 `TextField` 设置 `expand=True`。
- **等分卡片**：在 `Row` 中给所有卡片设置相同的 `expand` 值。

## 2. `expand_loose` 属性 (Flet V3.0+ 新特性)
`expand_loose` 提供了更具弹性的扩展方案。

### 核心特性
- **非强制性**：与 `expand` 不同，`expand_loose=True` 允许控件在需要时增长，但**不强制**其填满所有剩余空间。它会根据内容大小自动收缩，但上限受 `expand` 比例限制。
- **必要条件**：
    1. 必须位于 `Row`, `Column`, `View` 或 `Page` 中。
    2. 控件本身必须已经设置了非空的 `expand` 值。

### 典型应用：气泡对话框
在聊天界面中，消息气泡根据文字长度自适应宽度，但最长不能超过屏幕的一定比例：
```python
class MessageBubble(ft.Container):
    def __init__(self, text):
        super().__init__(
            content=ft.Text(text),
            expand=True,        # 允许扩展
            expand_loose=True,  # 但允许根据内容收缩 (不强制拉满)
            bgcolor=ft.Colors.GREEN_200,
            padding=10,
            border_radius=10
        )
```

## 3. 布局准则
- **嵌套布局对齐**：当使用 `ft.Stack` 或全屏视图时，通常需要将最外层的 `Column` 或 `Row` 设置为 `expand=True`，以确保内容填充整个视口。
- **避免过度扩展**：在复杂的 Dashboard 界面中，优先使用 `int` 比例而非简单的 `True`，以获得更精确的栅格化布局控制。
- **配合对齐方式**：在使用 `expand_loose` 时，父容器的 `alignment`（如 `MainAxisAlignment.START` 或 `END`）决定了收缩后控件的位置。

---
*来源：Flet 官方文档 - Expanding Controls*
