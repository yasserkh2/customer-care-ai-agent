from __future__ import annotations

from dataclasses import dataclass

from app.graph.state import ChatState


@dataclass(frozen=True, slots=True)
class AgentResult:
    state_update: ChatState

    def as_state_update(self) -> ChatState:
        return dict(self.state_update)
