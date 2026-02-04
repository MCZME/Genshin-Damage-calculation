# Core - 模拟上下文 (SimulationContext)

`SimulationContext` 是整个仿真引擎的“核心容器”。它持有当前模拟的所有状态，并负责协调各个子系统的运行。

## 核心设计
为了支持高性能的并行模拟，本项目彻底摒弃了全局变量。所有的状态都封装在 `SimulationContext` 实例中，并通过 `ContextVar` 实现线程/协程安全的访问。

### 关键组件
- **`current_frame`**: 当前模拟的总帧数。
- **`event_engine`**: 层级事件引擎，负责模拟内部的通讯。
- **`system_manager`**: 系统管理器，负责装配 `DamageSystem` 等核心逻辑。
- **`team`**: 当前参与模拟的队伍实例。
- **`target`**: 模拟的目标（敌人）。
- **`logger`**: 实例化的日志记录器。

## 使用方法

### 创建上下文
```python
from core.context import create_context

ctx = create_context() # 自动初始化注册表、Logger和所有核心 System
```

### 获取当前上下文
在任何地方，只要处于同一个调用链中，都可以通过 `get_context()` 安全获取：
```python
from core.context import get_context

ctx = get_context()
print(f"当前帧: {ctx.current_frame}")
```

## 生命周期
1. **初始化 (`create_context`)**: 加载配置，自动装配 `DamageSystem` 等。
2. **执行 (`Simulator`)**: 每一帧驱动 `ctx.advance_frame()` 并分发事件。
3. **重置 (`reset`)**: 清空所有实体、事件订阅和计时器，准备下一次模拟。
