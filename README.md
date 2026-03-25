# 原神伤害计算器 & 战斗仿真引擎 (V2.4)

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![UI: Flet](https://img.shields.io/badge/UI-Flet_0.80+-orange.svg)](https://flet.dev/)
[![Architecture: Intent-Driven](https://img.shields.io/badge/Architecture-Intent--Driven-green.svg)]()

> **”不只是计算，更是高保真、可回溯的战斗仿真。”**

这是一个为《原神》深度玩家与数值分析师设计的、基于**意图驱动 (Intent-Driven)** 与 **场景中心化 (Scene-Centric)** 架构的战斗仿真引擎。它能够高保真地模拟物理位移、动作时间轴、复杂的元素附着状态机，并提供直观的 Web 图形界面。

---

## 🌟 核心特性

*   **🎬 动作状态机 (ASM)**: 高精度模拟动画帧、判定点 (Hit-frames) 以及动作取消窗口 (Cancel Windows)。
*   **📐 场景化物理**: 具备真实坐标系 (X, Z) 的空间引擎，支持圆柱、长方体、扇形等多种几何碰撞检测。
*   **🧪 深度元素论**: 严格遵循附着论，完美支持元素消耗、叠加、反应优先级及 ICD 计数器。
*   **🧠 意图驱动架构**: 物理逻辑与交互逻辑解耦。UI 传输”意图”（如”点按/长按”），引擎自动产出物理动作块。
*   **📡 上下文隔离 (Context-Bound)**: 摒弃全局 `EventBus`，事件分发严格限制在 `SimulationContext` 内部，支持高并发多线程仿真。
*   **📊 双数据库动力**:
    *   **核心资产库 (MySQL)**: 维护全量角色、武器、圣遗物权威静态数据。
    *   **实时回溯库 (SQLite)**: 每一帧状态流式写入，支持秒级回溯分析与 DPS 曲线生成。
*   **🎨 现代 Web UI**: 基于 Flet 打造响应式面板，支持动态 Inspector 参数实时编辑。
*   **🔍 伤害审计系统**: 完整的修饰符追踪与属性审计，支持子帧精度的事件关联分析。

---

## 🛠️ 技术栈

*   **语言**: Python 3.13+
*   **前端框架**: Flet 0.80+ (基于 Flutter)
*   **持久化**: MySQL (静态资产), SQLite (运行快照), pandas (数据处理)
*   **并发模型**: asyncio (UI & I/O), multiprocessing (大规模批处理)
*   **可视化**: Plotly / Plotly.js

---

## 🚀 快速开始

### 1. 环境准备
确保已安装 Python 3.13.3+。建议使用终端 PowerShell。

```bash
# 克隆项目并安装依赖
pip install -r requirements.txt
```

### 2. 配置数据库
项目依赖 MySQL 存储基础资产。请确保已配置 `database` 项，并在 `main.py` 启动前完成连接测试。

### 3. 启动应用
**必须**使用虚拟环境下的 Python 启动：
```powershell
# 启动仿真工作台
python main.py
```
程序启动后，会自动打开默认浏览器进入 **仿真工作台**。

---

## 📁 项目结构

```
├── core/                    # 核心引擎
│   ├── context.py           # SimulationContext 上下文管理
│   ├── combat_space.py      # CombatSpace 场景物理引擎
│   ├── event.py             # 上下文绑定事件系统
│   ├── registry.py          # 装饰器自动发现机制
│   ├── simulator.py         # 仿真器主循环
│   ├── action/              # 动作状态机 (ASM)
│   ├── systems/             # 子系统层
│   │   ├── damage_system.py     # 伤害计算系统
│   │   ├── reaction_system.py   # 元素反应系统
│   │   ├── energy_system.py     # 能量系统
│   │   ├── shield_system.py     # 护盾系统
│   │   ├── health_system.py     # 生命值系统
│   │   └── resonance_system.py  # 元素共鸣系统
│   ├── mechanics/           # 机制实现 (ICD/附着)
│   ├── entities/            # 实体基类与协议
│   ├── data_models/         # 数据模型定义
│   └── factory/             # 工厂模式构造器
├── character/               # 角色实现 (按地区组织)
│   ├── FONTAINE/furina/     # 芙宁娜
│   │   ├── char.py          # 角色类定义
│   │   ├── data.py          # 原生帧数据
│   │   ├── skills.py        # 技能实现
│   │   ├── talents.py       # 被动天赋
│   │   ├── constellations.py # 命座效果
│   │   └── entities.py      # 召唤物/同伴
│   ├── NATLAN/              # 纳塔角色
│   ├── SUMERU/              # 须弥角色
│   ├── INAZUMA/             # 稻妻角色
│   ├── LIYUE/               # 璃月角色
│   └── MONDSTADT/           # 蒙德角色
├── weapon/                  # 武器实现 (按类型)
│   ├── SWORD/               # 单手剑
│   ├── CLAYMORE/            # 双手剑
│   ├── POLEARM/             # 长柄武器
│   ├── BOW/                 # 弓
│   └── CATALYST/            # 法器
├── artifact/                # 圣遗物系统
│   └── sets/                # 圣遗物套装效果
├── ui/                      # Flet UI 层
│   ├── app.py               # 应用入口
│   ├── layout.py            # 布局组件
│   ├── views/               # 视图层
│   ├── view_models/         # 视图模型
│   ├── components/          # UI 组件库
│   └── states/              # 状态管理
├── tests/                   # 测试套件
│   ├── unit/                # 单元测试
│   ├── integration/         # 集成测试
│   └── conftest.py          # 测试夹具
└── docs/                    # 文档
    ├── architecture/        # 架构文档
    │   ├── system/          # 系统设计
    │   ├── mechanics/       # 机制说明
    │   └── combat_space/    # 场景物理
    ├── core/                # 核心概念
    ├── development/         # 开发指南
    └── ui/                  # UI 文档
```

---

## 📖 文档索引

为了更好的开发体验，请参考 `docs/` 下的结构化文档：

### 架构文档
*   **[架构概览](./docs/architecture/system/架构概览.md)**: 系统核心分层与执行流
*   **[系统设计详述](./docs/architecture/system/系统设计详述.md)**: 各子系统详细设计
*   **[持久化架构说明](./docs/architecture/system/持久化架构说明.md)**: 数据库设计
*   **[伤害审计系统架构](./docs/architecture/system/伤害审计系统架构.md)**: 修饰符追踪机制

### 机制文档
*   **[元素附着与ICD机制](./docs/architecture/mechanics/元素附着与ICD机制.md)**: 附着论实现
*   **[数据契约与攻击定义](./docs/architecture/mechanics/数据契约与攻击定义.md)**: 伤害数据流

### 场景物理
*   **[场景化实体引擎](./docs/architecture/combat_space/场景化实体引擎.md)**: 物理模拟
*   **[物理碰撞与战斗反馈](./docs/architecture/combat_space/物理碰撞与战斗反馈.md)**: 碰撞检测

### 开发指南
*   **角色适配指南**: 参考 `character/FONTAINE/furina/` 作为实现模板
*   **测试指南**: 使用 `tests/conftest.py` 中的 `MockAttributeEntity` 进行测试

---

## 🏗️ 项目现状

*   ✅ 核心架构 Context 隔离重构完成
*   ✅ EventBus 移除，事件分发本地化
*   ✅ 伤害审计系统实现子帧精度追踪
*   ✅ 元素反应系统支持剧变反应
*   ✅ 基础面板修饰符提取功能
*   🚧 纳塔角色（如玛薇卡）机制实装中
*   🚧 批量仿真系统优化中

---

## 🧪 测试

```powershell
# 运行单元测试
python -m pytest tests/unit/ -v

# 运行集成测试
python -m pytest tests/integration/ -v

# 运行单个测试文件（详细输出）
python -m pytest tests/unit/mechanics/test_aura_theory.py -v -s
```

---

*版本: v2.4.0 (Combat-Centric)*
*日期: 2026-03-19*
