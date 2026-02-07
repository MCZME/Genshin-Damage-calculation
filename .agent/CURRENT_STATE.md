# Current Development State

**Last Updated:** 2026-02-07
**Status:** 🛠️ In Progress (场景实体化架构重构 #26)

## 📝 Recent Context
- **Last Action:** 完成了《场景化实体引擎》、《物理碰撞与战斗反馈》、《元素附着与ICD机制》、《数据契约与攻击定义》四个核心架构文档的编写与对齐。
- **Branch:** `feat/scene-entity-25` (注：此分支将涵盖 #26 的重构工作)
- **Focus:** 实现 CombatSpace 2D 几何判定模型与多实体广播机制。

## 📌 Critical Knowledge
- **空间模型**: 采用 2D (X, Z) 连续坐标判定。支持圆、矩形、扇形 AOE。
- **位移规则**: 仅支持技能触发的自驱动位移。忽略实体间推挤交互。
- **索敌系统**: CombatSpace 内置基于 AttackConfig 的目标自动选择逻辑。
- **数据驱动**: 核心参数（ICD标签、AOE形状、衰减序列）将全面指导附着与物理判定。

## 🔜 Next Steps
1.  **创建核心集成测试**: 在 `tests/integration/test_combat_space_logic.py` 中模拟多实体范围伤害与索敌场景。
2.  **定义 CombatEntity 接口**: 扩展 `BaseEntity`，引入 `handle_damage` 与 `apply_aura` 协议。
3.  **实现 CombatSpace**: 开发 2D 几何检索引擎与实体管理器。
4.  **重构 DamageSystem**: 将原本的 1-on-1 派发改造为 CombatSpace 广播模式。
