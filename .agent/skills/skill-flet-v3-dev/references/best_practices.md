# V3.0 组件开发最佳实践

## 1. 组件结构标准 (Boilerplate)

所有 UI 组件应采用类继承模式，并将 UI 构建逻辑与业务逻辑分离。

```python
import flet as ft

class MyComponent(ft.Container):
    def __init__(self, state):
        super().__init__(expand=True)
        self.state = state
        self._build_ui()
        self._render_data() # 初始填充数据

    def _build_ui(self):
        """仅定义静态结构"""
        self.list_view = ft.ListView(expand=True)
        self.content = ft.Column([
            ft.Text("Title", size=20, weight="bold"),
            self.list_view
        ])

    def _render_data(self):
        """填充/刷新数据逻辑"""
        self.list_view.controls.clear()
        # ... 数据填充逻辑 ...
        
        # 安全更新
        try:
            self.update()
        except Exception:
            pass # 挂载前调用 update 是允许失败的
```

## 2. 状态通信模式

*   **向下同步**: 父组件修改 `state` -> 调用子组件的 `_render_data()`。
*   **向上反馈**: 子组件事件触发 -> 调用 `state.some_action()` -> 调用 `state.refresh()` (即 `page.update()`)。

## 3. 布局避坑

*   **三栏布局**: 始终使用 `ft.Row(expand=True)` 作为顶层，并为中间栏设置 `expand=True`，侧边栏设置固定 `width`。
*   **层级显示**: 复杂的弹出层优先使用 `page.overlay.append()`。
*   **滚动控制**: 对于可能溢出的内容，务必在外层 Container 设置 `scroll=ft.ScrollMode.AUTO` 或使用 `ft.ListView`。
