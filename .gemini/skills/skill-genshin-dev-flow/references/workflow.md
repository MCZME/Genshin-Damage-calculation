# GitHub & 项目开发流程规范

本文档定义了人类开发者与 AI 代理在本项目中的协作模式和版本控制流程。

## 1. 分支管理 (Branching Model)

项目采用精细化的分支管理策略，明确 `dev` 为主要集成环境：

*   **`main` 分支**: 生产环境，仅通过 `dev` 的合并进行更新。
*   **`dev` 分支**: 开发主轴，所有功能的基准。
*   **功能分支 (feature/*)**:
    *   **命名**: `feature/描述`（例如 `feature/context-manager`）。
    *   **职责**: 单一 Issue 的实现。
*   **修复分支 (fix/*)**:
    *   **命名**: `fix/描述`（例如 `fix/formula-bug`）。

### 分支生命周期与清理
1.  **切出**: 始终从最新的 `dev` 切出。
2.  **合并**: 通过 PR 合并回 `dev`。
3.  **同步与删除 (清理)**: PR 合并后，开发者必须在本地执行：
    ```bash
    git checkout dev
    git pull && git fetch --prune
    git branch -d <feature-branch-name>
    ```

## 2. 提交与 PR 规范

### 提交消息 (Commit Messages)
采用 Conventional Commits 格式，且**描述部分必须使用中文**:
*   **格式**: `<type>: <中文描述> #<ID>`
*   **示例**: `feat: 优化 SimulationContext 的上下文管理器实现 #7`
*   **常用类型**: `feat`, `fix`, `refactor`, `test`, `docs`, `perf`, `chore`

### Pull Request (PR)
*   **语言**: 标题和描述均使用**中文**。
*   **基准**: Base 分支设为 `dev`。
*   **自动化**: 描述中必须包含 `Closes #ID` 以便自动关单。

## 3. 人机协同流程 (Human-AI Collaboration)

任务执行遵循“对齐-执行-验证”三部曲：

1.  **意图对齐 (Alignment)**:
    *   **人类角色**: 提出需求/Issue。
    *   **AI 角色**: 扫描全局，产出**技术方案 (Technical Proposal)**（中文）。
    *   **关键点**: AI 必须明确列出受影响的 `System`、`EventHandler` 及新增的 `EventType`。

2.  **迭代执行 (Iteration)**:
    *   **AI 角色**: 负责“测试先行 -> 逻辑实现 -> 自动化验证 -> Lint 修复”的闭环。
    *   **人类角色**: 负责 **GUI 视觉与交互验证**，并根据代码审美进行即时纠偏。

3.  **结果沉淀 (Persistence)**:
    *   **AI 角色**: 生成符合规范的 Commit Message 和 PR。
    *   **协同**: 共同更新 `GEMINI.md`。

## 4. Issue 开发标准作业程序 (SOP)

### 第一阶段：启动与方案对齐
1.  **状态流转**: 在 GitHub Projects 中将卡片移动至 `Todo`。
2.  **分支管理**: 基于 `dev` 分支创建新分支 `feature/ID-brief`。
3.  **技术提案**: 提交一份简短的方案草案（中文）。

### 第二阶段：测试驱动
1.  **复现/定义**: 在 `tests/` 目录下编写测试用例。
2.  **执行**: 运行测试，确认当前状态下测试失败。

### 第三阶段：实现与验证
1.  **编码**: 严格执行 `references/standards.md` 中的规范。
2.  **自测**: 运行测试确保通过。
3.  **合规性检查**: 运行 `ruff check .`。

### 第四阶段：交接与评审
1.  **提交**: 遵循中文提交规范。
2.  **PR**: 开启指向 `dev` 的 PR。

## 5. 关键交接标签 (Key Handover Labels)

1.  **`status:plan-pending`**:
    *   **何时添加**: Issue 进入 `Backlog` 或 `Todo`。
    *   **何时删除**: 方案对齐完成，进入编码。
2.  **`status:implemented`**:
    *   **何时添加**: 代码开发完成并开启 PR。
    *   **何时删除**: PR 合并，准备关闭 Issue。

## 6. 环境与工具
*   **Lint**: Ruff。
*   **Test**: Pytest / 项目自定义仿真。
*   **AI Context**: 持续维护 `GEMINI.md`。