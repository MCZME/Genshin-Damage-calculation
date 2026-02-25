# Flet 辅助功能 (Accessibility) 开发规范

Flet 基于 Flutter，提供了原生级别的辅助功能支持。为了确保应用对所有用户友好，必须遵循以下开发规范。

## 1. 核心原则
- **屏幕阅读器支持**：移动端支持 TalkBack (Android) 和 VoiceOver (iOS)；桌面端支持 JAWs/NVDA (Windows) 和 VoiceOver (macOS)。
- **Web 端激活**：Web 版用户需点击 "Enable accessibility" 按钮来构建语义树 (Semantics Tree)。

## 2. 控件规范

### 文本 (Text)
- 当 `Text` 控件的默认内容不足以描述其含义时，使用 `semantics_label` 属性覆盖默认语义。
  ```python
  ft.Text("3/10", semantics_label="得分：10分之3")
  ```

### 按钮 (Buttons)
- **文字按钮**：普通按钮会自动生成正确的语义。
- **图标按钮**：`IconButton`、`FloatingActionButton` 和 `PopupMenuButton` **必须**设置 `tooltip` 属性，屏幕阅读器会将其作为语义描述。
  ```python
  ft.IconButton(icon=ft.Icons.ADD, tooltip="添加新角色")
  ```

### 表单控件 (TextField & Dropdown)
- **必须**使用 `label` 属性。屏幕阅读器会读取此标签以告知用户该输入框的用途。
  ```python
  ft.TextField(label="角色姓名")
  ft.Dropdown(label="元素类型")
  ```

### 自定义语义 (Custom Semantics)
- 对于复杂的自定义组件，使用 `ft.Semantics()` 控件包裹，并定义其具体的语义属性。

## 3. 调试与验证
- **语义调试器**：在开发阶段，通过设置 `page.show_semantics_debugger = True` 查看框架报告的辅助功能信息。
- **快捷键方案**：推荐实现快捷键切换调试器：
  ```python
  def on_keyboard(e: ft.KeyboardEvent):
      if e.shift and e.key == "S":
          page.show_semantics_debugger = not page.show_semantics_debugger
          page.update()
  ```

---
*来源：Flet 官方文档 - Accessibility*
