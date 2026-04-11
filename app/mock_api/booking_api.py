from __future__ import annotations

import hashlib
import json
from typing import Literal, TypedDict, cast
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock, Thread
from urllib import parse

_SERVER_LOCK = Lock()
_server_base_url: str | None = None
_BOOKINGS_LOCK = Lock()

_STORE_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "booking_store.json"
)
_DEFAULT_START_DATE = "2026-04-15"
_DEFAULT_DAYS = 31


class SlotRecord(TypedDict):
    state: Literal["free", "booked"]
    title: str


DaySlots = dict[str, SlotRecord]
SlotsByDate = dict[str, DaySlots]


class BookingRecord(TypedDict):
    confirmation_id: str
    service: str
    date: str
    time: str
    name: str
    email: str
    title: str
    status: str


BookingsById = dict[str, BookingRecord]


class BookingStore(TypedDict):
    slots: SlotsByDate
    bookings: BookingsById


def _default_times() -> list[str]:
    times: list[str] = []
    hour = 9
    minute = 0
    while hour < 17 or (hour == 17 and minute == 0):
        display_hour = hour % 12 or 12
        suffix = "AM" if hour < 12 else "PM"
        times.append(f"{display_hour:02d}:{minute:02d} {suffix}")
        minute += 30
        if minute >= 60:
            minute = 0
            hour += 1
    return times


def _seed_slots() -> SlotsByDate:
    from datetime import date, timedelta

    start = date.fromisoformat(_DEFAULT_START_DATE)
    slots: SlotsByDate = {}
    for offset in range(_DEFAULT_DAYS):
        day = (start + timedelta(days=offset)).isoformat()
        slots[day] = {
            time: {"state": "free", "title": ""}
            for time in _default_times()
        }
    return slots


def _empty_store() -> BookingStore:
    return {"slots": _seed_slots(), "bookings": {}}


def _normalize_slots(raw_slots: object) -> SlotsByDate:
    if not isinstance(raw_slots, dict):
        return _seed_slots()

    raw_slots_dict = cast(dict[object, object], raw_slots)
    normalized: SlotsByDate = {}
    for raw_day, raw_day_slots in raw_slots_dict.items():
        if not isinstance(raw_day, str) or not isinstance(raw_day_slots, dict):
            continue
        raw_day_slots_dict = cast(dict[object, object], raw_day_slots)
        day_slots: DaySlots = {}
        for raw_time, raw_slot in raw_day_slots_dict.items():
            if not isinstance(raw_time, str) or not isinstance(raw_slot, dict):
                continue
            slot = cast(dict[str, object], raw_slot)
            raw_state = slot.get("state")
            raw_title = slot.get("title")
            state: Literal["free", "booked"] = "booked" if raw_state == "booked" else "free"
            day_slots[raw_time] = {
                "state": state,
                "title": raw_title if isinstance(raw_title, str) else "",
            }
        if day_slots:
            normalized[raw_day] = day_slots

    return normalized if normalized else _seed_slots()


def _normalize_bookings(raw_bookings: object) -> BookingsById:
    if not isinstance(raw_bookings, dict):
        return {}

    raw_bookings_dict = cast(dict[object, object], raw_bookings)
    normalized: BookingsById = {}
    for raw_confirmation_id, raw_booking in raw_bookings_dict.items():
        if not isinstance(raw_confirmation_id, str) or not isinstance(raw_booking, dict):
            continue
        booking = cast(dict[str, object], raw_booking)
        service = booking.get("service")
        date = booking.get("date")
        time = booking.get("time")
        name = booking.get("name")
        email = booking.get("email")
        title = booking.get("title")
        status = booking.get("status")
        confirmation_id = booking.get("confirmation_id")
        normalized[raw_confirmation_id] = {
            "confirmation_id": (
                confirmation_id if isinstance(confirmation_id, str) and confirmation_id.strip() else raw_confirmation_id
            ),
            "service": service if isinstance(service, str) else "",
            "date": date if isinstance(date, str) else "",
            "time": time if isinstance(time, str) else "",
            "name": name if isinstance(name, str) else "",
            "email": email if isinstance(email, str) else "",
            "title": title if isinstance(title, str) else "",
            "status": status if isinstance(status, str) else "confirmed",
        }
    return normalized


def _normalize_store(raw_store: object) -> BookingStore:
    if not isinstance(raw_store, dict):
        return _empty_store()
    store = cast(dict[str, object], raw_store)
    return {
        "slots": _normalize_slots(store.get("slots")),
        "bookings": _normalize_bookings(store.get("bookings")),
    }


def _load_store() -> BookingStore:
    if not _STORE_PATH.exists():
        store = _empty_store()
        _save_store(store)
        return store

    raw = _STORE_PATH.read_text(encoding="utf-8")
    try:
        raw_store: object = json.loads(raw)
    except json.JSONDecodeError:
        raw_store = {}
    return _normalize_store(raw_store)


