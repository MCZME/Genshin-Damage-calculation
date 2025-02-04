import DataRequest as dr
import json
from artifact import *
from role import *
from weapon import *
from data.Parameter.KVParameter import *

class Calculation:
    def __init__(self):
        self.ArtifactManager = artifact.ArtifactManager()
        self.Role = role.Role()
        self.weapon = weapon.Weapon()

    def attack(self):
        baseAttack = self.Role.attributePanel()['攻击力'] + self.weapon.panel()['攻击力']

        extraAttack_1 = 0
        extraAttack_2 = self.ArtifactManager.getArtifact('pod')['main_stat_value']
        for slot in self.ArtifactManager.GetArtifact().values():
            if slot['main_stat'] == '攻击力%':
                extraAttack_1 += slot['main_stat_value']
            else:
                for sub_stat in slot['sub_stat']:
                    if sub_stat == '攻击力%':
                        extraAttack_1 += slot['sub_stat'][sub_stat]
                    elif sub_stat == '攻击力':
                        extraAttack_2 += slot['sub_stat'][sub_stat]
        
        if self.Role.attributePanel()['攻击力%'] != 0:
            extraAttack_1 += self.Role.attributePanel()['攻击力%']

        extraAttack = (extraAttack_1/100)*baseAttack + extraAttack_2
        return {
            '基础攻击力':baseAttack,
            '额外攻击力':extraAttack,
            '总攻击力':baseAttack+extraAttack
        }

    def damageMultipiler(self):
        pass

    def damageBonus(self):
        pass

    def criticalBracket(self):
        pass

    def defense(self):
        pass

    def resistance(self):
        pass

    def reaction(self):
        pass

    def calculation(self):
        damage = self.attack() * self.damageMultipiler() * (1 + self.damageBonus()) * (1 + self.criticalBracket()) * self.defense() * self.resistance() * self.reaction()
        return damage

    def save(self):
        with open('./data/{}.json'.format(self.Role.name),'w') as f:
            json.dump([self.Role.to_dict(),self.weapon.to_dict(),self.ArtifactManager.to_dict()],f,indent=4)
    
    def load(self,name):
        with open('./data/{}.json'.format(name),'r') as f:
            data = json.load(f)
            self.Role = Parameter_r[data[0]['id']].from_dict(data[0])
            self.weapon = Parameter_w[data[1]['id']].from_dict(data[1])
            for slot in data[2]:
                data[2][slot]['name'] = Parameter_a[data[2][slot]['name']['id']].from_dict(data[2][slot]['name'])
            self.ArtifactManager = artifact.ArtifactManager(data[2])

    # 设置角色、武器、圣遗物
    def setDC(self,role,weapon,artifact):
        self.Role = role
        self.weapon = weapon
        self.ArtifactManager = artifact