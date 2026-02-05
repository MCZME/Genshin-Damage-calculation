# GitHub & 项目开发流程规范

本文档定义了人类开发者与 AI 代理在本项目中的协作模式和版本控制流程。

## 1. 分支管理 (Branching Model)

项目采用类 GitHub Flow 的管理模式，明确 `dev` 为主要集成环境：

*   **`main` 分支**: 稳定版本，受保护分支。仅接受来自 `dev` 的合并。
*   **`dev` 分支**: 开发集成中心。所有 `feature` 和 `fix` 分支的基准。
*   **`feature/` 分支**: 功能开发（从 `dev` 切出）。
*   **命名规范**: `feature/issue-ID-brief` 或 `fix/issue-ID-brief`。
*   **生命周期**: 任务开始时创建，PR 合并后立即删除本地与远程分支。

## 2. 人机协同流程 (Human-AI Collaboration)

任务执行遵循“对齐-执行-验证”三部曲：

1.  **意图对齐 (Alignment)**:
    *   **人类角色**: 提出需求/Issue，设定业务边界和架构约束。
    *   **AI 角色**: 使用 `codebase_investigator` 扫描全局，产出**技术方案 (Technical Proposal)**。
    *   **关键点**: AI 必须明确列出受影响的 `System`、`EventHandler` 及新增的 `EventType`，得到人类确认后方可开始编码。

2.  **迭代执行 (Iteration)**:
    *   **AI 角色**: 负责“测试先行 -> 逻辑实现 -> 自动化验证 -> Lint 修复”的闭环。
    *   **人类角色**: 负责 **GUI 视觉与交互验证**（由于 AI 无法直接观测 GUI 表现），并根据代码审美进行即时纠偏。

3.  **结果沉淀 (Persistence)**:
    *   **AI 角色**: 生成符合规范的 Commit Message 和 PR 描述。
    *   **协同**: 共同更新 `GEMINI.md` 或相关设计文档，确保项目架构理解在 AI 会话间保持连续。

## 3. Issue 开发标准作业程序 (SOP)

当开始处理一个 Issue 时，无论是 AI 还是人类开发者，都必须遵循以下流程：

### 第一阶段：启动与方案对齐 (Start & Align)
1.  **状态流转**: 在 GitHub Projects 中将卡片移动至 `In Progress (AI/Human)`，并确保已打上正确的 `layer:` 和 `domain:` 标签。
2.  **深度探索**: 使用 `codebase_investigator` 或 `search_file_content` 定位核心逻辑点。
3.  **技术提案**: **(AI 必做)** 在开始修改代码前，提交一份简短的方案草案，列出：
    *   **Impact**: 受影响的文件及函数。
    *   **Logic**: 核心逻辑改动点的伪代码或思路。
    *   **Events**: 是否需要新增或修改 `EventType`。
4.  **分支管理**: 基于 `dev` 分支创建新分支 `feature/issue-ID`。

### 第二阶段：测试驱动 (Test-First)
1.  **复现/定义**: 在 `tests/` 目录下编写测试用例。如果是 Bug，确保测试能触发该 Bug；如果是 Feature，确保测试覆盖了预期的边界条件。
2.  **执行**: 运行测试，确认当前状态下测试失败（Red 阶段）。

### 第三阶段：实现与验证 (Implement & Verify)
1.  **编码**: 严格执行 `docs/DEVELOPMENT_STANDARDS.md` 中的规范。
2.  **自测**: 运行测试确保通过（Green 阶段）。
3.  **合规性检查**: 运行 `ruff check` 确保无代码风格问题。

### 第四阶段：交接与评审 (Handover)
1.  **提交**: 使用 Conventional Commits 规范提交代码。
2.  **同步**: 更新 `GEMINI.md` 或相关架构文档。
3.  **UI 验证**: 如果涉及界面，移动卡片至 `Review & GUI Test` 并通知人类进行手动测试。

## 4. AI 代理开发流程 (Agent Workflow - 简略版)

## 4. 关键交接标签 (Key Handover Labels)

进度主要由看板列标识，标签仅用于标识特定的协作状态：

1.  **`status:plan-pending`**:
    *   **何时添加**: Issue 进入 `Backlog` 或 `Todo`。
    *   **何时删除**: 方案对齐完成，准备进入 `In Progress` 编码。
2.  **`status:implemented`**:
    *   **何时添加**: 代码开发与初步自测完成，移入 `Review & GUI Test`。
    *   **何时删除**: Review 通过，准备关闭 Issue。

## 5. 提交与合并规范 (Commit & PR)

### 提交消息
遵循 [Conventional Commits](https://www.conventionalcommits.org/)，并**强制要求包含 Issue 编号**:
*   **格式**: `<type>: <description> #<IssueID>`
*   **示例**: `feat: add elemental reaction logic #42`
*   **常用类型**: 
    *   `feat`: 新功能
    *   `fix`: 修复
    *   `refactor`: 重构
    *   `test`: 测试相关
    *   `docs`: 文档
    *   `perf`: 性能优化

### Pull Request 门禁
*   使用 `Closes #<IssueID>` 关键字确保 PR 合并后 Issue 自动关闭。

## 5. 环境与工具
*   **Lint**: Ruff (速度快且集成度高)。
*   **Test**: Pytest / 项目自定义 batch 仿真。
*   **AI Context**: 持续维护 `GEMINI.md` 以确保 AI 对系统架构的理解不产生偏差。