def _save_store(store: BookingStore) -> None:
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STORE_PATH.write_text(json.dumps(store, indent=2), encoding="utf-8")


def ensure_mock_booking_api_server_started() -> str:
    global _server_base_url
    with _SERVER_LOCK:
        if _server_base_url is not None:
            return _server_base_url

        server = ThreadingHTTPServer(("127.0.0.1", 0), _BookingApiHandler)
        host = str(server.server_address[0])
        port = int(server.server_address[1])
        _server_base_url = f"http://{host}:{port}"
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return _server_base_url


class _BookingApiHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed_url = parse.urlparse(self.path)
        if parsed_url.path.startswith("/bookings/"):
            confirmation_id = parsed_url.path.rsplit("/", 1)[-1].strip()
            booking = _get_saved_booking(confirmation_id)
            if booking is None:
                self._write_json(HTTPStatus.NOT_FOUND, {"error": "booking_not_found"})
                return

            self._write_json(
                HTTPStatus.OK,
                {
                    "success": True,
                    "confirmation_id": confirmation_id,
                    "service": str(booking["service"]),
                    "date": str(booking["date"]),
                    "time": str(booking["time"]),
                    "name": str(booking["name"]),
                    "email": str(booking["email"]),
                    "message": "Booking retrieved successfully.",
                    "saved_booking": booking,
                },
            )
            return

        if parsed_url.path == "/available-dates":
            query = parse.parse_qs(parsed_url.query)
            service = _first_value(query, "service")
            date_preference = _first_value(query, "date_preference")
            if not service:
                self._write_json(
                    HTTPStatus.BAD_REQUEST,
                    {"error": "service_required"},
                )
                return

            self._write_json(
                HTTPStatus.OK,
                {
                    "service": service,
                    "date_preference": date_preference,
                    "available_dates": _generate_available_dates(
                        service=service,
                        date_preference=date_preference,
                    ),
                },
            )
            return

        if parsed_url.path != "/availability":
            self._write_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return

        query = parse.parse_qs(parsed_url.query)
        service = _first_value(query, "service")
        date = _first_value(query, "date")
        time_preference = _first_value(query, "time_preference")

        if not service or not date:
            self._write_json(
                HTTPStatus.BAD_REQUEST,
                {"error": "service_and_date_required"},
            )
            return

        slots = _generate_available_slots(
            service=service,
            date=date,
            time_preference=time_preference,
        )
        self._write_json(
            HTTPStatus.OK,
            {
                "service": service,
                "date": date,
                "time_preference": time_preference,
                "slots": slots,
            },
        )

    def do_POST(self) -> None:
        if self.path != "/bookings":
            self._write_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return

        payload = self._read_json_body()
        required_fields = ("service", "date", "time", "name", "email")
        missing_fields = [
            field_name
            for field_name in required_fields
            if not str(payload.get(field_name, "")).strip()
        ]
        if missing_fields:
            self._write_json(
                HTTPStatus.BAD_REQUEST,
                {"error": "missing_fields", "fields": missing_fields},
            )
            return

        confirmation_id, booking_record = persist_booking(payload)
        self._write_json(
            HTTPStatus.OK,
            {
                "success": True,
                "confirmation_id": confirmation_id,
                "service": str(booking_record["service"]),
                "date": str(booking_record["date"]),
                "time": str(booking_record["time"]),
                "name": str(booking_record["name"]),
                "email": str(booking_record["email"]),
                "message": "Booking created successfully.",
                "saved_booking": booking_record,
            },
        )

    def do_DELETE(self) -> None:
        if not self.path.startswith("/bookings/"):
            self._write_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return

        confirmation_id = self.path.rsplit("/", 1)[-1].strip()
        deleted = delete_booking(confirmation_id)
        if not deleted:
            self._write_json(HTTPStatus.NOT_FOUND, {"error": "booking_not_found"})
            return

        self._write_json(
            HTTPStatus.OK,
            {"success": True, "confirmation_id": confirmation_id, "message": "Booking deleted successfully."},
        )

    def log_message(self, format: str, *args: object) -> None:
        return

    def _read_json_body(self) -> dict[str, object]:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            payload_obj: object = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            payload_obj = {}
        if not isinstance(payload_obj, dict):
            return {}
        payload_dict = cast(dict[object, object], payload_obj)
        normalized: dict[str, object] = {}
        for raw_key, raw_value in payload_dict.items():
            if isinstance(raw_key, str):
                normalized[raw_key] = raw_value
        return normalized

    def _write_json(self, status: HTTPStatus, payload: dict[str, object]) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def _generate_available_slots(
    service: str,
    date: str,
    time_preference: str | None,
) -> list[str]:
    store = _load_store()
    day_slots = store["slots"].get(date)
    if day_slots is None:
        return []

    free_slots = [
        time
        for time, slot in day_slots.items()
        if slot["state"] == "free"
    ]

    normalized_preference = (time_preference or "").strip().lower()
    if normalized_preference in {"morning", "afternoon", "evening"}:
        filtered: list[str] = []
        for slot in free_slots:
            minutes = _time_to_minutes(slot)
            if minutes is None:
                continue
            if normalized_preference == "morning" and minutes < 12 * 60:
                filtered.append(slot)
            elif normalized_preference == "afternoon" and 12 * 60 <= minutes < 17 * 60:
                filtered.append(slot)
            elif normalized_preference == "evening" and minutes >= 17 * 60:
                filtered.append(slot)
        free_slots = filtered

    return sorted(free_slots)


