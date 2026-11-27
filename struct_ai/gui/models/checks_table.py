"""Checks table adapter; no independent engineering values or pass/fail logic. Units: per row."""

from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor

from struct_ai.checks import CheckResult
from struct_ai.gui.theme.tokens import PALETTES, ThemeName


class ChecksTableModel(QAbstractTableModel):
    """Render the exact service CheckResults, including source clauses. Units: per check."""

    HEADERS = ("Independent check", "Error demand", "Error budget", "Ratio", "Units", "Status")

    def __init__(self) -> None:
        """Start with zero rows, never demonstration results. Units: none."""
        super().__init__()
        self.checks: tuple[CheckResult, ...] = ()
        self.theme: ThemeName = "light"

    def set_checks(self, checks: tuple[CheckResult, ...]) -> None:
        """Replace the immutable source collection. Units: unchanged."""
        self.beginResetModel()
        self.checks = checks
        self.endResetModel()

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        """Return source row count; no per-cell widgets. Units: count."""
        return 0 if parent is not None and parent.isValid() else len(self.checks)

    def columnCount(self, parent: QModelIndex | None = None) -> int:
        """Return column count. Units: count."""
        return 0 if parent is not None and parent.isValid() else len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> object:
        """Format display only; retain raw values for sorting and traceability. Units: per row."""
        if not index.isValid() or index.row() >= len(self.checks):
            return None
        check = self.checks[index.row()]
        raw = (check.name, check.demand, check.capacity, check.ratio, check.units, check.ok)
        if role == Qt.ItemDataRole.UserRole:
            return raw[index.column()]
        if role == Qt.ItemDataRole.ToolTipRole:
            return (
                f"{check.clause}\nDemand: {check.demand!r}\n"
                f"Capacity: {check.capacity!r} {check.units}"
            )
        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() in (1, 2, 3):
                return f"{raw[index.column()]:.3e}"
            if index.column() == 5:
                return "PASS" if check.ok else "FAIL"
            return raw[index.column()]
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return int(
                Qt.AlignmentFlag.AlignVCenter
                | (
                    Qt.AlignmentFlag.AlignRight
                    if index.column() in (1, 2, 3)
                    else Qt.AlignmentFlag.AlignLeft
                )
            )
        if role == Qt.ItemDataRole.ForegroundRole and index.column() == 5:
            p = PALETTES[self.theme]
            return QColor(p.success if check.ok else p.danger)
        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> object:
        """Label the numeric columns explicitly as diagnostic errors. Units: per row."""
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]
        return super().headerData(section, orientation, role)
