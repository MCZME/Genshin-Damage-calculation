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
    git checkout main ; git pull ; git fetch --prune ; git branch -d <feature-branch-name>
    ```

## 2. 提交与 PR 规范

### 提交消息 (Commit Messages)
采用 Conventional Commits 格式，且**正文必须使用中文**:
*   **格式**: `<type>: <中文描述> #<ID>`
*   **示例**: `feat: 增加 SimulationContext 的健康检查逻辑 #9`

### Pull Request (PR)
*   **语言**: 标题和描述均使用中文。
*   **基准**: Base 分支设为 `main`。
*   **自动关闭**: 描述中必须包含 `Closes #ID`。

## 3. Issue 开发标准作业程序 (SOP)

当开始处理一个 Issue 时，必须遵循以下流程：

### 第一阶段：启动与方案对齐 (Start & Align)
1.  **状态流转**: 在 GitHub Projects 中将卡片移动至 `Todo`。
2.  **分支管理**: 基于 `main` 分支创建新分支 `feature/描述`。
3.  **技术提案**: 提交一份简短的方案草案（中文），明确 Impact、Logic、Events。

### 第二阶段：测试驱动 (Test-First)
1.  **复现/定义**: 在 `tests/` 目录下编写测试用例。
2.  **执行**: 运行测试，确认当前状态下测试失败。

### 第三阶段：实现与验证 (Implement & Verify)
1.  **编码**: 严格执行 `references/standards.md` 中的规范。
2.  **自测**: 运行测试确保通过。
3.  **合规性检查**: 运行 `ruff check .`。

### 第四阶段：交接与评审 (Handover)
1.  **提交**: 遵循中文提交规范。
2.  **PR**: 开启指向 `main` 的 PR，描述包含 `Closes #ID`。
3.  **同步**: 更新任务清单。

## 4. 关键交接标签 (Key Handover Labels)

1.  **`status:plan-pending`**: 等待方案对齐。
2.  **`status:implemented`**: 逻辑实现完成，PR 已开启。

## 5. 环境与工具
*   **Lint**: Ruff。
*   **Test**: Pytest / 项目自定义仿真。
*   **AI Context**: 持续维护 `GEMINI.md`。