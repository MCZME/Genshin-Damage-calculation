import sys
import os
from unittest.mock import MagicMock

# ---------------------------------------------------------
# 极其重要的 Mock：在 import 任何项目代码前拦截依赖
# ---------------------------------------------------------
# Mock DataRequest
mock_dr = MagicMock()
sys.modules["DataRequest"] = MagicMock(DR=mock_dr)

# Mock pymongo (防止 DataRequest 内部报错)
sys.modules["pymongo"] = MagicMock()

# Mock Team (防止循环依赖)
mock_team = MagicMock()
sys.modules["core.Team"] = MagicMock(Team=mock_team)

# Mock Logger
mock_logger = MagicMock()
sys.modules["core.Logger"] = MagicMock(get_emulation_logger=lambda: mock_logger)

# 将项目根目录加入 path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.context import create_context, get_context
from core.base_entity import BaseEntity
from core.Event import GameEvent, EventType, DamageEvent
from core.action.damage import Damage, DamageType
# 延迟导入 DamageSystem，确保上面的 Mock 已生效
from core.systems.damage_system import DamageSystem

def test_damage_system_integration():
    print("--- 开始测试 DamageSystem 集成 ---")

    # 1. 创建上下文 (这会自动装配 DamageSystem)
    ctx = create_context()
    print("[1] SimulationContext 创建成功，系统已装配。")

    # 2. 创建 Mock 实体 (模拟角色)
    # 我们创建一个具体的子类，因为 BaseEntity 是抽象的
    class MockCharacter(BaseEntity):
        def on_frame_update(self, target): pass
    
    char = MockCharacter("测试角色")
    char.level = 90
    char.attributePanel = {
        "攻击力": 1000,
        "攻击力%": 0,
        "固定攻击力": 0,
        "暴击率": 50,
        "暴击伤害": 100,
        "伤害加成": 0,
        "火元素伤害加成": 20,
        "元素精通": 100
    }
    char.active_effects = []
    print(f"[2] Mock 角色 '{char.name}' 初始化完成，局部事件引擎已建立。")

    # 3. 创建 Mock 目标 (模拟怪物)
    target = MagicMock()
    target.defense = 1000
    target.current_resistance = {"火": 10}
    target.apply_elemental_aura.return_value = 1.0 # 默认无反应
    print("[3] Mock 目标初始化完成。")

    # 4. 创建伤害对象
    dmg = Damage(100.0, ("火", True), DamageType.NORMAL, "普通攻击一段")
    
    # 5. 注册一个监听器来验证 AFTER_DAMAGE 是否发布
    after_damage_triggered = False
    def on_after_damage(event):
        nonlocal after_damage_triggered
        after_damage_triggered = True
        print(f"[验证] 收到 AFTER_DAMAGE 事件！计算结果: {event.data['damage'].damage:.2f}")

    ctx.event_engine.subscribe(EventType.AFTER_DAMAGE, MagicMock(handle_event=on_after_damage))

    # 6. 在角色局部引擎发布事件 (模拟动作触发伤害)
    print("[4] 在角色局部引擎发布 BEFORE_DAMAGE 事件...")
    # 注意：DamageEvent 内部会设置 source 和 target
    event = DamageEvent(char, target, dmg, 1, before=True)
    char.event_engine.publish(event)

    # 7. 验证结果
    if after_damage_triggered:
        print("[结果] 测试通过：事件已通过冒泡被全局 DamageSystem 捕获并处理。")
    else:
        print("[错误] 测试失败：全局系统未捕获到局部冒泡的事件。")

if __name__ == "__main__":
    try:
        test_damage_system_integration()
    except Exception as e:
        print(f"[异常] 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
