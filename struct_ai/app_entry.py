"""Headless/frozen entry point; lazy GUI import and service-only engine access. Units: source."""

from __future__ import annotations

import argparse
import logging
import multiprocessing
import sys
import traceback
from pathlib import Path

from struct_ai.exceptions import EngineeringError
from struct_ai.services import engine_service


def main(argv: list[str] | None = None) -> int:
    """Run diagnostic desktop or explicit draft section commands. Units: source."""
    multiprocessing.freeze_support()
    parser = argparse.ArgumentParser(
        description="struct_ai — diagnostic desktop and draft section CLI, NOT building design"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--selftest", action="store_true", help="Data/native solver/determinism selftest"
    )
    mode.add_argument(
        "--gui-selftest", action="store_true", help="Real GUI/worker/resource smoke test"
    )
    mode.add_argument(
        "--diagnostics", action="store_true", help="Print local version/capability data"
    )
    mode.add_argument(
        "--beam-flexure", type=Path, help="Explicit M1 input JSON (draft, not a building)"
    )
    mode.add_argument(
        "--beam-checks", type=Path, help="Explicit M2 component input JSON (partial checks)"
    )
    parser.add_argument("--output", type=Path, help="Evidence/result JSON path")
    parser.add_argument("--report", type=Path, help="New section Markdown report path")
    parser.add_argument("--error-output", type=Path, help="New section failure JSON path")
    arguments = parser.parse_args(argv)
    try:
        log_folder = engine_service.initialise_logging()
        if arguments.beam_flexure is not None or arguments.beam_checks is not None:
            from struct_ai.cli import beam_checks, beam_flexure

            input_path = arguments.beam_flexure or arguments.beam_checks
            command = [str(input_path)]
            for flag, path in (
                ("--output", arguments.output),
                ("--report", arguments.report),
                ("--error-output", arguments.error_output),
            ):
                if path is not None:
                    command.extend((flag, str(path)))
            entry = beam_flexure.main if arguments.beam_flexure is not None else beam_checks.main
            return entry(command)
        if arguments.report or arguments.error_output:
            parser.error("--report and --error-output require a section command")
        output = arguments.output or log_folder / "selftest-result.json"
        if arguments.selftest:
            report = engine_service.run_packaging_selftest()
            engine_service.write_diagnostic_evidence(output, report)
            if sys.stdout is not None:
                print(f"M0b diagnostic selftest PASS (not building design): {output}")
            return 0
        if arguments.gui_selftest:
            from struct_ai.gui.smoke import run_gui_selftest

            return run_gui_selftest(output)
        if arguments.diagnostics:
            text = engine_service.get_diagnostics_text()
            if arguments.output:
                engine_service.write_diagnostic_evidence(arguments.output, {"diagnostics": text})
            if sys.stdout is not None:
                print(text)
            return 0
        if arguments.output:
            parser.error("--output requires --selftest, --gui-selftest or --diagnostics")
        from struct_ai.gui.app import main as gui_main

        return gui_main()
    except Exception as error:
        details = (
            error.as_dict()
            if isinstance(error, EngineeringError)
            else {
                "type": type(error).__name__,
                "message": str(error),
                "clause": "APPLICATION / PACKAGING (not an IS-code clause)",
                "value": type(error).__name__,
                "limit": "working dependencies, resources and output/log directories",
            }
        )
        technical = traceback.format_exc()
        logging.getLogger("struct_ai").error("%s\n%s", details, technical)
        if sys.stderr is not None:
            print(technical, file=sys.stderr)
        if arguments.output:
            # An output permission error is also fatal; never replace it with a success.
            engine_service.write_diagnostic_evidence(
                arguments.output,
                {
                    "kind": "M0B_SELFTEST_FAILURE",
                    "status": "FAIL",
                    "error": details,
                    "technical_details": technical,
                },
            )
        return 2
