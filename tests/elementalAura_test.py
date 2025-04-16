from character.character import Character
from core.Calculation.DamageCalculation import Damage, DamageType
from core.Target import Target


def test_ELECTRO_CHARGED():
    print('test')
    c = Character()
    target = Target(0,103)
    damage = Damage(0,('水',1),DamageType.NORMAL,'测试')
    damage.setSource(c)
    damage.setTarget(target)
    target.apply_elemental_aura(damage)
    damage.element = ('雷',1)
    target.apply_elemental_aura(damage)

    print(target.elementalAura)

    for i in range(200):
        target.update()
        if i == 60:
            damage.element = ('水',2)
            target.apply_elemental_aura(damage)
            damage.element = ('雷',1)
            target.apply_elemental_aura(damage)
    print(target.elementalAura)

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

    print(target.elementalAura)
    for i in range(200):
        target.update()
        if i == 60:
            damage.element = ('风',2)
            target.apply_elemental_aura(damage)
            


    print(target.elementalAura)
