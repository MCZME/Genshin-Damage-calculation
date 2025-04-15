import sys
sys.path.append("E:\\project\\Genshin Damage calculation\\")
sys.path.remove('e:\\project\\Genshin Damage calculation\\tests')
print(sys.path)
from setup.Target import Target


target = Target(0,103)
target.apply_elemental_aura(('雷',1))
print(target.elementalAura)
target.apply_elemental_aura(('水',1))
print(target.elementalAura)
for _ in range(200):
    target.update()

print(target.elementalAura)