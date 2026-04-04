from app.graph.state import ChatState
from app.services.contracts import IntentClassifier
from app.services.intent import KeywordIntentClassifier


class ClassifyIntentNode:
    def __init__(self, intent_classifier: IntentClassifier) -> None:
        self._intent_classifier = intent_classifier

    def __call__(self, state: ChatState) -> ChatState:
        decision = self._intent_classifier.classify(state)
        return decision.as_state_update()


_default_node = ClassifyIntentNode(KeywordIntentClassifier())


def classify_intent(state: ChatState) -> ChatState:
    return _default_node(state)
