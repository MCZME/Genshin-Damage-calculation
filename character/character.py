from abc import abstractmethod
from DataRequest import DR
import setup.Tool as T

class Character:
    def __init__(self,id=1,level=1,skill_level=[1,1,1]):
        self.id = id
        self.level = level
        self.skill_level = skill_level
        self.attributeData ={
            "生命值" : 0,
            "攻击力": 0,
            "固定攻击力":0,
            "防御力": 0,
            "元素精通" : 0,
            "暴击率" : 5,
            "暴击伤害" : 50,
            "治疗加成" : 0,
            "受治疗加成" : 0,
            "元素充能效率" : 100,
            "生命值%" : 0,
            "攻击力%": 0,
            "防御力%": 0,
            "火元素伤害加成": 0,
            "水元素伤害加成": 0,
            "雷元素伤害加成": 0,
            "冰元素伤害加成": 0,
            "岩元素伤害加成": 0,
            "风元素伤害加成": 0,
            "草元素伤害加成": 0,
            "物理伤害加成": 0
        }

        SQL = "SELECT * FROM `role_stats` WHERE role_id = {}".format(self.id)
        self.data = DR.read_data(SQL)[0]
        self.name = self.data[1]
        self.element = self.data[2]
        self.get_data(level)
        self.attributePanel = self.attributeData.copy()

        self._init_character()    # 初始化特有属性

    def get_data(self,level):
        l = T.level(level)
        self.attributeData["生命值"] = self.data[5+l]
        self.attributeData["攻击力"] = self.data[13+l]
        self.attributeData["防御力"] = self.data[21+l]
        t = T.attributeId(self.data[-1])
        if t != "元素伤害加成":
            self.attributeData[t] = self.data[29+l]
        else:
            self.attributeData[self.element+t] = self.data[29+l]

    @abstractmethod
    def _init_character(self):
        """初始化角色特有属性"""
        self.skill_params = {}    # 技能参数表
        self.talent_effects = []  # 天赋效果列表

    def setArtifact(self,artifact):
        self.artifactManager = artifact
        self.artifactManager.updatePanel()

    def setWeapon(self,weapon):
        self.weapon = weapon
        self.weapon.updatePanel()


    def normal_attack(self):
        """普攻"""
        self._normal_attack_impl()

    @abstractmethod
    def _normal_attack_impl(self):
        """普攻具体实现"""

    def heavy_attack(self):
        """重击（需体力）"""
        self._heavy_attack_impl()
    
    @abstractmethod
    def _heavy_attack_impl(self):
        """重击具体实现"""

    def elemental_skill(self):
        """元素战技"""
        self._elemental_skill_impl()
    
    @abstractmethod
    def _elemental_skill_impl(self):
        """元素战技具体实现"""
    
    def elemental_burst(self):
        """元素爆发"""
        self._elemental_burst_impl()

    @abstractmethod
    def _elemental_burst_impl(self):
        """元素爆发具体实现"""

    def apply_talents(self):
        """应用天赋效果"""
        for effect in self.talent_effects:
            effect.apply(self)


    def update(self):
        pass