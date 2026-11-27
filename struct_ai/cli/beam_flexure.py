"""Explicit draft M1 flexure JSON CLI, no engineering logic. Units: field suffixes."""

from __future__ import annotations

from struct_ai.cli.section_files import run_file_cli
from struct_ai.services import engine_service


def main(argv: list[str] | None = None) -> int:
    """Use only the service for validation, calculation and reporting. Units: payload-specific."""
    return run_file_cli(
        argv,
        description="UNVERIFIED beam flexure, NOT building design or bars.",
        calculate=engine_service.run_beam_flexure_json,
        render=engine_service.beam_flexure_report,
    )


if __name__ == "__main__":
    raise SystemExit(main())
