# GitHub & 开发工作流规范

本文档定义了开发者（包括人类与 AI）在项目中的具体操作流程、命令参考及协作标准。

## 1. 上下文感知 (Context Awareness) [CRITICAL]

任何开发活动的起点必须是获取当前的最新状态，以避免冲突和重复劳动。

*   **操作命令**: `python .gemini/skills/skill-genshin-dev-flow/scripts/fetch_context.py`
*   **关注重点**: 
    - 当前 Git 分支与未提交更改。
    - 关联 Issue 的编号及当前状态标签。

## 2. Issue 开发 SOP (Standard Operating Procedure)

开发者在处理 Issue 时必须经历的五个阶段：

### 阶段 0: 启动 (Initiate)
1.  **认领**: 使用 `gh issue edit <ID> --assignee @me`。
2.  **打标**: 根据任务性质添加 `type:*` 和 `status:plan-pending`。
3.  **看板**: 运行 `python .gemini/skills/skill-genshin-dev-flow/scripts/sync_board.py <ID> Todo`。

### 阶段 1: 方案对齐 (Align)
1.  **切分支**: `git checkout -b feature/描述`。
2.  **提交提案**: 输出 Technical Proposal（中文），包含：**Impact** (影响范围), **Logic** (逻辑变动), **Tests** (测试计划)。
3.  **确认**: 等待方案确认后方可进入下一阶段。

### 阶段 2: 测试先行 (Test-First)
1.  **编写测试**: 在 `tests/` 下编写脚本或直接修改 `test.py`。
2.  **验证失败**: 运行 `python test.py` 确保当前状态下测试无法通过。

### 阶段 3: 实现与验证 (Implement & Verify)
1.  **编码**: 遵循 `references/standards.md`。
2.  **更新看板**: 同步卡片至 `In Progress`，删除 `status:plan-pending`。
4.  **Lint**: 虚拟环境运行 `ruff` 检查提交文件。

### 阶段 4: 交付与存档 (Handover)
1.  **提交代码**: 遵循 Conventional Commits (中文)。格式：`<type>: 描述 #ID`。
2.  **开启 PR**: 开启指向 `main` 的 PR，添加 `status:implemented`。

## 3. 分支与提交规范

### 分支管理
- 永远从 `main` 切出，通过 PR 合并回 `main`。
- 合并后及时删除本地分支：`git branch -d <name>`。

### 提交消息
- **格式**: `<type>: <中文描述> #<ID>`
- **Type 推荐**: `feat`, `fix`, `refactor`, `perf`, `docs`, `chore`, `test`。

## 4. 环境与工具命令
- **运行入口**: `python main.py`
- **上下文获取**: `python .gemini/skills/skill-genshin-dev-flow/scripts/fetch_context.py`
- **看板同步**: `python .gemini/skills/skill-genshin-dev-flow/scripts/sync_board.py <ID> <Column>`
