# Flet 声明式编程 (Declarative Programming) 开发规范

Flet 已全面支持声明式编程范式，其核心理念是 **UI = f(state)**。开发者应从“直接操作控件”转向“管理状态，由框架驱动 UI 更新”。

## 1. 核心理念对比
- **命令式 (Imperative)**：手动设置 `control.visible = True`，然后调用 `page.update()`。代码分散且难以维护。
- **声明式 (Declarative)**：修改状态（State），组件根据当前状态自动返回对应的 UI。无需显式调用 `page.update()`。

## 2. 响应式模型 (@ft.observable)
用于定义应用的“真理之源”（持久化数据或领域模型）。
- **必须**使用 `@ft.observable` 和 `@dataclass` 组合。
- **自动化**：当修改被装饰类的属性（如 `user.name = "Ada"`）或操作列表（如 `app.users.append(user)`）时，引用该数据的组件会自动重绘。

```python
@ft.observable
@dataclass
class User:
    first_name: str
    last_name: str
```

## 3. 组件化开发 (@ft.component)
将 UI 拆分为独立的渲染单元。
- **函数式定义**：使用 `@ft.component` 装饰器。
- **纯粹性**：组件应基于传入的参数（Props）和内部状态（Hooks）返回控件，不应直接修改外部 Page。
- **渲染逻辑**：
  ```python
  @ft.component
  def UserRow(user: User) -> ft.Control:
      return ft.Row([ft.Text(f"{user.first_name}")])
  ```

## 4. 状态钩子 (Hooks - `ft.use_state`)
用于管理组件内部的、短期的、仅与视图相关的状态（如“是否正在编辑”、“输入框缓存”）。
- **持久性**：由于组件函数会多次运行，`use_state` 确保状态在重绘间得以保留。
- **触发重绘**：调用 setter 函数（如 `set_is_editing(True)`）会立即触发该组件及其子树的重新渲染。

```python
is_editing, set_is_editing = ft.use_state(False)
```

## 5. 重构准则 (从命令式转向声明式)

### A. 显隐控制 -> 条件渲染
- **禁止**：`self.control.visible = False; self.page.update()`
- **推荐**：
  ```python
  return ft.Row([...]) if not is_editing else ft.TextField(...)
  ```

### B. 直接修改控件值 -> 修改模型
- **禁止**：`self.text.value = "New Value"`
- **推荐**：`user.update(new_value)`

### C. `page.update()` -> 状态驱动
- 在声明式架构中，**严禁**在业务逻辑中到处调用 `page.update()`。通过更新 `observable` 字段或调用 `use_state` 的 setter 来驱动更新。

## 6. 本项目应用规范
- **大型列表**（如角色库、伤害事件流）：必须使用声明式组件，以利用 Flet 的局部重绘优化。
- **局部 UI 逻辑**：如“点击展开/收起”，使用 `ft.use_state`。
- **全局仿真数据**：使用 `@ft.observable` 定义 `SimulationState`。

---
*来源：Flet 官方文档 - From Imperative to Declarative*
