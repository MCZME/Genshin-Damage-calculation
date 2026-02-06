# 项目管理规范

本文档定义了如何使用 GitHub Issues, Milestones 和 Projects 来管理开发进度。

## 1. Issue 管理

所有开发活动必须关联一个 Issue。

### 1.1 Issue 模板要求
所有 Issue 必须通过 `.github/ISSUE_TEMPLATE/` 中定义的模板创建：
*   **Bug (`bug_report.yml`)**: 必须包含游戏版本、角色配置（等级/命座）、复现步骤以及预期结果。
*   **Feature (`feature_request.yml`)**: 必须链接到相关的数据来源或计算公式说明。
*   **Refactor (`refactor.yml`)**: 必须说明重构动机（痛点）、影响范围，并包含标准的执行计划清单。

### 1.2 标签体系与交接状态 (Labels & Status)

标签用于标识任务性质及关键的协作交接节点：

*   **工作类型 (Type)**: `type:bug`, `type:feature`, `type:refactor`, `type:perf`, `type:docs`
*   **架构层级 (Layer)**: `layer:core-engine`, `layer:systems`, `layer:gui`, `layer:data-factory`
*   **核心交接状态 (Status Labels)**:
    *   `status:plan-pending`: **方案对齐阶段**。Issue 已创建并认领，但尚未产出或确认 Technical Proposal。此时不可开始编码。
    *   `status:implemented`: **交付评审阶段**。逻辑实现已完成，PR 已开启。此时等待 Review 或集成测试。
    *   `status:blocked`: **阻塞状态**。由于外部原因（数据缺失、上游依赖）暂时无法继续。

## 2. 里程碑设计 (Milestones)

里程碑用于跟踪重大版本进度：
*   **Version (vX.Y)**: 同步游戏版本。
*   **Arch (架构)**: 底层重大变更。

## 3. 看板流程与自动化 (GitHub Projects)

进度追踪主要依靠看板列的流转，而非颗粒度状态标签。

### 3.1 核心流转路径
1.  **📥 Backlog**: 任务创建后的初始位置。标签包含 `status:plan-pending`。
2.  **🎯 Todo**: 确认要实施的任务移入此列。AI 开始分析并提供对齐方案。
3.  **🤖 In Progress (AI)**: 方案确认后移入。此时**删除** `status:plan-pending` 标签，开始开发。
4.  **🛠️ In Progress (Human)**: 人类开发者正在处理复杂逻辑。
5.  **🧪 Review & GUI Test**: 开发完成，**添加** `status:implemented` 标签并移入此列。
6.  **🏁 Done**: 验证通过，**删除** `status:implemented` 标签并关闭 Issue，卡片自动移入此列。

## 4. 开发进度追踪

*   **Issue Checklists**: 所有复杂 Issue 必须包含任务清单。
*   **Comment Footprints**: 关键逻辑完成后，在 Issue 评论区留下简短更新。

## 5. AI 代理的行为规范

AI 在项目管理中的核心职责：
1.  **认领与拆解**: AI 在认领任务后，必须自动在 Issue 描述中生成任务清单。
2.  **状态流转**: AI 必须根据开发阶段主动执行卡片移动指令。
3.  **标签清理**: 
    *   开始开发前确保删除 `status:plan-pending`。
    *   完成任务时确保添加 `status:implemented`。
    *   关闭任务前确保删除所有状态标签。
4.  **自动打标**: 根据 Issue 描述自动建议 Layer 标签。