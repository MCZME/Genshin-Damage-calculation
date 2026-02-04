from enum import Enum
from artifact.ArtfactSetEffectDict import ArtfactSetEffectDict
from character.character import Character

class ArtifactPiece(Enum):
    Flower_of_Life = 0
    Plume_of_Death = 1
    Sands_of_Eon = 2
    Goblet_of_Eonothem = 3
    Circlet_of_Logos = 4

class Artifact:
    def __init__(self,name,piece:ArtifactPiece,main=None,sub=None):
        self.name = name
        self.piece = piece
        if main == None:
            raise Exception("圣遗物主属性不能为空")
        else:
            self.main = main
        if sub == None:
            self.sub = {}
        else:
            self.sub = sub
    
    def getMain(self):
        return self.main

    def getSub(self):
        return self.sub
    
    def to_dict(self):
        return {
            'name': self.name,
            'piece': self.piece.name,
            'main': self.main,
            'sub': self.sub
        }

class ArtifactManager:

    def __init__(self,set:list[Artifact],character:Character):
        self.character = character
        self.Set = {
        'Flower_of_Life':None,
        'Plume_of_Death':None,
        'Sands_of_Eon':None,
        'Goblet_of_Eonothem':None,
        'Circlet_of_Logos':None
        }
        for artifact in set:
            if artifact.piece == ArtifactPiece.Flower_of_Life:
                self.Set['Flower_of_Life'] = artifact
            elif artifact.piece == ArtifactPiece.Plume_of_Death:
                self.Set['Plume_of_Death'] = artifact
            elif artifact.piece == ArtifactPiece.Sands_of_Eon:
                self.Set['Sands_of_Eon'] = artifact
            elif artifact.piece == ArtifactPiece.Goblet_of_Eonothem:
                self.Set['Goblet_of_Eonothem'] = artifact
            elif artifact.piece == ArtifactPiece.Circlet_of_Logos:  
                self.Set['Circlet_of_Logos'] = artifact
    
    def updatePanel(self):
        panel = {}
        for artifact in self.Set.values():
            if artifact != None:
                t = artifact.getMain()
                k = list(t.keys())[0]
                if k not in panel.keys():
                    panel[k] = t[k]
                else:
                    panel[k] += t[k]
                t = artifact.getSub()
                for key in t.keys():
                    if key not in panel.keys():
                        panel[key] = t[key]
                    else:
                        panel[key] += t[key]
        
        attributePanel = self.character.attributePanel
        for key in panel.keys():
            if key == '攻击力':
                attributePanel['固定攻击力'] += panel[key]
            elif key == '生命值':
                attributePanel['固定生命值'] += panel[key]
            elif key == '防御力':
                attributePanel['固定防御力'] += panel[key]
            else:
                attributePanel[key] += panel[key]
        
    
    def setEffect(self):
        setEffect = {}
        for artifact in self.Set.values():
            if artifact != None:
                if artifact.name not in setEffect.keys():
                    setEffect[artifact.name] = 1
                else:
                    setEffect[artifact.name] += 1
        
        for key in setEffect.keys():
            if setEffect[key] >= 4:
                a = ArtfactSetEffectDict[key]()
                a.four_SetEffect(self.character)
                a.tow_SetEffect(self.character)
            elif setEffect[key] >= 2 and setEffect[key] < 4:
                ArtfactSetEffectDict[key]().tow_SetEffect(self.character)
    
    def to_dict(self):
        return {
            'set': [artifact.to_dict() for artifact in self.Set.values() if artifact]
        }
