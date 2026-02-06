# Genshin Damage Calculation - 测试指南

本项目采用基于 **Pytest** 的分层测试架构，旨在通过高复用性的测试夹具（Fixtures）和参数化验证，确保伤害计算引擎的数值正确性与逻辑稳定性。

## 1. 测试架构概览

测试目录结构如下：

```text
tests/
├── conftest.py             # 全局配置与公共 Fixtures (Mock 对象、系统初始化)
├── unit/                   # 单元测试：验证最小逻辑单元（如公式、系统方法）
│   └── systems/            # 各核心系统的单元测试
└── integration/            # 集成测试：验证多系统交互（如攻击->反应->伤害全链路）
```

## 2. 核心组件 (Fixtures)

在 `tests/conftest.py` 中定义了以下核心 Fixtures，编写新测试时可直接通过参数请求：

*   `event_engine`: 提供一个干净的 `EventEngine` 实例。
*   `damage_system`: 一个已初始化的 `DamageSystem` 实例。
*   `source_entity`: 一个预设好的攻击者 Mock 对象 (Lv.90, 1000攻击力)。
*   `target_entity`: 一个预设好的目标 Mock 对象 (Lv.90, 500防御, 10%通用抗性)。
*   `create_damage_context`: 工厂函数，用于快速创建 `DamageContext`。

## 3. 编写测试规范

### 单元测试示例 (Unit Test)
使用 `@pytest.mark.parametrize` 进行批量数值验证：

```python
@pytest.mark.parametrize("res, expected_mult", [
    (10.0, 0.9),    # 10% 抗性 -> 0.9 乘数
    (-20.0, 1.1),   # 负抗性收益
])
def test_resistance_logic(pipeline, ctx, res, expected_mult):
    ctx.target.current_resistance['火'] = res
    pipeline._calculate_def_res(ctx)
    assert ctx.stats['抗性区系数'] == pytest.approx(expected_mult)
```

### 编写建议
1.  **Mock 优先**：单元测试应尽量使用 `MockAttributeEntity` 而非真实角色类，以保持测试速度和独立性。
2.  **断言精度**：涉及浮点数计算时，务必使用 `pytest.approx` 并指定精度。
3.  **配置隔离**：如需修改全局配置（如关闭暴击），请使用 `Config.set()` 且注意不要影响其他测试用例（Fixture 已默认处理部分初始化）。

## 4. 运行测试

在项目根目录下执行：

```bash
# 运行所有测试
.\genshin_damage_calculation\Scripts\python.exe -m pytest

# 运行特定测试文件并显示详细输出
.\genshin_damage_calculation\Scripts\python.exe -m pytest tests/unit/systems/test_damage_pipeline.py -v
```

## 5. 持续集成与标准
*   所有新功能或 Bug 修复必须附带对应的单元测试。
*   重构代码后，必须确保 `tests/unit/systems/test_damage_pipeline.py` 全量通过以保证核心计算无回归。
