import sys
import os
from unittest.mock import MagicMock

# ---------------------------------------------------------
# Mock 外部依赖
# ---------------------------------------------------------
sys.modules["DataRequest"] = MagicMock()
sys.modules["pymongo"] = MagicMock()
sys.modules["mysql.connector"] = MagicMock()

# 将项目根目录加入 path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.config import Config
from core.context import create_context, get_context
from core.registry import CharacterClassMap, initialize_registry
from core.event import EventType, DamageEvent
from core.action.damage import Damage

# 1. 首先加载配置 (必需，否则 Logger 会崩)
Config()

# 2. 强制导入以检查错误堆栈
try:
    from character.FONTAINE.charlotte import CHARLOTTE
    print("[调试] 夏洛蒂模块手动导入成功。")
except Exception as e:
    print(f"[调试] 夏洛蒂模块导入失败！错误: {e}")
    import traceback
    traceback.print_exc()

def test_charlotte_refactored():
    print("--- 开始测试夏洛蒂 (重构版) ---")

    # 1. 验证初始化与发现
    initialize_registry()
    if 74 in CharacterClassMap:
        print(f"[1] 注册表成功发现夏洛蒂类: {CharacterClassMap[74].__name__}")
    else:
        print("[错误] 注册表未发现夏洛蒂，请检查目录结构或装饰器。")
        return

    # 2. 创建上下文
    ctx = create_context()
    
    # 模拟基础数据注入
    base_stats = {
        "name": "夏洛蒂",
        "element": "冰",
        "type": "法器",
        "base_hp": 10000,
        "base_atk": 800,
        "base_def": 600,
        "breakthrough_attribute": "攻击力%",
        "breakthrough_value": 24.0
    }

    # 3. 实例化角色
    CharlotteClass = CharacterClassMap[74]
    char = CharlotteClass(level=90, skill_params=[10, 10, 10], base_data=base_stats)
    
    print(f"[2] 角色 '{char.name}' 实例化成功。")
    print(f"    基础攻击力: {char.attribute_panel['攻击力']} (期待值: 800)")
    print(f"    突破加成: {char.attribute_panel['攻击力%']}% (期待值: 24.0)")

    # 4. 模拟运行一个动作 (元素战技点按)
    print("[3] 模拟执行: 元素战技 (点按)")
    
    # 注册一个监听器记录产生的伤害
    damage_results = []
    def on_damage(event):
        dmg = event.data['damage']
        damage_results.append(dmg)
        print(f"    [伤害触发] {dmg.name}: {dmg.damage_multiplier}%")

    ctx.event_engine.subscribe(EventType.BEFORE_DAMAGE, MagicMock(handle_event=on_damage))

    # 执行动作
    char.elemental_skill() # 默认点按
    
    # 驱动 ASM 推进 60 帧 (点按命中点在 31 帧)
    target = MagicMock()
    target.name = "打桩木靶"
    target.active_effects = []
    target.event_engine = ctx.event_engine
    ctx.target = target # 关键：绑定到上下文
    
    # 建立 Mock 队伍以便产球逻辑生效
    ctx.team = MagicMock()
    ctx.team.team = [char]
    
    for _ in range(60):
        char.update(target)

    # 5. 验证结果
    if len(damage_results) > 0:
        print(f"[4] 测试成功：ASM 成功触发了 {len(damage_results)} 次伤害点。")
        hit_names = [d.name for d in damage_results]
        if any("点按" in n for n in hit_names):
            print("    验证通过：检测到 '点按伤害'")
    else:
        print("[错误] 没有任何伤害触发，ASM 可能未正确驱动。")

if __name__ == "__main__":
    test_charlotte_refactored()
