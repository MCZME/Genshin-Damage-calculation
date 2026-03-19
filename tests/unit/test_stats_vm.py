from types import SimpleNamespace

from ui.view_models.analysis.tile_vms.stats_vm import StatsViewModel
from ui.view_models.analysis.tile_vms.types import ModifierZone


class _DummyDataService:
    def __init__(self, char_base: dict[int, dict]):
        self._slot = SimpleNamespace(data=char_base)

    def get_cached(self, key: str):
        if key == "char_base":
            return self._slot
        return None


class _DummyMainVm:
    def __init__(self):
        self.current_frame = 0
        self.app_state = None

    def get_stat_preferences(self, _char_id: int):
        return None

    def get_status_bar_selection(self, _instance_id: str):
        return None

    def toggle_status_bar_selection(self, _instance_id: str, _selection: str):
        return None


class _DummyState:
    def __init__(self, char_base: dict[int, dict]):
        self.vm = _DummyMainVm()
        self.data_service = _DummyDataService(char_base)


def test_get_stat_breakdown_includes_base_panel_attack_bonus_sources():
    state = _DummyState({
        1: {
            "攻击力": 1000.0,
            "攻击力%": 20.0,
            "固定攻击力": 311.0,
        }
    })
    vm = StatsViewModel(state, "stats-test", initial_char_id=1)
    vm.snapshot = {
        "team": [
            {
                "entity_id": 1,
                "active_modifiers": [
                    {"name": "测试 Buff", "stat": "攻击力%", "value": 30.0, "op": "ADD"},
                ],
            }
        ]
    }
    vm._cache_frame_id = vm.frame_id

    result, zoned_mods = vm.get_stat_breakdown("攻击力")

    assert result.pct_sum == 50.0
    assert result.flat_sum == 311.0
    assert result.total == 1811.0

    assert any(
        m.name == "[基础面板]" and m.stat == "攻击力%" and m.value == 20.0 and m.zone == ModifierZone.PERCENT
        for m in zoned_mods
    )
    assert any(
        m.name == "[基础面板]" and m.stat == "固定攻击力" and m.value == 311.0 and m.zone == ModifierZone.FLAT
        for m in zoned_mods
    )


def test_cumulative_stat_uses_direct_attack_mod_as_base_before_percent():
    state = _DummyState({
        1: {
            "攻击力": 1000.0,
            "攻击力%": 20.0,
            "固定攻击力": 311.0,
        }
    })
    vm = StatsViewModel(state, "stats-test", initial_char_id=1)
    vm.snapshot = {
        "team": [
            {
                "entity_id": 1,
                "active_modifiers": [
                    {"name": "武器基础攻击", "stat": "攻击力", "value": 200.0, "op": "ADD"},
                    {"name": "测试 Buff", "stat": "攻击力%", "value": 30.0, "op": "ADD"},
                ],
            }
        ]
    }
    vm._cache_frame_id = vm.frame_id

    result, zoned_mods = vm.get_stat_breakdown("攻击力")

    assert result.base == 1000.0
    assert result.pct_sum == 50.0
    assert result.flat_sum == 311.0
    assert result.total == 2111.0
    assert any(
        m.name == "武器基础攻击" and m.stat == "攻击力" and m.value == 200.0 and m.zone == ModifierZone.BASE
        for m in zoned_mods
    )


def test_get_relevant_mods_includes_base_panel_hp_bonus_sources():
    state = _DummyState({
        1: {
            "生命值": 10000.0,
            "生命值%": 46.6,
            "固定生命值": 4780.0,
        }
    })
    vm = StatsViewModel(state, "stats-test", initial_char_id=1)
    vm.snapshot = {
        "team": [
            {
                "entity_id": 1,
                "active_modifiers": [],
            }
        ]
    }
    vm._cache_frame_id = vm.frame_id

    relevant_mods = vm.get_relevant_mods("生命值")

    assert {"name": "[基础面板]", "stat": "生命值%", "value": 46.6, "op": "ADD"} in relevant_mods
    assert {"name": "[基础面板]", "stat": "固定生命值", "value": 4780.0, "op": "ADD"} in relevant_mods
