from typing import Any

# 效果基类
class TalentEffect:
    def __init__(self, name: str):
        self.name = name
        self.character = None
        
    def apply(self, character: Any):
        self.character = character

    def update(self, target: Any):
        pass

class ConstellationEffect:
    def __init__(self, name: str):
        self.name = name
        self.character = None

    def apply(self, character: Any):
        self.character = character

    def update(self, target: Any):
        pass
