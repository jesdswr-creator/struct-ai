"""Real two-node OpenSeesPy diagnostic; no building/code design. Units: kN, m, rad."""

from __future__ import annotations

from collections.abc import Callable
from importlib.metadata import version
from threading import Lock

from struct_ai.arms.diagnostic_models import DiagnosticInput, SolverObservations
from struct_ai.exceptions import SolverFailure

_DOMAIN_LOCK = Lock()


def solve_cantilever(
    inputs: DiagnosticInput, progress: Callable[[str], None]
) -> tuple[SolverObservations, str, str]:
    """Build a vertical, fixed-base elastic member with an X tip force. Units: kN, m.

    The numerical path never calls the closed-form verification functions. OpenSees'
    process-global domain is wiped before AND after a run. Concurrent in-process
    calls are rejected; GUI jobs additionally run in separate spawned processes.
    """
    if not _DOMAIN_LOCK.acquire(blocking=False):
        raise SolverFailure(
            "OpenSees is already running in this process; use an isolated service job.",
            clause="OPENSEES PROCESS-GLOBAL DOMAIN (software constraint)",
            value="concurrent call",
            limit="one active OpenSees domain per process",
        )
    try:
        try:
            import openseespy.opensees as ops
        except (ImportError, RuntimeError, OSError) as error:
            raise SolverFailure(
                f"OpenSeesPy could not load its native library: {error}",
                clause="PACKAGING DIAGNOSTIC (not an IS-code clause)",
                value=type(error).__name__,
                limit="working pinned OpenSeesPy package and native libraries",
            ) from error
        try:
            progress("Building two-node model")
            ops.wipe()
            ops.model("basic", "-ndm", 2, "-ndf", 3)
            ops.node(1, 0.0, 0.0)
            ops.node(2, 0.0, inputs.length_m)
            ops.fix(1, 1, 1, 1)
            ops.geomTransf("Linear", 1)
            ops.element(
                "elasticBeamColumn",
                1,
                1,
                2,
                inputs.area_m2,
                inputs.elastic_modulus_kn_m2,
                inputs.inertia_m4,
                1,
            )
            ops.timeSeries("Linear", 1)
            ops.pattern("Plain", 1, 1)
            ops.load(2, inputs.force_kn, 0.0, 0.0)
            ops.constraints("Plain")
            ops.numberer("Plain")
            ops.system("BandGeneral")
            ops.algorithm("Linear")
            ops.integrator("LoadControl", 1.0)
            ops.analysis("Static")
            progress("Solving linear static analysis")
            return_code = ops.analyze(1)
            if return_code != 0:
                raise SolverFailure(
                    "OpenSees returned a nonzero analysis status; no result published.",
                    clause="OPENSEES analyze(1) return contract (not an IS-code clause)",
                    value=return_code,
                    limit=0,
                )
            ops.reactions()
            observation = SolverObservations(
                tip_displacement_m=ops.nodeDisp(2, 1),
                tip_rotation_rad=ops.nodeDisp(2, 3),
                support_fx_kn=ops.nodeReaction(1, 1),
                support_fy_kn=ops.nodeReaction(1, 2),
                support_mz_kn_m=ops.nodeReaction(1, 3),
            )
            return observation, str(ops.version()), version("openseespy")
        except SolverFailure:
            raise
        except Exception as error:
            # Native/Pydantic failures are translated with their cause, never swallowed.
            raise SolverFailure(
                f"The diagnostic failed: {type(error).__name__}: {error}",
                clause="TWO-NODE SOLVER DIAGNOSTIC (not an IS-code clause)",
                value=inputs.model_dump(mode="json"),
                limit="finite solver outputs and successful analytical verification",
            ) from error
        finally:
            ops.wipe()
    finally:
        _DOMAIN_LOCK.release()
