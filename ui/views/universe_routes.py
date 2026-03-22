from __future__ import annotations

import flet as ft

from ui.states.batch_universe_state import BatchUniverseState
from ui.views.universe_analysis_view import UniverseAnalysisView
from ui.views.universe_run_view import UniverseRunView
from ui.views.universe_view import UniverseView

UNIVERSE_EDITOR_ROUTE = "/"
UNIVERSE_RUN_ROUTE = "/run"
UNIVERSE_ANALYSIS_ROUTE = "/analysis"
UNIVERSE_ROUTE_DEFS = {
    UNIVERSE_EDITOR_ROUTE,
    UNIVERSE_RUN_ROUTE,
    UNIVERSE_ANALYSIS_ROUTE,
}


def resolve_universe_route(route: str | None) -> str:
    """将不支持的路由回退到编辑页路由。"""
    candidate = (route or UNIVERSE_EDITOR_ROUTE).split("?", 1)[0].strip()
    if not candidate:
        candidate = UNIVERSE_EDITOR_ROUTE
    if candidate in UNIVERSE_ROUTE_DEFS:
        return candidate
    return UNIVERSE_EDITOR_ROUTE


def build_universe_route_stack(route: str | None) -> list[str]:
    """构建分支宇宙子应用的声明式视图栈。"""
    resolved = resolve_universe_route(route)
    if resolved == UNIVERSE_EDITOR_ROUTE:
        return [UNIVERSE_EDITOR_ROUTE]
    return [UNIVERSE_EDITOR_ROUTE, resolved]


def build_universe_views(
    route: str | None,
    universe_state: BatchUniverseState,
) -> list[ft.View]:
    """根据当前路由栈构建具体 Flet 视图实例。"""
    views: list[ft.View] = []
    for route_item in build_universe_route_stack(route):
        if route_item == UNIVERSE_EDITOR_ROUTE:
            views.append(
                UniverseView(
                    editor_state=universe_state.editor_state,
                    run_state=universe_state.run_state,
                    analysis_state=universe_state.analysis_state,
                    universe_state=universe_state,
                    route=UNIVERSE_EDITOR_ROUTE,
                )
            )
        elif route_item == UNIVERSE_RUN_ROUTE:
            views.append(
                UniverseRunView(
                    state=universe_state.run_state,
                    route=UNIVERSE_RUN_ROUTE,
                )
            )
        elif route_item == UNIVERSE_ANALYSIS_ROUTE:
            views.append(
                UniverseAnalysisView(
                    state=universe_state.analysis_state,
                    route=UNIVERSE_ANALYSIS_ROUTE,
                )
            )
    return views
