from DataRequest import DR
from DataProcessing import DataProcessing as DP

class Artifact:
    def __init__(self,id=1):
        self.id = id
        SQL = "SELECT * FROM artifact WHERE id = {}".format(id)
        self.data = DR.read_data(SQL)[0]
        self.name = self.data[1]

    def tow_SetEffect(self):
        ...

    def four_SetEffect(self):
        ...

    def to_dict(self):
        return {
            'id':self.id,
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls()

class ArtifactManager:
    artifact = {
                    'fol':{
                        'name':Artifact(1),
                        'level':20,
                        'main_stat':'生命值',
                        'main_stat_value':4780,
                        'sub_stat':{
                            
                        }
                    },
                    'pod':{
                        'name':Artifact(1),
                        'level':20,
                        'main_stat':'攻击力',
                        'main_stat_value':311,
                        'sub_stat':{
                            
                        }
                    },
                    'soe':{
                        'name':Artifact(1),
                        'level':20,
                        'main_stat':'攻击力%',
                        'main_stat_value':0,
                        'sub_stat':{
                            
                        }
                    },
                    'goe':{
                        'name':Artifact(1),
                        'level':20,
                        'main_stat':'攻击力%',
                        'main_stat_value':0,
                        'element':'empty',
                        'sub_stat':{
                            
                        }
                    },
                    'col':{
                        'name':Artifact(1),
                        'level':20,
                        'main_stat':'攻击力%',
                        'main_stat_value':0,
                        'sub_stat':{
                            
                        }
                    }
                }
    def __init__(self,artifact:dict=None):
        if artifact:
            self.artifact = artifact
        
    def setSlot(self,slot,artifact,main_stat_value,sub_stat:dict,level=20):
        self.artifact[slot]['name'] = artifact
        self.artifact[slot]['level'] = level
        self.setMainStat(slot,main_stat_value)
        for key in sub_stat:
            self.setSubStat(slot,key,sub_stat[key])

    def SetSlot(self,slot,artifact,main_stat,main_stat_value,sub_stat:dict,level=20):
        self.artifact[slot]['name'] = artifact
        self.artifact[slot]['level'] = level
        self.setMainStat(slot,main_stat,main_stat_value)
        for key in sub_stat:
            self.setSubStat(slot,key,sub_stat[key])

    def setMainStat(self,slot,main_stat,main_stat_value):
        self.artifact[slot]['main_stat'] = main_stat
        self.artifact[slot]['main_stat_value'] = main_stat_value
    
    def SetMainStat(self,slot,main_stat_value):
        self.artifact[slot]['main_stat_value'] = main_stat_value
    
    def setSubStat(self,slot,sub_stat,sub_stat_value):
        self.artifact[slot]['sub_stat'][sub_stat] = sub_stat_value

    def GetArtifact(self):
        return self.artifact
    
    def getArtifact(self,slot):
        return self.artifact[slot]
    
    def getArtfifactSetEffect(self):
        T={}
        for slot in self.artifact:
            if slot['name'] in T.keys():
                T[slot['name']] += 1
            else:
                T[slot['name']] = 1
        
        for artifact in T:
            if T[artifact] >= 2:
                artifact.tow_SetEffect()
            elif T[artifact] >= 4:
                artifact.four_SetEffect()
    
    def to_dict(self):
        t= self.artifact
        for slot in t:
            t[slot]['name'] = t[slot]['name'].to_dict()
        return t
