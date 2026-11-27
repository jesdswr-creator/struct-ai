"""Opt-in draft-section JSON CLI; no GUI or engine implementation here. Units: input field
suffixes.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from struct_ai.exceptions import EngineeringError
from struct_ai.services import engine_service


def main(argv: list[str] | None = None) -> int:
    """Run an explicit input file; 0=section checks pass, 1=revise, 2=error. Units: API-defined."""
    parser = argparse.ArgumentParser(
        description="UNVERIFIED draft beam-section flexure, NOT building design or selected bars."
    )
    parser.add_argument(
        "input", type=Path, help="Explicit DESIGN or ASSESS JSON; no default sample"
    )
    parser.add_argument(
        "--output", type=Path, help="New result JSON path; otherwise JSON goes to stdout"
    )
    parser.add_argument(
        "--report", type=Path, help="New Markdown trace path, including all used constants"
    )
    args = parser.parse_args(argv)
    destinations = [path.resolve() for path in (args.output, args.report) if path is not None]
    if len(set(destinations)) != len(destinations) or args.input.resolve() in destinations:
        parser.error("Input, JSON output and report must have distinct paths")
    if any(path.exists() for path in destinations):
        parser.error("Output paths must be new; existing evidence will not be overwritten")
    try:
        # Read a bounded file rather than allocating arbitrary-size untrusted input.
        with args.input.open("r", encoding="utf-8") as stream:
            text = stream.read(1_000_001)
        run = engine_service.run_beam_flexure_json(text)
        report = engine_service.beam_flexure_report(run)
        for warning in run.result.warnings:
            print(warning, file=sys.stderr)
        output = run.model_dump_json(indent=2) + "\n"
        if args.output is None:
            print(output, end="")
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(output)
        if args.report is not None:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            with args.report.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(report)
    except EngineeringError as error:
        print(json.dumps(error.as_dict(), ensure_ascii=False, allow_nan=False), file=sys.stderr)
        return 2
    except (OSError, UnicodeError) as error:
        print(f"File operation failed; no successful output is claimed: {error}", file=sys.stderr)
        return 2
    return 0 if run.result.status == "DRAFT_SECTION_CHECKS_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
