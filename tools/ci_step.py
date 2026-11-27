"""Run one Python CI command with retained logs and API-visible outcomes. Units: none."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path


def annotation_text(text: str) -> str:
    """Escape workflow-command data without losing newlines or percent signs. Units: none."""
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def main() -> int:
    """Run a real command, preserve its exit code, and retain evidence. Units: none."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--output", type=Path, default=Path(".artifacts/ci"))
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", args.name):
        parser.error("--name must contain 1-64 lowercase ASCII letters, digits or hyphens")
    arguments = args.arguments[1:] if args.arguments[:1] == ["--"] else args.arguments
    if not arguments:
        parser.error("provide a Python command after --")
    args.output.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, *arguments]
    completed = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    log = args.output / f"{args.name}.log"
    log.write_bytes(completed.stdout)
    output = completed.stdout.decode("utf-8", errors="replace")
    print(output, end="", flush=True)
    evidence = {
        "kind": "CI_COMMAND_RESULT",
        "name": args.name,
        "command": command,
        "exit_code": completed.returncode,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "log": log.name,
        "log_sha256": hashlib.sha256(completed.stdout).hexdigest(),
    }
    (args.output / f"{args.name}.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )
    if os.environ.get("GITHUB_ACTIONS") == "true":
        severity = "error" if completed.returncode else "notice"
        # Full logs remain artifacts; bounded annotations are readable through the REST API.
        limit = 14000 if completed.returncode else 1800
        # Display annotations have canonical LF lines on every OS. The saved log
        # and its digest retain the subprocess's exact original bytes, including CRLF.
        tail = output.replace("\r\n", "\n")[-limit:]
        summary = f"Exit code: {completed.returncode}\nLog: {log}\n{tail}"
        # GitHub truncates individual annotation messages to about 4 KiB. Split on
        # a smaller UTF-8 byte budget so the final failure summary is not lost.
        chunks: list[str] = []
        current = ""
        byte_count = 0
        for character in summary:
            size = len(character.encode("utf-8"))
            if byte_count + size > 3000:
                chunks.append(current)
                current = ""
                byte_count = 0
            current += character
            byte_count += size
        if current:
            chunks.append(current)
        for index, chunk in enumerate(chunks, start=1):
            suffix = f" ({index}/{len(chunks)})" if len(chunks) > 1 else ""
            title = f"CI {args.name}{suffix}"
            print(f"::{severity} title={title}::{annotation_text(chunk)}", flush=True)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
