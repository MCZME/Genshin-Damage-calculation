"""
月兆系统测试用例。

测试内容：
1. 月兆角色判定
2. 月兆等级计算
3. 月兆效果应用
4. 非月兆角色增益计算
5. 增益覆盖机制
"""

from typing import Any

from core.systems.moonsign_system import MoonsignSystem
from core.effect.common import MoonsignTalent, TalentEffect, MoonsignNascentEffect, MoonsignAscendantEffect


class MockAttributeData:
    """模拟属性数据字典"""
    def __init__(self):
        self._data = {
            "生命值": 30000.0,
            "攻击力": 2000.0,
            "防御力": 800.0,
            "元素精通": 400.0,
        }

    def get(self, key: str, default: float = 0.0) -> float:
        return self._data.get(key, default)


class MockCharacter:
    """模拟角色对象"""

    def __init__(self, name: str, element: str = "水", has_moonsign: bool = False):
        self.name = name
        self.element = element
        self.level = 90
        self.attribute_data = MockAttributeData()
        self.dynamic_modifiers: list[Any] = []
        self.active_effects: list[Any] = []

        # 月兆天赋
        self.talents = []
        if has_moonsign:
            self.talents.append(MoonsignTalent())

    def add_effect(self, effect: Any) -> None:
        """添加效果"""
        self.active_effects.append(effect)

    def remove_effect(self, effect: Any) -> None:
        """移除效果"""
        if effect in self.active_effects:
            self.active_effects.remove(effect)


class MockTeam:
    """模拟队伍"""

    def __init__(self, members: list[MockCharacter]):
        self.members = members

    def get_members(self):
        return self.members


class MockSpace:
    """模拟战斗空间"""

    def __init__(self, team: MockTeam):
        self.team = team


class MockContext:
    """模拟上下文"""

    def __init__(self, team: MockTeam):
        self.space = MockSpace(team)
        self.event_engine = None


class TestMoonsignCharacterDetection:
    """测试月兆角色判定"""

    def test_is_moonsign_character_true(self):
        """测试月兆角色判定为真"""
        system = MoonsignSystem()
        char = MockCharacter("哥伦比娅", has_moonsign=True)

        assert system._is_moonsign_character(char) is True

    def test_is_moonsign_character_false(self):
        """测试非月兆角色判定为假"""
        system = MoonsignSystem()
        char = MockCharacter("普通角色", has_moonsign=False)

        assert system._is_moonsign_character(char) is False

    def test_detect_multiple_moonsign_characters(self):
        """测试检测多个月兆角色"""
        system = MoonsignSystem()

        team = MockTeam([
            MockCharacter("哥伦比娅", has_moonsign=True),
            MockCharacter("菲林斯", has_moonsign=True),
            MockCharacter("普通角色", has_moonsign=False),
        ])

        system.context = MockContext(team)
        system._detect_and_apply_moonsign()

        assert len(system.moonsign_characters) == 2
        assert system.moonsign_characters[0].name == "哥伦比娅"
        assert system.moonsign_characters[1].name == "菲林斯"


