# 原神伤害计算器 (Genshin Damage Calculation) - 项目概览

## 项目简介
本项目是一款为《原神》设计的深度伤害计算器与战斗仿真引擎。它采用 **“场景中心化 (Scene-Centric)”** 与 **“意图驱动 (Intent-Driven)”** 的架构，能够高保真地模拟物理位置、动作时间轴以及复杂的状态机交互。项目已全面进化至 V2.3 架构，具备基于 **Flet (Flutter)** 的响应式图形界面和基于 **SQLite** 的高性能仿真数据回溯系统。

## 核心技术栈
*   **编程语言:** Python 3.13+
*   **GUI 框架:** Flet (基于 Flutter 的跨平台响应式框架，原生支持 Asyncio) - *已替代 NiceGUI/PySide6*
*   **系统架构:** 局部事件引擎 (`EventEngine`)、组件化系统 (`core/systems`)、场景中心化 (`CombatSpace`)。
*   **数据持久化:** 
    *   **静态库 (MySQL)**: 存储角色、武器、圣遗物等基础资产数据。
    *   **运行库 (SQLite)**: 存储全帧仿真状态记录，支持秒级回溯分析。
*   **并发与异步:** `asyncio` (用于 UI 与 I/O 驱动)、`multiprocessing` (用于大规模并行仿真)。

## 架构概览 (V2.3.1)
项目采用四层解耦架构，强调 **Context 隔离**：

### 1. 基础设施层 (Infrastructure)
*   **`SimulationContext`**: “真理之源”。持有 `CombatSpace`、`EventEngine` 和 `SystemManager`，通过 `ContextVar` 实现多实例逻辑隔离。
*   **`EventEngine`**: 局部神经中枢。每个上下文拥有独立引擎，彻底移除了全局 `EventBus`。
*   **`Registry`**: 自动发现机制。基于装饰器（如 `@register_character`）实现组件的自动装配。

### 2. 物理与场景层 (Scene & Physics)
*   **`CombatSpace`**: 场景管理器。负责实体的坐标 (X, Z)、朝向及阵营管理，执行基于 `AttackConfig` 的几何碰撞检测。
*   **`CombatEntity`**: 战斗实体基类。管理生命周期、元素附着（Aura）、ICD 以及护盾列表。

### 3. 动作与意图层 (Action & Intent)
*   **`ActionManager (ASM)`**: 动作状态机。精确控制动作时间轴、判定帧及取消窗口。
*   **`Intent-Driven Interface`**: 逻辑与物理分离。技能类通过 `to_action_data(intent)` 将 UI 传来的意图（字典）转化为物理动作块。

### 4. 业务子系统层 (Systems)
*   **`DamageSystem`**: 伤害流水线。执行属性快照、碰撞广播、反应结算及数值合算。
*   **`ReactionSystem`**: 反应分发中心。实装了结晶晶片、扩散传播、草原核实体及受击 ICD。
*   **`Shield & Health Systems`**: 处理生存屏障与最终生命值扣除，支持无视护盾（侵蚀）伤害。

## UI 架构: 模块化工作台 (Flet Workbench)

项目 UI 采用模块化设计，实现了“配置即所得”的交互体验：

### 1. 视图划分 (Views)
*   **战略视图 (Strategic View)**: 负责编队管理、角色/武器/圣遗物面板配置。
*   **战术编排 (Tactical View)**: 提供树形或列表式的动作序列编辑器。
*   **可视化看板 (Visual Pane)**: 基于场景快照渲染实时的实体位置与状态关系。

### 2. 元数据驱动 (Metadata-Driven Inspector)
*   **Discovery 机制**: 角色类实现类方法 `get_action_metadata()`。
*   **动态渲染**: UI 根据 Metadata 自动生成属性调节器（如“点按/长按”下拉框、蓄力段数滑块），无需为每个角色手动编写 UI 代码。

## 工作流: 配置 -> 仿真 -> 分析

1.  **配置 (Flet UI):** 在工作台定义队伍、目标及意图参数。
2.  **仿真 (Core):** `Simulator` 驱动 `CombatSpace` 进行物理模拟，每一帧状态流式写入 SQLite。
3.  **分析 (Analysis):** 通过回溯 SQLite 数据生成 DPS 曲线、元素附着时间轴及详尽的计算审计报告。

## 构建与运行

### 快速启动
1.  **安装依赖**: `pip install -r requirements.txt`
2.  **启动应用**: 
    ```powershell
    python main.py
    ```
    (推荐在 `genshin_damage_calculation` 虚拟环境下启动)

### 开发规范
*   **严格类型**: 所有 `core` 方法必须包含类型标注。
*   **卫语句**: 优先处理异常分支，减少代码嵌套。
*   **无 print**: 严禁直接 `print`，统一使用 `get_emulation_logger().log_info/debug`。

## 目录结构
*   `character/`, `weapon/`, `artifact/`: 业务逻辑模块包。
*   `core/`: 仿真引擎核心。
    *   `action/`: 动作与契约定义。
    *   `factory/`: 组装器与实体工厂。
    *   `mechanics/`: 附着论与 ICD。
    *   `systems/`: 局部子系统实现。
*   `ui/`: Flet 组件与视图逻辑。
*   `docs/`: 结构化开发文档。
