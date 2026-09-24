import tempfile
import unittest
from pathlib import Path

from soc_triage.parser import load_csv


class ParserTests(unittest.TestCase):
    def test_loads_valid_rows_and_reports_invalid_rows(self):
        content = (
            "timestamp,username,source_ip,status,hostname\n"
            "2026-09-22T10:00:00,Ana,203.0.113.5,success,NOTEBOOK-ANA\n"
            "invalid,Ana,999.0.0.1,failure,host\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.csv"
            path.write_text(content, encoding="utf-8")
            events, errors = load_csv(path)

        self.assertEqual(1, len(events))
        self.assertEqual("ana", events[0].username)
        self.assertEqual("notebook-ana", events[0].hostname)
        self.assertEqual(1, len(errors))


if __name__ == "__main__":
    unittest.main()
