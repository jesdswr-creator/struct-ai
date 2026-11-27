import pytest
from PySide6.QtCore import QSettings

from struct_ai.gui.app import configure_application
from struct_ai.gui.spike_window import SpikeWindow


@pytest.fixture
def window(qapp, qtbot, tmp_path):
    configure_application(qapp)
    settings = QSettings(str(tmp_path / "preferences.ini"), QSettings.Format.IniFormat)
    widget = SpikeWindow(settings=settings, theme="light")
    qtbot.addWidget(widget)
    widget.show()
    qapp.processEvents()
    yield widget
    widget.close()
