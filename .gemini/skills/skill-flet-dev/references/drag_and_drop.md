# Flet 拖放 (Drag and Drop) 开发规范

Flet 通过 `Draggable` 和 `DragTarget` 控件提供了简洁的拖放机制。

## 1. 核心组件
- **`Draggable`**：拖拽源。
- **`DragTarget`**：放置目标。
- **`group` 属性**：只有当 `Draggable` 和 `DragTarget` 具有相同的 `group` 名称时，拖放才会生效。

## 2. 交互逻辑
当放置成功时，`DragTarget` 会触发 `on_accept` 事件。
- **获取源控件**：通过 `page.get_control(e.src_id)` 获取被拖拽的源对象。
- **数据传递**：开发者需自行决定拖放后的业务逻辑（如交换数据、更新状态）。

## 3. 视觉反馈规范 (UX)
为了提升交互体验，本项目**强制要求**实现以下反馈：

### 拖拽源反馈
- **`content_when_dragging`**：当控件被拖走时，在原位留下的占位控件（通常是半透明或虚线框）。
- **`content_feedback`**：鼠标指针下方跟随的控件。默认是 50% 不透明度的原控件。

### 放置目标反馈
- **`on_will_accept`**：当拖拽物进入目标区域时触发。应在此处改变目标的样式（如增加边框、高亮背景）以告知用户“可以放置”。
- **`on_leave`**：当拖拽物离开或放置取消时，必须还原目标样式。
- **`on_accept`**：放置成功后，除了业务逻辑，也必须还原目标样式。

## 4. 代码模板
```python
def drag_accept(e):
    src = page.get_control(e.src_id) # 获取源
    # 业务逻辑：例如交换位置数据
    # 样式重置
    e.control.content.border = None
    page.update()

def drag_will_accept(e):
    # e.data 为 "true" 表示 group 匹配，允许放置
    e.control.content.border = ft.border.all(2, ft.Colors.BLACK45 if e.data == "true" else ft.Colors.RED)
    e.control.update()

# UI 定义
draggable = ft.Draggable(
    group="team_slot",
    content=character_card,
    content_when_dragging=placeholder_card, # 占位符
    content_feedback=mini_card # 指针跟随
)

target = ft.DragTarget(
    group="team_slot",
    on_accept=drag_accept,
    on_will_accept=drag_will_accept,
    on_leave=lambda e: setattr(e.control.content, "border", None) or e.control.update()
)
```

## 5. 本项目应用场景建议
- **角色面板切换**：拖拽角色图标到特定槽位进行编队。
- **动作条排序**：在战术视图中通过拖拽调整技能释放顺序。

---
*来源：Flet 官方文档 - Drag and Drop*
