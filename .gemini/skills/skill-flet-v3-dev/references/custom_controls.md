# Flet 自定义控件 (Custom Controls) 开发规范

Flet 允许通过 Python 的面向对象编程特性创建可重用的 UI 组件。自定义控件分为“样式化控件”和“复合控件”。

## 1. 定义方式：`@ft.control` 装饰器
**必须**使用 `@ft.control` 装饰器来定义自定义控件。这使得类可以像普通 Flet 控件一样通过属性定义和构造。

### 样式化控件 (Styled Controls)
用于创建具有统一风格（颜色、形状、行为）的基类控件。
```python
@ft.control
class MyButton(ft.Button):
    bgcolor: ft.Colors = ft.Colors.ORANGE_300
    color: ft.Colors = ft.Colors.GREEN_800
    # 复杂类型使用 default_factory
    style: ft.ButtonStyle = field(
        default_factory=lambda: ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10)
        )
    )
```

### 复合控件 (Composite Controls)
继承自 `ft.Column`, `ft.Row`, `ft.Stack` 或 `ft.Container`，组合多个基础控件。
- **推荐在 `init()` 中初始化子控件**，而不是 `__init__`。
```python
@ft.control
class TaskItem(ft.Row):
    text: str = ""

    def init(self):
        self.text_view = ft.Text(value=self.text)
        self.controls = [ft.Checkbox(), self.text_view]
```

## 2. 字段定义规则
- **类型注解是必须的**：字段必须有类型注解（如 `expand: int = 1`），否则它不会覆盖继承的属性。
- **默认值**：
    - 简单类型（int, bool, str）：直接使用字面量。
    - 不可变或复杂类型（class, list, dict）：使用 `field(default_factory=lambda: ...)`。

## 3. 生命周期方法 (Life-cycle Hooks)
- `build()`: 在控件被创建并分配 `self.page` 时调用。适合需要根据 `page.platform` 等页面属性进行逻辑判断的场景。
- `did_mount()`: 在控件被添加到页面后调用。适合启动后台任务（如 `page.run_task`）。
- `will_unmount()`: 在控件从页面移除前调用。执行清理工作（如停止计时器）。
- `before_update()`: 每次控件更新前调用。**严禁在此方法内调用 `self.update()`**。

## 4. 隔离方法 (`is_isolated`)
- **原则**：任何在内部类方法中调用 `self.update()` 的自定义控件，其 `is_isolated` 方法**应返回为 `True`**。
- **效果**：隔离控件在父级更新时不会重新渲染其子控件树，只有在其显式调用 `self.update()` 时才会推送更新，从而显著提升大型应用的性能。

## 5. 最佳实践
- **内部逻辑封装**：复杂的交互逻辑（如点击后的 UI 状态切换）应封装在自定义控件的类方法中，并内部调用 `self.update()`。
- **组合优于继承**：尽量通过 `Composite Controls` 组合功能，而不是创建深层的继承树。
- **自包含任务**：利用 `did_mount` 和 `will_unmount` 让控件具备自驱动能力（如实时 DPS 刷新）。

---
*来源：Flet 官方文档 - Custom Controls*
