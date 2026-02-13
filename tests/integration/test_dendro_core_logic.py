import pytest
from core.context import create_context
from core.entities.base_entity import Faction, CombatEntity
from core.systems.contract.damage import Damage, DamageType
from core.systems.contract.attack import AttackConfig, HitboxConfig, AOEShape
from core.mechanics.aura import Element
from core.entities.elemental_entities import DendroCoreEntity
from core.systems.damage_system import DamageContext
from core.mechanics.icd import ICDManager

class MockCharacter(CombatEntity):
    def __init__(self, name, element):
        super().__init__(name, Faction.PLAYER)
        self.element = element
        self.level = 90
        self.icd_manager = ICDManager(self)
        # 初始化基础属性
        self.attribute_panel = {
            "攻击力": 2000,
            "元素精通": 200,
            "火元素伤害加成": 0,
            "草元素伤害加成": 0,
            "暴击率": 50,
            "暴击伤害": 100,
            "防御力": 800
        }

    def handle_damage(self, damage): pass

class MockEnemy(CombatEntity):
    def __init__(self, name):
        super().__init__(name, Faction.ENEMY)
        self.level = 90
        self.icd_manager = ICDManager(self)
        self.attribute_panel = {
            "防御力": 500,
            "火元素抗性": 10,
            "草元素抗性": 10,
            "水元素抗性": 10,
            "草元素伤害加成": 0 # 辅助计算
        }

    def handle_damage(self, damage):
        damage.set_target(self)
        self.apply_elemental_aura(damage)

    def apply_elemental_aura(self, damage: Damage) -> list:
        # 模拟真实的附着与结果同步逻辑
        results = self.aura.apply_element(damage.element[0], damage.element[1])
        damage.reaction_results.extend(results)
        return results

class TestDendroCoreLogic:
    """
    草原核实体 logic 验证测试。
    """

    @pytest.fixture
    def setup_scene(self):
        ctx = create_context()
        player = MockCharacter("草主", Element.DENDRO)
        enemy = MockEnemy("丘丘人")
        
        # 放置位置
        player.set_position(0, 0)
        enemy.set_position(1, 0) # 1米外
        
        ctx.space.register(player)
        ctx.space.register(enemy)
        
        return ctx, player, enemy

    def test_bloom_spawns_dendro_core(self, setup_scene):
        """验证：水草反应产生草原核"""
        ctx, player, enemy = setup_scene
        
        # 1. 先给敌人挂水 (1.0U)
        hydro_dmg = Damage(0, (Element.HYDRO, 1.0), DamageType.SKILL, "挂水")
        hydro_dmg.set_source(player)
        enemy.handle_damage(hydro_dmg)
        assert any(a.element == Element.HYDRO for a in enemy.aura.auras)
        
        # 2. 草主发起攻击 (1.0U)，配置可部署 (is_deployable=True)
        config = AttackConfig(is_deployable=True, hitbox=HitboxConfig(shape=AOEShape.SINGLE))
        dendro_dmg = Damage(100, (Element.DENDRO, 1.0), DamageType.SKILL, "草攻击", config=config)
        dendro_dmg.set_source(player)
        
        # 通过 DamageSystem 处理，触发 Pipeline
        pipeline = ctx.get_system("DamageSystem").pipeline
        pipeline.run(DamageContext(dendro_dmg, player, enemy))
        
        # 3. 验证场景中是否出现了草原核
        neutrals = ctx.space._entities[Faction.NEUTRAL]
        core = next((e for e in neutrals if isinstance(e, DendroCoreEntity)), None)
        
        assert core is not None
        assert core.name == "草原核"
        # 验证位置在敌人处
        assert core.pos[0] == enemy.pos[0]

    def test_burgeon_reaction(self, setup_scene):
        """验证：火攻击草原核触发烈绽放"""
        ctx, player, enemy = setup_scene
        
        # 1. 手动生成一个草原核
        core = DendroCoreEntity(player, (1.0, 0.0, 0.0))
        ctx.space.register(core)
        
        # 2. 火角色发起攻击 (AOE 圆柱体，覆盖草原核)
        fire_config = AttackConfig(hitbox=HitboxConfig(shape=AOEShape.CYLINDER, radius=2.0))
        fire_dmg = Damage(100, (Element.PYRO, 1.0), DamageType.SKILL, "火攻击", config=fire_config)
        fire_dmg.set_source(player)
        
        pipeline = ctx.get_system("DamageSystem").pipeline
        pipeline.run(DamageContext(fire_dmg, player)) # 无目标广播
        
        # 推进一帧以处理 finish
        ctx.advance_frame()
        
        # 3. 验证草原核是否消失 (触发了 finish)
        assert core not in ctx.space._entities[Faction.NEUTRAL]
        # 列表也应清空
        assert core not in DendroCoreEntity.active_cores

    def test_core_max_limit(self, setup_scene):
        """验证：草原核上限 5 个，第 6 个生成时第 1 个爆炸"""
        ctx, player, enemy = setup_scene
        DendroCoreEntity.active_cores.clear() # 清理静态列表
        
        # 生成 5 个
        cores = []
        for i in range(5):
            c = DendroCoreEntity(player, (float(i), 0, 0))
            ctx.space.register(c)
            cores.append(c)
            
        assert len(DendroCoreEntity.active_cores) == 5
        
        # 生成第 6 个
        c6 = DendroCoreEntity(player, (10, 0, 0))
        ctx.space.register(c6)
        
        # 推进一帧以驱动状态转换
        ctx.advance_frame()

        # 第 1 个应处于销毁状态
        from core.entities.base_entity import EntityState
        assert cores[0].state == EntityState.DESTROYED
        assert len(DendroCoreEntity.active_cores) == 5
        assert cores[0] not in DendroCoreEntity.active_cores
