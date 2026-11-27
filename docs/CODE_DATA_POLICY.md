# Code-data policy — M1/M2 public-draft route

The user explicitly authorised numerical transcription from **cited public sources for
draft implementation** on 2026-11-27. This supersedes earlier research-only permission,
not the fail-closed/verification policy. It does **not** establish controlled-code,
amendment-complete or production-compliance data.

There are four required code namespaces. IS 456 now contains **159 unverified records**:
155 numeric values and four nulls (amendment applicability, fire cover, maximum crack
spacing and deflection-chart factors). M1 contributes 33 records; M2 contributes 126. The
other three catalogues remain empty. Whole-building design still raises
`NotImplementedError`. Current-amended-code section calculations raise `MissingCodeValue`.
See the [M1 basis](research/M1_DRAFT_DESIGN_BASIS.md) and
[M2 basis](research/M2_DRAFT_DESIGN_BASIS.md) for exact source locations,
precision conventions, independent derivations and exclusions.

Every scalar, table cell, prescribed coefficient and limit belongs in
`struct_ai/codes/<namespace>/data/*.json`. A catalogue has `schema_version: 1`, a `code`
namespace and a `constants` array. Each record requires:

- `key`: stable identifier local to its namespace;
- `value`: finite JSON number or `null` (no numeric strings or booleans);
- `clause`, `code_edition`, `units`: explicit non-empty source metadata;
- `verified`: ship `false`;
- `verified_by`: ship `null`;
- `source`: identifies the authorised source, without reproducing code text;
- `verification_note`: includes `TODO_VERIFY` when the numerical value is missing.

Do not replace unknown values or references with remembered values. `require()` raises
`MissingCodeValue` when an identifier is absent, its value is null, or its edition,
clause or units still contains `TODO_VERIFY`. M1/M2 callers also declare expected units;
a mismatch raises `CodeDataError` before consumption is recorded. Invalid physical
curve ordering and required missing values do not receive fallbacks.

Usable but unverified values are logged in a run-local tracker. A result retains that
immutable snapshot and its data hash. The report/GUI warning is exactly
`UNVERIFIED CODE CONSTANTS USED: N` when N > 0. N counts **distinct consumed records**,
not repeated accesses or all catalogue entries. Render that snapshot rather than
recounting the registry. The M0b solver diagnostic still consumes **zero** code values,
even though the inventory is no longer empty; its data digest changes with the inventory.

An explicit verification workflow is not implemented. Tests enforce that all shipped
records remain unverified. The schema can represent a future verified record only with
a numerical value and an identified verifier; it does not grant verification itself.
M1/M2 results always declare `verified_code_compliance:false`. A changed amendment scalar
cannot turn on a compliance workflow that does not exist.

`python tools/list_unverified.py` lists every unverified entry, including nulls.
`--json` returns the inventory and canonical data digest. `--data-root PATH` is an
explicit alternate audit/testing input, never a silent fallback for missing packaged
data. Malformed/missing catalogues, duplicate JSON keys and duplicate IDs fail loudly.

Unit conversion factors, algebraic integration and mathematical identities are not code
constants. Numerical root budgets/reserves must be named, documented and disclosed;
they may not relax an engineering pass/fail limit. Draft section examples are explicitly
SAMPLE. Synthetic registry fixtures remain labelled non-code; independent section tests
state the actual unverified draft basis rather than masquerading as certified examples.

Changing data makes a different deterministic result/data hash. Historical source,
CI, frozen or user-report evidence is preserved with its original scope/revision, not
rewritten to imply it tested a newer method or adopted source set.
