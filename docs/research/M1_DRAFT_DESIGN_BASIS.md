# M1 draft beam flexure — adopted basis and independent verification

**Status: UNVERIFIED PUBLIC-SOURCE DRAFT. Not current-code compliance or a building design.**
Recorded 2026-11-27. The user explicitly selected
`engineering_data_route=authorize_public_draft_data`. This permits cited numerical
transcription for draft implementation; it does not verify a value, an amendment set,
a steel product, or a design. Every shipped record has `verified:false` and
`verified_by:null`. No standard prose, source PDF, SP16 table or chart is bundled.

## 1. Source intake and limits

The following were reviewed as **parsed text**, not original PDF bytes/figures.
No controlled publication or amendment-complete standard has been reviewed.

| ID | Public source | Actually used |
|---|---|---|
| N02 | [NPTEL / IIT Kharagpur Lesson 2](https://archive.nptel.ac.in/content/storage2/courses/105105104/pdf/m1l2.pdf), §1.2.4 | Steel modulus; representative cold-worked stress-ratio / inelastic-strain primitives; design stress fy/gamma and linear interpolation of total strain. |
| N04 | [Lesson 4](https://archive.nptel.ac.in/content/storage2/courses/105105104/pdf/m3l4.pdf), §§3.4.2, 3.4.5 | Bending strains, concrete law/rounded peak, minimum tensile-strain condition, force equilibrium, and separately labelled equivalent-block comparison. |
| N08 | [Lesson 8](https://archive.nptel.ac.in/content/storage2/courses/105105104/pdf/m4l8.pdf), §§4.8.3–4.8.5 | Compatible compression-steel strain, displaced-concrete correction, minimum tension and maximum tension/compression reinforcement. |
| N10 | [Lesson 10](https://archive.nptel.ac.in/content/storage2/courses/105105104/pdf/m5l10.pdf), §5.10.2 and flange discussion | Composite-action prerequisite, transverse-reinforcement condition, four effective-width rules and actual-width caps, compression/tension-face treatment. |
| F-WEB | [Reinforced Concrete Design, chapter 10 continuation](https://limitstatelessons.blogspot.com/2015/10/Deflection-control-preliminary-dimensions-of-flanged-beams-T-beams.html), items 5/6 | Secondary cross-check for using web width in flanged longitudinal reinforcement limits. This is a teaching blog, not a controlled standard. |

The historical [research-only dossier](M1_PUBLIC_REFERENCES.md) and its source register
retain their earlier status. This document records the subsequent authorised adoption.
NPTEL Lesson 11/12 examples and the ETABS 2016 manual opening were also inspected for
research; **their numerical design answers are not adopted as exact test oracles**.
They use different rounding/simplification conventions. No source's label “all
amendments” is accepted as proof of current completeness. The older NPTEL earthquake
lesson is not a source for IS 13920:2016.

### Explicitly blocked / excluded

- `applicability.current_amendment_review` is **null / TODO_VERIFY**. The BIS metadata
  retrieval/amendment-number discrepancy in the earlier dossier remains unresolved.
- `CURRENT_AMENDED_CODE` requests raise `MissingCodeValue`; editing a scalar cannot
  enable a compliance workflow that has not been implemented.
- The contradictory N04 answer-key inequality and N08 analysis classification are
  not adopted. Use the explicit minimum tensile-strain statement and equilibrium.
- N08's suggestion to relax neutral-axis restrictions for double reinforcement is
  not adopted: every admitted result must remain within the strain-derived limit.
- N08's practical hanger/compression-steel suggestions are **not** mandatory code
  minima. Its SP16 total-strain/stress table is not digitised. Instead derive the
  curve from N02's primitive stress ratios and inelastic strains.
- No automatic TMT/manufacturer-curve substitution, Fe250/550, axial-force design,
  moment redistribution, code load factoring, or seismic detailing is implemented.

## 2. One continuous response model; a separate Annex G comparison

The response model is explicitly named `CONTINUOUS_STRAIN_COMPATIBILITY`. Let y be
the distance from the **active compression face**, x the neutral-axis depth, and d
the distance to the principal tension layer. The explicit sign convention is:
positive moment → top compression; negative → bottom compression. Physical top and
bottom centroid offsets are separate inputs, so reversing sign does not reuse an
inappropriate effective depth.

### Concrete response

Use the adopted N04 teaching convention:

- ultimate concrete bending strain εcu = 0.0035;
- onset of the plateau ε0 = 0.002;
- peak design compression **0.446 fck**, explicitly the rounded NPTEL value.

For 0 < ε < ε0, stress is peak × [2(ε/ε0) − (ε/ε0)²]; for ε0 ≤ ε ≤ εcu,
it equals the peak. Concrete tension is excluded. Plane-section strain is
ε(y) = εcu(1 − y/x). The kernel integrates stress and stress×y analytically over
piecewise-constant widths. There is **no fibre mesh resolution** and no equivalent
rectangular stress-block coefficient inside this integration.

A compression flange adds width bf−bw over its actual thickness. This is continuous
through x=Df and through the plateau/parabola intersection. The Annex G rounded
0.36/0.42 web and 0.45/yf flange approximation is **not spliced into this curve**.
Those approximations can have small boundary inconsistencies when mixed; they are
not silently “fixed” by changing a source coefficient. This draft integrated model
must not be represented as an exact implementation of all Annex G branches.

### Steel response and ductility

Use **fd = fy/1.15 consistently**, not a mixture of fd and rounded 0.87fy. Only
explicitly selected representative cold-worked Fe415/Fe500 is admitted. The primitive
curve has stress ratios 0.80, 0.85, 0.90, 0.95, 0.975, 1.00 and corresponding
inelastic strains 0, 0.0001, 0.0003, 0.0007, 0.0010, 0.0020. Total design strain
at a point is stress/Es + inelastic strain, with Es=200000 N/mm². Interpolate in
**total design strain**, using the elastic line below the first point and the idealised
plateau beyond the last. Tension/compression have the same signed curve. This does
not certify product ductility, fracture strain or a manufacturer's stress-strain law.

The principal tension strain must be at least fd/Es + 0.002. Derive

`r = xu,max/d = εcu / (εcu + fd/Es + 0.002)`.

Do not substitute the rounded 0.48/0.46 values. The floating-point endpoint is made
conservatively representable if necessary so the literal strain check has **no passing
tolerance**. Supplied steel requiring equilibrium beyond the endpoint is refused,
not clamped to a limiting capacity.

For the opposite layer at d′, use εs′=εcu(1−d′/x). Its **net** force is
`As′ [fs(εs′) − fc(εs′)]`. Subtract the concrete displaced at that location. If the
layer is actually in tension, retain its negative force and zero concrete-tension
stress; do not pretend it is yielded compression steel. A loss of positive net
concrete compression is an invalid smeared-layer geometry, not a usable capacity.

### Derived comparison coefficients — not response coefficients

The separate rectangular Annex G comparison is `kG = 0.36 r (1−0.42 r)`:

| Grade | Strain-derived r | kG, equivalent-block comparison | kint, integrated rounded-peak curve |
|---|---:|---:|---:|
| Fe415 | 23/48 = 0.479166666667 | **0.137784375 ≈ 0.138** | 0.138519708404 |
| Fe500 | 161/353 = 0.456090651558 | **0.132740209776 ≈ 0.133** | 0.133429433936 |

For a full rectangle, direct integration gives `C = (17/21) peak b x` and
`Q = (33/98) peak b x²`, hence its centroid is `(99/238)x`. Therefore
`kint = 0.446(17/21)r[1−(99/238)r]`.
These rational factors are mathematical integrations, not separately remembered code
values. The engine derives them by integration; tests use this different closed form.
Both coefficients are returned and labelled. Their difference is not hidden inside
an acceptance tolerance or used to alter expected results.

## 3. Flange participation and reinforcement provisions

For compression flanges, the caller must explicitly confirm integral/effectively
bonded action. Where main slab reinforcement is parallel to the beam, supplied
transverse steel is checked against the cited 60% requirement; absent or inadequate
areas block flanged calculations. No slab design is implied.

The caller supplies **distance between zero moments**, not just a span. No 0.7 span
factor is selected. N10's four width expressions are implemented, always taking the
lesser of computed and actual available width:

- slab-beam T: bw + l0/6 + 6Df;
- slab-beam L: bw + l0/12 + 3Df;
- isolated T: bw + l0/(l0/b + 4);
- isolated L: bw + 0.5l0/(l0/b + 4).

This prescribed lesser-of rule is recorded, not hidden input clamping. A flange in
tension is ignored and the active concrete width is bw. An unusually thick
opposite-face flange that could enter the compression zone is explicitly outside
this ordinary web-only idealisation and is refused. L-section torsion and lateral
response are not covered by pure vertical section flexure.

Longitudinal minimum tension steel uses 0.85 bw d/fy. Maximum tension and opposite
layer limits use **0.04 bw D with overall D**, never d or effective flange width.
If the opposite layer is in tension its area also counts in total tension steel;
the opposite-layer maximum is retained as an additional conservative application
bound, not a claim of compression action. Cover, spacing, bar selection, development,
side-face steel, durability and IS 13920:2016 remain outside M1.

## 4. Inverse sizing, strict checks and numerical policy

The engine sizes **continuous areas**, not bars. The user explicitly chooses
`SINGLE_ONLY` or `ALLOW_COMPRESSION_STEEL`. Over-limit single-only sizing raises a typed
error; geometry is never enlarged. For double sizing, determine a compatible near-limit
state and solve for the extra net compression/tension couple. Then independently
forward-solve force equilibrium for the returned areas before emitting checks.

Computational parameters are named in code and are **not** Indian Standard constants:

- root bracket relative width 1e-13, maximum 128 iterations;
- axial equilibrium error budget 1e-9 of the largest force magnitude;
- positive moment sizing reserve nominally 1e-9 relative, restricted by the single limit;
- double-steel neutral-axis sizing target 1e-8 below the strain-derived endpoint.

Exact limiting-moment equality is compared in the public/check units (kN m), then the
known neutral-axis endpoint is used directly. This avoids falsely rejecting equality
because kN m → N mm → kN m is not always bit-exact. The next representable public-unit
overload still fails single-only sizing; no inequality tolerance is introduced.

These tiny reserves are disclosed in results and actually increase required provision;
they never change a demanded action or relax `demand <= capacity`. Minimum tension
steel can govern and is explicitly identified. Such a case is intentionally stronger
than a tiny requested moment, not forced to pass an artificial exact round-trip test.

Every numerical check is a CheckResult. Inadequate strength/steel provision returns
`REVISE_SECTION` with failed checks. Invalid geometry, unsupported scope, nonpositive
capacity, over-reinforcement, missing data and numerical failures raise typed errors
with clause/value/limit context. A valid SHA-256 is integrity/reproducibility evidence,
not engineering certification.

## 5. Independent checks and examples

The tests import no production material/section calculation into their reference helper.
For b=300 mm, D=550 mm, d=500 mm, fck=25 N/mm² and **no opposite steel**, independent
rational integration gives:

| xu (mm) | C (N) | Ast Fe415 (mm²) | Ast Fe500 (mm²) | M (kN m) |
|---:|---:|---:|---:|---:|
| 60 | 162471.428571 | 450.222030981 | 373.684285714 | 77.1807551020 |
| 120 | 324942.857143 | 900.444061962 | 747.368571429 | 146.251591837 |
| 210 | 568650 | 1575.77710843 | 1307.895 | 234.65175 |

Separate flange tests use piecewise Simpson integration (exact for each quadratic
stress / cubic moment polynomial), not the production antiderivatives. Tests cover
both grades, non-yielded compression steel, displaced concrete including its parabolic
range, an opposite layer in tension, flange/web/plateau transitions, four width rules,
negative bending, mirrored geometry, zero overhang, minimum provision, overall-D maximum
steel, explicit failures, units, provenance, service isolation and deterministic JSON.
Hypothesis exercises inverse/forward round trips (≤0.1%), tension-steel monotonicity and
admissible-flange-width monotonicity. No expected engineering values are tuned to match
a production result. No textbook values or SP16 charts have been supplied/verified.

Opt-in JSONs in `examples/SAMPLE_beam_*.json` are hypothetical numerical examples,
**not the user's building, defaults or construction designs**. The GUI remains the
M0b diagnostic. A new screenshot would not demonstrate M1 section UI because that UI
is not implemented; the M13 screenshot/feedback gates remain outstanding.

## 6. Human review still required

1. Obtain the controlled current IS 456 edition/amendments and reconcile each record,
   clause, constitutive interpretation and applicability assumption.
2. Review the chosen rounded teaching curve versus the intended production method;
   do not mislabel the integrated response as Annex G equivalent-block compliance.
3. Confirm steel-product curve/ductility, material exposure suitability, geometry,
   actual reinforcement positions and composite action.
4. Independently check hand/reference examples and all subsequent engineering gates.
5. Retain the separate OS/selftest evidence for the user's clean-Windows acceptance.
6. Do not use a draft-section PASS as a building, detailing or construction approval.
