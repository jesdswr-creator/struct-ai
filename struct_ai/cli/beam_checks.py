"""Explicit draft M2 component JSON CLI, never building design. Units: field suffixes."""

from __future__ import annotations

from struct_ai.cli.section_files import run_file_cli
from struct_ai.services import engine_service


def main(argv: list[str] | None = None) -> int:
    """Use only the service for validation, calculation and reporting. Units: payload-specific."""
    return run_file_cli(
        argv,
        description="UNVERIFIED beam component subchecks, NOT complete design.",
        calculate=engine_service.run_beam_checks_json,
        render=engine_service.beam_checks_report,
    )


if __name__ == "__main__":
    raise SystemExit(main())
