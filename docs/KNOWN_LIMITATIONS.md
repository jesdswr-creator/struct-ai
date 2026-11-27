# Known limitations — M1/scoped M2 drafts / diagnostic desktop

## Not a complete structural design application

- M1 provides **unverified beam-section flexure only**, through the service/CLI, not
  the diagnostic GUI. Its integrated teaching curve is not the Annex G equivalent
  block; the latter is a separate comparison. [Exact basis and limitations](research/M1_DRAFT_DESIGN_BASIS.md).
- M2 adds **scoped** shear/torsion, straight Ld, base cover/minimum clear spacing and
  externally supplied service-deflection limit checks. Fire, maximum crack spacing and
  deflection-chart requests fail closed. This is **not full-member design or full M2
  acceptance**. [Details](M2_BEAM_CHECKS.md).
- No BuildingInput, RC building model, seismic analysis, member-line design or independent
  building verification exists. `design_building()` rejects every request.
- Therefore no specific regularity, soft/weak-storey, cantilever or other v1 scope
  screening is claimed. Unsupported and otherwise-supported buildings are all refused.
- IS 456 has 155 numeric public-draft values and four null missing records,
  all unverified. Current-amended-code compliance is blocked. IS 875 / IS 1893 /
  IS 13920 catalogues remain empty. Unimplemented M2 routes and M3–M15 remain gated.
- No slab/footing/staircase design, bar selection, drawings, schedules, DOCX, DXF,
  spreadsheet output or project save/load. Explicit Python stubs raise NotImplementedError.
- No Ollama integration, assistant tools, inference, training, weights or fine-tuning.
- No M13 nine-page desktop workflow, first-run acknowledgement flow, plan editor,
  modal/seismic charts or building result browsing. This window is only an M0b diagnostic.

## Diagnostic assumptions and software bounds

The real numerical model is a vertical 2D elastic Euler–Bernoulli cantilever, fixed at
its base, with a signed horizontal tip force. Analysis uses kN/m/rad. It excludes
self-weight, shear deformation, dynamics, seismic effects and Indian Standard design.

The displayed synthetic inputs are benchmark parameters, not project defaults or
material values selected from a code. Schema limits are computational-domain limits,
not Indian Standard restrictions. The nonzero force magnitude must be at least 1e-6 kN
to avoid subnormal analytical/error-budget underflow across the allowed domain. No
out-of-range input is clamped. Convergence or independent-check failure blocks the run.

`CheckResult` currently represents a non-negative required amount versus a positive
available amount. Minimum-provision checks would encode required/provided in that
order. Signed actions live in separate observations. Zero/undefined capacity must
raise instead of producing NaN or infinity. The diagnostic's displayed ratios are
**numerical error / error budget**, not member structural utilisations.

## Packaging acceptance remains open

- Windows 11 x64 is proposed, not certified; Windows 10 and ARM64 are not tested.
- Current source tests pass **526 cases on both Windows and Ubuntu 24.04**. The
  actual Windows onedir build, both frozen diagnostic selftests and 15 section-command
  paths pass, including source/frozen result/report comparisons. The build host is
  **Windows Server 2025** with the native `windows` Qt plugin, not a separate clean
  Windows 11 machine. See [saved M2 CI/publication evidence](evidence/m2/README.md).
- A [seven-day section-enabled draft EXE bundle](WINDOWS_DRAFT_BUNDLE.md) was uploaded
  by an explicitly user-authorised manual run at `c60b6e9`. Automatic binary publication
  remains disabled; this is not commercial redistribution approval. No installer has
  been generated. The interactive `.cmd` SAMPLE launcher itself has not been observed
  end-to-end here; its underlying frozen section commands passed CI.
- Historical Linux source/frozen evidence used a custom matching shared Python runtime
  for the restricted sandbox. That excluded bundle/cache is not retained and was not
  rebuilt after the Windows fixes.
- The user reports clean Windows without Python/Qt/OpenSees/Ollama, five passing GUI
  checks and both documented selftests. M0b execution is accepted **on that report**;
  no OS version, JSON reports, hashes or screenshots were independently reviewed.
  The earlier download still contains only the M0b diagnostic, not M1 functionality.
  A newer section-enabled Actions build does not inherit clean-machine acceptance from it;
  [new bundle instructions](WINDOWS_DRAFT_BUNDLE.md) distinguish its scope and test gates.
- The supplementary Linux onedir build is tested with Qt's offscreen backend only;
  optional XCB/GTK dependencies emitted warnings. A Linux graphical desktop release
  is not claimed or supported by this spike.
- Offscreen scaled captures use logical viewport dimensions. They do not prove fit
  on a 1366×768 physical display at 125%/150%. The requested 1100×700 minimum logical
  window itself exceeds that physical workspace at those scales; resolve this trade-off
  with the user before M13. The prototype has a scrollable content area.
- Native Windows cold-start, idle-memory, accessibility and antivirus measurements
  remain pending. A 337 MiB Linux bundle size is disk usage, not an idle-RAM result.
- No signed EXE, Inno Setup installer or automatic update mechanism exists.

## Licensing and engineering decisions

OpenSeesPy's bundled notice requires a separate licence for commercial redistribution.
Qt/LGPL, font and all transitive dependency obligations require release review.

Exact G+4-only versus up-to-six-storey scope, structural-height definition, site/soil,
occupancy/importance, lateral-system classification, load takedown, wind inclusion,
infill treatment, preliminary members, concrete/steel grades, exposure, cover,
aggregate size, fire resistance, source editions/amendments and irregularity criteria
are unresolved. No defaults have been silently chosen for these decisions.

A passing solver diagnostic is neither code compliance nor engineering approval.
All later outputs must be reviewed and sealed by a licensed structural engineer.
