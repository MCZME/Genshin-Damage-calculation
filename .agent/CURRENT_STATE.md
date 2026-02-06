# Current Development State

**Last Updated:** 2026-02-06
**Status:** 🛠️ In Progress (正在进行核心引擎重构)

## 📝 Recent Context
- **Last Action:** 删除了 `core/base_event_handler.py` 并清理了相关引用 (Issue #14)。
- **Branch:** `refactor/technical-debt-cleanup`
- **Focus:** 核心引擎架构规范化，移除所有不必要的遗留处理逻辑。
- **Improvements:**
    - **模块清理**: 彻底删除了 `core/base_event_handler.py`，并清理了 `main.py` 中的订阅逻辑。
    - **BaseEntity 迁移**: 成功将 `BaseEntity` 迁移至 `core/entities/base_entity.py`。
    - **去兼容层**: 移除了 `base_class.py`, `map.py` 等所有 shim 文件。
    - **属性标准化**: 护盾、生命、能量、伤害子系统已完成 `AttributeCalculator` 的集成。

## 📌 Critical Knowledge
- **核心逻辑**: `core` 目录现在只包含纯粹的引擎逻辑，不再持有具体的 UI 事件处理器或遗留兼容别名。
- **标准路径**: `BaseEntity` 导入路径为 `core.entities.base_entity.BaseEntity`。

## 🔜 Next Steps
1.  **自动化迁移脚本**: 编写脚本批量更新 `character/` 目录下所有角色文件的 `BaseObject` 引用和导入路径。
2.  **仿真恢复**: 尝试修复 `test.py` 或创建新的全量集成测试。
3.  **DataHandler 重构**: 在下一阶段对 `dataHandler` 进行统一清理。
