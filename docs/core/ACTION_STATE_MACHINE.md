# Core - 动作状态机 (ASM Engine)

`ActionManager` 是仿真的心脏，负责处理角色的所有动作（普攻、技能、冲刺等）。

## 核心概念
ASM 引擎将动作抽象为 **帧序列 (Frames)**，而不是简单的 CD 计时器。

### `ActionFrameData`
定义了一个动作的物理参数：
- **`total_frames`**: 动作总长度。
- **`hit_frames`**: 所有的伤害判定点（如第 13, 25 帧）。
- **`cancel_windows`**: 允许被其他动作取消的起始帧（如 "dash": 12 意味着 12 帧后可以闪避取消）。

## 命中回调机制
当 `ActionManager` 运行到 `hit_frames` 定义的某一帧时，它会自动触发回调：
1. 查找当前动作关联的 `runtime_skill_obj`。
2. 调用 `skill_obj.on_execute_hit(target, hit_index)`。
3. 此时 `Skill` 对象发布具体的伤害事件。

## 状态转换逻辑
- **请求动作 (`request_action`)**: 引擎会检查当前是否正在执行动作。
- **取消检查**: 如果当前动作已进入 `cancel_window`，新动作将立即替换旧动作。
- **并发控制**: 一个实体同一时间只能有一个“活动动作”。
