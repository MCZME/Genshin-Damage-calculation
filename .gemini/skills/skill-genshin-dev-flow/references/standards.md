# 开发规范 (Development Standards)

本文档旨在统一项目开发的代码风格、命名约定、类型系统及工程实践，确保人类开发者与 AI 代理（如 Gemini, Antigravity）能够高效协作。

## 1. 代码风格 (Code Style)

*   **PEP 8**: 严格遵守 Python 标准 PEP 8。
*   **格式化工具**: 
    *   推荐使用 `Ruff` 或 `Black` 进行代码格式化。
    *   行宽限制：88 字符。
    *   引号：统一使用双引号 `"`。
*   **Import 排序**: 
    *   使用 `isort` 或 `Ruff` 排序。
    *   顺序：标准库 -> 第三方库 -> 本地项目库。
*   **注释规范**: 
    *   **Docstrings**: 所有类和公共方法必须包含 Docstring（推荐 Google Style）。
    *   **Logic Comments**: 解释“为什么”这么写，而非“在做什么”。

## 2. 命名约定 (Naming Conventions)

*   **类名**: `PascalCase` (如 `DamageCalculator`)。
*   **变量与函数**: `snake_case` (如 `calculate_base_damage`)。
*   **常量**: `UPPER_CASE` (如 `MAX_ELEMENTAL_MASTERY`)。
*   **模块与文件**: 
    *   **新文件**: 必须使用 `snake_case` (如 `artifact_handler.py`)。
    *   **旧文件**: 历史遗留的 `PascalCase` 文件名暂时保持，但在重构时应逐步迁移。
*   **私有成员**: 使用单下划线前缀 `_internal_method`。

## 3. 类型系统 (Type System)

*   **强制类型标注**: 所有函数签名必须显式标注参数和返回值类型。
    *   *Bad*: `def calc(atk, rate):`
    *   *Good*: `def calc(atk: float, rate: float) -> float:`
*   **避免 Any**: 尽量使用 `Union`, `Optional` 或具体的类名。
*   **数据模型**: 复杂的数据结构优先使用 `dataclasses` 或 `Pydantic`。

## 4. 异常处理 (Error Handling)

*   **显式捕获**: 严禁使用 `try: ... except: pass`。
*   **自定义异常**: 继承 `core.BaseObject` 或特定基础异常类，定义具有业务含义的异常。
*   **卫语句 (Guard Clauses)**: 优先处理异常分支并提前返回，减少代码缩进。

## 5. 项目工程实践 (Engineering Practices)

*   **日志**: 严禁在生产代码中使用 `print()`。必须使用 `core.Logger`。
*   **配置**: 严禁硬编码。所有可调参数必须通过 `core.Config` 管理。
*   **测试**: 
    *   使用 `pytest` 编写测试用例。
    *   核心计算逻辑（公式、反应倍率）必须实现 100% 的单元测试覆盖。
*   **AI 协作**:
    *   修改代码前，先通过 `read_file` 确认上下文。
    *   复杂的重构应分步提交，并附带测试验证。

---
*Last Updated: 2026-02-04*
