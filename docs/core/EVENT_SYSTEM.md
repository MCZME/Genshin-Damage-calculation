# Core - 事件驱动系统 (Event System)

本项目采用全异步、层级化的事件驱动架构。

## 结构化事件 (Dataclass Events)
所有事件均定义在 `core/event.py` 中，使用 `dataclass` 替代了旧版的字典传参，提供了更好的类型提示和 IDE 支持。

### 常用事件示例
- **`DamageEvent`**: 携带攻击者、目标、伤害对象。
- **`HealEvent`**: 携带来源、目标、治疗对象。
- **`HealthChangeEvent`**: 统一的 HP 变化通知。
- **`ActionEvent`**: 普攻、技能、大招等动作的触发。

## 层级冒泡机制
事件不再是全局广播，而是遵循 **实体 (Local) -> 队伍 (Team) -> 全局 (Global)** 的流向。

1. **发布 (`publish`)**: 角色产生的事件首先在自己的局部引擎发布。
2. **冒泡**: 如果局部没有处理完（且未停止传播），事件会自动上升到 `SimulationContext` 的全局引擎。
3. **取消与拦截**: 事件对象支持 `.cancel()` (取消效果) 和 `.stop_propagation()` (防止冒泡)。

## 事件监听器 (`EventHandler`)
任何类只需实现 `handle_event` 接口即可成为监听器：

```python
class MyBuff(BaseEffect, EventHandler):
    def on_apply(self):
        self.owner.event_engine.subscribe(EventType.AFTER_DAMAGE, self)

    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.AFTER_DAMAGE:
            print("触发了伤害后效果")
```
