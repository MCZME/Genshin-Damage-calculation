# Current Development State

**Last Updated:** 2026-02-06
**Status:** 🛠️ In Progress (正在进行核心引擎重构)

## 📝 Recent Context
- **Last Action:** 统一了护盾、生命与能量系统的属性提取逻辑，并修复了关键导入错误 (Issue #14)。
- **Branch:** `refactor/technical-debt-cleanup`
- **Focus:** 扩展 `AttributeCalculator` 工具类并重构相关子系统。
- **Improvements:**
    - **属性计算标准化**: 在 `AttributeCalculator` 中新增了护盾强效、元素充能、治疗/受治疗加成的计算方法。
    - **系统集成**: 完成了 `ShieldSystem`、`HealthSystem` 和 `EnergySystem` 的重构，彻底移除了对属性字典键名的硬编码。
    - **架构兼容性修复**: 
        - 将 `core/Team.py` 重命名为 `core/team.py`，解决跨平台导入的大小写敏感问题。
        - 修复了 `artifact/ArtifactSetEffect.py` 中指向已废弃或拼写错误模块（如 `ArtfactEffect`）的导入路径。
    - **工具函数增强**: 在 `stat_modifier.py` 中补全了 `ElementalMasteryBoostEffect` 工厂函数。

## 📌 Critical Knowledge
- **核心工具**: `core/systems/utils.py:AttributeCalculator` 是所有面板属性提取的唯一标准入口。
- **命名规范**: 核心模块统一使用 `snake_case`（如 `team.py`, `tool.py`），角色类中使用 `from core.team import Team`。
- **环境要求**: 必须使用虚拟环境 `.\genshin_damage_calculation\Scripts\python.exe` 运行脚本，并在 PowerShell 中使用 `;` 作为命令分隔符。

## 🔜 Next Steps
1.  **DamageSystem 深度重构**: 进一步清理 `DamageSystem` 中冗余的计算逻辑。
2.  **兼容层构建**: 考虑建立 `core/BaseObject.py` 兼容层，以平滑迁移旧的角色定义代码。
3.  **仿真恢复**: 逐步修复模块间依赖，直至 `python test.py` 能够重新进行全量仿真验证。