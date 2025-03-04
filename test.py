

from artifact.artifact import Artifact,ArtifactPiece,ArtifactManager
from character.GAMING import GaMing
from weapon.SerpentSpine import SerpentSpine


a1 = Artifact('a',ArtifactPiece.Flower_of_Life,{'生命值':1000},{"攻击力%": 18.5,"暴击率": 5.6,"暴击伤害": 62.3,"元素精通": 187})
a2 = Artifact('a',ArtifactPiece.Plume_of_Death,{'攻击力':1000},{"攻击力": 10,"暴击率": 5.5,"暴击伤害": 16.0,"生命值%": 20.0})
a3 = Artifact('a',ArtifactPiece.Sands_of_Eon,{'防御力':1000},{"防御力": 80, "元素精通": 12, "暴击率": 6.0, "元素充能效率": 18.0})
a4 = Artifact('a',ArtifactPiece.Goblet_of_Eonothem,{'元素精通':100},{"攻击力%": 18.0, "防御力%": 25.0, "暴击伤害": 15.0, "生命值%": 15.0})
a5 = Artifact('a',ArtifactPiece.Circlet_of_Logos,{'暴击率':10},{"攻击力%": 8.5,"防御力": 5.6,"暴击伤害": 6.3,"元素精通": 18})

Gaming = GaMing(90,[10,10,10])
weapon = SerpentSpine(Gaming,90,2)
am = ArtifactManager([a1,a2,a3,a4,a5],Gaming)
Gaming.setArtifact(am)
Gaming.setWeapon(weapon)

print(Gaming.attributePanel)