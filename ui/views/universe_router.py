from __future__ import annotations

from dataclasses import dataclass

import flet as ft

from ui.states.batch_analysis_state import BatchAnalysisState
from ui.states.batch_editor_state import BatchEditorState
from ui.states.batch_run_state import BatchRunState
from ui.states.batch_universe_state import BatchUniverseState
from ui.views.universe_routes import (
    UNIVERSE_ANALYSIS_ROUTE,
    UNIVERSE_EDITOR_ROUTE,
    UNIVERSE_RUN_ROUTE,
    build_universe_views,
    resolve_universe_route,
)


@ft.observable
@dataclass
class UniverseRouterState:
    route: str

    def route_change(self, e: ft.RouteChangeEvent) -> None:
        self.route = resolve_universe_route(e.route)

    async def view_popped(self, e: ft.ViewPopEvent) -> None:
        views = ft.unwrap_component(ft.context.page.views)
        if len(views) > 1:
            await ft.context.page.push_route(views[-2].route)
            return
        await ft.context.page.push_route(UNIVERSE_EDITOR_ROUTE)


@ft.component
def UniverseRouter(
    universe_state: BatchUniverseState,
    editor_state: BatchEditorState,
    run_state: BatchRunState,
    analysis_state: BatchAnalysisState,
):
    _ = editor_state, run_state, analysis_state
    router, _ = ft.use_state(
        UniverseRouterState(route=resolve_universe_route(ft.context.page.route))
    )

    ft.context.page.on_route_change = router.route_change
    ft.context.page.on_view_pop = router.view_popped

    if router.route not in {
        UNIVERSE_EDITOR_ROUTE,
        UNIVERSE_RUN_ROUTE,
        UNIVERSE_ANALYSIS_ROUTE,
    }:
        router.route = UNIVERSE_EDITOR_ROUTE

    return build_universe_views(router.route, universe_state)