def _generate_available_dates(
    service: str,
    date_preference: str | None,
) -> list[str]:
    store = _load_store()
    available_dates: list[str] = []
    for day, slots in store["slots"].items():
        if any(
            slot["state"] == "free"
            for slot in slots.values()
        ):
            available_dates.append(day)

    preferred = _format_date_label(date_preference)
    if preferred and preferred in available_dates:
        available_dates.remove(preferred)
        available_dates.insert(0, preferred)

    return available_dates


def _build_confirmation_id(payload: dict[str, object]) -> str:
    digest = hashlib.sha256(
        "|".join(
            [
                str(payload["service"]),
                str(payload["date"]),
                str(payload["time"]),
                str(payload["name"]),
                str(payload["email"]),
            ]
        ).encode("utf-8")
    ).hexdigest()
    return f"apt_{digest[:10]}"


def persist_booking(payload: dict[str, object]) -> tuple[str, BookingRecord]:
    confirmation_id = _build_confirmation_id(payload)
    booking_record: BookingRecord = {
        "confirmation_id": confirmation_id,
        "service": str(payload["service"]).strip(),
        "date": str(payload["date"]).strip(),
        "time": str(payload["time"]).strip(),
        "name": str(payload["name"]).strip(),
        "email": str(payload["email"]).strip(),
        "title": str(payload.get("title") or "").strip(),
        "status": "confirmed",
    }
    _save_booking(confirmation_id, booking_record)
    return confirmation_id, booking_record


def _save_booking(confirmation_id: str, booking_record: BookingRecord) -> None:
    with _BOOKINGS_LOCK:
        store = _load_store()
        bookings = store["bookings"]
        slots_by_date = store["slots"]

        date = booking_record["date"].strip()
        time = booking_record["time"].strip()
        day_slots = slots_by_date.get(date)
        if day_slots is not None and time in day_slots:
            slot = day_slots.get(time)
            if slot is not None and slot["state"] == "free":
                slot["state"] = "booked"
                slot["title"] = booking_record["title"]

        bookings[confirmation_id] = booking_record
        _save_store(store)


def _get_saved_booking(confirmation_id: str) -> BookingRecord | None:
    with _BOOKINGS_LOCK:
        store = _load_store()
        booking = store["bookings"].get(confirmation_id)
        return cast(BookingRecord, dict(booking)) if booking is not None else None


def get_saved_booking(confirmation_id: str) -> BookingRecord | None:
    return _get_saved_booking(confirmation_id)


def delete_booking(confirmation_id: str) -> bool:
    with _BOOKINGS_LOCK:
        store = _load_store()
        bookings = store["bookings"]
        slots_by_date = store["slots"]
        booking = bookings.pop(confirmation_id, None)
        if booking is None:
            return False
        date = booking["date"].strip()
        time = booking["time"].strip()
        day_slots = slots_by_date.get(date)
        if day_slots is not None and time in day_slots:
            slot = day_slots.get(time)
            if slot is not None:
                slot["state"] = "free"
                slot["title"] = ""
        _save_store(store)
        return True


def _format_date_label(date_text: str | None) -> str | None:
    if not date_text:
        return None
    words = [word.capitalize() for word in date_text.strip().split()]
    return " ".join(words) or None


def _time_to_minutes(value: str) -> int | None:
    try:
        time_part, suffix = value.strip().split()
        hour_text, minute_text = time_part.split(":")
        hour = int(hour_text)
        minute = int(minute_text)
    except ValueError:
        return None
    suffix = suffix.upper()
    if suffix not in {"AM", "PM"}:
        return None
    if hour < 1 or hour > 12 or minute not in {0, 30}:
        return None
    if suffix == "AM":
        hour = 0 if hour == 12 else hour
    else:
        hour = 12 if hour == 12 else hour + 12
    return hour * 60 + minute


def _first_value(query: dict[str, list[str]], key: str) -> str | None:
    values = query.get(key, [])
    if not values:
        return None
    value = values[0].strip()
    return value or None
