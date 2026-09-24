from __future__ import annotations

import argparse
import json

from .database import (
    connect,
    get_alert_case,
    get_summary,
    list_alerts,
    save_results,
    update_alert_status,
)
from .parser import load_csv
from .rules import detect_alerts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Triagem local de eventos de autenticação")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser("ingest", help="Importa e analisa um arquivo CSV")
    ingest.add_argument("csv_file")
    ingest.add_argument("--database", default="soc_triage.db")

    summary = subparsers.add_parser("summary", help="Exibe o resumo da base")
    summary.add_argument("--database", default="soc_triage.db")

    alerts = subparsers.add_parser("alerts", help="Lista alertas priorizados por risco")
    alerts.add_argument("--database", default="soc_triage.db")

    status = subparsers.add_parser("status", help="Atualiza o estado de um alerta")
    status.add_argument("alert_id", type=int)
    status.add_argument("new_status", choices=["open", "investigating", "resolved"])
    status.add_argument("--analyst", required=True)
    status.add_argument("--note", required=True)
    status.add_argument("--database", default="soc_triage.db")

    case = subparsers.add_parser("case", help="Exibe um alerta e seu histórico")
    case.add_argument("alert_id", type=int)
    case.add_argument("--database", default="soc_triage.db")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    connection = connect(args.database)

    if args.command == "ingest":
        events, errors = load_csv(args.csv_file)
        alerts = detect_alerts(events)
        inserted_events, inserted_alerts = save_results(connection, events, alerts)
        result = {
            "valid_events": len(events),
            "invalid_events": len(errors),
            "inserted_events": inserted_events,
            "detected_alerts": len(alerts),
            "inserted_alerts": inserted_alerts,
            "errors": errors,
        }
    elif args.command == "summary":
        result = get_summary(connection)
    elif args.command == "alerts":
        result = list_alerts(connection)
    elif args.command == "status":
        updated = update_alert_status(
            connection,
            args.alert_id,
            args.new_status,
            args.analyst,
            args.note,
        )
        result = {
            "alert_id": args.alert_id,
            "status": args.new_status,
            "updated": updated,
        }
    else:
        result = get_alert_case(connection, args.alert_id)
        if result is None:
            result = {"alert_id": args.alert_id, "found": False}

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
