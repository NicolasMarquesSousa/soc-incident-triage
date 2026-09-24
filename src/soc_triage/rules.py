from __future__ import annotations

from collections import defaultdict, deque
from datetime import timedelta

from .models import Alert, AuthEvent


def detect_alerts(events: list[AuthEvent]) -> list[Alert]:
    alerts: list[Alert] = []
    failures_by_ip: dict[str, deque[AuthEvent]] = defaultdict(deque)
    failures_by_identity: dict[tuple[str, str], deque[AuthEvent]] = defaultdict(deque)
    brute_force_windows: set[tuple[str, object]] = set()

    for event in sorted(events, key=lambda item: item.timestamp):
        cutoff = event.timestamp - timedelta(minutes=10)
        ip_failures = failures_by_ip[event.source_ip]
        identity_failures = failures_by_identity[(event.source_ip, event.username)]

        while ip_failures and ip_failures[0].timestamp < cutoff:
            ip_failures.popleft()
        while identity_failures and identity_failures[0].timestamp < cutoff:
            identity_failures.popleft()

        if event.status == "failure":
            ip_failures.append(event)
            identity_failures.append(event)

            if len(ip_failures) >= 5:
                window_key = (event.source_ip, ip_failures[0].timestamp)
                if window_key not in brute_force_windows:
                    brute_force_windows.add(window_key)
                    alerts.append(
                        Alert(
                            rule_id="BRUTE_FORCE",
                            severity="high",
                            risk_score=min(70 + len(ip_failures) * 3, 95),
                            source_ip=event.source_ip,
                            username=event.username,
                            first_seen=ip_failures[0].timestamp,
                            last_seen=event.timestamp,
                            evidence=f"{len(ip_failures)} falhas em até 10 minutos",
                        )
                    )
            continue

        if len(identity_failures) >= 3:
            alerts.append(
                Alert(
                    rule_id="SUCCESS_AFTER_FAILURES",
                    severity="critical",
                    risk_score=95,
                    source_ip=event.source_ip,
                    username=event.username,
                    first_seen=identity_failures[0].timestamp,
                    last_seen=event.timestamp,
                    evidence=f"Login bem-sucedido após {len(identity_failures)} falhas",
                )
            )

        if event.timestamp.hour >= 22 or event.timestamp.hour < 6:
            alerts.append(
                Alert(
                    rule_id="OFF_HOURS_LOGIN",
                    severity="medium",
                    risk_score=50,
                    source_ip=event.source_ip,
                    username=event.username,
                    first_seen=event.timestamp,
                    last_seen=event.timestamp,
                    evidence=f"Login bem-sucedido às {event.timestamp:%H:%M}",
                )
            )

    return alerts
