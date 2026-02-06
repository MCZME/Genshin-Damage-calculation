# 原神伤害计算 - 架构概览 (V2)

## 核心哲学
本项目旨在建立一个**工业级、高性能、完全解耦**的原神战斗平台。

## 系统分层

### 1. 基础设施层 (Infrastructure)
- **`SimulationContext`**: 唯一的真理来源，持有全量状态。
- **`EventEngine`**: 基于层级冒泡的通讯枢纽。
- **`Registry`**: 自动扫描发现所有角色、武器、圣遗物类。

### 2. 逻辑控制层 (Engine)
- **ASM (ActionManager)**: 控制所有实体的物理动作时间轴。
- **SystemManager**: 自动装配各个业务子系统。

### 3. 业务子系统层 (Systems)
- **`DamageSystem`**: 负责核心乘区计算。
- **`ReactionSystem`**: 负责元素附着与反应触发逻辑。
- **`HealthSystem` / `ShieldSystem`**: 处理生存相关的状态变更。

### 4. 数据资产层 (Entities & Content)
- **`Character`**: 基于 ASM 的角色模型。
- **`Effect`**: 物理隔离的 Buff/Debuff 实现。
- **`Artifact` / `Weapon`**: 按文件隔离的装备效果实现。

## 执行流
1. 创建 `Context`。
2. 通过 `TeamFactory` 加载角色实例。
3. `Simulator` 开启主循环。
4. 每帧：驱动 `ActionManager` -> 触发事件 -> System 计算 -> 更新面板。