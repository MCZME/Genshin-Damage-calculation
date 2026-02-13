from typing import Any

from core.entities.base_entity import CombatEntity, Faction
from core.action.action_data import AttackConfig, HitboxConfig, AOEShape, StrikeType
from core.action.damage import Damage
from core.event import GameEvent, EventType
from core.tool import get_current_time
from character.FONTAINE.furina.data import (
    ATTACK_DATA, ELEMENTAL_SKILL_DATA, MECHANISM_CONFIG
)


class FurinaSummonBase(CombatEntity):
    """芙宁娜召唤物基类。"""

    def __init__(self, name: str, owner: Any, context: Any) -> None:
        super().__init__(
            name=name,
            faction=Faction.PLAYER,
            life_frame=1800,  # 30s
            context=context
        )
        self.owner = owner
        self.skill_lv = owner.skill_params[1]

    # 这又是什么
    def get_owner_attr(self, attr_name: str) -> float:
        return self.owner.attribute_panel.get(attr_name, 0.0)

    def _build_attack_config(self, name: str) -> AttackConfig:
        """从原生数据构建物理契约。"""
        p = ATTACK_DATA[name]
        
        # 映射形状 (原生中文 -> Enum)
        shape_map = {"球": AOEShape.SPHERE, "圆柱": AOEShape.CYLINDER, "长方体": AOEShape.BOX, "单体": AOEShape.SINGLE}
        # 映射打击类型
        strike_map = {"默认": StrikeType.DEFAULT, "突刺": StrikeType.THRUST, "切割": StrikeType.SLASH, "钝击": StrikeType.BLUNT, "穿刺": StrikeType.PIERCE}
        
        return AttackConfig(
            attack_tag=p["attack_tag"],
            extra_attack_tags=p.get("extra_attack_tags", []),
            icd_tag=p["icd_tag"],
            icd_group=p["icd_group"],
            strike_type=strike_map.get(p["strike_type"], StrikeType.DEFAULT),
            is_ranged=p["is_ranged"],
            hitbox=HitboxConfig(
                shape=shape_map.get(p["shape"], AOEShape.SINGLE),
                radius=p.get("radius", 0.0),
                width=p.get("width", 0.0),
                height=p.get("height", 0.0),
                length=p.get("length", 0.0),
                offset=p.get("offset", (0.0, 0.0, 0.0))
            )
        )


class SalonMember(FurinaSummonBase):
    """孤心沙龙成员 (荒性)。"""

    def __init__(self, name: str, owner: Any, context: Any, attack_name: str) -> None:
        super().__init__(name, owner, context)
        self.attack_name = attack_name # 对应 ATTACK_DATA 的 Key (如 "乌瑟勋爵伤害")
        self.timer = 0
        
        # 获取机制常量中的间隔
        interval_key = {
            "乌瑟勋爵伤害": "SKILL_USHER_INTERVAL",
            "海薇玛夫人伤害": "SKILL_CHEVALMARIN_INTERVAL",
            "谢贝蕾妲小姐伤害": "SKILL_CRABALETTA_INTERVAL"
        }[attack_name]
        self.interval = MECHANISM_CONFIG[interval_key]
        
        # 预载配置
        self.attack_config = self._build_attack_config(attack_name)

    def on_frame_update(self) -> None:
        self.timer += 1
        if self.timer >= self.interval:
            self.execute_attack()
            self.timer = 0

    def execute_attack(self) -> None:
        bonus = self._process_hp_consumption()
        
        # 获取倍率
        multiplier = ELEMENTAL_SKILL_DATA[self.attack_name][1][self.skill_lv - 1]
        
        # 构造伤害对象，Key 即是 Name
        dmg_obj = Damage(
            element=("水", 1.0),
            damage_multiplier=multiplier * bonus,
            scaling_stat="生命值",
            config=self.attack_config,
            name=self.attack_name
        )
        
        # 注入 element_u (从原生数据读取)
        dmg_obj.set_element("水", ATTACK_DATA[self.attack_name]["element_u"])
        
        self.ctx.event_engine.publish(GameEvent(
            EventType.BEFORE_DAMAGE,
            get_current_time(),
            source=self.owner,
            data={"character": self.owner, "damage": dmg_obj}
        ))

    def _process_hp_consumption(self) -> float:
        if not self.ctx.team: return 1.0
        
        healthy_count = 0
        consume_key = self.attack_name.replace("伤害", "消耗生命值")
        ratio = ELEMENTAL_SKILL_DATA[consume_key][1][0] / 100.0
        
        for m in self.ctx.team.get_members():
            max_hp = m.attribute_panel.get("生命值", 1.0)
            if m.current_hp / max_hp > 0.5:
                healthy_count += 1
                consume_val = max_hp * ratio
                self.ctx.event_engine.publish(GameEvent(
                    EventType.BEFORE_HURT,
                    get_current_time(),
                    source=self.owner,
                    data={"character": self.owner, "target": m, "amount": consume_val, "ignore_shield": True}
                ))
                
        return 1.0 + min(4, healthy_count) * 0.1


class SingerOfManyWaters(FurinaSummonBase):
    """众水的歌者 (芒性)。"""

    def __init__(self, owner: Any, context: Any) -> None:
        super().__init__("众水的歌者", owner, context)
        self.first_heal = MECHANISM_CONFIG["SKILL_FIRST_HEAL_FRAME"]
        self.current_interval = MECHANISM_CONFIG["SKILL_HEAL_INTERVAL"]
        self.timer = 0
        self.has_first_healed = False

    def on_frame_update(self) -> None:
        if not self.has_first_healed:
            if self.current_frame >= self.first_heal:
                self.execute_healing()
                self.has_first_healed = True
                self.timer = 0
            return

        self.timer += 1
        if self.timer >= self.current_interval:
            self.execute_healing()
            self.timer = 0

    def execute_healing(self) -> None:
        if not self.ctx.team: return
        
        # 动态更新间隔 (天赋二驱动)
        self.current_interval = getattr(self.owner, "singer_interval_override", MECHANISM_CONFIG["SKILL_HEAL_INTERVAL"])

        mult_info = ELEMENTAL_SKILL_DATA["众水的歌者治疗量"]
        perc, flat = mult_info[1][self.skill_lv - 1]
        
        # 构造规范治疗
        from core.action.healing import Healing, HealingType
        heal_obj = Healing(base_multiplier=(perc, flat), healing_type=HealingType.SKILL, name="众水的歌者治疗")
        heal_obj.set_scaling_stat("生命值")
        
        active_char = self.ctx.team.current_character
        if active_char:
            self.ctx.event_engine.publish(GameEvent(
                EventType.BEFORE_HEAL, get_current_time(),
                source=self.owner, data={"character": self.owner, "target": active_char, "healing": heal_obj}
            ))
