from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from character.character import Character

class Weapon:
    def __init__(self, character: Character, id=1, level=1, lv=1, base_data: dict = None):
        self.character = character
        self.id = id
        self.level = level
        self.lv = lv
        self.attributeData = {
            "攻击力": 0, "元素精通": 0, "暴击率": 0, "暴击伤害": 0, "治疗加成": 0,
            "受治疗加成": 0, "元素充能效率": 0, "生命值%": 0, "攻击力%": 0, "防御力%": 0,
            "火元素伤害加成": 0, "水元素伤害加成": 0, "雷元素伤害加成": 0, "冰元素伤害加成": 0,
            "岩元素伤害加成": 0, "风元素伤害加成": 0, "草元素伤害加成": 0, "物理伤害加成": 0
        }

        if base_data:
            self.name = base_data.get('name', 'Unknown')
            # 填充基础数值
            self.attributeData["攻击力"] = base_data.get('base_atk', 0)
            
            # 处理副词条
            sub_name = base_data.get('secondary_attribute')
            sub_val = base_data.get('secondary_value', 0)
            if sub_name and sub_name in self.attributeData:
                self.attributeData[sub_name] = sub_val
        else:
            self.name = "Unknown"

    def updatePanel(self):
        attributePanel = self.character.attributePanel
        for i in self.attributeData:
            attributePanel[i] += self.attributeData[i]

    def skill(self):
        ...

    def update(self,target):
        ...

    def to_dict(self):
        return {
            'id': self.id,
            'level': self.level,
            'lv': self.lv
        }
