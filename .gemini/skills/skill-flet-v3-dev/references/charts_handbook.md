# Flet Charts 攻略手册 (Flet Charts Handbook)

> 本文档记录了在 Flet V3 (0.80+) 环境下使用 `flet_charts` 库进行数据可视化的核心规范与避坑指南。

---

## 1. 基础配置 (Namespace)
在当前重构架构中，高级图表功能由 `flet_charts` 提供。

### 导入规范
```python
import flet as ft
import flet_charts as fch
```

## 2. LineChart (折线图) 规范

### LineChartData (数据序列)
*   **数据点参数**: 必须使用 `points` 属性。
    *   ✅ `fch.LineChartData(points=chart_spots, ...)`
    *   ❌ `data_points` 或 `spots` (会导致 `unexpected keyword argument` 崩溃)。
*   **外观配置**:
    *   `curved`: `bool` - 设为 `True` 开启平滑曲线。
    *   `point`: 使用 `fch.ChartCirclePoint(radius=4, color=ft.Colors.WHITE)` 定义节点形状。

### LineChart (图表容器)
*   **事件监听**: 必须使用 `on_event`。
    *   ✅ `fch.LineChart(on_event=self._handle_event, ...)`
    *   ❌ `on_chart_event` (会导致构造函数崩溃)。
*   **交互性**: `interactive=True` 必须开启，否则无法触发点击和悬停提示。

## 3. 交互事件处理 (Interaction)

### LineChartEvent 属性映射
当用户点击或悬停图表时，会触发 `fch.LineChartEvent`。

*   **e.type**: 交互类型。
    *   `"point_click"`: 重点关注，用于触发数据下钻（Audit Drill-down）。
*   **e.spots**: `list[LineChartEventSpot]`。
    *   `spot.bar_index`: 线的索引（第几条折线）。
    *   `spot.spot_index`: **核心索引**。数据点在原始序列中的索引位置，用于精准定位数据模型。

## 4. 视觉与对齐 (Styling)

*   **常量大写**: 严格遵循 Flet V3 规范，所有枚举与对齐常量必须全大写。
    *   `begin=ft.Alignment.TOP_CENTER`
    *   `end=ft.Alignment.BOTTOM_CENTER`
*   **Tooltip 避坑**: 
    *   不要使用 `ft.Tooltip(...)` 控件包装图表内的子组件（如 Container）。
    *   应直接使用组件自带的 `tooltip` 属性：`ft.Container(tooltip="信息", ...)`。

---
*更新日期: 2026-02-23*
