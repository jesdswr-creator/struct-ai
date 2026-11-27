from pathlib import Path

import pytest

from struct_ai.exceptions import CodeDataError
from struct_ai.resources import resource_path


def test_source_catalogue_resource_exists():
    assert resource_path("codes/is456_2000/data/catalogue.json").is_file()


def test_frozen_layout_contract_with_explicit_resource_root(tmp_path):
    root = tmp_path / "_internal" / "struct_ai"
    root.mkdir(parents=True)
    (root / "resource.txt").write_text("actual resource", encoding="utf-8")
    assert resource_path("resource.txt", package_root=root).read_text() == "actual resource"


@pytest.mark.parametrize("path", ["../outside", "/etc/passwd", "C:\\Windows\\file", "..\\file"])
def test_resource_traversal_rejected(path):
    with pytest.raises(CodeDataError, match="cannot escape"):
        resource_path(path)


def test_missing_resource_fails_loudly(tmp_path):
    with pytest.raises(CodeDataError, match="missing"):
        resource_path("not-shipped.json", package_root=Path(tmp_path))
