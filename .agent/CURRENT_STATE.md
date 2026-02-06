# Current Development State

**Last Updated:** 2026-02-06
**Status:** 🛠️ In Progress (核心引擎命名规范化已完成)

## 📝 Recent Context
- **Last Action:** 彻底移除了 `Damage` 类中的驼峰命名兼容层，并同步适配了 `DamageSystem` 和 `ReactionSystem` (Issue #21, PR #22)。
- **Branch:** `main` (待 PR 合并)
- **Focus:** 核心引擎 `snake_case` 标准化。
- **Improvements:**
    - **Damage 类**: 移除了所有 `@property` 兼容层，统一使用 `damage_multiplier`, `set_panel` 等符合 PEP 8 的接口。
    - **系统适配**: `core/systems/` 下的核心系统已完成对新 API 的适配。

## 📌 Critical Knowledge
- **重大变更**: 移除兼容层后，所有尚未重构的角色和武器文件（仍使用驼峰命名者）将会报错。这是为了强制项目完全迁移至新标准。
- **开发流**: 启用了 `skill-genshin-dev-flow`，严格遵循 Issue -> Proposal -> Implementation 的 SOP。

## 🔜 Next Steps
1.  **伤害系统评估**: 对 `core/systems/damage_system.py` 进行深度评估，优化 `Calculation` 类的逻辑结构和扩展性。
2.  **全量角色适配**: 启动批量重构，修复因 `Damage` API 变更导致的角色模块报错。
3.  **最终仿真运行**: 待系统重构稳定后，恢复 `test.py` 的全量测试。

