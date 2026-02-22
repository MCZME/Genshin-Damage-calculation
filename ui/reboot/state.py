class StrategicState:
    """
    战略视图的状态管理器。
    负责维护 4 人编队的静态资产配置。
    """
    def __init__(self):
        # 1. 成员数据 (4 人编队)
        self.team_data = [self._create_empty_member() for _ in range(4)]
        self.current_index = 0
        self.current_tab = "Character"
        
        # 2. 目标实体列表 (支持多目标)
        self.targets = [self._create_target_instance("target_0", "遗迹守卫")]
        self.selected_target_index = 0 # 当前选中的目标索引
        
        # 3. 战场空间 (坐标单位: 米)
        self.spatial_data = {
            "player_pos": {"x": 0.0, "z": 0.0},
            "target_positions": {
                "target_0": {"x": 0.0, "z": 5.0} # 默认距离 5 米
            }
        }
        
        # 4. 场景与环境共鸣
        self.scene_data = {
            "weather": "Clear", # Clear, Rain, etc.
            "field": "Neutral", # Grass, Water, etc.
            "manual_buffs": []  # 自定义增益
        }

    def _create_target_instance(self, target_id, name="新目标"):
        return {
            "id": target_id,
            "name": name,
            "level": "90",
            "resists": {
                "火": "10", "水": "10", "草": "10", "雷": "10", 
                "风": "10", "冰": "10", "岩": "10", "物理": "10"
            }
        }

    def add_target(self, name="遗迹守卫"):
        new_id = f"target_{len(self.targets)}"
        new_target = self._create_target_instance(new_id, name)
        self.targets.append(new_target)
        self.spatial_data["target_positions"][new_id] = {"x": 0.0, "z": 5.0}
        self.selected_target_index = len(self.targets) - 1

    def remove_target(self, index):
        if len(self.targets) > 1:
            target_id = self.targets[index]['id']
            self.targets.pop(index)
            if target_id in self.spatial_data["target_positions"]:
                del self.spatial_data["target_positions"][target_id]
            self.selected_target_index = min(self.selected_target_index, len(self.targets) - 1)

    @property
    def current_target(self):
        return self.targets[self.selected_target_index]

    def _create_empty_member(self):
        return {
            "id": None,
            "name": "Empty Slot",
            "element": "Neutral",
            "level": "90",
            "constellation": "0",
            "talents": {"na": "10", "e": "10", "q": "10"},
            "weapon": {"id": None, "level": "90", "refinement": "1"},
            "artifacts": {
                "Flower": {"name": "", "main": "生命值", "main_val": "4780", "subs": [["暴击率%", "0.0"], ["暴击伤害%", "0.0"], ["攻击力%", "0.0"], ["元素精通", "0"]]},
                "Plume": {"name": "", "main": "攻击力", "main_val": "311", "subs": [["暴击率%", "0.0"], ["暴击伤害%", "0.0"], ["攻击力%", "0.0"], ["元素精通", "0"]]},
                "Sands": {"name": "", "main": "攻击力%", "main_val": "46.6", "subs": [["暴击率%", "0.0"], ["暴击伤害%", "0.0"], ["生命值%", "0.0"], ["元素精通", "0"]]},
                "Goblet": {"name": "", "main": "火元素伤害加成%", "main_val": "46.6", "subs": [["暴击率%", "0.0"], ["暴击伤害%", "0.0"], ["攻击力%", "0.0"], ["元素精通", "0"]]},
                "Circlet": {"name": "", "main": "暴击率%", "main_val": "31.1", "subs": [["暴击伤害%", "0.0"], ["攻击力%", "0.0"], ["生命值%", "0.0"], ["元素精通", "0"]]},
            }
        }

    @property
    def current_member(self):
        return self.team_data[self.current_index]

    def select_member(self, index: int):
        self.current_index = index

    def add_member(self, index: int, char_data: dict):
        """初始化并分配成员基础数据"""
        new_member = self._create_empty_member()
        new_member.update({
            "id": char_data['id'],
            "name": char_data['name'],
            "element": char_data.get('element', 'Neutral'),
            "type": char_data.get('type', '单手剑'), # 同步武器类型
            "rarity": char_data.get('rarity', 5)
        })
        self.team_data[index] = new_member

    def remove_member(self, index: int):
        """清空成员数据"""
        self.team_data[index] = self._create_empty_member()

    def update_current_member(self, key: str, value):
        self.team_data[self.current_index][key] = value

    def to_config_dict(self):
        """序列化为标准 Config 对象"""
        return self.team_data
