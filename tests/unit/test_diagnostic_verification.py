from struct_ai.arms.diagnostic_models import SolverObservations
from struct_ai.arms.diagnostic_verification import verify_observations


def test_independent_checker_rejects_a_wrong_sign():
    reference = SolverObservations(
        tip_displacement_m=0.0054,
        tip_rotation_rad=-0.0027,
        support_fx_kn=-12.0,
        support_fy_kn=0.0,
        support_mz_kn_m=36.0,
    )
    actual = SolverObservations(**(reference.model_dump() | {"support_mz_kn_m": -36.0}))
    checks = verify_observations(actual, reference)
    assert checks[-1].demand == 72.0
    assert not checks[-1].ok
    assert all(check.ok for check in checks[:-1])
