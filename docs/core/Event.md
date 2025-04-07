# 事件系统文档

## 事件类型枚举(EventType)

事件系统定义了游戏中各种关键时点的枚举类型，用于标识不同的事件触发点：

```python
class EventType(Enum):
    # 战斗相关事件
    FRAME_END = auto()        # 每帧结束时
    BEFORE_DAMAGE = auto()    # 伤害计算前
    AFTER_DAMAGE = auto()     # 伤害计算后
    
    # 属性计算事件
    BEFORE_ATTACK = auto()    # 攻击力计算前
    AFTER_ATTACK = auto()     # 攻击力计算后
    
    # 伤害计算事件
    BEFORE_DAMAGE_MULTIPLIER = auto()  # 伤害倍率计算前
    AFTER_DAMAGE_MULTIPLIER = auto()   # 伤害倍率计算后
    
    # 元素反应事件
    BEFORE_ELEMENTAL_REACTION = auto()  # 元素反应触发前
    AFTER_ELEMENTAL_REACTION = auto()   # 元素反应触发后
    
    # 角色行为事件
    BEFORE_NORMAL_ATTACK = auto()  # 普通攻击前
    AFTER_NORMAL_ATTACK = auto()   # 普通攻击后
    
    # 角色状态事件
    BEFORE_HEALTH_CHANGE = auto()  # 角色血量变化前
    AFTER_HEALTH_CHANGE = auto()   # 角色血量变化后
    
    # 完整列表请参考Event.py文件
```

## 事件类(GameEvent)

基础事件类，所有具体事件都继承自此类：

```python
class GameEvent:
    def __init__(self, event_type: EventType, frame, **kwargs):
        self.event_type = event_type  # 事件类型
        self.frame = frame            # 发生帧数
        self.data = kwargs            # 扩展数据
        self.cancelled = False       # 是否取消事件
```

### 常用事件子类

1. **DamageEvent**: 伤害事件
   - 包含source(来源)、target(目标)、damage(伤害值)等数据
   - 分BEFORE_DAMAGE和AFTER_DAMAGE两种类型

2. **CharacterSwitchEvent**: 角色切换事件
   - 包含old_character(原角色)和new_character(新角色)

3. **ElementalReactionEvent**: 元素反应事件
   - 包含elementalReaction(元素反应类型)

## 事件处理器接口

```python
class EventHandler(ABC):
    @abstractmethod
    def handle_event(self, event: GameEvent):
        pass
```

使用步骤：
1. 实现EventHandler接口
2. 在handle_event方法中处理特定事件
3. 向EventBus注册处理器

## 事件总线(EventBus)

事件总线采用单例模式，提供订阅/发布机制：

```python
# 订阅事件
EventBus.subscribe(EventType.BEFORE_DAMAGE, my_handler)

# 取消订阅
EventBus.unsubscribe(EventType.BEFORE_DAMAGE, my_handler)

# 发布事件
event = DamageEvent(...)
EventBus.publish(event)
```

## 使用示例

```python
class MyDamageHandler(EventHandler):
    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.BEFORE_DAMAGE:
            # 在伤害计算前修改伤害值
            event.data['damage'].value *= 1.2  # 增加20%伤害

# 注册处理器
handler = MyDamageHandler()
EventBus.subscribe(EventType.BEFORE_DAMAGE, handler)
