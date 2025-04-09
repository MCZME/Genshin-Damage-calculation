# 伤害计算系统文档

## 伤害类型定义(DamageType)

```python
class DamageType(Enum):
    NORMAL = "普通攻击"
    CHARGED = "重击"
    SKILL = "元素战技" 
    BURST = "元素爆发"
    PLUNGING = "下落攻击"
    REACTION = "剧变反应"
```

伤害类型用于区分不同来源的伤害，影响伤害计算和事件触发。

## 伤害基础类(Damage)

```python
class Damage():
    def __init__(self, damageMultipiler, element, damageType:DamageType, name, **kwargs):
        self.damageMultipiler = damageMultipiler  # 伤害倍率
        self.element = element      # 元素类型
        self.damageType = damageType # 伤害类型
        self.name = name            # 伤害名称
        self.damage = 0             # 最终伤害值
        self.baseValue = '攻击力'    # 基础属性(攻击力/生命值/防御力)
        self.reaction = None        # 元素反应实例
        self.data = kwargs          # 额外数据
        self.panel = {}             # 伤害计算面板数据
```

Damage类存储伤害计算所需的所有数据，并提供以下方法：
- `setSource()`: 设置伤害来源
- `setTarget()`: 设置伤害目标  
- `setBaseValue()`: 设置基础属性类型
- `setReaction()`: 设置元素反应
- `setDamageData()`: 设置额外数据
- `setPanel()`: 设置面板数据

## 伤害计算类(Calculation)

Calculation类实现各种伤害计算公式，主要方法包括：

### 基础属性计算
```python
def attack(self):  # 攻击力计算
def health(self):  # 生命值计算  
def DEF(self):     # 防御力计算
```

### 伤害乘区计算
```python
def damageMultipiler(self):  # 伤害倍率计算
def damageBonus(self):       # 伤害加成计算
def critical(self):          # 暴击率计算
def criticalBracket(self):   # 暴击伤害计算
def defense(self):           # 防御减免计算
def resistance(self):        # 元素抗性计算
def reaction(self):          # 元素反应系数计算
```

### 最终伤害计算
```python
def calculation_by_attack(self):  # 基于攻击力的伤害计算
def calculation_by_hp(self):      # 基于生命值的伤害计算  
def calculation_by_def(self):     # 基于防御力的伤害计算
def calculation_by_reaction(self): # 剧变反应伤害计算
```

## 伤害事件处理(DamageCalculateEventHandler)

```python
class DamageCalculateEventHandler(EventHandler):
    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_DAMAGE:
            # 处理元素附魔
            self.handle_elemental_infusion(character, damage)
            
            # 根据基础属性类型选择计算公式
            if damage.damageType == DamageType.REACTION:
                calculation.calculation_by_reaction()
            elif damage.baseValue == '攻击力':
                calculation.calculation_by_attack()
            elif damage.baseValue == '生命值':
                calculation.calculation_by_hp() 
            elif damage.baseValue == '防御力':
                calculation.calculation_by_def()
```

事件处理器主要功能：
1. 处理元素附魔效果
2. 根据伤害类型选择适当的计算公式
3. 发布相关事件(BEFORE_DAMAGE/AFTER_DAMAGE)
4. 处理元素反应额外伤害

## 使用示例

```python
# 创建伤害实例
damage = Damage(
    damageMultipiler=150, 
    element=('火', 0),
    damageType=DamageType.SKILL,
    name="元素战技伤害"
)

# 触发伤害计算事件
event = GameEvent(EventType.BEFORE_DAMAGE, GetCurrentTime(),
                 character=character,
                 target=target,
                 damage=damage)
EventBus.publish(event)
```

## 元素反应支持

当前支持的元素反应类型：
- 超载(OVERLOAD)
- 超导(SUPERCONDUCT) 
- 融化(MELT)
- 蒸发(VAPORIZE)

待实现反应类型：
- 燃烧
- 绽放/超绽放/烈绽放
- 激化/超激化/蔓激化  
- 感电
- 扩散
- 碎冰
- 冻结
