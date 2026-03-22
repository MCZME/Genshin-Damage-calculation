from ui.universe_launcher import (
    UNIVERSE_ANALYSIS_ROUTE,
    UNIVERSE_EDITOR_ROUTE,
    UNIVERSE_RUN_ROUTE,
    build_universe_route_stack,
    resolve_universe_route,
)


def test_resolve_universe_route_editor_kept():
    assert resolve_universe_route(UNIVERSE_EDITOR_ROUTE) == UNIVERSE_EDITOR_ROUTE


def test_resolve_universe_route_unknown_fallback_to_editor():
    assert resolve_universe_route("/batch/run") == UNIVERSE_EDITOR_ROUTE


def test_resolve_universe_route_empty_fallback_to_editor():
    assert resolve_universe_route("") == UNIVERSE_EDITOR_ROUTE


def test_resolve_universe_route_run_and_analysis_kept():
    assert resolve_universe_route(UNIVERSE_RUN_ROUTE) == UNIVERSE_RUN_ROUTE
    assert resolve_universe_route(UNIVERSE_ANALYSIS_ROUTE) == UNIVERSE_ANALYSIS_ROUTE


def test_build_universe_route_stack_editor_only():
    assert build_universe_route_stack("/unknown") == [UNIVERSE_EDITOR_ROUTE]
    assert build_universe_route_stack(UNIVERSE_EDITOR_ROUTE) == [UNIVERSE_EDITOR_ROUTE]


def test_build_universe_route_stack_run():
    assert build_universe_route_stack(UNIVERSE_RUN_ROUTE) == [UNIVERSE_RUN_ROUTE]


def test_build_universe_route_stack_analysis():
    assert build_universe_route_stack(UNIVERSE_ANALYSIS_ROUTE) == [
        UNIVERSE_ANALYSIS_ROUTE
    ]
