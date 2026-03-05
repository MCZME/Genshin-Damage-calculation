from typing import Dict, Any, Optional, List
import random

from core.systems.utils import AttributeCalculator
from core.systems.base_system import GameSystem
from core.context import EventEngine
from core.event import GameEvent, EventType
from core.systems.contract.damage import Damage
from core.systems.contract.modifier import ModifierRecord
from core.mechanics.aura import Element
from core.config import Config
from core.logger import get_emulation_logger
from core.tool import get_current_time


class DamageContext:
    """伤害计算上下文 (支持全过程审计)。"""

    def __init__(self, damage: Damage, source: Any, target: Optional[Any] = None):
        self.damage = damage
        self.source = source
        self.target = target
        self.config = damage.config

        self.stats: Dict[str, float] = {
            "攻击力": 0.0,
            "生命值": 0.0,
            "防御力": 0.0,
            "元素精通": 0.0,
            "固定伤害值加成": 0.0,
            "伤害加成": 0.0,
            "暴击率": 0.0,
            "暴击伤害": 0.0,
            "防御区系数": 0.0,
            "抗性区系数": 0.0,
            "反应基础倍率": 0.0,
            "反应加成系数": 0.0,
        }
        self.audit_trail: List[ModifierRecord] = []
        self.final_result: float = 0.0
        self.is_crit: bool = False

    def add_modifier(
        self, source: str, stat: str, value: float, op: str = "ADD"
    ) -> None:
        if stat not in self.stats:
            self.stats[stat] = 0.0 if op == "ADD" else 1.0
        if op == "ADD":
            self.stats[stat] += value
        elif op == "MULT":
            self.stats[stat] *= value
        elif op == "SET":
            self.stats[stat] = value
            
        # 从上下文获取唯一 ID
        from core.context import get_context
        m_id = 0
        try:
            m_id = get_context().get_next_modifier_id()
        except:
            pass

        self.audit_trail.append(ModifierRecord(m_id, source, stat, value, op))


