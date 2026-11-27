"""Single source of UI tokens; no engineering constants. Units: logical px and sRGB hex."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ThemeName = Literal["light", "dark"]
SPACING = (8, 16, 24, 32, 40, 48)
CARD_RADIUS = 10
CONTROL_RADIUS = 8
FONT_SIZES = {"caption": 12, "body": 14, "subtitle": 16, "title": 20, "kpi": 28}
ELEVATION = {"card_border_px": 1, "shadow": "none"}


@dataclass(frozen=True)
class Palette:
    """Semantic colours for one theme. Units: sRGB hexadecimal."""

    background: str
    surface: str
    sidebar: str
    text: str
    muted: str
    border: str
    accent: str
    accent_text: str
    accent_surface: str
    primary: str
    primary_text: str
    success: str
    success_surface: str
    warning: str
    warning_surface: str
    danger: str
    danger_surface: str
    grid: str


PALETTES = {
    "light": Palette(
        background="#F3F6FA",
        surface="#FFFFFF",
        sidebar="#FAFBFD",
        text="#182840",
        muted="#53637A",
        border="#DCE4EE",
        accent="#245EDB",
        accent_text="#245EDB",
        accent_surface="#ECF2FF",
        primary="#245EDB",
        primary_text="#FFFFFF",
        success="#11633F",
        success_surface="#E8F5ED",
        warning="#795214",
        warning_surface="#FFF4D9",
        danger="#AA2922",
        danger_surface="#FDEDEA",
        grid="#E8EDF4",
    ),
    "dark": Palette(
        background="#101824",
        surface="#182335",
        sidebar="#121D2C",
        text="#EDF2FA",
        muted="#AFBED2",
        border="#33445C",
        accent="#92B5FF",
        accent_text="#ACCAFF",
        accent_surface="#233653",
        primary="#245EDB",
        primary_text="#FFFFFF",
        success="#8CDEB2",
        success_surface="#163B2C",
        warning="#F1CF8B",
        warning_surface="#3F321C",
        danger="#FFAFA6",
        danger_surface="#482A2B",
        grid="#24334A",
    ),
}


def contrast_ratio(foreground: str, background: str) -> float:
    """Compute WCAG relative luminance contrast for UI tests. Units: dimensionless ratio."""

    def luminance(colour: str) -> float:
        """Decode sRGB channels and linearise them. Units: dimensionless luminance."""
        channels = [int(colour[index : index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [
            channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
            for channel in channels
        ]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    first, second = sorted((luminance(foreground), luminance(background)))
    return (second + 0.05) / (first + 0.05)
