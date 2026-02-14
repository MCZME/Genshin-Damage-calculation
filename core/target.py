from typing import Any, Dict
from core.entities.base_entity import CombatEntity, Faction


class Target(CombatEntity):
    """
    仿真场景中的受击目标 (通常为敌方实体)。
    负责承载基础属性、抗性面板以及伤害处理逻辑。
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化受击目标。

        Args:
            config: 包含目标属性的配置字典，支持 name, level, attributes 等字段。
        """
        name = config.get("name", "未命名目标")
        super().__init__(
            name=name, faction=Faction.ENEMY, pos=(0.0, 0.0, 0.0), hitbox=(0.5, 2.0)
        )

        self.level: int = config.get("level", 90)

        # 基础属性面板：从 config 的 attributes 字段获取，或使用默认值
        input_attrs = config.get("attributes", {})

        self.attribute_data: Dict[str, float] = {
            "生命值": float(input_attrs.get("生命值", 100000.0)),
            "防御力": float(input_attrs.get("防御力", 500.0)),
        }

        # 初始化元素抗性 (默认为 10%)
        elements = ["火", "水", "风", "雷", "草", "冰", "岩", "物理"]
        for el in elements:
            key = f"{el}元素抗性"
            self.attribute_data[key] = float(input_attrs.get(key, 10.0))

        self.current_hp: float = self.attribute_data["生命值"]

    def handle_damage(self, damage: Any) -> None:
        """处理作用于该目标的伤害逻辑。

        V2.3: 此处目前主要负责触发元素附着逻辑 (ICD 判定)。
        具体的伤害数值扣除逻辑由 HealthSystem 监听事件处理。

        Args:
            damage: 伤害对象 (core.systems.contract.damage.Damage)。
        """
        # 1. 尝试触发元素附着 (Aura Application)
        self.apply_elemental_aura(damage)

        # 2. 标记 Damage 对象已命中该目标
        damage.set_target(self)

    def export_state(self) -> Dict[str, Any]:
        """导出目标的实时仿真状态快照。

        Returns:
            Dict[str, Any]: 包含位置、生命值比例、抗性等信息的字典。
        """
        base = super().export_state()
        base.update(
            {
                "level": self.level,
                "hp_percent": round(
                    (self.current_hp / self.attribute_data["生命值"]) * 100, 2
                ),
                "resistances": {
                    k: v for k, v in self.attribute_data.items() if "抗性" in k
                },
            }
        )
        return base
