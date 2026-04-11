from __future__ import annotations

from collections.abc import Callable

from app.agents.contracts import StateAgent
from app.graph.state import ChatState
from app.mock_api.escalation_api import persist_escalation
from app.observability import get_logger, summarize_state, summarize_update
from app.services.contracts import EscalationService

logger = get_logger("agents.escalation")

EscalationRecorder = Callable[[ChatState], str]


def _default_escalation_recorder(state: ChatState) -> str:
    escalation_id, _ = persist_escalation(
        {
            "name": state.get("escalation_contact_name"),
            "email": state.get("escalation_contact_email"),
            "phone": state.get("escalation_contact_phone"),
            "reason": state.get("escalation_reason"),
        }
    )
    return escalation_id


class HumanEscalationAgent(StateAgent):
    def __init__(
        self,
        escalation_service: EscalationService,
        escalation_recorder: EscalationRecorder | None = None,
    ) -> None:
        self._escalation_service = escalation_service
        self._escalation_recorder = escalation_recorder or _default_escalation_recorder

    def execute(self, state: ChatState) -> ChatState:
        logger.info("escalation agent received state: %s", summarize_state(state))
        contact_update = self._extract_contact_update(state)
        state_with_contact = {**state, **contact_update}
        escalation_case_id = str(state.get("escalation_case_id") or "").strip() or None

        if escalation_case_id is None and self._has_contact_channel(state_with_contact):
            try:
                escalation_case_id = self._escalation_recorder(state_with_contact)
            except Exception as exc:
                logger.exception("failed to persist escalation record: %s", exc)

        state_with_contact = {
            **state_with_contact,
            "escalation_case_id": escalation_case_id,
        }
        update = {
            "intent": "human_escalation",
            "handoff_pending": True,
            "active_action": None,
            "appointment_slots": {},
            "missing_slots": [],
            "available_dates": [],
            "date_confirmed": False,
            "available_slots": [],
            "time_confirmed": False,
            "awaiting_confirmation": False,
            "final_response": self._escalation_service.build_response(state_with_contact),
            "escalation_case_id": escalation_case_id,
            **contact_update,
        }
        logger.info("escalation agent produced update: %s", summarize_update(update))
        return update

    @staticmethod
    def _extract_contact_update(state: ChatState) -> ChatState:
        name = str(state.get("escalation_contact_name") or "").strip()
        email = str(state.get("escalation_contact_email") or "").strip()
        phone = str(state.get("escalation_contact_phone") or "").strip()

        return {
            "escalation_contact_name": name or None,
            "escalation_contact_email": email or None,
            "escalation_contact_phone": phone or None,
        }

    @staticmethod
    def _has_contact_channel(state: ChatState) -> bool:
        return bool(
            str(state.get("escalation_contact_email") or "").strip()
            or str(state.get("escalation_contact_phone") or "").strip()
        )
