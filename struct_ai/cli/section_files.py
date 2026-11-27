"""Shared file transport for source/frozen section CLIs, no engineering. Units: payload-defined."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from struct_ai.exceptions import EngineeringError


def run_file_cli(
    argv: list[str] | None,
    *,
    description: str,
    calculate: Callable[[str], Any],
    render: Callable[[Any], str],
) -> int:
    """Run service callbacks; 0=requested checks pass, 1=revise, 2=error. Units: field suffixes."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("input", type=Path, help="Explicit JSON input; no implicit sample")
    parser.add_argument("--output", type=Path, help="New JSON path; required without a console")
    parser.add_argument("--report", type=Path, help="New Markdown trace path")
    parser.add_argument(
        "--error-output", type=Path, help="New failure JSON path, written only on error"
    )
    args = parser.parse_args(argv)

    def error_result(details: dict[str, Any]) -> int:
        """Keep frozen errors visible without relying on a console. Units: context-specific."""
        text = json.dumps(details, ensure_ascii=False, allow_nan=False)
        if sys.stderr is not None:
            print(text, file=sys.stderr)
        logger = logging.getLogger("struct_ai")
        if logger.hasHandlers():
            logger.error("Section command failed: %s", text)
        if args.error_output is not None and args.error_output.resolve() != args.input.resolve():
            try:
                args.error_output.parent.mkdir(parents=True, exist_ok=True)
                with args.error_output.open("x", encoding="utf-8", newline="\n") as stream:
                    stream.write(
                        json.dumps(
                            {"kind": "DRAFT_SECTION_FAILURE", "status": "FAIL", "error": details},
                            ensure_ascii=False,
                            indent=2,
                        )
                        + "\n"
                    )
            except OSError as write_error:
                if logger.hasHandlers():
                    logger.error("Cannot save failure evidence: %s", write_error)
                if sys.stderr is not None:
                    print(f"Cannot save failure evidence: {write_error}", file=sys.stderr)
        return 2

    destinations = [
        p.resolve() for p in (args.output, args.report, args.error_output) if p is not None
    ]
    if (
        len(set(destinations)) != len(destinations)
        or args.input.resolve() in destinations
        or any(p.exists() for p in destinations)
    ):
        # Do not write the failure file either if destinations conflict or already exist.
        args.error_output = None
        return error_result(
            {
                "type": "FileContractError",
                "message": "Input/output/report/error paths must be distinct; "
                "output paths must be new.",
            }
        )
    if args.output is None and sys.stdout is None:
        return error_result(
            {
                "type": "FileContractError",
                "message": "A windowed executable requires an explicit --output path.",
            }
        )
    try:
        with args.input.open("r", encoding="utf-8") as stream:
            text = stream.read(1_000_001)
        run = calculate(text)
        report = render(run)
        for warning in run.result.warnings:
            if sys.stderr is not None:
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
        return error_result(error.as_dict())
    except (OSError, UnicodeError) as error:
        return error_result(
            {
                "type": type(error).__name__,
                "message": str(error),
                "scope": "File operation failed; partial files may exist, no success claimed",
            }
        )
    return 1 if run.result.status == "REVISE_SECTION" else 0
