import unittest
from datetime import datetime

from soc_triage.database import (
    connect,
    get_alert_case,
    list_alerts,
    save_results,
    update_alert_status,
)
from soc_triage.models import Alert


class DatabaseTests(unittest.TestCase):
    def test_lists_alerts_from_highest_to_lowest_risk(self) -> None:
        connection = connect(":memory:")
        alerts = [
            Alert(
                rule_id="OFF_HOURS_LOGIN",
                severity="medium",
                risk_score=50,
                source_ip="192.0.2.25",
                username="carla",
                first_seen=datetime.fromisoformat("2026-09-22T23:40:00"),
                last_seen=datetime.fromisoformat("2026-09-22T23:40:00"),
                evidence="Login fora do horário",
            ),
            Alert(
                rule_id="SUCCESS_AFTER_FAILURES",
                severity="critical",
                risk_score=95,
                source_ip="203.0.113.10",
                username="ana",
                first_seen=datetime.fromisoformat("2026-09-22T21:55:00"),
                last_seen=datetime.fromisoformat("2026-09-22T22:00:00"),
                evidence="Sucesso após falhas",
            ),
        ]

        save_results(connection, [], alerts)
        result = list_alerts(connection)

        self.assertEqual([95, 50], [row["risk_score"] for row in result])
        self.assertEqual("SUCCESS_AFTER_FAILURES", result[0]["rule_id"])

    def test_updates_alert_status(self) -> None:
        connection = connect(":memory:")
        alert = Alert(
            rule_id="BRUTE_FORCE",
            severity="high",
            risk_score=85,
            source_ip="203.0.113.10",
            username="ana",
            first_seen=datetime.fromisoformat("2026-09-22T21:55:00"),
            last_seen=datetime.fromisoformat("2026-09-22T21:59:00"),
            evidence="5 falhas em até 10 minutos",
        )
        save_results(connection, [], [alert])

        updated = update_alert_status(
            connection, 1, "investigating", "Nicolas", "Reviewing source IP"
        )
        result = list_alerts(connection)
        case = get_alert_case(connection, 1)

        self.assertTrue(updated)
        self.assertEqual("investigating", result[0]["status"])
        self.assertIsNotNone(case)
        self.assertEqual("Nicolas", case["history"][0]["analyst"])
        self.assertEqual("open", case["history"][0]["previous_status"])
        self.assertEqual("investigating", case["history"][0]["new_status"])

    def test_rejects_invalid_alert_status(self) -> None:
        connection = connect(":memory:")

        with self.assertRaises(ValueError):
            update_alert_status(connection, 1, "closed", "Nicolas", "Invalid status")

    def test_does_not_update_missing_alert(self) -> None:
        connection = connect(":memory:")

        updated = update_alert_status(
            connection, 999, "resolved", "Nicolas", "Alert not found"
        )

        self.assertFalse(updated)
        self.assertIsNone(get_alert_case(connection, 999))


if __name__ == "__main__":
    unittest.main()
