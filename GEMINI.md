# 原神伤害计算器 (Genshin Damage Calculation) - 项目概览

## 项目简介
本项目是一款为《原神》设计的深度伤害计算器与战斗仿真引擎。它采用 **“场景中心化 (Scene-Centric)”** 与 **“意图驱动 (Intent-Driven)”** 的架构，能够高保真地模拟物理位置、动作时间轴以及复杂的状态机交互。项目已全面进化至 **V2.4 架构**，具备基于原生数据的自动化装配能力与全流程伤害审计系统。

## 核心技术栈
*   **编程语言:** Python 3.13+
*   **GUI 框架:** Flet (基于 Flutter 的跨平台响应式框架，原生支持 Asyncio)
*   **审计系统**: DamageAuditSystem (基于审计链的伤害追溯机制)
*   **系统架构:** 局部事件引擎 (`EventEngine`)、组件化系统 (`core/systems`)、场景中心化 (`CombatSpace`)。
*   **数据持久化:** 
    *   **静态库 (MySQL)**: 存储角色、武器、圣遗物等基础资产数据。
    *   **运行库 (SQLite)**: 存储全帧仿真状态记录，支持秒级回溯分析。
*   **并发与异步:** `asyncio` (用于 UI 与 I/O 驱动)、`multiprocessing` (用于大规模并行仿真)。

## 架构概览 (V2.4.1)
项目采用四层解耦架构，强调 **Context 隔离** 与 **计算即审计**：

### 1. 基础设施层 (Infrastructure)
*   **`SimulationContext`**: “真理之源”。持有 `CombatSpace`、`EventEngine` 和 `SystemManager`。
*   **`DamageAudit`**: 每一笔伤害都携带完整的 `audit_trail`（包含面板、转换、Buff 及修正的详细来源声明）。
*   **`Registry`**: 自动发现机制。基于装饰器（如 `@register_character`）实现组件的自动装配。

### 2. 物理与场景层 (Scene & Physics)
*   **`CombatSpace`**: 场景管理器。负责几何碰撞检测，支持空间广播模式。
*   **`Height-Aware Physics`**: 角色拥有 3D 坐标 (X, Y, Z)，下落攻击判定由触地物理瞬间 (Y <= 0) 触发。
*   **`CombatEntity`**: 战斗实体基类。管理生命周期、元素附着（Aura）、ICD 以及护盾列表。

### 3. 动作与技能层 (Action & Skill)
*   **`ActionManager (ASM)`**: 动作状态机。管理自动连击段位、判定帧及根据动作类型（dash/jump）的中断优先级。
*   **`Stateless Factories`**: 技能类被重构为无状态工厂。通过注入 `data.py` 的原生数据实现 0 翻译的物理与时序装配。

### 4. 业务子系统层 (Systems)
*   **`DamageSystem`**: 伤害流水线。通过 `add_modifier` 规范接口强制执行审计注入，涵盖基础快照、反应结算及数值合算。
*   **`ReactionSystem`**: 反应分发中心。实装了等级系数、EM 增益审计及受击 ICD。
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
*   **计算即审计**: 严禁直接修改 `stats` 字典，所有增益必须通过 `ctx.add_modifier` 注入审计链。
*   **零翻译录入**: `data.py` 中的物理参数保持原生中文描述（如“球”、“默认”），在装配阶段映射。
*   **无硬编码**: 严禁在 `skills.py` 中写死帧数或物理参数，必须从 `ACTION_FRAME_DATA` 等字典索引。
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
