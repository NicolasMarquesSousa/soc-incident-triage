from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from .models import Alert, AuthEvent

SCHEMA = """
CREATE TABLE IF NOT EXISTS auth_events (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    username TEXT NOT NULL,
    source_ip TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('success', 'failure')),
    hostname TEXT NOT NULL,
    UNIQUE(timestamp, username, source_ip, status, hostname)
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY,
    rule_id TEXT NOT NULL,
    severity TEXT NOT NULL,
    risk_score INTEGER NOT NULL CHECK (risk_score BETWEEN 0 AND 100),
    source_ip TEXT NOT NULL,
    username TEXT NOT NULL,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    evidence TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    UNIQUE(rule_id, source_ip, username, first_seen, last_seen)
);

CREATE TABLE IF NOT EXISTS alert_history (
    id INTEGER PRIMARY KEY,
    alert_id INTEGER NOT NULL,
    previous_status TEXT NOT NULL,
    new_status TEXT NOT NULL,
    analyst TEXT NOT NULL,
    note TEXT NOT NULL,
    changed_at TEXT NOT NULL,
    FOREIGN KEY(alert_id) REFERENCES alerts(id)
);
"""


def connect(path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA)
    return connection


def save_results(
    connection: sqlite3.Connection, events: list[AuthEvent], alerts: list[Alert]
) -> tuple[int, int]:
    event_rows = [
        (event.timestamp.isoformat(), event.username, event.source_ip, event.status, event.hostname)
        for event in events
    ]
    alert_rows = [
        (
            alert.rule_id,
            alert.severity,
            alert.risk_score,
            alert.source_ip,
            alert.username,
            alert.first_seen.isoformat(),
            alert.last_seen.isoformat(),
            alert.evidence,
        )
        for alert in alerts
    ]

    before_events = connection.total_changes
    connection.executemany(
        """INSERT OR IGNORE INTO auth_events
        (timestamp, username, source_ip, status, hostname) VALUES (?, ?, ?, ?, ?)""",
        event_rows,
    )
    inserted_events = connection.total_changes - before_events

    before_alerts = connection.total_changes
    connection.executemany(
        """INSERT OR IGNORE INTO alerts
        (rule_id, severity, risk_score, source_ip, username, first_seen, last_seen, evidence)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        alert_rows,
    )
    inserted_alerts = connection.total_changes - before_alerts
    connection.commit()
    return inserted_events, inserted_alerts


def get_summary(connection: sqlite3.Connection) -> dict[str, object]:
    total_events = connection.execute("SELECT COUNT(*) FROM auth_events").fetchone()[0]
    total_alerts = connection.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
    by_severity = dict(
        connection.execute(
            "SELECT severity, COUNT(*) FROM alerts GROUP BY severity ORDER BY COUNT(*) DESC"
        ).fetchall()
    )
    top_ips = [
        dict(row)
        for row in connection.execute(
            """SELECT source_ip, COUNT(*) AS alert_count, MAX(risk_score) AS max_risk
            FROM alerts GROUP BY source_ip ORDER BY max_risk DESC, alert_count DESC LIMIT 5"""
        ).fetchall()
    ]
    return {
        "total_events": total_events,
        "total_alerts": total_alerts,
        "by_severity": by_severity,
        "top_ips": top_ips,
    }


def list_alerts(connection: sqlite3.Connection) -> list[dict[str, object]]:
    """Retorna os alertas priorizados por risco e recência."""
    return [
        dict(row)
        for row in connection.execute(
            """SELECT id, rule_id, severity, risk_score, username, source_ip,
                      first_seen, last_seen, evidence, status
               FROM alerts
               ORDER BY risk_score DESC, last_seen DESC"""
        ).fetchall()
    ]


def update_alert_status(
    connection: sqlite3.Connection,
    alert_id: int,
    status: str,
    analyst: str,
    note: str,
) -> bool:
    """Atualiza um alerta e registra a mudança em uma trilha de auditoria."""
    allowed_statuses = {"open", "investigating", "resolved"}
    if status not in allowed_statuses:
        raise ValueError(f"Status inválido: {status}")
    analyst = analyst.strip()
    note = note.strip()
    if not analyst:
        raise ValueError("O nome do analista é obrigatório")
    if not note:
        raise ValueError("A observação é obrigatória")

    current = connection.execute(
        "SELECT status FROM alerts WHERE id = ?", (alert_id,)
    ).fetchone()
    if current is None:
        return False

    previous_status = current["status"]
    changed_at = datetime.now(UTC).isoformat()
    with connection:
        connection.execute(
            "UPDATE alerts SET status = ? WHERE id = ?", (status, alert_id)
        )
        connection.execute(
            """INSERT INTO alert_history
               (alert_id, previous_status, new_status, analyst, note, changed_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (alert_id, previous_status, status, analyst, note, changed_at),
        )
    return True


def get_alert_case(
    connection: sqlite3.Connection, alert_id: int
) -> dict[str, object] | None:
    """Retorna o alerta e todo o seu histórico de atendimento."""
    alert = connection.execute(
        "SELECT * FROM alerts WHERE id = ?", (alert_id,)
    ).fetchone()
    if alert is None:
        return None

    history = [
        dict(row)
        for row in connection.execute(
            """SELECT previous_status, new_status, analyst, note, changed_at
               FROM alert_history
               WHERE alert_id = ?
               ORDER BY changed_at, id""",
            (alert_id,),
        ).fetchall()
    ]
    return {"alert": dict(alert), "history": history}
