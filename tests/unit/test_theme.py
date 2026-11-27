import hashlib
import json

import pytest

from struct_ai.gui.theme.tokens import PALETTES, contrast_ratio
from struct_ai.resources import resource_path


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_text_token_pairs_meet_wcag_aa(theme):
    p = PALETTES[theme]
    pairs = [
        (p.text, p.background),
        (p.text, p.surface),
        (p.muted, p.background),
        (p.muted, p.surface),
        (p.muted, p.sidebar),
        (p.primary_text, p.primary),
        (p.accent_text, p.accent_surface),
        (p.warning, p.warning_surface),
        (p.success, p.success_surface),
        (p.danger, p.danger_surface),
    ]
    for foreground, background in pairs:
        assert contrast_ratio(foreground, background) >= 4.5, (theme, foreground, background)


def test_inter_is_bundled_unchanged_with_its_licence():
    folder = resource_path("gui/resources/fonts")
    for entry in json.loads((folder / "SOURCE.json").read_text(encoding="utf-8")):
        assert hashlib.sha256((folder / entry["file"]).read_bytes()).hexdigest() == entry["sha256"]
    assert "SIL OPEN FONT LICENSE" in (folder / "OFL.txt").read_text(encoding="utf-8")


def test_opensees_redistribution_restriction_is_not_hidden():
    text = resource_path("gui/resources/licenses/OpenSeesPy-LICENSE.md").read_text(encoding="utf-8")
    assert "Commercial redistribution" in text
    assert "requires a license" in text
