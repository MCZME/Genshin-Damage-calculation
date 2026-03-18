# Flet 开发建议

> 本文档结合当前项目中的实际实现，总结 Flet 组件、ViewModel 和嵌套状态管理的开发建议。

---

## 1. 先定状态归属，再写组件

在本项目里，**只要组件里有会变化的数据，就应该先定义对应的 `ViewModel`**，再让组件绑定这个 `ViewModel`。

例如：
- 角色卡片要展示名称、等级、命座、武器和圣遗物摘要，就应该有 `CharacterViewModel`
- 武器卡片要展示名称、等级、精炼，就应该有 `WeaponViewModel`
- 圣遗物部位要展示套装、主词条、副词条，就应该有 `ArtifactPieceViewModel`
- 目标面板要展示名称、等级、位置和抗性，就应该有 `TargetViewModel`

这样做的原因很直接：
- 组件只负责渲染，不负责存储业务状态
- 数据变化时，只需要更新对应的 VM
- 后续重构 UI 时，不会把数据逻辑散落到各个组件里

参考实现：
- `ui/view_models/strategic/character_vm.py`
- `ui/view_models/strategic/weapon_vm.py`
- `ui/view_models/strategic/artifact_vm.py`
- `ui/view_models/scene/target_vm.py`

---

## 2. ViewModel 要负责”状态 + 变更通知”

项目里统一使用 `@ft.observable` + `dataclass` 的方式定义 VM。

### 2.1 基本模式

```python
@ft.observable
@dataclass
class ExampleViewModel:
    value: str = “”

    def set_value(self, value: str):
        self.value = value
        # 修改属性后 Flet 会自动触发重渲染，无需手动调用 notify()
```

**要点**：
- `@ft.observable` 装饰的类，属性修改会**自动触发**绑定组件的重渲染
- 不需要手动调用 `notify()`（除非有特殊需求）
- 组件只读 VM 属性，不直接读写底层 `dict`

### 2.2 官方推荐的嵌套 observable 模式

当父 VM 需要持有**多个同类型**子 VM 时，可以使用 `list` 或 `dict`：

```python
@ft.observable
@dataclass
class User:
    first_name: str
    last_name: str

    def update(self, first_name: str, last_name: str):
        self.first_name = first_name
        self.last_name = last_name


@ft.observable
@dataclass
class App:
    users: list[User] = field(default_factory=list)

    def add_user(self, first_name: str, last_name: str):
        self.users.append(User(first_name, last_name))

    def delete_user(self, user: User):
        self.users.remove(user)


@ft.component
def AppView():
    # 直接传入实例
    app, _ = ft.use_state(App(users=[
        User(“John”, “Doe”),
        User(“Jane”, “Doe”),
    ]))

    # 列表变化会自动触发重渲染
    return [UserView(user, app.delete_user) for user in app.users]
```

**关键点**：
- `list[ObservableClass]` 或 `dict[str, ObservableClass]` 可以正常工作
- 单独的嵌套 observable 字段需要延迟初始化（见 3.2 节）
- `use_state` 直接传入实例，不要传入类

参考实现：
- `ui/view_models/base_vm.py`
- `ui/view_models/layout_vm.py`
- `ui/view_models/analysis/bottom_panel/bottom_panel_vm.py`

---

## 3. 嵌套状态要特别小心

Flet 的响应式更新不是”自动深度追踪所有嵌套对象”的。
如果你的数据结构是：

- 数据类 A 里嵌套数据类 B
- 组件 A 里嵌套组件 B

那么 B 更新时，**不一定会自动触发 A 对应的 UI 刷新**。

### 3.1 为什么会这样

Flet 识别的是”当前绑定的可观察对象”是否发生变化，而不是无限深度地跟踪普通 Python 对象内部字段。

换句话说：
- 你改了 B 的内部字段
- 但 A 没有 notify
- 那么绑定在 A 上的组件可能不会重绘

### 3.2 嵌套 @ft.observable 的初始化陷阱

**重要**：当一个 `@ft.observable` dataclass 包含另一个 `@ft.observable` 类型的字段时，**不要在 `field(default_factory=...)` 或 `__post_init__` 中直接初始化**。

这会导致组件初始化时卡住或无限循环：

```python
# ❌ 错误：会导致初始化卡住
@ft.observable
@dataclass
class ParentViewModel:
    # 问题：default_factory 会在 dataclass 创建时立即执行
    child: ChildViewModel = field(default_factory=ChildViewModel)

    # 问题：__post_init__ 也会在创建时立即执行
    def __post_init__(self):
        self.child = ChildViewModel()

# ✅ 正确：延迟初始化
@ft.observable
@dataclass
class ParentViewModel:
    child: ChildViewModel | None = field(default=None, init=False)

    def ensure_initialized(self):
        “””确保子 ViewModel 已初始化”””
        if self.child is None:
            self.child = ChildViewModel()
```

在组件中使用：

```python
@ft.component
def MyComponent():
    vm, _ = ft.use_state(ParentViewModel())

    def _init():
        vm.ensure_initialized()

    ft.use_effect(_init, [])

    # ...
```

### 3.3 use_state 的正确用法

**重要**：`ft.use_state` 应该传入**实例**，而不是**类**。

```python
# ❌ 错误：每次渲染都会触发新实例创建
vm, _ = ft.use_state(MyViewModel)

# ✅ 正确：直接传入实例
vm, _ = ft.use_state(MyViewModel())

# ✅ 正确：如果需要参数化初始化，使用工厂函数
vm, _ = ft.use_state(lambda: MyViewModel(param=value))
```

