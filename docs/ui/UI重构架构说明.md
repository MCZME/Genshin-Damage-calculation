# UI 重构架构说明 (Strategic & Tactical Reboot)

## 1. 核心设计哲学
- **资产导向 (Asset-Centric)**: UI 逻辑以原神游戏内的角色、武器、圣遗物为最小录入单元。
- **意图驱动 (Intent-Driven)**: 用户的每一项配置都是一种“意图声明”，而非对最终属性的赋值。
- **全流程解耦**: 
  - 战略视图只负责装配意图。
  - 战术视图只负责动作序列意图。
  - 分析视图负责对前两者在仿真中产生的结果进行追溯。

## 2. 状态管理 (State Management)
采用分层级的局部状态机，避免全局 `AppState` 过于臃肿：
- `StrategicState`: 维护 4 人编队的静态参数（ID, Level, Stats）。
- `TacticalState`: 维护线性动作序列。
- `AnalysisState`: 映射仿真输出的审计追踪 (Audit Trail)。
- **服务解耦**: 通过 `PersistenceManager` 服务接管所有文件系统交互，UI 仅发起异步请求并接收结果回调。

## 3. Flet V3 (0.80+) 适配规范
项目强制执行以下现代 Flet 标准：
- **Async Return Path**: 所有的 FilePicker 交互、异步保存/加载任务必须通过 `await` 处理。
- **Mounted Check**: 调用 `update()` 前必须确保组件处于挂载状态。
- **控制器模式**: 必须采用控制器模式管理复杂组件（如 `StrategicView`），严禁直接通过 Index 强行关联。
- **服务注入**: 将公共服务（如持久化）注入 `page` 实例，方便跨视图调用。

## 4. 交互流向 (Workflow)
1. **Strategic View**: 用户选人、配装 -> 产生 `TeamConfig`。
2. **Scene View**: 配置敌方实体与空间坐标。
3. **Tactical View**: 编排动作序列 -> 产生 `ActionSequence`。
4. **Engine Run**: 提交配置并启动 Simulator。
5. **Analysis View**: 渲染审计报告与 DPS 曲线。

---
*版本: v3.1.5*
*更新日期: 2026-02-22*
