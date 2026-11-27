import hashlib

import pytest

from tools.smoke_frozen import bundle_inventory, file_sha256, isolated_environment


def test_runtime_inventory_hashes_real_bytes_and_is_ordered_and_repeatable(tmp_path):
    # These are software-only file fixtures, not an executable or engineering evidence.
    (tmp_path / "nested").mkdir()
    first = tmp_path / "nested" / "resource.txt"
    second = tmp_path / "alphabet.txt"
    first.write_bytes(b"exact resource\r\n")
    second.write_bytes(b"abc")
    expected = [
        {"path": "alphabet.txt", "bytes": 3, "sha256": hashlib.sha256(b"abc").hexdigest()},
        {
            "path": "nested/resource.txt",
            "bytes": 16,
            "sha256": hashlib.sha256(b"exact resource\r\n").hexdigest(),
        },
    ]
    assert bundle_inventory(tmp_path) == expected
    assert bundle_inventory(tmp_path) == expected
    assert file_sha256(first) == expected[1]["sha256"]
    first.write_bytes(b"changed resource\r\n")
    assert bundle_inventory(tmp_path)[1]["sha256"] != expected[1]["sha256"]


@pytest.mark.parametrize("root_key", ["SystemRoot", "SYSTEMROOT"])
def test_windows_smoke_environment_honours_case_and_removes_developer_paths(root_key):
    inherited = {
        root_key: "C:\\Windows",
        "Path": "C:\\Python312;C:\\DeveloperTools",
        "PythonPath": "C:\\Checkout",
        "PYTHONHOME": "C:\\Python312",
        "VIRTUAL_ENV": "C:\\Checkout\\.venv",
        "QT_PLUGIN_PATH": "C:\\Qt",
        "QT_QPA_PLATFORM_PLUGIN_PATH": "C:\\Qt\\plugins",
        "QT_QPA_PLATFORM": "offscreen",
        "APPDATA": "C:\\User\\AppData\\Roaming",
    }
    environment = isolated_environment(inherited, windows=True)
    assert environment["PATH"] == "C:\\Windows\\System32;C:\\Windows"
    assert environment["SYSTEMROOT"] == "C:\\Windows"
    assert environment["APPDATA"] == inherited["APPDATA"]
    assert environment["PYTHONUTF8"] == "1"
    assert not {
        "PYTHONPATH",
        "PYTHONHOME",
        "VIRTUAL_ENV",
        "QT_PLUGIN_PATH",
        "QT_QPA_PLATFORM_PLUGIN_PATH",
        "QT_QPA_PLATFORM",
    }.intersection(environment)
    assert inherited["QT_QPA_PLATFORM"] == "offscreen"  # Never mutate the build environment.


def test_windows_smoke_environment_refuses_missing_root_instead_of_guessing():
    with pytest.raises(RuntimeError, match="SYSTEMROOT"):
        isolated_environment({}, windows=True)


def test_linux_smoke_environment_removes_library_overrides_and_is_explicitly_offscreen():
    environment = isolated_environment(
        {"PATH": "/usr/bin", "LD_LIBRARY_PATH": "/developer/libs", "LD_PRELOAD": "developer.so"},
        windows=False,
    )
    assert environment == {"PATH": "/usr/bin", "QT_QPA_PLATFORM": "offscreen", "PYTHONUTF8": "1"}
