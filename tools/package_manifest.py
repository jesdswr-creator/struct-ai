"""Inventory a complete draft distribution after adding docs/evidence. Units: file bytes."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.smoke_frozen import bundle_inventory  # noqa: E402


def write_manifest(bundle: Path, source_commit: str) -> dict:
    """Hash every existing bundle file; manifest excludes only itself. Units: bytes."""
    if not re.fullmatch(r"[a-f0-9]{40}", source_commit):
        raise ValueError("An exact source commit SHA is required")
    bundle = bundle.resolve(strict=True)
    destination = bundle / "DRAFT-BUNDLE-MANIFEST.json"
    if destination.exists():
        raise FileExistsError("Do not silently replace a completed bundle manifest")
    entries = bundle_inventory(bundle)
    manifest = {
        "kind": "STRUCT_AI_DRAFT_DISTRIBUTION",
        "source_commit": source_commit,
        "scope": "Diagnostic desktop plus M1 flexure / restricted M2 component file commands",
        "building_design_available": False,
        "ollama_integration_available": False,
        "verified_code_compliance": False,
        "installer": False,
        "digitally_signed": False,
        "excludes": [destination.name],
        "files": entries,
    }
    with destination.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return manifest


def main() -> int:
    """Require explicit folder/commit; never bundle source credentials or weights. Units: bytes."""
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    manifest = write_manifest(args.bundle, args.commit)
    print(f"Draft distribution manifest: {len(manifest['files'])} files; source {args.commit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
