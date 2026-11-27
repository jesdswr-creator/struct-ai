# Code-data policy (M0)

No Indian Standard calculation is implemented, and no numerical code record has been
supplied. All four shipped catalogues are deliberately empty. This does **not** make
a building design verified. The building-design service raises `NotImplementedError`.

Every future scalar, table cell, prescribed coefficient and limit belongs in
`struct_ai/codes/<namespace>/data/*.json`. A catalogue has `schema_version: 1`, a `code`
namespace and a `constants` array. Each record requires:

- `key`: stable identifier local to its namespace;
- `value`: finite JSON number or `null` (no numeric strings or booleans);
- `clause`, `code_edition`, `units`: explicit non-empty source metadata;
- `verified`: ship `false`;
- `verified_by`: ship `null`;
- `source`: identifies the supplied authorised source, without reproducing code text;
- `verification_note`: includes `TODO_VERIFY` when the numerical value is missing.

Do not replace unknown values or references with remembered values. `require()` raises
`MissingCodeValue` when an identifier is absent, its value is null, or its edition,
clause or units still contains `TODO_VERIFY`. Usable but unverified values are logged
in a run-local tracker. A result must retain that immutable snapshot and its data hash.
The GUI/report warning is exactly `UNVERIFIED CODE CONSTANTS USED: N` when N > 0.
N counts **distinct consumed records**, not repeated accesses or all catalogue entries.
Reports and widgets must render that snapshot rather than recounting the registry.

An explicit verification workflow is not implemented. Tests enforce that all shipped
records remain unverified. The schema can represent a future verified record only with
a numerical value and an identified verifier; it does not grant verification itself.

`python tools/list_unverified.py` lists every unverified entry, including nulls.
`--json` returns the inventory and canonical data digest. `--data-root PATH` is an
explicit audit input, never a silent fallback for missing packaged data. Malformed or
missing catalogues, duplicate JSON keys and duplicate IDs fail with structured errors.

Unit conversion factors and mathematical identities are not code constants. Numerical
comparison tolerances must be named and documented as computational tolerances; they
may not relax an engineering acceptance limit. Test fixtures use clearly labelled
synthetic records, not invented Indian Standard values.
