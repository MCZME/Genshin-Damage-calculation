# 事件系统文档

## 事件类型枚举(EventType)

事件系统定义了游戏中各种关键时点的枚举类型，用于标识不同的事件触发点：

```python
class EventType(Enum):
    # 帧事件
    FRAME_END = auto()        # 每帧结束时
    
    # 伤害计算事件
    BEFORE_DAMAGE = auto()    # 伤害计算前
    AFTER_DAMAGE = auto()     # 伤害计算后
    BEFORE_CALCULATE = auto() # 计算前
    AFTER_CALCULATE = auto()  # 计算后
    
    # 属性计算事件
    BEFORE_ATTACK = auto()    # 攻击力计算前
    AFTER_ATTACK = auto()     # 攻击力计算后
    BEFORE_DAMAGE_MULTIPLIER = auto()  # 伤害倍率计算前
    AFTER_DAMAGE_MULTIPLIER = auto()   # 伤害倍率计算后
    BEFORE_DAMAGE_BONUS = auto()  # 伤害加成计算前
    AFTER_DAMAGE_BONUS = auto()   # 伤害加成计算后
    BEFORE_CRITICAL = auto()     # 暴击率计算前
    AFTER_CRITICAL = auto()      # 暴击率计算后
    BEFORE_CRITICAL_BRACKET = auto()  # 暴击伤害计算前
    AFTER_CRITICAL_BRACKET = auto()   # 暴击伤害计算后
    BEFORE_DEFENSE = auto()       # 防御力计算前
    AFTER_DEFENSE = auto()       # 防御力计算后
    BEFORE_RESISTANCE = auto()   # 抗性计算前
    AFTER_RESISTANCE = auto()    # 抗性计算后
    BEFORE_INDEPENDENT_DAMAGE = auto()  # 独立伤害倍率计算前
    AFTER_INDEPENDENT_DAMAGE = auto()   # 独立伤害倍率计算后
    BEFORE_FIXED_DAMAGE = auto()  # 固定伤害加成计算前
    AFTER_FIXED_DAMAGE = auto()   # 固定伤害加成计算后
    
    # 元素反应事件
    BEFORE_ELEMENTAL_REACTION = auto()  # 元素反应触发前
    AFTER_ELEMENTAL_REACTION = auto()   # 元素反应触发后
    BEFORE_FREEZE = auto()       # 冻结反应前
    AFTER_FREEZE = auto()        # 冻结反应后
    BEFORE_QUICKEN = auto()     # 原激化反应前
    AFTER_QUICKEN = auto()      # 原激化反应后
    BEFORE_AGGRAVATE = auto()   # 超激化反应前
    AFTER_AGGRAVATE = auto()    # 超激化反应后
    BEFORE_SPREAD = auto()      # 蔓激化反应前
    AFTER_SPREAD = auto()       # 蔓激化反应后
    BEFORE_VAPORIZE = auto()    # 蒸发反应前
    AFTER_VAPORIZE = auto()     # 蒸发反应后
    BEFORE_MELT = auto()        # 融化反应前
    AFTER_MELT = auto()         # 融化反应后
    BEFORE_OVERLOAD = auto()    # 超载反应前
    AFTER_OVERLOAD = auto()     # 超载反应后
    BEFORE_SWIRL = auto()       # 扩散反应前
    AFTER_SWIRL = auto()        # 扩散反应后
    BEFORE_SHATTER = auto()     # 碎冰反应前
    AFTER_SHATTER = auto()      # 碎冰反应后
    BEFORE_BURNING = auto()     # 燃烧反应前
    AFTER_BURNING = auto()      # 燃烧反应后
    BEFORE_SUPERCONDUCT = auto()  # 超导反应前
    AFTER_SUPERCONDUCT = auto()   # 超导反应后
    BEFORE_ELECTRO_CHARGED = auto()  # 感电反应前
    AFTER_ELECTRO_CHARGED = auto()   # 感电反应后
    BEFORE_BLOOM = auto()       # 绽放反应前
    AFTER_BLOOM = auto()        # 绽放反应后
    BEFORE_HYPERBLOOM = auto()  # 超绽放反应前
    AFTER_HYPERBLOOM = auto()   # 超绽放反应后
    BEFORE_BURGEON = auto()     # 烈绽放反应前
    AFTER_BURGEON = auto()      # 烈绽放反应后
    
    # 角色状态事件
    BEFORE_HEALTH_CHANGE = auto()  # 角色血量变化前
    AFTER_HEALTH_CHANGE = auto()   # 角色血量变化后
    BEFORE_HEAL = auto()         # 治疗计算前
    AFTER_HEAL = auto()          # 治疗后
    BEFORE_HURT = auto()         # 受伤计算前
    AFTER_HURT = auto()          # 受伤后
    BEFORE_SHIELD_CREATION = auto()  # 护盾生成前
    AFTER_SHIELD_CREATION = auto()   # 护盾生成后
    BEFORE_ENERGY_CHANGE = auto()  # 能量变化前
    AFTER_ENERGY_CHANGE = auto()   # 能量变化后
    
    # 对象事件
    OBJECT_CREATE = auto()  # 对象创建
    OBJECT_DESTROY = auto()  # 对象销毁
    
    # 角色行为事件
    BEFORE_NORMAL_ATTACK = auto()  # 普通攻击前
    AFTER_NORMAL_ATTACK = auto()   # 普通攻击后
    BEFORE_CHARGED_ATTACK = auto()  # 重击前
    AFTER_CHARGED_ATTACK = auto()   # 重击后
    BEFORE_PLUNGING_ATTACK = auto()  # 下落攻击前
    AFTER_PLUNGING_ATTACK = auto()   # 下落攻击后
    BEFORE_SKILL = auto()        # 技能使用前
    AFTER_SKILL = auto()         # 技能使用后
    BEFORE_BURST = auto()        # 爆发使用前
    AFTER_BURST = auto()         # 爆发使用后
    BEFORE_DASH = auto()         # 冲刺前
    AFTER_DASH = auto()          # 冲刺后
    BEFORE_JUMP = auto()         # 跳跃前
    AFTER_JUMP = auto()          # 跳跃后
    BEFORE_FALLING = auto()     # 下落前
    AFTER_FALLING = auto()       # 下落后
    
    # 角色切换事件
    BEFORE_CHARACTER_SWITCH = auto()   # 角色切换前
    AFTER_CHARACTER_SWITCH = auto()    # 角色切换后
    
    # 夜魂系统事件
    BEFORE_NIGHTSOUL_BLESSING = auto()  # 夜魂加持前
    AFTER_NIGHTSOUL_BLESSING = auto()  # 夜魂加持后
    BEFORE_NIGHT_SOUL_CHANGE = auto()  # 夜魂改变前
    AFTER_NIGHT_SOUL_CHANGE = auto()  # 夜魂改变后
    NIGHTSOUL_BURST = auto()      # 夜魂迸发
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

### 事件子类

1. **DamageEvent**: 伤害事件
   - 包含source(来源)、target(目标)、damage(伤害值)等数据
   - 分BEFORE_DAMAGE和AFTER_DAMAGE两种类型

2. **CharacterSwitchEvent**: 角色切换事件
   - 包含old_character(原角色)和new_character(新角色)

3. **ElementalReactionEvent**: 元素反应事件
   - 包含elementalReaction(元素反应类型)

4. **NormalAttackEvent**: 普通攻击事件
   - 包含segment(攻击段数)信息

5. **ChargedAttackEvent**: 重击事件
   - 包含重击相关信息

6. **PlungingAttackEvent**: 下落攻击事件
   - 包含is_plunging_impact(是否坠地冲击)信息

7. **NightSoulBlessingEvent**: 夜魂加持事件
   - 包含夜魂加持相关信息

8. **NightSoulChangeEvent**: 夜魂变化事件
   - 包含amount(变化量)信息

9. **HealEvent**: 治疗事件
   - 包含healing(治疗量)信息

10. **HurtEvent**: 受伤事件
    - 包含amount(伤害量)信息

11. **ShieldEvent**: 护盾事件
    - 包含shield(护盾)信息

12. **EnergyChargeEvent**: 能量变化事件
    - 包含amount(变化量)、is_fixed(是否固定值)、is_alone(是否单独计算)信息

13. **ObjectEvent**: 对象事件
    - 包含object(对象)信息

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

# 清空所有事件处理器
EventBus.clear()
```

## 使用示例

```python
# 伤害处理示例
class DamageHandler(EventHandler):
    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.BEFORE_DAMAGE:
            # 在伤害计算前修改伤害值
            event.data['damage'].damage *= 1.2  # 增加20%伤害

# 元素反应处理示例
class ReactionHandler(EventHandler):
    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.AFTER_ELEMENTAL_REACTION:
            # 处理元素反应后逻辑
            reaction_type = event.data['elementalReaction']
            print(f"触发了{reaction_type}反应")

# 注册处理器
damage_handler = DamageHandler()
reaction_handler = ReactionHandler()

EventBus.subscribe(EventType.BEFORE_DAMAGE, damage_handler)
EventBus.subscribe(EventType.AFTER_ELEMENTAL_REACTION, reaction_handler)
```
