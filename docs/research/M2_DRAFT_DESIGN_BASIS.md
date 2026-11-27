# M2 draft basis and announced implementation plan — 2026-11-27

**UNVERIFIED PUBLIC-SOURCE DRAFT. Not current-code compliance, a building design or
construction documentation.** The user's existing public-draft-data authorisation
continues. No constants are promoted to verified by software tests.

## Increment planned before implementation

1. Add provenance-bound Table 19/20 shear data and explicit vertical-stirrup checks.
2. Assess supplied shear/torsion actions, actual longitudinal areas and closed stirrups;
   report equivalent moments and forward-check both required physical faces with M1.
3. Add straight development-length checks for explicitly declared IS 1786 deformed
   bars; do not infer lap length, bend credit, joint anchorage or seismic detailing.
4. Add limited cover/clear-spacing checks and checks of independently supplied final
   service deflections. Missing fire/maximum-spacing/deflection-chart data block those
   requested routes, not get replaced with guessed factors.
5. Independent table transcription expectations, rational arithmetic, signs/units,
   physical geometry, missing data, exact boundaries and property-based tests.
6. Expose these operations through the sole engine service and a strict JSON CLI.
7. Run full source CI, then actual frozen section calculations in Windows Actions and
   publish an explicitly draft onedir bundle following the user's request. This is not
   completion of M13–M15, an installer, a clean-machine M2 test or whole-building design.

## Sources actually read

All are parsed text (no downloaded/visually verified source PDF bytes). No copyrighted
standard prose or PDF is copied into this repository. Numerical records remain
`verified:false`, `verified_by:null`. Dates below are access dates, not standards dates.

- **N13** https://archive.nptel.ac.in/content/storage2/courses/105105104/pdf/m6l13.pdf
  chunks 0–1, 2026-11-27: §§6.13.3–8; Table 6.1 (IS 456 Table 19), Table 6.2
  (Table 20), vertical stirrups, minimum reinforcement, fy ceiling, spacing.
- **N14** https://archive.nptel.ac.in/content/storage2/courses/105105104/pdf/m6l14.pdf
  chunk 0, 2026-11-27: §6.14.2 Problem 1 explicitly uses linear interpolation in
  tensile-steel percentage. Published steel/bar/percentage rounding is not an exact oracle.
- **N15** https://archive.nptel.ac.in/content/storage2/courses/105105104/pdf/m6l15.pdf
  chunks 0–1, 2026-11-27: §6.15.2 Table 6.4, §6.15.3 Eq.6.12 and bundle increases.
  **Do not adopt the surrounding claim that a 25%/60% increase in bond stress gives
  a 25%/60% reduction in length.** The equilibrium equation gives reciprocal factors.
  No SP16 table, hook/bend credit, lap or support M/V rule is implemented here.
- **N16** https://archive.nptel.ac.in/content/storage2/courses/105105104/pdf/m6l16.pdf
  chunks 0–1, 2026-11-27: §§6.16.6–8, equivalent shear/moments, two-legged closed
  stirrups, corner-bar geometry, side faces and torsion spacing. The apparent missing
  division sign in Eq.6.29 and inconsistent worked-example side-face depth are NOT
  adopted; M1 owns minimum longitudinal reinforcement and side-face area uses bw*D.
- **N17** https://archive.nptel.ac.in/content/storage2/courses/105105104/pdf/m7l17.pdf
  chunk 0, 2026-11-27: §7.17.3 final and post-partition deflection limits. Figures
  4/5/6 and Annex C effective stiffness/creep/shrinkage calculations are NOT adopted.
- **COVER** https://www.civilengineeringweb.com/2024/03/concrete-cover.html
  chunks 0–1, 2026-11-27: Table 16 exposure-based base covers only. Ignore blanket
  member-type 'typical covers', reductions, tolerance advice and unread fire-table image.
- **SPACING** https://civil4m.com/threads/minimum-spacing-between-vertical-bars-of-column-as-per-is-code-is.4757/
  chunk 0, 2026-11-27: staff explanation attributed to 26.3.2 (horizontal diameter/
  aggregate+5, aligned rows and vertical 15/2/3 aggregate/diameter). It is a secondary
  forum explanation, not authority. No needle-vibrator reduction is adopted.
