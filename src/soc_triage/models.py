from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class AuthEvent:
    timestamp: datetime
    username: str
    source_ip: str
    status: str
    hostname: str


@dataclass(frozen=True, slots=True)
class Alert:
    rule_id: str
    severity: str
    risk_score: int
    source_ip: str
    username: str
    first_seen: datetime
    last_seen: datetime
    evidence: str
