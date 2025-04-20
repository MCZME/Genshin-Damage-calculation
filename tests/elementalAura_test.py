from character.character import Character
from core.calculation.DamageCalculation import Damage, DamageType
from core.Target import Target


def test_ELECTRO_CHARGED():
    print('感电测试')
    element = {0:'火',1:'风',2:'岩'}
    for e in range(3):
        c = Character()
        target = Target(0,103)
        damage = Damage(0,('水',1),DamageType.NORMAL,'测试')
        damage.setSource(c)
        damage.setTarget(target)
        target.apply_elemental_aura(damage)
        damage.element = ('雷',1)
        target.apply_elemental_aura(damage)

        print(target.aura.elementalAura)

        for i in range(200):
            target.update()
            if i == 30:
                damage.element = (element[e],2)
                target.apply_elemental_aura(damage)
                print(target.aura.elementalAura)

        print(f"--------第{e}测试结束--------")

def test_SWIRL():
    print('test')
    c = Character()
    target = Target(0,103)
    damage = Damage(0,('水',1),DamageType.NORMAL,'测试')
    damage.setSource(c)
    damage.setTarget(target)
    target.apply_elemental_aura(damage)
    damage.element = ('雷',1)
    target.apply_elemental_aura(damage)

    print(target.aura.elementalAura)
    for i in range(200):
        target.update()
        if i == 60:
            damage.element = ('风',2)
            target.apply_elemental_aura(damage)

    print(target.aura.elementalAura)

def test_FREEZE():
    print('冻结反应测试')
    element = {0:'火',1:'风',2:'岩',3:'雷'}
    for e in range(4):
        c = Character()
        target = Target(0,103)
        damage = Damage(0,('水',2),DamageType.NORMAL,'测试')
        damage.setSource(c)
        damage.setTarget(target)
        target.apply_elemental_aura(damage)
        damage.element = ('冰',1)
        target.apply_elemental_aura(damage)
        target.update()
        # damage.element = ('水',1)
        # target.apply_elemental_aura(damage)

        print(target.aura.elementalAura)

        for i in range(200):
            target.update()
            if i == 40:
                damage.element = (element[e],2)
                target.apply_elemental_aura(damage)
                print(target.aura.elementalAura)

        print(f"--------第{e}测试结束--------")


def test_BURNING():
    print('燃烧测试')
    e = {0:'水',1:'草',2:'冰',3:'岩',4:'雷',5:'风',6:'火'}
    for n in range(7):
        c = Character()
        target = Target(0,103)
        damage = Damage(0,('火',1),DamageType.NORMAL,'测试')
        damage.setSource(c)
        damage.setTarget(target)
        target.apply_elemental_aura(damage)
        damage.element = ('草',1)
        target.apply_elemental_aura(damage)

        print(target.aura.elementalAura)
        print(target.aura.burning_elements)

        for i in range(200):
            target.update()
            if i == 60:
                damage.element = (e[n],1)
                target.apply_elemental_aura(damage)

        print(target.aura.elementalAura)
        print(target.aura.burning_elements)
        print(f"--------第{n}测试结束--------")