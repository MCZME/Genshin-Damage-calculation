# 重构计划 (Refactoring Plan)

本文档基于 `ARCHITECTURE_OVERVIEW.md` 和 `DEVELOPMENT_STANDARDS.md`，制定了详细的代码重构路线图。

## 目标 (Goals)
1.  **基础设施标准化**: 统一 `snake_case` 命名，添加 Type Hints。
2.  **去全局化 (De-globalization)**: 移除 `EventBus` 和 `Team` 的静态状态，引入 `SimulationContext`。
3.  **核心架构升级**: 引入动作状态机 (ASM) 和数据驱动的角色定义 (DDCD)。
4.  **可测试性增强**: 引入 DI (依赖注入) 和 Mocking 机制。

---

## Phase 1: 基础设施与上下文 (Infrastructure & Context)
*目标：建立新的上下文环境，为去全局化做准备，不破坏现有逻辑。*

- [ ] **Task 1.1: 创建 `SimulationContext`**
    - 创建 `core/context.py`。
    - 定义 `SimulationContext` 类，包含 `current_frame`, `global_move_dist` 等属性。
    - 引入 `EventEngine` (非静态版 EventBus) 并集成进 Context。

- [ ] **Task 1.2: 重构 `EventBus` (向后兼容)**
    - 修改 `core/Event.py`。
    - 保留静态 `EventBus` 接口，但在内部代理调用 `SimulationContext.current.event_bus` (利用 ContextVar 实现过渡期的全局访问)。
    - 重命名文件为 `core/event.py` (需同步更新所有 import)。

- [ ] **Task 1.3: 统一基类命名**
    - 重命名 `core/BaseObject.py` -> `core/base_object.py`。
    - 将 `baseObject` 类重命名为 `BaseObject`。
    - 将 `ArkheObject`, `EnergyDropsObject` 等具体实现移至 `core/entities/` 或 `core/objects/`。

- [ ] **Task 1.4: 核心事件系统重构 (Core Systems & Hierarchical Events)**
    - **升级 EventEngine**: 修改 `core/context.py`，支持父子级联 (Parent-Child Cascade) 和事件冒泡机制。
    - **Entity 集成**: 修改 `BaseEntity`，使其自带一个 `LocalEventEngine` 实例，并将事件自动冒泡至 Global Engine。
    - **创建 Systems**: 建立 `core/systems/` 目录，定义 `GameSystem` 基类和 `SystemManager`。
    - **迁移核心逻辑**: 将 `DamageCalculation.py` 迁移为 `core/systems/damage_system.py`，并实现自动装配。

---

## Phase 2: 数据层与工厂模式 (Data Layer & Factory)
*目标：解耦数据加载逻辑，移除 `Emulation.py` 中的硬编码。*

- [ ] **Task 2.1: 定义数据仓库接口**
    - 创建 `core/data/repository.py`。
    - 定义 `DataRepository` 抽象基类。
    - 实现 `MySQLDataRepository` (封装现有的 `DataRequest.py`)。
    - 实现 `JsonDataRepository` (用于测试)。

- [ ] **Task 2.2: 实现 `TeamFactory`**
    - 创建 `core/factory/team_factory.py`。
    - 将 `Emulation.set_data` 中的解析逻辑迁移至此。
    - 使用 `DataRepository` 获取基础数据，而非直接调用 SQL。

- [ ] **Task 2.3: 动作序列解析器**
    - 创建 `core/factory/action_parser.py`。
    - 负责将 JSON 动作序列解析为 `Action` 对象列表。
    - 处理 `params` 解析和中文名映射。

---

## Phase 3: 模拟引擎升级 (Simulation Engine Upgrade)
*目标：替换 `Emulation.py`，引入 ASM。*

- [ ] **Task 3.1: 定义动作数据结构**
    - 创建 `core/action/action_data.py`。
    - 定义 `ActionFrameData` (包含 `hit_frames`, `cancel_windows`, `displacement`)。
    - 定义 `ActionState` 枚举。

- [ ] **Task 3.2: 实现动作状态机 (ASM)**
    - 创建 `core/action/action_manager.py`。
    - 实现基于 Context 的状态流转逻辑 (Start -> Execute -> End)。
    - 实现取消窗口 (Cancel Window) 检查逻辑。

- [ ] **Task 3.3: 创建新版 `Simulator`**
    - 创建 `core/simulator.py`。
    - 仅负责驱动帧循环和 `ActionManager`。
    - 移除所有业务逻辑 (如圣遗物判断)，只做调度。

---

## Phase 4: 角色与技能重构 (Character & Skill Refactoring)
*目标：落地数据驱动设计，减少重复代码。*

- [ ] **Task 4.1: 重构 `Character` 基类**
    - 剥离 `update` 中的状态机逻辑，对接 `ActionManager`。
    - 引入 `Stats` 组件管理属性面板。

- [ ] **Task 4.2: 通用技能模板**
    - 创建 `core/skills/generic_skills.py`。
    - 实现 `GenericNormalAttack`, `GenericElementalSkill`。
    - 支持从 Config 注入倍率和帧数。

- [ ] **Task 4.3: 迁移现有角色**
    - 选择一个简单角色 (如班尼特) 进行迁移验证。
    - 验证新架构下的伤害计算准确性。

---

## Phase 5: 清理与规范化 (Cleanup & Standardization)
*目标：全面推行代码规范。*

- [ ] **Task 5.1: 全局重命名**
    - 将剩余的 `PascalCase` 文件全部转换为 `snake_case`。
    - 修复所有受影响的 Import。

- [ ] **Task 5.2: 类型提示补全**
    - 为核心模块补充 100% 的 Type Hints。
    - 运行 `mypy` 检查。

- [ ] **Task 5.3: 单元测试覆盖**
    - 为 `Simulator`, `ActionManager`, `EventEngine` 编写单元测试。
    - 验证 Mock 数据的可行性。
