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
- **分支管理**: 
    - **命名规范**: 必须使用 `type/描述` 格式（例如：`feature/context-manager`）。
    - **基准分支**: 必须从 `main` 切出: `git checkout main && git pull && git checkout -b <branch-name>`。
- **方案对齐**: 编码前输出 Technical Proposal（中文）。

### 2. 实施阶段 (Implementation)
- **启动开发**: 方案确认后，将卡片移至 `In Progress`，删除 `status:plan-pending`。
- **测试先行**: 修改逻辑前，在 `tests/` 下编写脚本。
- **提交规范**: 
    - **语言**: 提交说明必须使用 **中文**。
    - **格式**: `<type>: 简短描述 #ID`（例如：`feat: 实现伤害计算核心逻辑 #5`）。
- **提交与同步 (Commit & Sync)**:
    1. **Git Commit**: 必须包含 Issue ID。
    2. **自动汇报**: 每次 Commit 后，检查并同步更新 Issue Checklist。
- **Lint**: 提交前运行 `ruff check .`。

### 3. 完成与交接 (Handover)
- **打标并移动**: 开发完成后，运行 `gh issue edit <ID> --add-label "status:implemented"`，并将卡片移至 `Review`。
- **PR 流程**: 
    - 开启 Pull Request 指向 **`main`** 分支。
    - PR 标题应包含 Issue ID，描述中使用 `Closes #ID`。
- **发布足迹**: 发送 `gh issue comment <ID> --body "🚀 [Progress]: 已完成核心改动，PR 已开启。"`。

### 4. 收尾清理 (Post-Merge Cleanup)
- **同步与删除**: 当 PR 被合并后，执行以下动作：
    1. 切换回基准分支: `git checkout main`。
    2. 同步远程状态: `git pull && git fetch --prune`。
    3. 删除本地分支: `git branch -d <feature-branch>`。
- **归档**: 确认 Issue 已自动关闭，删除所有状态标签。
- **文档**: 更新 `GEMINI.md`。

## 参考指南
- 详细协作流程见 [workflow.md](references/workflow.md)。
- 项目管理与标签定义见 [management.md](references/management.md)。
