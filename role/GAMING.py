from .role import Role

class GaMing(Role):
    ID = 78
    def __init__(self,level):
        super().__init__(self.ID,level)
    
    def attributePanel(self):
        return self.attributeData