class DamagePipeline:
    def __init__(self, engine: EventEngine):
        self.engine = engine

    def run(self, ctx: DamageContext):
        # 2. 建立基础引用
        ctx.damage.set_source(ctx.source)

        # 3. 发布事件 (允许外部系统注入修正)
        self.engine.publish(
            GameEvent(
                EventType.BEFORE_CALCULATE,
                get_current_time(),
                source=ctx.source,
                data={"damage_context": ctx},
            )
        )

        # 4. 目标锁定与空间广播
        if not ctx.target:
            self._dispatch_broadcast(ctx)
        else:
            ctx.damage.set_target(ctx.target)
            ctx.target.handle_damage(ctx.damage)

        if not ctx.damage.target:
            return
        ctx.target = ctx.damage.target

        # 5. 即时契约快照 (捕捉最终倍率和专项增伤)
        self._snapshot_instant(ctx)

        # 6. 后续结算
        self._preprocess_reaction_stats(ctx)
        self._calculate_def_res(ctx)
        self._calculate(ctx)

        ctx.damage.damage = ctx.final_result
        ctx.damage.data["audit_trail"] = ctx.audit_trail

    def _snapshot_instant(self, ctx: DamageContext):
        """阶段 2: 即时契约快照 (捕捉经过事件修改后的最终值)。"""
        src = ctx.source
        scaling_stats = ctx.damage.scaling_stat

        # 按需注入主属性向量
        for s_name in scaling_stats:
            if s_name == "固定值": 
                continue
            val = AttributeCalculator.get_val_by_name(src, s_name)
            ctx.add_modifier("[实体面板]", s_name, val, "ADD")

        # 记录暴击面板 (作为基础)
        ctx.add_modifier(
            "[实体面板]", "暴击率", AttributeCalculator.get_crit_rate(src) * 100, "ADD"
        )

        # 1. 捕捉最终倍率向量 (可能被 BEFORE_CALCULATE 修改)
        mults = ctx.damage.damage_multiplier
        stats = ctx.damage.scaling_stat
        for i, s_name in enumerate(stats):
            m_val = mults[i] if i < len(mults) else 0.0
            ctx.add_modifier("[技能契约]", f"{s_name}倍率", m_val, "ADD")

        # 2. 反应所需精通 (只有可能触发反应时注入)
        el = ctx.damage.element[0]
        el_name = el.value if isinstance(el, Element) else el
        if "元素精通" not in stats and el_name not in ("无", "物理"):
            em_val = AttributeCalculator.get_val_by_name(src, "元素精通")
            ctx.add_modifier("[实体面板同步]", "元素精通", em_val, "ADD")

        # 3. 动态增伤区汇总 (此时已包含 BEFORE_CALCULATE 注入的所有 Buff)
        bonus = AttributeCalculator.get_damage_bonus(src, el_name) * 100

        ctx.add_modifier("[最终增伤区]", "伤害加成", bonus, "ADD")

    def _calculate_def_res(self, ctx: DamageContext):
        target_def = ctx.target.attribute_data.get("防御力", 0)
        coeff_def = (5 * ctx.source.level + 500) / (
            target_def + 5 * ctx.source.level + 500
        )
        ctx.add_modifier("防御减免结算", "防御区系数", coeff_def, "ADD")

        el = ctx.damage.element[0]
        el_name = el.value if isinstance(el, Element) else el

        res = ctx.target.attribute_data.get(f"{el_name}元素抗性", 10.0)
        coeff_res = 1.0
        if res > 75:
            coeff_res = 1 / (1 + 4 * res / 100)
        elif res < 0:
            coeff_res = 1 - res / 2 / 100
        else:
            coeff_res = 1 - res / 100
        ctx.add_modifier(f"{el_name}抗性结算", "抗性区系数", coeff_res, "ADD")

    def _calculate(self, ctx: DamageContext):
        s = ctx.stats
        from core.action.attack_tag_resolver import AttackTagResolver, AttackCategory

        categories = AttackTagResolver.resolve_categories(
            ctx.config.attack_tag, ctx.config.extra_attack_tags
        )

        # 剧变反应结算
        if AttackCategory.REACTION in categories:
            em_inc = (16 * s["元素精通"]) / (s["元素精通"] + 2000)
            level_coeff = ctx.damage.data.get("等级系数", 0)
            react_base = ctx.damage.data.get("反应系数", 1.0)
            bonus = ctx.damage.data.get("反应伤害提高", 0)
            ctx.final_result = (
                level_coeff * react_base * (1 + em_inc + bonus) * s["抗性区系数"]
            )
            ctx.add_modifier("剧变反应基础", "最终伤害", ctx.final_result, "SET")
            return

        # 基础增伤区合算 (向量点积结果)
        base_val = self._get_base_value(ctx)

        bonus_mult = 1 + s["伤害加成"] / 100
        crit_mult = self._get_crit_mult(ctx)

        react_mult = 1.0
        if s["反应基础倍率"] > 1.0:
            react_mult = s["反应基础倍率"] * (1 + s["反应加成系数"])

        ctx.final_result = (
            (base_val + s["固定伤害值加成"])
            * bonus_mult
            * crit_mult
            * react_mult
            * s["防御区系数"]
            * s["抗性区系数"]
        )

    def _get_base_value(self, ctx: DamageContext) -> float:
        d = ctx.damage
        stats = d.scaling_stat
        mults = d.damage_multiplier
        
        total_base = 0.0
        for i, s_name in enumerate(stats):
            m_val = mults[i] if i < len(mults) else 0.0
            # 从 ctx.stats 中获取之前 _snapshot 注入的数值
            val = ctx.stats.get(s_name, 0.0)
            total_base += val * (m_val / 100.0) if s_name != "固定值" else m_val
            
        return total_base

    def _get_crit_mult(self, ctx: DamageContext) -> float:
        if Config.get("emulation.open_critical"):
            if random.uniform(0, 100) <= ctx.stats["暴击率"]:
                ctx.is_crit = True
                ctx.add_modifier(
                    "暴击区", "暴击伤害", 100 + AttributeCalculator.get_crit_damage(ctx.source), "ADD"
                )
                return 1 + ctx.stats["暴击伤害"] / 100
        return 1.0

    def _dispatch_broadcast(self, ctx: DamageContext):
        from core.context import get_context

        sim_ctx = get_context()
        sim_ctx.space.broadcast_damage(ctx.source, ctx.damage)

    def _preprocess_reaction_stats(self, ctx: DamageContext):
        for res in ctx.damage.reaction_results:
            ctx.add_modifier(
                f"反应:{res.reaction_type.name}", "反应基础倍率", res.multiplier, "SET"
            )


class DamageSystem(GameSystem):
    def initialize(self, context):
        super().initialize(context)
        self.pipeline = DamagePipeline(self.engine)

    def register_events(self, engine: EventEngine):
        engine.subscribe(EventType.BEFORE_DAMAGE, self)

    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.BEFORE_DAMAGE:
            char = event.data["character"]
            dmg = event.data["damage"]
            target = event.data.get("target")
            ctx = DamageContext(dmg, char, target)
            self.pipeline.run(ctx)

            if dmg.target:
                get_emulation_logger().log_damage(char, dmg.target, dmg)
                self.engine.publish(
                    GameEvent(
                        event_type=EventType.AFTER_DAMAGE,
                        frame=event.frame,
                        source=char,
                        data={
                            "character": char, 
                            "target": dmg.target, 
                            "target_id": getattr(dmg.target, "entity_id", None),
                            "damage": dmg
                        },
                    )
                )
