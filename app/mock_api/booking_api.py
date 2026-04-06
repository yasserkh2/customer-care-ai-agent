from __future__ import annotations

import hashlib
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock, Thread
from urllib import parse

_SERVER_LOCK = Lock()
_SERVER_BASE_URL: str | None = None
_BOOKINGS_LOCK = Lock()
_SAVED_BOOKINGS: dict[str, dict[str, object]] = {}


def ensure_mock_booking_api_server_started() -> str:
    global _SERVER_BASE_URL
    with _SERVER_LOCK:
        if _SERVER_BASE_URL is not None:
            return _SERVER_BASE_URL

        server = ThreadingHTTPServer(("127.0.0.1", 0), _BookingApiHandler)
        host, port = server.server_address
        _SERVER_BASE_URL = f"http://{host}:{port}"
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return _SERVER_BASE_URL


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

    def log_message(self, format: str, *args: object) -> None:
        return

    def _read_json_body(self) -> dict[str, object]:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            payload = {}
        return payload if isinstance(payload, dict) else {}

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
    all_slots = ["09:00 AM", "10:30 AM", "01:00 PM", "02:30 PM", "04:00 PM"]
    digest = hashlib.sha256(f"{service}|{date}".encode("utf-8")).hexdigest()
    rotation = int(digest[:2], 16) % len(all_slots)
    rotated_slots = all_slots[rotation:] + all_slots[:rotation]

    normalized_preference = (time_preference or "").strip().lower()
    if normalized_preference == "morning":
        filtered_slots = [slot for slot in rotated_slots if slot.endswith("AM")]
    elif normalized_preference in {"afternoon", "evening"}:
        filtered_slots = [slot for slot in rotated_slots if slot.endswith("PM")]
    else:
        filtered_slots = rotated_slots

    return filtered_slots[:3]


def _generate_available_dates(
    service: str,
    date_preference: str | None,
) -> list[str]:
    all_dates = [
        "Tomorrow",
        "Next Tuesday",
        "Next Thursday",
        "Next Monday",
        "Next Friday",
    ]
    digest = hashlib.sha256(f"dates|{service}".encode("utf-8")).hexdigest()
    rotation = int(digest[:2], 16) % len(all_dates)
    rotated_dates = all_dates[rotation:] + all_dates[:rotation]

    preferred = _format_date_label(date_preference)
    if preferred and preferred in rotated_dates:
        rotated_dates.remove(preferred)
        rotated_dates.insert(0, preferred)

    return rotated_dates[:3]


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


def persist_booking(payload: dict[str, object]) -> tuple[str, dict[str, object]]:
    confirmation_id = _build_confirmation_id(payload)
    booking_record = {
        "confirmation_id": confirmation_id,
        "service": str(payload["service"]).strip(),
        "date": str(payload["date"]).strip(),
        "time": str(payload["time"]).strip(),
        "name": str(payload["name"]).strip(),
        "email": str(payload["email"]).strip(),
        "status": "confirmed",
    }
    _save_booking(confirmation_id, booking_record)
    return confirmation_id, booking_record


def _save_booking(confirmation_id: str, booking_record: dict[str, object]) -> None:
    with _BOOKINGS_LOCK:
        _SAVED_BOOKINGS[confirmation_id] = dict(booking_record)


def _get_saved_booking(confirmation_id: str) -> dict[str, object] | None:
    with _BOOKINGS_LOCK:
        booking = _SAVED_BOOKINGS.get(confirmation_id)
        return dict(booking) if booking is not None else None


def get_saved_booking(confirmation_id: str) -> dict[str, object] | None:
    return _get_saved_booking(confirmation_id)


def _format_date_label(date_text: str | None) -> str | None:
    if not date_text:
        return None
    words = [word.capitalize() for word in date_text.strip().split()]
    return " ".join(words) or None


def _first_value(query: dict[str, list[str]], key: str) -> str | None:
    values = query.get(key, [])
    if not values:
        return None
    value = values[0].strip()
    return value or None
