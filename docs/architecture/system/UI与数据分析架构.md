# UI 与数据分析系统架构设计 (V3)

## 1. 设计背景
V3 架构旨在解决大规模参数扫描时的“维度爆炸”问题。通过引入图形化的分支管理与意图驱动的指令编排，UI 系统从简单的配置工具进化为专业的仿真工作台。

## 2. 技术选型
*   **UI 框架**: **Flet** (基于 Flutter 引擎的现代桌面应用框架)
    *   *优点*: 渲染速度极快（Flutter 原生绘制）、跨平台一致性、支持高性能 Canvas 与交互手势、零延迟的 Python 异步绑定。
*   **存储引擎**: **SQLite + aiosqlite**
    *   *优点*: 异步非阻塞 IO，支持在仿真运行期间流式记录帧快照，实现“边跑边存”。
*   **核心模式**: **State-Driven UI (AppState)**
    *   应用状态集中管理，组件通过 `refresh()` 机制实现响应式更新。

## 3. 核心交互阶段 (Strategic -> Tactical -> Review)

### 3.1 战略筹备：分支宇宙 (Branching Universe)
用户通过可视化画布定义实验方案：
*   **变异节点 (Mutation Node)**: 每个节点代表一个规则改变（如“全员增加 100 精通”、“换用绝缘套”）。
*   **层级继承**: 子节点自动继承父路径上的所有修改规则，形成路径叠加。
*   **属性编辑器 (Property Editor)**: 针对选中的角色/目标，提供基于 Metadata 的配置表单。

### 3.2 战术编排：意图指令 (Intent Commands)
编排战斗逻辑：
*   **动作库 (Action Library)**: 自动发现队伍中角色的可用技能。
*   **时间轴序列**: 线性排列执行指令。
*   **动态检视器 (Action Inspector)**: 
    *   UI 调用后端的 `get_action_metadata()`。
    *   根据返回的参数类型（select, number, bool），动态生成对应的 Flet 控件。
    *   修改参数即时同步至 `AppState.action_sequence`。

### 3.3 批量仿真与进度反馈 (Batch Simulation)
点击“开始运行”：
1.  **任务生成**: `ConfigGenerator` 对宇宙树执行 DFS，将每个叶子节点转化为独立的仿真 Bundle。
2.  **并行执行**: `BatchRunner` 启动多进程池，每个 Worker 独立加载环境运行仿真。
3.  **实时进度**: Footer 状态栏通过劫持 `AppState.refresh`，实现毫秒级的进度更新（Completed/Total）。

### 3.4 战果复盘 (Analysis & Review)
*   **全局 DPS 标注**: 画布节点在运行结束后自动标注计算结果（Max/Avg DPS）。
*   **任意帧回溯**: 点击节点加载对应的 SQLite 数据库，通过 `Analysis Dashboard` 进行帧级复盘。

## 4. 关键技术改进

### 4.1 高性能画布 (Universe Canvas)
*   **实现**: 使用 Flet `ft.Stack` + `cv.Canvas` 组合。
*   **绘图**: 采用三次贝塞尔曲线绘制节点连接，通过手势处理器（Panning）实现平滑拖拽。

### 4.2 意图驱动协议 (Intent Protocol)
UI 严禁直接修改实体的内部状态，必须通过 **Intent Dict** 进行通信：
```python
# UI 发送的指令格式
{
    "char_name": "夏洛蒂",
    "action_id": "elemental_skill",
    "params": {"type": "Hold"} 
}
```
后端负责将 `params` 转换为具体的物理帧数据，确保了 UI 与物理逻辑的完美隔离。

---
*版本: v3.0.0*
*日期: 2026-02-09*