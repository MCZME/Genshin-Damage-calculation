# 原神伤害计算器 (Genshin Damage Calculation) - 项目概览

## 项目简介
本项目是一款为《原神》设计的深度伤害计算器与战斗仿真引擎。它采用 **“场景中心化 (Scene-Centric)”** 与 **“事件驱动 (Event-Driven)”** 的架构，能够高保真地模拟物理位置、动作时间轴以及复杂的状态机交互。项目已全面进化至 V2 架构，具备基于 **NiceGUI** 的 Web 图形界面和基于 **SQLite** 的高性能仿真数据回溯系统。

## 核心技术栈
*   **编程语言:** Python 3.13+
*   **GUI 框架:** NiceGUI (基于 Web 的响应式框架，原生支持 Asyncio) - *已替代 PySide6*
*   **系统架构:** 事件驱动 (`EventBus`)、组件化系统 (`core/systems`)、场景中心化 (`CombatSpace`)。
*   **数据持久化:** SQLite (嵌入式数据库)，用于存储配置信息及全帧仿真状态记录。
*   **并发与异步:** `asyncio` (用于 UI 与 I/O)、`multiprocessing` (用于大规模无头仿真)。
*   **测试框架:** `pytest` (配合 `pytest-asyncio` 与 `pytest-trio`)。

## 架构概览 (V2)
项目采用四层解耦架构：

### 1. 基础设施层 (Infrastructure)
*   **`SimulationContext`**: “真理之源”。持有 `CombatSpace`、`EventEngine` 和所有实体的引用，通过 `ContextVar` 实现逻辑隔离。
*   **`EventEngine`**: 神经中枢。负责跨系统的逻辑解耦与通信。
*   **`Registry`**: 自动发现与加载机制。负责扫描并注册角色、武器、圣遗物和各种效果。

### 2. 物理与场景层 (Scene & Physics)
*   **`CombatSpace`**: 核心空间管理器。负责维护实体坐标 (X, Z) 与朝向，执行高精度几何碰撞检测（圆柱、长方体、扇形）。
*   **`CombatEntity`**: 所有战斗实体（角色、怪物、部署物）的基类。管理生命周期、元素附着（Aura）和 ICD。

### 3. 动作与控制层 (Action & ASM)
*   **`ActionManager (ASM)`**: 动作状态机。控制实体的动作时间轴，处理判定帧、动作取消窗口 (Cancel Window) 以及技能流转。
*   **`Skill System`**: 模块化技能实现。支持参数化触发（点按、长按、多段触发）。

### 4. 业务子系统层 (Systems)
*   **`DamageSystem`**: 伤害流水线 (`DamagePipeline`) 驱动者。处理快照、广播、受击响应、反应结算及数值合并。
*   **`ReactionSystem`**: 元素反应中枢。基于附着论处理元素的叠加、消耗与反应触发。
*   **`ResultDatabase`**: 异步流式持久化。将每一帧的实体状态抓取并写入 SQLite。

## 工作流: 配置 -> 仿真 -> 分析

1.  **配置 (UI):** 用户在 NiceGUI 前端定义角色、敌人及动作序列。
2.  **仿真 (Headless):** `Simulator` 在独立线程/进程中全速运行逻辑，并将全帧状态（通过 `export_state`）流式写入 SQLite。
3.  **分析 (UI):** 分析仪表盘通过查询 SQLite 实现“任意帧回溯”，展示 DPS 曲线、时间轴及详细的事件记录。

## 构建与运行

### 前置要求
*   Python 3.13.3+
*   虚拟环境: `genshin_damage_calculation` (必须使用此环境运行)
*   依赖库: `nicegui`, `aiosqlite`, `pandas`, `plotly`, `pytest` (详见 `requirements.txt`)
*   终端建议: PowerShell

### 安装步骤
1.  克隆仓库。
2.  创建虚拟环境并安装依赖:
    ```bash
    # 使用 virtualenv 创建名为 genshin_damage_calculation 的环境
    pip install -r requirements.txt
    ```

### 启动应用
**必须**在虚拟环境下执行以下命令启动 Web UI:
```powershell
.\genshin_damage_calculation\Scripts\python.exe main.py
```
系统将初始化配置，启动 NiceGUI 服务器并自动打开默认浏览器。

### 运行测试
**必须**使用虚拟环境中的 Python 运行测试，以确保依赖与路径正确:
```powershell
# 运行全量测试 (PowerShell)
.\genshin_damage_calculation\Scripts\python.exe -m pytest

# 运行特定模块
.\genshin_damage_calculation\Scripts\python.exe -m pytest tests/unit/mechanics/test_aura_theory.py -v
```

## 开发规范与注意事项

*   **初始化顺序:** 在 `main.py` 中，`Config()` **必须**在导入任何 UI 或数据库模块之前初始化，否则会导致配置项读取失败。
*   **事件驱动伤害:** **严禁**在技能逻辑中直接调用 `broadcast_damage`。必须发布 `BEFORE_DAMAGE` 事件，由 `DamageSystem` 统一接管后续流水线。
*   **数据契约:**
    *   **实体状态:** 所有实体必须实现 `export_state()`，返回一个扁平化的、可序列化的字典。
    *   **字段命名:** 基础属性使用 `base_xxx` (如 `base_hp`)。
*   **命名约定:**
    *   在 Action 类中使用 **`scaling_stat`** 代替 `base_value`，以避免与“基础伤害倍率”产生歧义。
*   **异步测试:** 涉及数据库或 UI 组件的测试必须使用 `@pytest.mark.asyncio` 以确保与 `aiosqlite` 的兼容性。

## 目录结构
*   `artifact/`, `character/`, `weapon/`: 实体逻辑实现。
*   `core/`: 核心引擎组件。
    *   `action/`: ASM 与动作定义。
    *   `data/`: 数据库仓储与 Schema。
    *   `entities/`: 实体基类。
    *   `mechanics/`: 附着、ICD、附魔逻辑。
    *   `systems/`: 逻辑管理器 (伤害、反应、能量)。
*   `data/`: 运行时数据存储。
*   `docs/`: 详细的架构与开发文档。
*   `ui/`: NiceGUI 页面与组件。
    *   `pages/`: 应用视图 (配置、分析)。
