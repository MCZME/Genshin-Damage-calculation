from .role import Role

class GaMing(Role):
    ID = 1
    def __init__(self,level):
        super().__init__(self.ID)
        self.level = level
        self.get_data(level)

    def get_name(self):
        return self.name

    def get_element(self):
        return self.element
    
    def attributePanel(self):
        pass