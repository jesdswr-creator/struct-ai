"""Cards, chips, metrics and schematic rendering; no engineering logic. Units: logical px."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from struct_ai.gui.theme.tokens import PALETTES, ThemeName


def label(text: str, role: str = "body", *, wrap: bool = False) -> QLabel:
    """Create a semantic text label. Units: content-specific, no conversion."""
    widget = QLabel(text)
    widget.setProperty("role", role)
    widget.setWordWrap(wrap)
    widget.setTextFormat(Qt.TextFormat.PlainText)
    return widget


class Card(QFrame):
    """A single bordered surface. Units: layout spacing in logical px."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Create an 8px-grid card without decorative animation. Units: logical px."""
        super().__init__(parent)
        self.setProperty("card", True)
        self.content = QVBoxLayout(self)
        self.content.setContentsMargins(16, 16, 16, 16)
        self.content.setSpacing(8)


class StatusChip(QLabel):
    """Always combine semantic colour with an explicit text status. Units: none."""

    def __init__(self, text: str, kind: str = "info") -> None:
        """Set text and semantic state, without interpreting engineering values. Units: none."""
        super().__init__(text)
        self.setProperty("chip", kind)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAccessibleName(text)

    def set_status(self, text: str, kind: str) -> None:
        """Render a service/UI state; do not calculate pass/fail here. Units: none."""
        self.setText(text)
        self.setAccessibleName(text)
        self.setProperty("chip", kind)
        self.style().unpolish(self)
        self.style().polish(self)


class KpiTile(QWidget):
    """A result display which is empty until supplied with a real service value. Units: text."""

    def __init__(self, title: str, units: str) -> None:
        """Reserve sufficient width for a tabular numerical value. Units: units label."""
        super().__init__()
        self.setMinimumWidth(145)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.heading = label(title, "caption")
        self.value = label("—", "kpi")
        numeric_font = QFont(self.value.font())
        numeric_font.setFeature(QFont.Tag("tnum"), 1)
        self.value.setFont(numeric_font)
        self.units = label(units, "caption")
        self.value.setAccessibleName(f"{title}, not run")
        layout.addWidget(self.heading)
        layout.addWidget(self.value)
        layout.addWidget(self.units)

    def show_value(self, text: str) -> None:
        """Display supplied formatted text, not a derived quantity. Units: unchanged."""
        self.value.setText(text)
        self.value.setAccessibleName(f"{self.heading.text()}: {text} {self.units.text()}")


class CantileverSchematic(QWidget):
    """Illustrative fixed topology, NOT a numerical model. Units: screen px."""

    def __init__(self) -> None:
        """Create a CPU-rendered diagram with no OpenGL dependency. Units: logical px."""
        super().__init__()
        self.theme: ThemeName = "light"
        self.setMinimumHeight(150)
        self.setAccessibleName("Schematic: vertical two-node cantilever, global X tip load")

    def sizeHint(self) -> QSize:
        """Provide a compact illustrative canvas. Units: logical px."""
        return QSize(520, 162)

    def paintEvent(self, event: object) -> None:
        """Paint a schematic, not analysis output or geometry-to-scale. Units: logical px."""
        p = PALETTES[self.theme]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(p.background))
        painter.setPen(QPen(QColor(p.grid), 1))
        for x in range(0, self.width(), 24):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), 24):
            painter.drawLine(0, y, self.width(), y)
        cx, top, base = self.width() * 0.42, 26.0, self.height() - 24.0
        painter.setPen(QPen(QColor(p.accent), 7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(cx, top), QPointF(cx, base))
        painter.setPen(QPen(QColor(p.text), 2))
        painter.drawLine(QPointF(cx - 36, base + 4), QPointF(cx + 36, base + 4))
        for offset in range(-32, 36, 8):
            painter.drawLine(QPointF(cx + offset, base + 4), QPointF(cx + offset - 7, base + 12))
        painter.setPen(QPen(QColor(p.accent), 2))
        painter.drawLine(QPointF(cx + 4, top), QPointF(cx + 94, top))
        painter.setBrush(QColor(p.accent))
        painter.drawPolygon(
            QPolygonF([QPointF(cx + 94, top), QPointF(cx + 85, top - 5), QPointF(cx + 85, top + 5)])
        )
        painter.setBrush(QColor(p.surface))
        painter.drawEllipse(QPointF(cx, top), 5, 5)
        painter.drawEllipse(QPointF(cx, base), 5, 5)
        painter.setPen(QPen(QColor(p.muted), 1))
        painter.drawLine(QPointF(cx - 58, top), QPointF(cx - 58, base))
        for y in (top, base):
            painter.drawLine(QPointF(cx - 63, y), QPointF(cx - 53, y))
        font = QFont(self.font())
        font.setPixelSize(12)
        painter.setFont(font)
        painter.drawText(QRectF(cx - 90, (top + base) / 2 - 10, 30, 24), "L")
        painter.drawText(QRectF(cx + 102, top - 10, 120, 24), "P · global +X")
        painter.drawText(QRectF(cx + 18, base - 20, 150, 20), "1 · fixed base")
        painter.drawText(QRectF(cx + 18, top + 12, 130, 20), "2 · free node")
        painter.drawText(QRectF(12, self.height() - 22, 190, 20), "SCHEMATIC · NOT TO SCALE")
        painter.end()
