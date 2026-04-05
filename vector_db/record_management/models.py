from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class StoredVectorRecord:
    point_id: str
    record_id: str
    payload: dict[str, Any]
    vector: list[float] | None = None
