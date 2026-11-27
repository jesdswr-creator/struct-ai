"""CLI audit presentation; all engine access goes through the service. Units: per record."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from struct_ai.exceptions import EngineeringError
from struct_ai.services import engine_service


def main(argv: list[str] | None = None) -> int:
    """Print every unverified constant; return nonzero on malformed data. Units: per record."""
    parser = argparse.ArgumentParser(description="List all unverified struct_ai code constants.")
    parser.add_argument("--data-root", type=Path, help="Explicit alternate codes/ root to audit")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable inventory")
    arguments = parser.parse_args(argv)
    try:
        audit = engine_service.list_code_constants(data_root=arguments.data_root)
    except EngineeringError as error:
        print(json.dumps(error.as_dict(), ensure_ascii=False, allow_nan=False), file=sys.stderr)
        return 2
    if arguments.json:
        print(audit.model_dump_json(indent=2))
        return 0
    if not audit.records:
        print("No engineering code constants implemented. Building design is unavailable.")
        print("An empty catalogue is NOT evidence of verified design.")
        return 0
    print(f"UNVERIFIED CATALOGUE CONSTANTS: {len(audit.unverified)}")
    print("Inventory count, NOT the number used by any particular design.")
    for record in audit.unverified:
        data = record.data
        value = "null / TODO_VERIFY" if data.value is None else str(data.value)
        print(
            f"{record.identifier} | {value} {data.units} | {data.code_edition} | "
            f"clause {data.clause} | verified=false | verified_by=null | {data.verification_note}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
