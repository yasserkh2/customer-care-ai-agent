from app.graph.state import ChatState
from app.services.contracts import EscalationEvaluator
from app.services.escalation import PostTurnEscalationEvaluator


class EvaluateEscalationNode:
    def __init__(self, evaluator: EscalationEvaluator) -> None:
        self._evaluator = evaluator

    def __call__(self, state: ChatState) -> ChatState:
        return self._evaluator.evaluate(state)


_default_node = EvaluateEscalationNode(PostTurnEscalationEvaluator())


def evaluate_escalation(state: ChatState) -> ChatState:
    return _default_node(state)