class TestMoonsignLevel:
    """测试月兆等级计算"""

    def test_level_zero_no_moonsign(self):
        """测试无月兆角色时等级为0"""
        system = MoonsignSystem()

        team = MockTeam([
            MockCharacter("普通角色1", has_moonsign=False),
            MockCharacter("普通角色2", has_moonsign=False),
        ])

        system.context = MockContext(team)
        system._detect_and_apply_moonsign()

        assert system.moonsign_level == 0
        assert system.get_moonsign_level_name() == "无"

    def test_level_one_single_moonsign(self):
        """测试单月兆角色时等级为1"""
        system = MoonsignSystem()

        team = MockTeam([
            MockCharacter("哥伦比娅", has_moonsign=True),
            MockCharacter("普通角色", has_moonsign=False),
        ])

        system.context = MockContext(team)
        system._detect_and_apply_moonsign()

        assert system.moonsign_level == 1
        assert system.get_moonsign_level_name() == "月兆·初辉"

    def test_level_two_dual_moonsign(self):
        """测试双月兆角色时等级为2"""
        system = MoonsignSystem()

        team = MockTeam([
            MockCharacter("哥伦比娅", has_moonsign=True),
            MockCharacter("菲林斯", has_moonsign=True),
            MockCharacter("普通角色", has_moonsign=False),
        ])

        system.context = MockContext(team)
        system._detect_and_apply_moonsign()

        assert system.moonsign_level == 2
        assert system.get_moonsign_level_name() == "月兆·满辉"

    def test_level_two_triple_moonsign(self):
        """测试三个月兆角色时等级仍为2（满辉）"""
        system = MoonsignSystem()

        team = MockTeam([
            MockCharacter("哥伦比娅", has_moonsign=True),
            MockCharacter("菲林斯", has_moonsign=True),
            MockCharacter("兹白", has_moonsign=True),
            MockCharacter("普通角色", has_moonsign=False),
        ])

        system.context = MockContext(team)
        system._detect_and_apply_moonsign()

        assert system.moonsign_level == 2
        assert system.get_moonsign_level_name() == "月兆·满辉"


class TestMoonsignEffectApplication:
    """测试月兆效果应用"""

    def test_nascent_effect_applied(self):
        """测试初辉效果被应用"""
        system = MoonsignSystem()

        team = MockTeam([
            MockCharacter("哥伦比娅", has_moonsign=True),
            MockCharacter("普通角色", has_moonsign=False),
        ])

        system.context = MockContext(team)
        system._detect_and_apply_moonsign()

        # 检查所有角色都有初辉效果
        for char in team.get_members():
            assert system.has_nascent(char) is True

    def test_ascendant_effect_applied(self):
        """测试满辉效果被应用"""
        system = MoonsignSystem()

        team = MockTeam([
            MockCharacter("哥伦比娅", has_moonsign=True),
            MockCharacter("菲林斯", has_moonsign=True),
            MockCharacter("普通角色", has_moonsign=False),
        ])

        system.context = MockContext(team)
        system._detect_and_apply_moonsign()

        # 检查所有角色都有满辉效果
        for char in team.get_members():
            assert system.has_ascendant(char) is True
            # 满辉也包含初辉
            assert system.has_nascent(char) is True

    def test_no_effect_when_level_zero(self):
        """测试等级为0时无效果"""
        system = MoonsignSystem()

        team = MockTeam([
            MockCharacter("普通角色1", has_moonsign=False),
            MockCharacter("普通角色2", has_moonsign=False),
        ])

        system.context = MockContext(team)
        system._detect_and_apply_moonsign()

        for char in team.get_members():
            assert system.has_nascent(char) is False
            assert system.has_ascendant(char) is False


class TestNonMoonsignBonusCalculation:
    """测试非月兆角色增益计算"""

    def test_fire_element_bonus(self):
        """测试火元素角色增益（基于攻击力）"""
        system = MoonsignSystem()
        char = MockCharacter("火角色", element="火", has_moonsign=False)
        char.attribute_data._data["攻击力"] = 2000.0

        bonus = system._calculate_non_moonsign_bonus(char)

        # 2000攻击力 / 100 * 0.9% = 18%
        assert bonus == 18.0

    def test_water_element_bonus(self):
        """测试水元素角色增益（基于生命值）"""
        system = MoonsignSystem()
        char = MockCharacter("水角色", element="水", has_moonsign=False)
        char.attribute_data._data["生命值"] = 30000.0

        bonus = system._calculate_non_moonsign_bonus(char)

        # 30000生命值 / 1000 * 0.6% = 18%
        assert bonus == 18.0

    def test_geo_element_bonus(self):
        """测试岩元素角色增益（基于防御力）"""
        system = MoonsignSystem()
        char = MockCharacter("岩角色", element="岩", has_moonsign=False)
        char.attribute_data._data["防御力"] = 2000.0

        bonus = system._calculate_non_moonsign_bonus(char)

        # 2000防御力 / 100 * 1% = 20%
        assert bonus == 20.0

    def test_anemo_element_bonus(self):
        """测试风元素角色增益（基于元素精通）"""
        system = MoonsignSystem()
        char = MockCharacter("风角色", element="风", has_moonsign=False)
        char.attribute_data._data["元素精通"] = 800.0

        bonus = system._calculate_non_moonsign_bonus(char)

        # 800元素精通 / 100 * 2.25% = 18%
        assert bonus == 18.0

    def test_dendro_element_bonus(self):
        """测试草元素角色增益（基于元素精通）"""
        system = MoonsignSystem()
        char = MockCharacter("草角色", element="草", has_moonsign=False)
        char.attribute_data._data["元素精通"] = 1000.0

        bonus = system._calculate_non_moonsign_bonus(char)

        # 1000元素精通 / 100 * 2.25% = 22.5%
        assert bonus == 22.5

    def test_bonus_cap(self):
        """测试增益上限"""
        system = MoonsignSystem()
        char = MockCharacter("火角色", element="火", has_moonsign=False)
        char.attribute_data._data["攻击力"] = 10000.0

        bonus = system._calculate_non_moonsign_bonus(char)

        # 理论值 10000/100*0.9 = 90%，但上限36%
        assert bonus == 36.0


