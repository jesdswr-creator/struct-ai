import subprocess
import sys

import pytest

from struct_ai.design.footing import design_footing
from struct_ai.design.slab import design_slab
from struct_ai.design.staircase import design_staircase
from struct_ai.services import engine_service


def test_capabilities_never_claim_building_design():
    status = engine_service.get_engine_status()
    assert not status.building_design_available
    assert "not implemented" in status.message
    assert status.draft_beam_flexure_available
    assert not status.ollama_integration_available
    assert engine_service.list_code_constants().records
    assert all(not r.data.verified for r in engine_service.list_code_constants().records)


@pytest.mark.parametrize(
    "building_request", [None, {}, {"storeys": 7}, {"structural_system": "flat slab"}]
)
def test_every_building_request_is_refused_while_unimplemented(building_request):
    with pytest.raises(NotImplementedError, match="No design"):
        engine_service.design_building(building_request)


@pytest.mark.parametrize("function", [design_slab, design_footing, design_staircase])
def test_out_of_v1_design_stubs_never_return_fake_numbers(function):
    with pytest.raises(NotImplementedError, match="outside v1"):
        function()


def test_importing_service_does_not_import_heavy_or_llm_dependencies():
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; from struct_ai.services import engine_service; "
            "assert not any(n.startswith(('openseespy', 'PySide6', 'ollama', 'torch')) "
            "for n in sys.modules); assert not engine_service.get_engine_status()"
            ".building_design_available",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    assert completed.returncode == 0, completed.stderr
