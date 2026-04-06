from __future__ import annotations

from typing import Protocol

from app.graph.state import ChatState


class StateAgent(Protocol):
    def execute(self, state: ChatState) -> ChatState:
        ...
