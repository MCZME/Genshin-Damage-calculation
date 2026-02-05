---
name: skill-genshin-dev-flow
description: 强制执行原神伤害计算器项目的开发标准和 GitHub 自动化工作流。当你需要认领 Issue、提交代码或同步项目进度时激活此技能。
---

# Skill: Genshin Dev Flow

作为项目的主导 AI 开发者，你必须严格遵循本项目的一系列 SOP 和自动化规范。

## 核心职责

### 1. 任务启动 (Task Start)
- **强制检查**: 任何编码工作前必须确认已关联 GitHub Issue。
- **里程碑**: 必须关联当前活跃里程碑。
- **分支管理**: 从 `main` 切出描述性分支（`feature/描述`）。
- **自动化流转**: 
    1. 认领并初始化: `gh issue edit <ID> --add-label "status:plan-pending" --assignee @me --milestone "<Milestone>"`。
    2. **看板同步**: 运行 `python .gemini/skills/skill-genshin-dev-flow/scripts/sync_board.py <ID> Todo`。
- **方案对齐**: 编码前输出 Technical Proposal（中文）。

### 2. 实施阶段 (Implementation)
- **启动开发**: 方案确认后，运行 `python .gemini/skills/skill-genshin-dev-flow/scripts/sync_board.py <ID> "In Progress"`，并删除 `status:plan-pending` 标签。
- **测试先行**: 修改逻辑前，在 `tests/` 下编写脚本。
- **提交规范**: 提交信息使用中文，格式 `<type>: 简短描述 #ID`。每次提交后同步 Issue Checklist。

### 3. 完成与交接 (Handover)
- **看板同步**: 开发完成开启 PR 后，运行 `gh issue edit <ID> --add-label "status:implemented"`，并运行 `python .gemini/skills/skill-genshin-dev-flow/scripts/sync_board.py <ID> Review`。
- **PR 目标**: 始终指向 `main`。

### 4. 收尾清理 (Post-Merge Cleanup)
- **同步与删除**: 当 PR 被合并后，切换回 `main` 并删除本地分支。
- **归档**: 确认 Issue 关闭，清理 `status:implemented` 标签，运行 `python .gemini/skills/skill-genshin-dev-flow/scripts/sync_board.py <ID> Done`。