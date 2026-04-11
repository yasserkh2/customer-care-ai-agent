from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import TypedDict, cast
from uuid import uuid4

_ESCALATIONS_LOCK = Lock()
_STORE_PATH = Path(__file__).resolve().parents[2] / "data" / "escalation_store.json"


class EscalationRecord(TypedDict):
    escalation_id: str
    name: str
    email: str
    phone: str
    reason: str
    status: str
    created_at_utc: str


EscalationsById = dict[str, EscalationRecord]


class EscalationStore(TypedDict):
    escalations: EscalationsById


def _empty_store() -> EscalationStore:
    return {"escalations": {}}


def _normalize_escalations(raw_escalations: object) -> EscalationsById:
    if not isinstance(raw_escalations, dict):
        return {}

    normalized: EscalationsById = {}
    for raw_id, raw_record in cast(dict[object, object], raw_escalations).items():
        if not isinstance(raw_id, str) or not isinstance(raw_record, dict):
            continue
        record = cast(dict[str, object], raw_record)
        escalation_id = str(record.get("escalation_id") or raw_id).strip() or raw_id
        normalized[raw_id] = {
            "escalation_id": escalation_id,
            "name": str(record.get("name") or "").strip(),
            "email": str(record.get("email") or "").strip(),
            "phone": str(record.get("phone") or "").strip(),
            "reason": str(record.get("reason") or "").strip(),
            "status": str(record.get("status") or "open").strip() or "open",
            "created_at_utc": str(record.get("created_at_utc") or "").strip(),
        }
    return normalized


def _normalize_store(raw_store: object) -> EscalationStore:
    if not isinstance(raw_store, dict):
        return _empty_store()
    store = cast(dict[str, object], raw_store)
    return {"escalations": _normalize_escalations(store.get("escalations"))}


def _load_store() -> EscalationStore:
    if not _STORE_PATH.exists():
        store = _empty_store()
        _save_store(store)
        return store

    raw = _STORE_PATH.read_text(encoding="utf-8")
    try:
        payload: object = json.loads(raw)
    except json.JSONDecodeError:
        payload = {}
    return _normalize_store(payload)


def _save_store(store: EscalationStore) -> None:
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STORE_PATH.write_text(json.dumps(store, indent=2), encoding="utf-8")


def _build_escalation_id() -> str:
    return f"esc_{uuid4()}"


def persist_escalation(payload: dict[str, object]) -> tuple[str, EscalationRecord]:
    escalation_id = _build_escalation_id()
    record: EscalationRecord = {
        "escalation_id": escalation_id,
        "name": str(payload.get("name") or "").strip(),
        "email": str(payload.get("email") or "").strip(),
        "phone": str(payload.get("phone") or "").strip(),
        "reason": str(payload.get("reason") or "").strip(),
        "status": "open",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    _save_escalation(escalation_id, record)
    return escalation_id, record


def _save_escalation(escalation_id: str, escalation_record: EscalationRecord) -> None:
    with _ESCALATIONS_LOCK:
        store = _load_store()
        store["escalations"][escalation_id] = escalation_record
        _save_store(store)


def get_saved_escalation(escalation_id: str) -> EscalationRecord | None:
    with _ESCALATIONS_LOCK:
        store = _load_store()
        escalation = store["escalations"].get(escalation_id)
        return cast(EscalationRecord, dict(escalation)) if escalation is not None else None
