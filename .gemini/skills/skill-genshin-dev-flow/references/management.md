# 项目管理规范

本文档定义了如何使用 GitHub Issues, Milestones 和 Projects 来管理开发进度。

## 1. Issue 管理

所有开发活动必须关联一个 Issue。

### 1.1 Issue 模板要求
*   **Bug**: 必须包含游戏版本、角色配置（等级/命座）、以及预期结果与计算结果的差值。
*   **Feature**: 必须链接到相关的数据来源。
*   **Refactor**: 必须说明重构的原因及预期的架构提升。

### 1.2 标签体系 (Labels)

标签仅用于标识任务性质 and 关键交接状态：

*   **工作类型 (Type)**: `type:bug`, `type:feature`, `type:refactor`, `type:perf`, `type:docs`
*   **架构层级 (Layer)**: `layer:core-engine`, `layer:systems`, `layer:gui`, `layer:data-factory`
*   **协作状态 (Status)**:
    *   `status:plan-pending`: 方案尚未确定，等待 AI 或人类产出 Technical Proposal。
    *   `status:implemented`: 逻辑代码已编写完成，并已通过初步自测，等待 Review 或 GUI 验证。
    *   `status:blocked`: 任务由于外部原因（如数据缺失）暂时阻塞。

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