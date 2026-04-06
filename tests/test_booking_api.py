from __future__ import annotations

import unittest

from app.mock_api.booking_api import get_saved_booking, persist_booking


class MockBookingPersistenceTests(unittest.TestCase):
    def test_persist_booking_saves_and_returns_record(self) -> None:
        confirmation_id, saved_booking = persist_booking(
            {
                "service": "Credentialing",
                "date": "Next Tuesday",
                "time": "02:30 PM",
                "name": "Ahmed Hassan",
                "email": "ahmed@example.com",
            }
        )
        fetched = get_saved_booking(confirmation_id)

        self.assertEqual(saved_booking["confirmation_id"], confirmation_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["status"], "confirmed")
        self.assertEqual(fetched["email"], "ahmed@example.com")


if __name__ == "__main__":
    unittest.main()
