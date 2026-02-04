# 系统架构概览 (Architecture Overview)

本文档描述了 *Genshin Damage Calculation* 项目的核心架构理念、分层设计及未来重构方向。

## 1. 项目愿景 (Project Vision)

打造一个 **工业级、数据驱动的、高还原度** 的原神战斗仿真引擎。
*   **核心能力**：基于帧 (Frame-Based) 的离散事件模拟，支持精确的伤害计算、元素反应覆盖率分析及循环轴优化。
*   **设计目标**：模块化（Modular）、去全局化（Context-Aware）、可测试（Testable）、高性能（High Performance）。

## 2. 核心架构模式 (Core Patterns)

### 2.1 层级发布-订阅模式 (Hierarchical Publisher-Subscriber)
*   为了解决“广播风暴”问题，系统采用层级事件总线设计。
*   **三层架构**:
    *   **Local Bus (Character/Entity)**: 处理仅针对该实体的事件（如自身的天赋触发、单体 Buff）。
    *   **Team Bus**: 处理队伍级事件（如元素共鸣、全队治疗、产球）。
    *   **Global Bus (Context)**: 处理环境、时间及跨队伍事件。
*   **事件冒泡 (Event Bubbling)**:
    *   事件默认在产生该事件的实体（Source）的 Local Bus 上发布。
    *   随后自动向上冒泡至 Team Bus，最后至 Global Bus。
    *   Listener 可以选择拦截事件，停止冒泡 (`event.stop_propagation()`)。
*   **优势**: 极大减少无效的事件回调，确保逻辑的封装性和性能。

### 2.2 帧驱动循环 (Frame-Driven Loop)
*   模拟器以 `60 FPS` 为时间基准。
*   所有状态更新（冷却、Buff、元素衰减）均以“帧”为最小单位。

## 3. 系统分层 (Layered Architecture)

为了实现关注点分离，系统划分为以下三层：

### 3.1 仿真层 (Simulation Layer)
*   **职责**：负责驱动时间轴，触发动作，分发事件。
*   **核心组件**：
    *   `Simulator` (原 `Emulation`): 模拟控制器，持有 `SimulationContext`。
    *   `SimulationContext`: 包含当前帧、`EventBus` 实例、`Team` 实例、`Target` 实例。
    *   `ActionEngine`: 解析并执行动作序列。

### 3.2 模型层 (Model Layer)
*   **职责**：表示游戏实体及其状态，响应事件。
*   **核心组件**：
    *   `Character`: 角色实体（属性、天赋、命座）。
    *   `Weapon`: 武器实体（基础面板、特效）。
    *   `Artifact`: 圣遗物实体（套装效果）。
    *   `BaseObject`: 所有场上实体（召唤物、护盾、元素微粒）的基类。

### 3.3 数据访问层 (Data Access Layer)
*   **职责**：提供静态元数据（基础属性、倍率表）。
*   **核心组件**：
    *   `DataRequest` (现有): 连接 MySQL 服务器获取敏感/静态数据。
    *   `DataRepository` (规划中): 抽象接口，隔离具体的数据源（MySQL/JSON/Mock）。
*   **设计原则**：**依赖倒置**。模型层不应直接依赖具体的数据库实现，数据应在工厂层被注入。

## 4. 核心子系统升级 (Subsystem Upgrades)

为了解决“更新困难”和“模拟失真”的痛点，将引入以下两个关键子系统：

### 4.1 动作状态机 (Action State Machine - ASM)
不再使用简单的“耗时 X 帧”模型，而是将每个动作视为一个具有生命周期的状态对象。

*   **动作生命周期**:
    *   `Start`: 动作开始，消耗资源。
    *   `Hit/Damage`: 判定点（可有多个）。
    *   `Cancel Window`: 取消窗口（Jump, Dash, Swap）。允许后续动作提前打断当前动作。
    *   `End`: 动作自然结束。
*   **位移元数据 (Displacement Metadata)**:
    *   动作可携带可选的 `horizontal_dist` (水平位移) 和 `vertical_dist` (垂直位移) 参数。
    *   **按需配置**: 仅针对依赖位移的特殊机制（如基于移动距离的增伤、下落攻击高度判定）进行配置，默认值为 0。
*   **卡肉模拟 (Hitlag)**:
    *   引入局部时间流速控制。当近战攻击发生时，暂停角色动画计时器及 Buff 计时器，但保持全局计时器运行。
*   **数据驱动**: 动作逻辑由 `ActionFrameData` 配置驱动（包含前摇、后摇、取消帧等数据），而非硬编码逻辑。

### 4.2 数据驱动的角色定义 (Data-Driven Character Definition)
...
### 4.3 全局上下文管理 (Global Context Management)
引入 `SimulationContext` 作为模拟过程中的“唯一事实来源”，以支持去全局化和并行模拟。

*   **状态追踪**:
    *   `global_move_dist`: 累积全队在当前循环下的总水平移动距离。
    *   `global_vertical_dist`: 记录当前动作的下落高度/垂直位移。
    *   这些值由 ASM 在执行动作时根据位移元数据自动更新。
将角色逻辑从 Python 代码中剥离，通过配置定义行为。

*   **目标**: 新增角色主要通过“填表”（JSON/YAML 配置）完成，而非编写大量 Python 代码。
*   **实现**: 
    *   定义通用的 Effect 和 Trigger 描述语言（DSL）。
    *   使用解释器解析配置并自动挂载 EventListener。

## 5. 数据流向 (Data Flow)

1.  **配置输入**: 用户提供 `UserConfig` (JSON, 包含面板与动作)。
2.  **工厂组装 (Factory Assembly)**:
    *   `TeamFactory` 读取 `UserConfig`。
    *   调用 `DataRepository` 获取角色/武器的基础元数据 (MySQL)。
    *   实例化 `Character` 和 `Weapon`，注入合成后的属性。
3.  **模拟运行 (Simulation Run)**:
    *   `Simulator` 初始化 `Context`。
    *   按帧执行动作 -> 触发 `Event` -> `Handlers` 计算数值。
4.  **结果输出**:
    *   `Logger` 记录过程。
    *   `DataHandler` 生成统计报表。

## 5. 即将进行的重构 (Refactoring Roadmap)

1.  **基础设施 (Infrastructure)**:
    *   统一文件命名为 `snake_case`。
    *   建立 `core/context.py` 和 `core/factory/`。
2.  **核心解耦 (Core Decoupling)**:
    *   移除全局静态变量（`Team.active_objects`, `EventBus._handlers`）。
    *   引入 `SimulationContext` 传递状态。
3.  **数据层抽象 (Data Abstraction)**:
    *   定义 `Repository` 接口，Mock 掉 `DataRequest` 以支持本地测试。

---
*Last Updated: 2026-02-04*
