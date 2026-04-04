from app.graph.state import ChatState
from app.services.contracts import IntentRouter
from app.services.router import DefaultIntentRouter


class GraphRouter:
    def __init__(self, router: IntentRouter) -> None:
        self._router = router

    def __call__(self, state: ChatState) -> str:
        return self._router.route(state)


_default_router = GraphRouter(DefaultIntentRouter())


def route_intent(state: ChatState) -> str:
    return _default_router(state)
