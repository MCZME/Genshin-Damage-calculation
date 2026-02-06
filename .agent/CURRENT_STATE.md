# Current Development State

**Last Updated:** 2026-02-06
**Status:** 🛠️ In Progress

## 📝 Recent Context
- **Last Action:** Cleaned up technical debt and aligned core engine systems (Issue #14).
- **Branch:** `refactor/technical-debt-cleanup`
- **Focus:** Extracted `AttributeCalculator` for unified attribute retrieval; refactored `DamageSystem` and `HealthSystem`.
- **Improvements:** 
    - Resolved case-sensitivity issue for `core/tool.py`.
    - Enhanced `BaseEntity` to support explicit context passing.
    - Added unit test `tests/test_core_refactor_unit.py` to verify core logic.

## 📌 Critical Knowledge
- **New Utility:** `core/systems/utils.py:AttributeCalculator` should be used for all base attribute (ATK, HP, DEF) calculations.
- **Entity Init:** `BaseEntity` now accepts an optional `context` argument to avoid singleton dependency.
- **File Naming:** Core utility is renamed to `core/tool.py` (lowercase) for consistency.
- **Environment:** Use `.\genshin_damage_calculation\Scripts\python.exe` for all commands.

## 🔜 Next Steps
1.  Verify full engine compatibility with refactored `AttributeCalculator`.
2.  Refactor `ShieldSystem` and other systems to use `AttributeCalculator`.
3.  Perform full regression testing via `python test.py` after fixing existing module issues.