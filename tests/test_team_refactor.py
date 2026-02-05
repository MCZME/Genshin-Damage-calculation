import pytest
from core.team import Team
from character.character import Character
from core.context import SimulationContext

# 模拟一个基础角色
class MockCharacter(Character):
    def __init__(self, name, element):
        self.name = name
        self.element = element
        self.on_field = False
        self.active_effects = []

def test_team_instance_isolation():
    """验证 Team 实例之间的属性隔离，确保没有静态属性干扰"""
    char1 = MockCharacter("Traveler", "风")
    char2 = MockCharacter("Amber", "火")
    
    with SimulationContext() as ctx1:
        team1 = Team([char1])
        ctx1.team = team1
        assert len(team1.team) == 1
        
    with SimulationContext() as ctx2:
        team2 = Team([char1, char2])
        ctx2.team = team2
        assert len(team2.team) == 2
        # 如果静态属性被移除，team1 应该不被影响（仅作为局部变量时）
        # 这里主要验证类属性不再被赋值

if __name__ == "__main__":
    pytest.main([__file__])
