from app.graph.state import ChatState
from app.observability import get_logger, summarize_state
from app.services.contracts import IntentRouter

logger = get_logger("graph.router")


class ActiveFlowRouter:
    def __call__(self, state: ChatState) -> str:
        if state.get("handoff_pending"):
            has_contact_channel = bool(
                state.get("escalation_contact_email")
                or state.get("escalation_contact_phone")
            )
            route = "human_escalation" if has_contact_channel else "classify_intent"
        elif state.get("active_action") == "appointment_scheduling":
            route = "action_request"
        else:
            route = "classify_intent"
        logger.info("active_flow route=%s state=%s", route, summarize_state(state))
        return route


class GraphRouter:
    def __init__(self, router: IntentRouter) -> None:
        self._router = router

    def __call__(self, state: ChatState) -> str:
        route = self._router.route(state)
        logger.info(
            "intent route=%s intent=%s confidence=%s",
            route,
            state.get("intent"),
            state.get("confidence"),
        )
        return route

class PostTurnRouter:
    def __call__(self, state: ChatState) -> str:
        if state.get("handoff_pending"):
            route = "human_escalation"
        else:
            route = "response"
        logger.info("post_turn route=%s state=%s", route, summarize_state(state))
        return route


class ServiceResultRouter:
    def __call__(self, state: ChatState) -> str:
        if state.get("handoff_pending"):
            route = "human_escalation"
        elif state.get("turn_outcome") == "resolved" and not state.get("frustration_flag"):
            route = "response"
        else:
            route = "evaluate_escalation"
        logger.info("service_result route=%s state=%s", route, summarize_state(state))
        return route
