# Draft M2 beam component checks

**DRAFT: must be reviewed and sealed by a licensed structural engineer.**
**Not a complete member or building design. No current-code compliance is established.**

Four explicitly requested operations now use the sole `engine_service` boundary:

| Operation | Implemented draft subchecks | Not claimed |
|---|---|---|
| `SHEAR_TORSION` | Table 19/20 shear; supplied vertical stirrups; rectangular closed-cage torsion, equivalent moments through M1; side-face requirements | Generated actions, support enhancement, curtailment, flanged torsion, seismic capacity design, full bar/cage layout |
| `DEVELOPMENT_LENGTH` | Supplied straight length vs deformed-bar Ld, explicit stress/state/equal-diameter bundle | Lap, hook/bend credit, support M/V, joint/seismic anchorage or bundle-layout approval |
| `COVER_SPACING` | Base exposure cover/bar diameter, minimum horizontal/vertical clear spacing | Fire, maximum crack-spacing, concrete mix durability, cover reduction, cage-fit or construction tolerance |
| `DEFLECTION_LIMITS` | Both final and post-finish limits against documented externally supplied service deflections | Calculating building deflections, effective stiffness, creep/shrinkage/temperature or chart factors |

Requests for fire, maximum crack-spacing or span/depth charts raise `MissingCodeValue`.
Filling a single placeholder cannot enable an unimplemented workflow. All current-amended
code requests remain blocked. Do not interpret unrequested/unsupported checks as passed.

## Source use

```python
from struct_ai.services import engine_service
run = engine_service.assess_beam_checks(explicit_input_dict)
trace = engine_service.beam_checks_report(run)
```

Input and result models are strict, immutable and revalidated at service ingress. No
coercion, project/site defaults or automatic bar/section selection. Each `CheckResult`
is literal demand <= capacity, with no positive passing tolerance. Minimum provisions
are represented by required minimum as demand and actual provision as capacity.

```sh
python -m struct_ai.cli.beam_checks examples/SAMPLE_beam_shear.json \
  --output results/shear.json --report results/shear.md --error-output results/shear-error.json
```

The application entry also exposes `python -m struct_ai --beam-checks INPUT.json`,
and M1 via `--beam-flexure INPUT.json`. These switches are usable in the Windows EXE.
The desktop itself is still the solver-diagnostic screen, not a new beam/building UI.

All destination paths must be new and distinct. Error JSON is written only on error;
`REVISE_SECTION` is a completed failed assessment with result JSON, not an exception.
Exit **0** means only requested draft checks pass; **1** means revise; **2** means error.
No pass means verified code compliance. File-operation failures may leave partial outputs,
are reported nonzero and must not be treated as a completed result.

## Explicit SAMPLE inputs

- `examples/SAMPLE_beam_shear.json`
- `examples/SAMPLE_beam_torsion.json`
- `examples/SAMPLE_beam_development_length.json`
- `examples/SAMPLE_beam_cover_spacing.json`
- `examples/SAMPLE_beam_deflection_limits.json`

Samples are opt-in synthetic numerical inputs, **not a project design**. The deflection
sample contains supplied test numbers, not the result of any building analysis.

## Units, geometry and stress conventions

Actions are already-factored **kN / kN m**; geometry **mm**; areas **mm²**; stress **N/mm²**.
Shear/torsion magnitudes are used, while signed bending identifies the physical principal
layers. Pure torsion/zero bending is currently refused. Shear uses web width and active d;
torsion equivalent moment and side-face area use overall D. Closed stirrup centreline
width/depth are distinct from corner-bar centre distances; the latter depth is obtained
from the declared physical principal-layer centroids.

Shear formulas use the sourced **0.87fy** and explicitly report both declared and credited
stirrup fy (including the 415 N/mm² ceiling). M1 still uses **fy/1.15** for its constitutive
law; its data, numerical expectations and model revision are not changed. Equivalent
longitudinal moments and transverse torsion are conservatively retained for all nonzero
torsion, including below tau_c. No torsion is silently discarded.

The Table 19 axis and full selected grade column are consumed to validate monotonicity,
then linearly interpolated in actual tensile percentage; labelled end rows are explicit.
No interpolation between concrete grades, nor extrapolation above M40, is implemented.
Side-face reinforcement is additional, not credited to M1's two principal layers.

## Data and verification limits

M2 adds **126 unverified records: 123 numeric and three null**. With M1 the catalogue has
**159 unverified records: 155 numeric and four null**. Each result/report displays its
own actual-use count; this is not the inventory total. Data/inputs/results are hashed.

[Detailed adopted sources, known source discrepancies and restrictions](research/M2_DRAFT_DESIGN_BASIS.md).
Independent tests validate the implemented draft arithmetic and contracts, not the source's
current legal/engineering applicability. Controlled amendments, visual source review,
material applicability and independent licensed-engineer review remain outstanding.
