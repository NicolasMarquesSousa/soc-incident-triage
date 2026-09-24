from __future__ import annotations

import csv
import ipaddress
from datetime import datetime
from pathlib import Path

from .models import AuthEvent

REQUIRED_COLUMNS = {"timestamp", "username", "source_ip", "status", "hostname"}
VALID_STATUS = {"success", "failure"}


def parse_event(row: dict[str, str], line_number: int) -> AuthEvent:
    try:
        timestamp = datetime.fromisoformat(row["timestamp"].strip())
    except (KeyError, ValueError) as exc:
        raise ValueError(f"Linha {line_number}: timestamp inválido") from exc

    username = row.get("username", "").strip().lower()
    hostname = row.get("hostname", "").strip().lower()
    status = row.get("status", "").strip().lower()
    source_ip = row.get("source_ip", "").strip()

    if not username or not hostname:
        raise ValueError(f"Linha {line_number}: usuário e hostname são obrigatórios")
    if status not in VALID_STATUS:
        raise ValueError(f"Linha {line_number}: status deve ser success ou failure")
    try:
        ipaddress.ip_address(source_ip)
    except ValueError as exc:
        raise ValueError(f"Linha {line_number}: endereço IP inválido") from exc

    return AuthEvent(timestamp, username, source_ip, status, hostname)


def load_csv(path: str | Path) -> tuple[list[AuthEvent], list[str]]:
    events: list[AuthEvent] = []
    errors: list[str] = []

    with Path(path).open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        columns = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - columns
        if missing:
            raise ValueError(f"Colunas ausentes: {', '.join(sorted(missing))}")

        for line_number, row in enumerate(reader, start=2):
            try:
                events.append(parse_event(row, line_number))
            except ValueError as exc:
                errors.append(str(exc))

    events.sort(key=lambda event: event.timestamp)
    return events, errors
