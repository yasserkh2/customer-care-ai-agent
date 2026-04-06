from app.graph.state import ChatState
from app.services.contracts import IntentRouter
from app.services.router import DefaultIntentRouter


class ActiveFlowRouter:
    def __call__(self, state: ChatState) -> str:
        if state.get("handoff_pending"):
            return "human_escalation"
        if state.get("active_action") == "appointment_scheduling":
            return "action_request"
        return "classify_intent"


class GraphRouter:
    def __init__(self, router: IntentRouter) -> None:
        self._router = router

    def __call__(self, state: ChatState) -> str:
        return self._router.route(state)


_default_active_flow_router = ActiveFlowRouter()
_default_router = GraphRouter(DefaultIntentRouter())


class PostTurnRouter:
    def __call__(self, state: ChatState) -> str:
        if state.get("handoff_pending"):
            return "human_escalation"
        return "response"


class ServiceResultRouter:
    def __call__(self, state: ChatState) -> str:
        if state.get("handoff_pending"):
            return "human_escalation"
        return "evaluate_escalation"


def route_active_flow(state: ChatState) -> str:
    return _default_active_flow_router(state)


def route_intent(state: ChatState) -> str:
    return _default_router(state)


def route_post_turn(state: ChatState) -> str:
    return PostTurnRouter()(state)


def route_service_result(state: ChatState) -> str:
    return ServiceResultRouter()(state)
