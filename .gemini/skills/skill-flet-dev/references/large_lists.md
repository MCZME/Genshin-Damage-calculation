# Flet 海量列表 (Large Lists) 开发规范

在处理数百甚至数千个子控件时，传统的 `Column` 和 `Row` 会因为全量渲染导致严重的 UI 卡顿。本项目规定必须使用高效的虚拟化容器。

## 1. 容器选择原则
- **禁止**：在预期条目超过 100 条的场景下使用 `Column` 或 `Row` 加 `scroll` 属性。
- **强制要求**：
    - **单列/单行列表**：使用 `ft.ListView`。
    - **网格布局**：使用 `ft.GridView`。
- **原因**：`ListView` 和 `GridView` 仅渲染当前滚动视口内可见的控件（按需渲染），能显著提升首屏加载速度和滚动流畅度。

## 2. ListView 性能优化
为了获得极佳的滚动性能，应提供尺寸暗示：
- **`item_extent`**：如果所有子条目高度固定，**必须**设置此属性。
- **`first_item_prototype`**：若不确定具体高度但所有条目高度一致，设置此属性为 `True`，框架将以第一个条目作为原型计算所有条目尺寸。
- **约束**：`ListView` 必须有明确的高度（或宽度）。通常设置 `expand=True` 以填充父容器空间。

## 3. GridView 响应式配置
`GridView` 能够高效排列大量方块元素（如角色库、圣遗物背包）：
- **`max_extent`**：定义单元格的最大尺寸，列数将根据可用宽度自动调整（推荐用于响应式布局）。
- **`runs_count`**：强制指定固定的列数或行数。
- **`child_aspect_ratio`**：定义子控件的宽高比（默认为 1.0，即正方形）。

## 4. 分批更新 (Batch Updates)
直接在一个循环中添加数千个控件并最后调用一次 `page.update()` 会产生巨大的 WebSocket 消息，导致界面长时间白屏或超时。

**强制规范**：在循环添加大量数据时，必须进行分批更新。
```python
def load_data(e):
    lv = ft.ListView(expand=True, item_extent=50)
    page.add(lv)
    
    for i in range(5000):
        lv.controls.append(ft.Text(f"条目 {i}"))
        if i % 500 == 0: # 每 500 条更新一次 UI
            page.update()
    page.update() # 刷新剩余部分
```

## 5. 消息大小限制
如果初始化数据量极大，可能需要调整环境变量 `FLET_WS_MAX_MESSAGE_SIZE`（默认 1MB）。但在本项目中，**优先考虑分批更新**而非盲目调大消息上限。

---
*来源：Flet 官方文档 - Large Lists*