参考实现：
- `ui/view_models/analysis/bottom_panel/bottom_panel_vm.py`
- `ui/components/analysis/bottom_panel/main_panel.py`

---

## 4. 两种解决方案

### 4.1 方案一：父 VM 持有子 VM，子 VM 变更后回调父 VM

适合**需要保留状态**的场景。

当前项目里，`ArtifactPieceViewModel` 就用了这种方式：
- 子 VM 修改副词条、主词条等数据后调用自己的 `notify_update()`
- 再级联调用父 VM 的 `notify_update()`
- 父组件绑定的是父 VM，因此能稳定刷新整块卡片

这种方式的优点：
- 子状态独立存在
- 切换视图或局部刷新后，状态可以保留
- 适合“父组件展示子组件摘要”的场景

适用场景：
- 角色卡片里的武器、圣遗物摘要
- 详情面板里需要保持当前编辑状态
- 子状态需要被父级汇总或派生显示

参考实现：
- `ui/view_models/strategic/character_vm.py`
- `ui/view_models/strategic/artifact_vm.py`
- `ui/view_models/strategic/active_character_vm.py`

### 4.2 方案二：父 VM 不拥有子 VM，创建时直接传入

适合**局部更新、短生命周期**的场景。

这类子数据通常只在组件内部使用，或者每次渲染时都可以重新创建。

优点：
- 结构简单
- 避免复杂的父子通知链
- 更适合只负责局部显示的组件

适用场景：
- 某个列表项只依赖一小段只读数据
- 组件内部临时生成的渲染辅助对象
- 不需要跨页面保留的短暂 UI 状态

---

## 5. 选型原则

这两种方式不要混着用，优先按状态生命周期决定。

### 5.1 需要保留状态时，选“父持有 + 回调通知”

如果切换组件后，还要回到原来的状态，优先让父 VM 持有子 VM。

当前项目里的典型例子：
- `StrategicPageViewModel` 持有 4 个 `CharacterViewModel`
- `CharacterViewModel` 再持有 `WeaponViewModel` 和多个 `ArtifactPieceViewModel`
- 切换圣遗物部位后，原状态依然保留

### 5.2 只做局部展示时，选“创建即传入”

如果数据只是当前渲染用，不需要长期保存，就直接在组件创建时传入。

这样可以减少对象层级，也能降低维护成本。

---

## 6. 切换活跃对象时，优先用 Proxy

如果一个详情面板会在多个对象之间切换，不要频繁销毁和重建整棵控件树。

项目里使用了 `ActiveCharacterProxy`：
- 外部绑定的对象实例保持不变
- 内部通过 `bind_to()` 切换真实目标
- 这样 Flet 只需要做局部属性更新，而不是整块重建

这类模式适合：
- 左侧列表选中项变化
- 右侧详情面板跟随切换
- 需要保持输入控件焦点或局部编辑状态的页面

参考实现：
- `ui/view_models/strategic/active_character_vm.py`
- `ui/view_models/strategic/strategic_page_vm.py`

---

## 7. 临时交互状态不要强行塞进 VM

像 hover、展开/收起、编辑态切换这类状态，很多时候更适合放在组件内部，用 `ft.use_state()` 处理。

当前项目里的例子：
- `PropertySlider` 用本地状态保存编辑态和滑块临时值
- `StatInputField` 用本地状态记录焦点态
- `ActionCard` 用本地状态控制悬浮删除按钮
- `StatsDetailAudit` 用本地状态保存当前选中的审计属性

这类状态的特点：
- 生命周期短
- 只影响当前组件
- 不需要跨页面共享

如果把它们都塞进 VM：
- VM 会变得很重
- 会增加 notify 次数
- 还容易让状态边界变模糊

参考实现：
- `ui/components/strategic/property_slider.py`
- `ui/components/scene/stat_input.py`
- `ui/components/tactical/action_card.py`
- `ui/components/analysis/stats/stats_detail_audit.py`

---

## 8. 推荐的更新链路

建议按下面的顺序组织数据流：

1. 数据模型持有原始数据
2. ViewModel 提供可读属性和 setter
3. 组件只绑定 VM，不直接改字典
4. setter 修改后立刻 `notify_update()`
5. 父子 VM 需要联动时，子 VM 负责级联通知

这条链路在当前项目里已经比较清晰：
- `CharacterViewModel` 负责角色信息汇总
- `WeaponViewModel` 和 `ArtifactPieceViewModel` 负责局部编辑
- `ActiveCharacterProxy` 负责详情区稳定绑定

---

## 9. 实践清单

写 Flet 组件前，建议先检查：

- 这个组件有没有状态
- 状态是否会变化
- 这个状态应该归谁管理
- 组件是否只需要临时 UI 状态
- 是否存在父子 VM 级联更新问题
- 是否会频繁切换对象并需要稳定控件树

如果答案不清晰，先把状态边界画出来，再写 UI。

---

## 10. 结论

一句话总结：

- **有业务数据，就配 ViewModel**
- **需要保留状态，就让父 VM 持有子 VM，并级联 notify**
- **只做局部更新，就直接创建并传入**
- **需要稳定切换，就用 Proxy**
- **hover / 编辑态 / 临时交互状态，优先放组件本地**

---

*适用范围: 本项目的 Flet MVVM 组件开发*
*参考实现: `ui/view_models/`、`ui/components/`*
*版本: v1.1*
*Date: 2026-03-18*
