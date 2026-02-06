# 原神伤害计算 - 技术设计详述

## 1. 核心运行机制

### 1.1 时间驱动模型 (Frame-Based)
模拟引擎采用固定步长的帧驱动模型（默认为 60 FPS）。
- `Simulator` 负责主循环的推进。
- 每帧状态更新遵循：`ActionManager` (动作状态) -> `Character/Entity Update` (逻辑更新) -> `Event Publication` (事件触发) -> `System Processing` (业务处理)。

### 1.2 事件管道 (Event Pipeline)
事件系统是整个引擎的“神经系统”，实现了业务逻辑的完全解耦。
- **订阅制**：各个 `System` 在初始化时订阅感兴趣的 `EventType`。
- **冒泡与取消**：事件支持冒泡机制，并允许处理器通过 `event.cancel()` 拦截后续逻辑（例如：无敌状态拦截伤害事件）。
- **生命周期**：
    1. `BEFORE_...`：逻辑执行前的预处理，常用于修改参数（如属性加成）。
    2. 执行核心计算。
    3. `AFTER_...`：逻辑执行后的后处理，常用于触发连锁反应（如反应后触发的被动）。

## 2. 伤害计算体系 (`DamageSystem`)

### 2.1 乘区模型
计算器严格遵循《原神》官方伤害公式：
`伤害 = 基础值 × 倍率 × (1 + 伤害加成) × 暴击乘区 × 防御乘区 × 抗性乘区 × 反应乘区 × 独立乘区`

- **基础值**：支持攻击力、生命值、防御力或精通，甚至支持多属性复合基础值。
- **固定伤害加成**：通过 `固定伤害基础值加成` 字段支持如云堇、申鹤的增伤逻辑。
- **独立乘区**：通过 `BEFORE_INDEPENDENT_DAMAGE` 事件实现动态注入。

### 2.2 元素附着与反应
- **状态管理**：每个实体持有 `ElementalAura` 实例，负责元素附着量（Gauge）的消减与叠层。
- **反应触发**：由 `ReactionSystem` 监听伤害事件，根据当前附着状态判断触发的反应类型，并反馈修正系数给伤害系统。

## 3. 扩展与开发指引

### 3.1 增加新角色
1. 在 `character/` 对应地区目录下创建类文件。
2. 继承 `Character` 基类并实现 `_init_character`。
3. 定义技能（NormalAttack, Skill, Burst 等）并注册到 `ActionManager`。

### 3.2 增加新系统
1. 继承 `GameSystem`。
2. 在 `register_events` 中订阅所需事件。
3. 在 `core/context.py` 的 `create_context` 中将其加入 `system_manager`。

## 4. 状态隔离与并发
- **Context 隔离**：所有的运行状态（包括注册表快照、实体列表、事件处理器）均封装在 `SimulationContext` 中。
- **安全性**：通过 Python 的 `ContextVar` 确保多协程/多线程环境下，全局 `get_context()` 始终指向当前模拟链路的上下文。
