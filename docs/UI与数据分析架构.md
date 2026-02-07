# UI 与数据分析系统架构设计 (V2)

## 1. 设计背景
原有的 UI 方案（PySide6）存在内存占用过高（O(N) 帧对象存储）、界面美观度不足以及开发维护成本高等问题。为了支持 V2 架构的高性能仿真及“任意帧状态回溯”的核心需求，UI 系统将进行全面重构。

## 2. 技术选型
*   **UI 框架**: **NiceGUI** (基于 Python 的现代 Web 响应式框架)
    *   *优点*: 纯 Python 开发、原生支持 Tailwind CSS 与 Material Design、异步性能优异、内置丰富的图表组件。
*   **存储引擎**: **SQLite** (本地嵌入式数据库)
    *   *优点*: 零配置、读写极快、支持索引（实现任意帧随机访问的关键）、便于持久化分享。
*   **通讯协议**: **Asyncio + WebSocket** (NiceGUI 默认)

## 3. 核心架构逻辑 (Config -> Simulate -> Analyze)

### 3.1 阶段一：可视化配置编辑器 (Config Editor)
用户通过 UI 界面定义模拟环境：
*   **角色配置**: 通过下拉列表和滑块设置角色等级、天赋、武器及圣遗物。
*   **敌人配置**: 定义目标等级、抗性等。
*   **动作编排**: 交互式序列编辑器，支持拖拽、参数设置。
*   **数据导出**: 配置将生成标准 JSON 契约，传递给 `Simulator`。

### 3.2 阶段二：静默仿真与流式持久化 (Headless Simulation)
点击“开始模拟”后：
1.  **无头运行**: `Simulator` 在独立线程/进程中全速运行，不进行实时 UI 渲染以确保性能。
2.  **状态抓取 (Snapshotting)**: 每帧调用实体的 `export_state()` 方法，将 `attribute_panel`、`aura`、`pos` 等关键数值提取为**扁平字典**。
3.  **持久化写入**: 抓取到的数据与该帧触发的事件（`DamageEvent` 等）被批量写入 SQLite 数据库。
    *   *表结构示例*: `frames` (存储实体状态), `events` (存储伤害/反应事件)。

### 3.3 阶段三：交互式结果分析器 (Analysis Dashboard)
模拟完成后，用户进入分析界面：
*   **时间轴控制器 (Timeline Slider)**: 一个贯穿底部的长滑块。
*   **任意帧回溯 (Random Access)**: 
    *   当用户拖动滑块至第 X 帧时，UI 触发查询：`SELECT * FROM frames WHERE frame_id = X`。
    *   由于 SQLite 索引的支持，查询耗时在毫秒级，实现瞬间查看任意时刻的战场状态。
*   **可视化图表**: 使用 ECharts 展示 DPS 曲线、属性动态变化。
*   **事件追溯**: 点击某个伤害数字，自动跳转并高亮该帧的所有计算细节（乘区快照）。

## 4. 关键技术改进

### 4.1 内存优化：从“内存列表”到“磁盘索引”
*   **V1 问题**: `total_frame_data = [frame1_dict, frame2_dict, ...]` 导致模拟步长增加时内存溢出。
*   **V2 方案**: 模拟时**流式写入**磁盘，分析时**按需读取**。内存中仅保留当前显示的帧数据和精简的汇总数据（如秒级 DPS）。

### 4.2 状态导出协议 (`export_state`)
所有参与仿真的实体（`Character`, `Target`, `DendroCore`）必须实现该协议：
```python
def export_state(self) -> dict:
    return {
        "name": self.name,
        "hp_pct": self.current_hp / self.max_hp,
        "pos": self.pos.copy(),
        "attributes": self.attribute_panel.copy(),
        "auras": self.aura.to_list()
    }
```
*注：严禁在导出字典中包含 Python 对象引用，确保数据可序列化。*

## 5. 工作流规划 (Status: In Progress)
1.  **第一步**: 实现核心实体的 `export_state` 协议。 (✅ Done)
2.  **第二步**: 编写 SQLite 存储驱动（Result Persistence Layer）。 (✅ Done)
3.  **第三步**: 使用 NiceGUI 搭建基础配置面板。 (✅ Done)
4.  **第四步**: 实现带滑块的时间轴分析器。 (✅ Done)

## 6. 异步仿真设计详解
为了支持 UI 的非阻塞响应，`Simulator` 进行了如下改造：
- **Async 循环**: `Simulator.run` 变更为 `async def run`，使得它能在 NiceGUI 的事件循环中被 `await` 调用。
- **快照流**: 在主循环的每一帧末尾，调用 `db.record_snapshot()` 将当前帧数据压入异步队列。
- **后台写入**: `ResultDatabase` 启动一个后台 Worker 协程，负责从队列取出数据并批量写入 SQLite，彻底解耦计算与 IO。

---
*版本: v1.0.0*
*日期: 2026-02-07*
