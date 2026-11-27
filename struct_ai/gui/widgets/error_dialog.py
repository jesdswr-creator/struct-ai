"""Actionable engine-error presentation with complete copyable context. Units: error-specific."""

from __future__ import annotations

import json
from typing import Any

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from struct_ai.gui.widgets.primitives import label


class ErrorDialog(QDialog):
    """Display, never suppress or convert, a service failure. Units: error-supplied."""

    def __init__(self, error: dict[str, Any], technical_details: str, parent: QWidget) -> None:
        """Expose message/clause/value/limit and expandable traceback. Units: error-supplied."""
        super().__init__(parent)
        self.setWindowTitle("Diagnostic could not complete")
        self.setMinimumWidth(600)
        self.setAccessibleName("Engine error details")
        self.error = error
        self.copy_text = (
            json.dumps(error, indent=2, ensure_ascii=False) + "\n\n" + technical_details
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        layout.addWidget(label("No result was published", "title"))
        self.message = label(error["message"], wrap=True)
        layout.addWidget(self.message)
        self.context = QPlainTextEdit()
        self.context.setReadOnly(True)
        self.context.setAccessibleName("Clause, offending value and required limit")
        self.context.setPlainText(
            json.dumps(
                {key: error.get(key) for key in ("type", "clause", "value", "limit")},
                indent=2,
                ensure_ascii=False,
            )
        )
        self.context.setMinimumHeight(140)
        layout.addWidget(self.context)
        self.details_toggle = QPushButton("Show technical details")
        self.details_toggle.setCheckable(True)
        self.details_toggle.setAccessibleName("Show or hide error traceback")
        layout.addWidget(self.details_toggle)
        self.technical_box = QPlainTextEdit(technical_details)
        self.technical_box.setReadOnly(True)
        self.technical_box.setAccessibleName("Technical error traceback")
        self.technical_box.hide()
        self.details_toggle.toggled.connect(self.technical_box.setVisible)
        layout.addWidget(self.technical_box)
        buttons = QHBoxLayout()
        buttons.addStretch()
        self.copy_button = QPushButton("Copy error details")
        self.copy_button.setAccessibleName("Copy complete engine error")
        self.copy_button.clicked.connect(lambda: QApplication.clipboard().setText(self.copy_text))
        close = QPushButton("Close")
        close.setAccessibleName("Close engine error dialog")
        close.clicked.connect(self.accept)
        buttons.addWidget(self.copy_button)
        buttons.addWidget(close)
        layout.addLayout(buttons)
