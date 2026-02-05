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
    - **基准分支**: 必须从 `dev` 切出: `git checkout dev && git pull && git checkout -b <branch-name>`。
- **方案对齐**: 编码前输出 Technical Proposal（中文）。

### 2. 实施阶段 (Implementation)
- **启动开发**: 方案确认后，将卡片移至 `In Progress`，删除 `status:plan-pending`。
- **测试先行**: 修改逻辑前，在 `tests/` 下编写脚本。
- **提交规范**: 
    - **语言**: 提交说明必须使用 **中文**。
    - **格式**: `<type>: 简短描述 #ID`（例如：`feat: 实现伤害计算核心逻辑 #5`）。
- **Lint**: 提交前运行 `ruff check .`。

### 3. 完成与交接 (Handover)
- **PR 流程**: 
    - 开启 PR 指向 `dev` 分支，标题和正文使用 **中文**。
    - 正文包含 `Closes #ID`。
- **打标并移动**: 运行 `gh issue edit <ID> --add-label "status:implemented"`，并将卡片移至 `Review`。

### 4. 收尾清理 (Post-Merge Cleanup)
- **同步与删除**: 当 PR 被合并后，执行以下动作：
    1. 切换回基准分支: `git checkout dev`。
    2. 同步远程状态: `git pull && git fetch --prune`。
    3. 删除本地分支: `git branch -d <feature-branch>`。
- **归档**: 确认 Issue 已关闭，删除 `status:implemented` 标签。
- **文档**: 更新 `GEMINI.md`。