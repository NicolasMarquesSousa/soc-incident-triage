# SOC Incident Triage Platform

An explainable, local-first security operations project that transforms fictional authentication logs into prioritized alerts and auditable investigation cases.

> Built as a hands-on portfolio project covering Python, SQL, detection engineering, incident triage, automated tests, Git and Linux-compatible CI.

## Why this project exists

Security teams receive large volumes of authentication events. Analysts need a repeatable way to validate records, identify suspicious behavior, prioritize risk and document every investigation decision.

This project demonstrates that workflow without using real personal or corporate data.

## Current capabilities

- CSV ingestion, validation and normalization;
- explainable detection rules and risk scores;
- idempotent SQLite persistence;
- prioritized alert queue;
- incident lifecycle: `open` → `investigating` → `resolved`;
- analyst, note and UTC timestamp audit trail;
- case history queries;
- automated unit tests;
- GitHub Actions pipeline running on Linux.

## Architecture

```text
Fictional CSV logs
        │
        ▼
Validation and normalization
        │
        ▼
Detection rules and risk scoring
        │
        ▼
SQLite ── auth_events
   │    ├─ alerts
   │    └─ alert_history
   ▼
CLI: summary, alert queue and case history
```

## Detection rules

| Rule | Logic | Severity | MITRE ATT&CK context |
|---|---|---:|---|
| `BRUTE_FORCE` | Five or more failures from one IP within ten minutes | High | T1110 — Brute Force |
| `SUCCESS_AFTER_FAILURES` | Successful login after three or more recent failures | Critical | Possible account compromise |
| `OFF_HOURS_LOGIN` | Successful login between 22:00 and 06:00 | Medium | Contextual anomaly |

The rules are intentionally transparent. Each alert stores human-readable evidence so an analyst can understand why it fired.

## Quick start

Requires Python 3.11 or newer. The application has no external runtime dependencies.

### Windows PowerShell

```powershell
$env:PYTHONPATH="src"
python -m soc_triage.cli ingest data/sample_auth_events.csv --database soc_triage.db
python -m soc_triage.cli summary --database soc_triage.db
python -m soc_triage.cli alerts --database soc_triage.db
```

### Linux or macOS

```bash
export PYTHONPATH=src
python -m soc_triage.cli ingest data/sample_auth_events.csv --database soc_triage.db
python -m soc_triage.cli summary --database soc_triage.db
python -m soc_triage.cli alerts --database soc_triage.db
```

## Investigation workflow

Assign an alert to an analyst and document the decision:

```bash
python -m soc_triage.cli status 2 investigating \
  --analyst "Nicolas Marques" \
  --note "Reviewing the source IP and authentication timeline" \
  --database soc_triage.db
```

Resolve it after investigation:

```bash
python -m soc_triage.cli status 2 resolved \
  --analyst "Nicolas Marques" \
  --note "Confirmed simulated activity; no containment required" \
  --database soc_triage.db
```

Read the complete case and its audit history:

```bash
python -m soc_triage.cli case 2 --database soc_triage.db
```

## Tests

```bash
python -m unittest discover -s tests -v
```

Tests cover CSV validation, detection behavior, false-positive prevention, risk ordering, status validation, missing alerts and the audit trail.

## Engineering decisions

- **Standard library first:** keeps setup simple and makes the core logic easy to review.
- **Parameterized SQL:** prevents values from being concatenated into queries.
- **Unique constraints:** importing the same file again does not duplicate events or alerts.
- **UTC audit timestamps:** produces consistent investigation records across locations.
- **In-memory databases in tests:** keeps tests isolated, fast and repeatable.
- **Fictional data only:** avoids exposing personal, customer or employer information.

## Roadmap

- REST API with FastAPI;
- operational dashboard;
- local IP reputation enrichment;
- filters by severity, status, user and time range;
- Docker and PostgreSQL;
- Power BI executive report;
- additional ATT&CK-aligned detection rules.

## Versão em português

Plataforma educacional de triagem de incidentes que importa logs fictícios, valida os registros, detecta comportamentos suspeitos, prioriza alertas por risco e mantém um histórico auditável da investigação. O projeto demonstra competências práticas em Python, SQL, Segurança da Informação, testes automatizados, Git e automação.

## Security and privacy

- Do not commit real logs, secrets or credentials.
- All sample identities and IP addresses are fictional or documentation ranges.
- This educational detection engine does not replace a production SIEM.

## Author

**Nicolas Marques** — Information Security student and network technician building practical experience in security operations, data analysis and automation.
