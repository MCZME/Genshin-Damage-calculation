# GitHub & 项目开发流程规范

本文档定义了人类开发者与 AI 代理在本项目中的协作模式和版本控制流程。

## 1. 分支管理 (Branching Model)

项目采用简化的分支策略，以 `main` 为核心：

*   **`main` 分支**: 唯一的长效分支，生产与开发的总轴。
*   **功能分支 (feature/*)**:
    *   **命名**: `feature/描述`（例如 `feature/context-manager`）。
    *   **职责**: 单一 Issue 的实现。
*   **修复分支 (fix/*)**:
    *   **命名**: `fix/描述`（例如 `fix/formula-bug`）。

### 分支生命周期与清理
1.  **切出**: 始终从最新的 `main` 切出。
2.  **合并**: 通过 Pull Request 合并回 `main`。
3.  **同步与删除 (清理)**: PR 合并后，开发者必须在本地执行：
    ```bash
    git checkout main
    git pull && git fetch --prune
    git branch -d <feature-branch-name>
    ```

## 2. 提交与 PR 规范

### 提交消息 (Commit Messages)
采用 Conventional Commits 格式，且描述部分必须使用**中文**:
*   **格式**: `<type>: <中文描述> #<ID>`
*   **示例**: `feat: 增加 SimulationContext 的健康检查逻辑 #9`

### Pull Request (PR)
*   **语言**: 标题和描述均使用中文。
*   **基准**: Base 分支设为 `main`。
*   **自动关闭**: 描述中必须包含 `Closes #ID`。由于合并目标是 `main`，GitHub 将在合并后自动关闭关联 Issue。

## 3. 人机协同流程 (Human-AI Collaboration)

任务执行遵循“对齐-执行-验证”三部曲：

1.  **意图对齐 (Alignment)**:
    *   **人类角色**: 提出需求/Issue。
    *   **AI 角色**: 产出中文技术方案，明确改动点。
2.  **迭代执行 (Iteration)**:
    *   **AI 角色**: 负责“编写测试 -> 实现逻辑 -> 运行 Lint”。
3.  **结果沉淀 (Persistence)**:
    *   **AI 角色**: 生成符合规范的中文提交和 PR。

## 4. 关键交接标签 (Key Handover Labels)

1.  **`status:plan-pending`**: 等待方案对齐。
2.  **`status:implemented`**: 逻辑实现完成，PR 已开启。

## 5. 环境与工具
*   **Lint**: Ruff。
*   **Test**: Pytest / 项目自定义仿真。
