# 原神伤害计算器 & 战斗仿真引擎 (V2.3)

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![UI: NiceGUI](https://img.shields.io/badge/UI-NiceGUI-orange.svg)](https://nicegui.io/)
[![Architecture: Intent--Driven](https://img.shields.io/badge/Architecture-Intent--Driven-green.svg)]()

> **“不只是计算，更是高保真、可回溯的战斗仿真。”**

这是一个为《原神》深度玩家与数值分析师设计的、基于**意图驱动 (Intent-Driven)** 与 **场景中心化 (Scene-Centric)** 架构的战斗仿真引擎。它能够高保真地模拟物理位移、动作时间轴、复杂的元素附着状态机，并提供直观的 Web 图形界面。

---

## 🌟 核心特性

*   **🎬 动作状态机 (ASM)**: 高精度模拟动画帧、判定点 (Hit-frames) 以及动作取消窗口 (Cancel Windows)。
*   **📐 场景化物理**: 具备真实坐标系 (X, Z) 的空间引擎，支持圆柱、长方体、扇形等多种几何碰撞检测。
*   **🧪 深度元素论**: 严格遵循附着论，完美支持元素消耗、叠加、反应优先级及 ICD 计数器。
*   **🧠 意图驱动架构**: 物理逻辑与交互逻辑解耦。UI 传输“意图”（如“点按/长按”），引擎自动产出物理动作块。
*   **📊 双数据库动力**: 
    *   **核心资产库 (MySQL)**: 维护全量角色、武器、圣遗物权威静态数据。
    *   **实时回溯库 (SQLite)**: 每一帧状态流式写入，支持秒级回溯分析与 DPS 曲线生成。
*   **🎨 现代 Web UI**: 基于 NiceGUI 打造的响应式面板，支持动态 Inspector 参数实时编辑。

---

## 🛠️ 技术栈

*   **语言**: Python 3.13+
*   **前端框架**: NiceGUI (基于 FastAPI + Vue.js + Tailwind)
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
.\genshin_damage_calculation\Scripts\python.exe main.py
```
程序启动后，会自动打开默认浏览器进入 **仿真工作台**。

---

## 📖 文档索引

为了更好的开发体验，请参考 `docs/` 下的结构化文档：
*   **[架构概览](./docs/architecture/system/架构概览.md)**: 了解 V2.3 系统的核心分层与执行流。
*   **[角色适配指南](./docs/architecture/system/角色子类适配指南.md)**: 如何根据 V2.3 规范接入新角色。
*   **[日志系统架构](./docs/architecture/system/日志系统架构.md)**: 结构化日志的设计与 UI 接入标准。
*   **[开发维护](./docs/development/)**: 包含测试指南与重构记录。

---

## 🏗️ 项目现状

目前已完成阶段二“战术编排”的开发，实现了从 UI 配置到后端仿真的全链路闭环。下一阶段将聚焦于“战果复盘”与“批量处理设计”。

---
*版本: v2.3.0-Stable*
*日期: 2026-02-09*
