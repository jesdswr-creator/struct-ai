"""Resource resolution for source and PyInstaller onedir execution. Units: none."""

from __future__ import annotations

import sys
from pathlib import Path, PureWindowsPath

from struct_ai.exceptions import CodeDataError


def resource_path(relative: str, *, package_root: Path | None = None) -> Path:
    """Resolve an existing package resource, refusing path traversal. Units: none."""
    if package_root is None:
        frozen_root = getattr(sys, "_MEIPASS", None)
        package_root = (
            Path(frozen_root) / "struct_ai" if frozen_root else Path(__file__).resolve().parent
        )
    path = Path(relative)
    windows_path = PureWindowsPath(relative)
    if path.is_absolute() or windows_path.anchor or ".." in windows_path.parts:
        raise CodeDataError(
            "Resource paths must be relative and cannot escape the package.",
            clause="PACKAGING RESOURCE CONTRACT (not an IS-code clause)",
            value=relative,
            limit="existing resource inside struct_ai/",
        )
    resolved_root = package_root.resolve()
    resolved_path = (resolved_root / path).resolve()
    if not resolved_path.is_relative_to(resolved_root) or not resolved_path.exists():
        raise CodeDataError(
            "Required packaged resource is missing or outside the package.",
            clause="PACKAGING RESOURCE CONTRACT (not an IS-code clause)",
            value=relative,
            limit="existing resource inside struct_ai/",
        )
    return resolved_path