class TestNonMoonsignBonusOverride:
    """测试非月兆角色增益覆盖机制"""

    def test_bonus_override(self):
        """测试后施放技能的角色覆盖前者的增益"""
        system = MoonsignSystem()

        # 第一个非月兆角色施放技能
        char1 = MockCharacter("火角色", element="火", has_moonsign=False)
        char1.attribute_data._data["攻击力"] = 2000.0

        system.non_moonsign_bonus = 0.0
        system.non_moonsign_timer = 0
        bonus1 = system._calculate_non_moonsign_bonus(char1)
        system.non_moonsign_bonus = bonus1
        system.non_moonsign_source = char1
        system.non_moonsign_timer = 1200

        assert system.non_moonsign_bonus == 18.0

        # 第二个非月兆角色施放技能（覆盖）
        char2 = MockCharacter("岩角色", element="岩", has_moonsign=False)
        char2.attribute_data._data["防御力"] = 3000.0

        bonus2 = system._calculate_non_moonsign_bonus(char2)
        system.non_moonsign_bonus = bonus2
        system.non_moonsign_source = char2

        # 增益被覆盖
        assert system.non_moonsign_bonus == 30.0
        assert system.non_moonsign_source == char2

    def test_bonus_not_applied_to_moonsign_character(self):
        """测试月兆角色施放技能不触发增益"""
        system = MoonsignSystem()

        char = MockCharacter("哥伦比娅", element="水", has_moonsign=True)
        char.attribute_data._data["生命值"] = 50000.0

        # 月兆角色不应触发增益
        assert system._is_moonsign_character(char) is True


class TestMoonsignEffectClasses:
    """测试月兆效果类"""

    def test_moonsign_nascent_effect_creation(self):
        """测试初辉效果创建"""
        char = MockCharacter("测试角色")
        effect = MoonsignNascentEffect(char)

        assert effect.name == "月兆·初辉"
        assert effect.owner == char
        assert effect.duration == -1  # 永久

    def test_moonsign_ascendant_effect_creation(self):
        """测试满辉效果创建"""
        char = MockCharacter("测试角色")
        effect = MoonsignAscendantEffect(char)

        assert effect.name == "月兆·满辉"
        assert effect.owner == char
        assert effect.duration == -1  # 永久


class TestMoonsignTalentClass:
    """测试月兆天赋类"""

    def test_moonsign_talent_creation(self):
        """测试月兆天赋创建"""
        talent = MoonsignTalent("测试月兆天赋")

        assert talent.name == "测试月兆天赋"
        assert talent.unlock_level == 1

    def test_moonsign_talent_is_subclass_of_talent_effect(self):
        """测试月兆天赋是TalentEffect子类"""
        talent = MoonsignTalent()

        assert isinstance(talent, TalentEffect)
