from app.agents import ActionRequestAgent
from app.graph.state import ChatState
from app.llm.action_factory import ActionReplyGeneratorFactory
from app.llm.action_extraction import AppointmentExtractorFactory
from app.services.action_request import AppointmentActionService
from app.services.booking_api import LocalMockBookingApiClient


class ActionRequestNode:
    def __init__(self, agent: ActionRequestAgent) -> None:
        self._agent = agent

    def __call__(self, state: ChatState) -> ChatState:
        return self._agent.execute(state)

_default_node = ActionRequestNode(
    ActionRequestAgent(
        AppointmentActionService(
            extractor=AppointmentExtractorFactory().build(),
            booking_api_client=LocalMockBookingApiClient(),
            response_generator=ActionReplyGeneratorFactory().build(),
        )
    )
)


def action_request(state: ChatState) -> ChatState:
    return _default_node(state)