- **CODE-INDEX** https://www.svvv.edu.in/assets/pdf/Institute/Civil%20Engineering/IS%20456-2000.pdf
  search excerpt only, 2026-11-27: 26.4.1 cover at least bar diameter; Table 16 base
  cover cross-check. Weaker search-only evidence is explicitly recorded, not called a
  reviewed full standard. Apply the largest nominated bar diameter conservatively to
  the nominal cover to the outermost reinforcement; no cover reduction is credited.

The Public.Resource mirror https://law.resource.org/pub/in/bis/S03/is.456.2000.pdf
was fetched at chunk 0. Its title identifies the April 2007 tenth reprint with
Amendments 1 and 2. The tool limits PDF extraction to 30 pages, so later cover/shear
provisions were NOT reviewed there. This does not resolve present-day amendments.

## Restricted model and audit choices

- One already-factored signed moment/shear/torsion station of a uniform-depth beam.
  No axial force, taper, enhancement near support, curtailment, action selection,
  redistribution, dynamic/cyclic shear or IS 13920 capacity design is inferred.
- Caller confirms the critical action location and tension-steel anchorage/continuity.
  Shear uses web width and active effective depth; concrete grades are discrete M20,
  M25, M30, M35, M40. No interpolation across concrete grades or extension above M40.
- Table 19 row interpolation is linear in the actual percentage; the labelled <=0.15
  and >=3.00 rows apply at their respective ends. The actual percentage is retained,
  never silently replaced. The complete selected column and row axis are validated
  and appear as consumed records; other concrete-grade columns are not consumed.
- Shear uses the catalogued **0.87fy**, including the explicit **415 N/mm² fy ceiling**.
  This is a different approximation from M1's **fy/1.15** constitutive law. Both are
  labelled; no substitution into M1 or alteration of its expected tests.
- Positive and negative shear/torsion are assessed by magnitudes; the signed bending
  direction maps the physical longitudinal layers. Pure torsion/zero bending is refused
  until a separate directional contract exists. Torsion is restricted to rectangles,
  two-legged closed rectangular stirrups, confirmed corner bars and supplied geometry.
- Nonzero torsion always retains both applicable equivalent moments for the M1 forward
  checks, even below the concrete shear threshold (an explicit conservative policy).
  The transverse torsion equation is also always evaluated, not erased below a threshold.
- Side-face provisions use **overall D** and supplied separate face areas/maximum
  spacing; these areas are not credited to M1's two principal layers. Full bar-layout,
  cage-fit, crack control and seismic checks remain separate future gates.
- Ld is straight available length compared with phi*sigma/(4*tau_bd); specified stress
  is not silently taken as yield. Equal-diameter bundles only; the bundle Ld increase
  is not approval of bundle layout, laps, bend bearing or compression confinement.
- Cover/spacing is explicitly partial: base durability cover, bar diameter and minimum
  clear distances only; no Table 15 crack-spacing/fire/mix-design verification. Vertical
  spacing applies only to multiple aligned rows. No compaction reduction is credited.
- Deflection service checks **externally calculated, explicitly documented unfactored
  final and post-finish deflections** including creep/shrinkage/temperature. It does not
  generate those deflections from a building or certify their source. Missing charts
  raise MissingCodeValue when requested; a supplied factor cannot bypass the catalogue.
- Only requested subchecks can pass; result status will be `DRAFT_COMPONENT_CHECKS_PASS`,
  never a complete-member/building approval. Failed checks give `REVISE_SECTION`.
  Input/data/scope errors raise typed errors; no sizing/clamping/rounding to pass.

## Human verification still required

Controlled and current-amended standards; every table cell, equation and material
assumption; source visual checking; fire and crack-spacing provisions; actual cage and
anchorage; seismic detailing; independently derived loads/service deflections and
building analysis; and licensed structural-engineer review. Full feature verification
cannot be claimed while these gates are outstanding.
