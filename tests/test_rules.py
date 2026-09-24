import unittest
from datetime import datetime, timedelta

from soc_triage.models import AuthEvent
from soc_triage.rules import detect_alerts


class RuleTests(unittest.TestCase):
    def test_detects_brute_force_and_success_after_failures(self):
        start = datetime(2026, 9, 22, 21, 55)
        events = [
            AuthEvent(start + timedelta(minutes=index), "ana", "203.0.113.10", "failure", "host")
            for index in range(5)
        ]
        events.append(AuthEvent(start + timedelta(minutes=5), "ana", "203.0.113.10", "success", "host"))

        rule_ids = {alert.rule_id for alert in detect_alerts(events)}

        self.assertIn("BRUTE_FORCE", rule_ids)
        self.assertIn("SUCCESS_AFTER_FAILURES", rule_ids)
        self.assertIn("OFF_HOURS_LOGIN", rule_ids)

    def test_does_not_flag_normal_business_hours_login(self):
        events = [AuthEvent(datetime(2026, 9, 22, 14, 0), "bruno", "198.51.100.7", "success", "host")]
        self.assertEqual([], detect_alerts(events))


if __name__ == "__main__":
    unittest.main()
