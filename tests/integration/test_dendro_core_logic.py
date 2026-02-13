import pytest
from core.context import create_context
from core.entities.base_entity import Faction, CombatEntity
from core.systems.contract.damage import Damage
from core.systems.contract.attack import AttackConfig, HitboxConfig, AOEShape
from core.mechanics.aura import Element
from core.entities.elemental_entities import DendroCoreEntity
from core.mechanics.icd import ICDManager
from core.event import GameEvent, EventType
from core.tool import get_current_time

class MockCharacter(CombatEntity):
    def __init__(self, name, element):
        super().__init__(name, Faction.PLAYER)
        self.element = element
        self.level = 90
        self.icd_manager = ICDManager(self)
        self.skill_params = [1, 1, 1]
        self.attribute_data = {
            "攻击力": 2000,
            "元素精通": 200,
            "火元素伤害加成": 0,
            "草元素伤害加成": 0,
            "暴击率": 50,
            "暴击伤害": 100,
            "防御力": 800,
            "生命值": 20000,
            "固定生命值": 0,
            "生命值%": 0
        }

    def handle_damage(self, damage): pass

class MockEnemy(CombatEntity):
    def __init__(self, name):
        super().__init__(name, Faction.ENEMY)
        self.level = 90
        self.icd_manager = ICDManager(self)
        self.attribute_data = {
            "防御力": 500,
            "火元素抗性": 10,
            "草元素抗性": 10,
            "水元素抗性": 10,
            "草元素伤害加成": 0 
        }

    def handle_damage(self, damage):
        damage.set_target(self)
        self.apply_elemental_aura(damage)

class TestDendroCoreLogic:
    @pytest.fixture
    def setup_scene(self):
        ctx = create_context()
        player = MockCharacter("草主", Element.DENDRO)
        enemy = MockEnemy("丘丘人")
        player.set_position(0, 0)
        enemy.set_position(1, 0)
        ctx.space.register(player)
        ctx.space.register(enemy)
        return ctx, player, enemy

    def test_bloom_spawns_dendro_core(self, setup_scene):
        """验证：水草反应产生草原核"""
        ctx, player, enemy = setup_scene
        hydro_dmg = Damage(
            element=(Element.HYDRO, 1.0),
            damage_multiplier=0,
            scaling_stat="攻击力",
            name="挂水",
            config=AttackConfig(icd_tag="Independent") # 确保挂上
        )
        hydro_dmg.set_source(player)
        enemy.handle_damage(hydro_dmg)
        assert any(a.element == Element.HYDRO for a in enemy.aura.auras)
        
        config = AttackConfig(is_deployable=True, hitbox=HitboxConfig(shape=AOEShape.SINGLE), icd_tag="Independent")
        dendro_dmg = Damage(
            element=(Element.DENDRO, 1.0),
            damage_multiplier=100.0,
            scaling_stat="攻击力",
            name="草攻击",
            config=config
        )
        dendro_dmg.set_source(player)
        
        # 通过事件引擎发布，触发 DamageSystem -> ReactionSystem 的完整链条
        ctx.event_engine.publish(GameEvent(
            EventType.BEFORE_DAMAGE, 
            get_current_time(), 
            source=player, 
            data={'character': player, 'target': enemy, 'damage': dendro_dmg}
        ))
        
        neutrals = ctx.space._entities[Faction.NEUTRAL]
        core = next((e for e in neutrals if isinstance(e, DendroCoreEntity)), None)
        assert core is not None
        assert core.pos[0] == enemy.pos[0]

    def test_burgeon_reaction(self, setup_scene):
        """验证：火攻击草原核触发烈绽放"""
        ctx, player, enemy = setup_scene
        core = DendroCoreEntity(player, (1.0, 0.0, 0.0))
        ctx.space.register(core)
        
        fire_config = AttackConfig(hitbox=HitboxConfig(shape=AOEShape.CYLINDER, radius=2.0))
        fire_dmg = Damage(
            element=(Element.PYRO, 1.0),
            damage_multiplier=100.0,
            scaling_stat="攻击力",
            name="火攻击",
            config=fire_config
        )
        fire_dmg.set_source(player)
        
        # 使用事件引擎
        ctx.event_engine.publish(GameEvent(
            EventType.BEFORE_DAMAGE, 
            get_current_time(), 
            source=player, 
            data={'character': player, 'damage': fire_dmg}
        ))
        
        ctx.advance_frame()
        # 被销毁的实体应从空间移除
        assert core not in ctx.space._entities[Faction.NEUTRAL]

    def test_core_max_limit(self, setup_scene):
        """验证：草原核上限 5 个，第 6 个生成时第 1 个爆炸"""
        ctx, player, enemy = setup_scene
        # 清理已有核心 (避免干扰)
        ctx.space._entities[Faction.NEUTRAL].clear()
        DendroCoreEntity.active_cores.clear()
        
        cores = []
        for i in range(5):
            c = DendroCoreEntity(player, (float(i), 0, 0))
            ctx.space.register(c)
            cores.append(c)
            
        c6 = DendroCoreEntity(player, (10, 0, 0))
        ctx.space.register(c6)
        ctx.advance_frame()
        # 第 1 个应处于 FINISHING 或 DESTROYED 状态，且不在活跃列表
        from core.entities.base_entity import EntityState
        assert cores[0].state in [EntityState.FINISHING, EntityState.DESTROYED]
