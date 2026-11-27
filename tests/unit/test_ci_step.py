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
