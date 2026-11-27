"""Generate QSS from tokens, without QtWebEngine or third-party themes. Units: logical px."""

from struct_ai.gui.theme.tokens import CARD_RADIUS, CONTROL_RADIUS, FONT_SIZES, PALETTES, ThemeName


def stylesheet(theme: ThemeName) -> str:
    """Build calm, high-contrast widget styling for a theme. Units: logical px, sRGB colours."""
    p = PALETTES[theme]
    return f"""
    QWidget {{ color: {p.text}; font-family: Inter, "Segoe UI", sans-serif;
        font-size: {FONT_SIZES["body"]}px; }}
    QMainWindow, QWidget#workspace, QScrollArea, QScrollArea > QWidget > QWidget {{
        background: {p.background}; }}
    QFrame#sidebar {{ background: {p.sidebar}; border-right: 1px solid {p.border}; }}
    QFrame#topbar {{ background: {p.surface}; border-bottom: 1px solid {p.border}; }}
    QFrame#footer {{ background: {p.sidebar}; border-top: 1px solid {p.border}; }}
    QFrame[card="true"] {{ background: {p.surface}; border: 1px solid {p.border};
        border-radius: {CARD_RADIUS}px; }}
    QLabel {{ background: transparent; border: none; }}
    QLabel[role="caption"] {{ font-size: {FONT_SIZES["caption"]}px; color: {p.muted}; }}
    QLabel[role="muted"] {{ color: {p.muted}; }}
    QLabel[role="title"] {{ font-size: {FONT_SIZES["title"]}px; font-weight: 650; }}
    QLabel[role="subtitle"] {{ font-size: {FONT_SIZES["subtitle"]}px; font-weight: 600; }}
    QLabel[role="brand"] {{ font-size: 24px; font-weight: 700; letter-spacing: -1px; }}
    QLabel[role="kpi"] {{ font-size: {FONT_SIZES["kpi"]}px; font-weight: 600; }}
    QLabel[role="eyebrow"] {{ font-size: {FONT_SIZES["caption"]}px; color: {p.accent};
        font-weight: 600; letter-spacing: 1px; }}
    QLabel[chip="info"] {{ color: {p.accent_text}; background: {p.accent_surface};
        border-radius: 7px; padding: 5px 9px; font-size: 12px; font-weight: 600; }}
    QLabel[chip="success"] {{ color: {p.success}; background: {p.success_surface};
        border-radius: 7px; padding: 5px 9px; font-size: 12px; font-weight: 600; }}
    QLabel[chip="warning"] {{ color: {p.warning}; background: {p.warning_surface};
        border-radius: 7px; padding: 5px 9px; font-size: 12px; font-weight: 600; }}
    QLabel[chip="danger"] {{ color: {p.danger}; background: {p.danger_surface};
        border-radius: 7px; padding: 5px 9px; font-size: 12px; font-weight: 600; }}
    QFrame#scopeBanner {{ background: {p.warning_surface}; border-radius: 8px; }}
    QFrame#scopeBanner QLabel {{ color: {p.warning}; font-size: 12px; }}
    QPushButton {{ background: {p.surface}; border: 1px solid {p.border};
        border-radius: {CONTROL_RADIUS}px; padding: 8px 14px; font-weight: 550; }}
    QPushButton:hover {{ background: {p.accent_surface}; border-color: {p.accent}; }}
    QPushButton:pressed {{ border: 2px solid {p.accent}; }}
    QPushButton:focus, QLineEdit:focus, QTableView:focus {{ border: 2px solid {p.accent}; }}
    QPushButton:disabled {{ background: {p.background}; color: {p.muted}; }}
    QPushButton[primary="true"] {{ background: {p.primary}; color: {p.primary_text};
        border: 1px solid {p.primary}; padding: 9px 18px; }}
    QPushButton[primary="true"]:disabled {{ background: {p.border}; color: {p.text};
        border-color: {p.border}; }}
    QPushButton[nav="true"] {{ background: transparent; border: 1px solid transparent;
        text-align: left; padding: 11px 12px; }}
    QPushButton[nav="true"][active="true"] {{ background: {p.accent_surface};
        color: {p.accent_text}; font-weight: 600; }}
    QPushButton[nav="true"]:hover {{ border-color: {p.border}; }}
    QLineEdit {{ background: {p.background}; border: 1px solid {p.border};
        border-radius: {CONTROL_RADIUS}px; padding: 7px 10px;
        selection-background-color: {p.primary};
        selection-color: {p.primary_text}; }}
    QLineEdit:disabled {{ color: {p.muted}; }}
    QTableView {{ background: {p.surface}; alternate-background-color: {p.background};
        gridline-color: {p.border}; border: none; selection-background-color: {p.accent_surface};
        selection-color: {p.text}; font-size: 12px; outline: none; }}
    QTableView::item {{ padding: 4px 8px; border-bottom: 1px solid {p.border}; }}
    QHeaderView::section {{ background: {p.background}; color: {p.muted}; font-size: 12px;
        border: none; padding: 7px 8px; font-weight: 600; text-align: left; }}
    QProgressBar {{ background: {p.border}; border: none; border-radius: 2px; max-height: 4px; }}
    QProgressBar::chunk {{ background: {p.primary}; border-radius: 2px; }}
    QScrollBar:vertical {{ background: {p.background}; width: 10px; margin: 0px; }}
    QScrollBar::handle:vertical {{ background: {p.border}; min-height: 30px; border-radius: 5px; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
    QDialog, QMessageBox {{ background: {p.surface}; }}
    QPlainTextEdit {{ background: {p.background}; border: 1px solid {p.border};
        border-radius: 8px; padding: 8px; font-size: 12px; }}
    QToolTip {{ background: {p.surface}; color: {p.text};
        border: 1px solid {p.border}; padding: 6px; }}
    """
