import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "ci_step.py"


@pytest.mark.parametrize("exit_code", [0, 7])
def test_ci_step_runs_real_command_and_retains_exact_exit_code(tmp_path, exit_code):
    environment = dict(os.environ, GITHUB_ACTIONS="true", PYTHONUTF8="1")
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--name",
            "actual-command",
            "--output",
            str(tmp_path),
            "--",
            "-c",
            f"import sys; print('actual 50% output'); print('detail', file=sys.stderr); "
            f"sys.exit({exit_code})",
        ],
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=15,
    )
    assert completed.returncode == exit_code
    log = (tmp_path / "actual-command.log").read_bytes()
    assert b"actual 50% output" in log
    assert b"detail" in log
    report = json.loads((tmp_path / "actual-command.json").read_text(encoding="utf-8"))
    assert report["exit_code"] == exit_code
    assert report["log_sha256"] == hashlib.sha256(log).hexdigest()
    severity = "error" if exit_code else "notice"
    assert f"::{severity} title=CI actual-command::Exit code: {exit_code}%0A" in completed.stdout
    assert "50%25 output" in completed.stdout


@pytest.mark.parametrize("name", ["../escape", "bad\nname", ""])
def test_ci_step_rejects_unsafe_log_names_before_execution(tmp_path, name):
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--name",
            name,
            "--output",
            str(tmp_path),
            "--",
            "-c",
            "raise AssertionError('must not run')",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=15,
    )
    assert completed.returncode == 2
    assert "--name must contain" in completed.stderr
    assert not list(tmp_path.iterdir())


def test_long_unicode_failure_annotations_preserve_the_final_diagnostic(tmp_path):
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--name",
            "long-output",
            "--output",
            str(tmp_path),
            "--",
            "-c",
            "import sys; print('start-' + '\\u2713' * 2500 + '-FINAL-DIAGNOSTIC'); sys.exit(3)",
        ],
        env=dict(os.environ, GITHUB_ACTIONS="true", PYTHONUTF8="1"),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=15,
    )
    assert completed.returncode == 3
    parts = [
        line.split("::", 2)[2].replace("%0A", "\n").replace("%0D", "\r").replace("%25", "%")
        for line in completed.stdout.splitlines()
        if line.startswith("::error title=CI long-output")
    ]
    assert len(parts) >= 3
    assert all(len(part.encode("utf-8")) <= 3000 for part in parts)
    assert "".join(parts).endswith("-FINAL-DIAGNOSTIC\n")
