# M1 public-reference review — historical research-only record

**Later authorisation/adoption:** the user subsequently authorised public-source numerical
**draft implementation**. See [the adopted M1 basis](M1_DRAFT_DESIGN_BASIS.md) and
[separate adoption record](M1_DRAFT_SOURCE_ADOPTION.json). The original research findings
below and `M1_SOURCE_REGISTER.json` are preserved as historical records, not current
claims that permission or clean-machine acceptance is still missing. The adopted data
remains unverified; current-amendment applicability remains unresolved.

Research date: **2026-11-27**. The user authorised locating public references for review.
This does **not** accept M0b, start the M1 implementation, approve a design basis, or verify
any code constant. The runtime catalogues remain empty. No standard text, PDF, design-aid
table or numerical stress-strain table has been copied into the repository.

## 1. Source shortlist and retrieval quality

### BIS publication record — primary metadata, retrieval incomplete

The search-index preview of BIS's standard-details record identifies IS 456:2000, fourth
revision, and lists six amendments, including a 2024 sixth amendment. **Direct retrieval
returned HTTP 500**, so this is an indexed discovery lead, not a freshly verified amendment
set. Obtain the controlled publication and all applicable amendments before adopting values.
[2](https://standards.bis.gov.in/website/standard-details?encryptedId=eyJpdiI6InVIejZUOFI5V1Z5RXZMWEZGNnh4a1E9PSIsInZhbHVlIjoiZ1ZhcnlpWEFRVE00Q1dndk1Tc3lrQT09IiwibWFjIjoiYjAzMjg2ZDY3YWE0NzhkNGRlZDczYzI2ZGJiZTVkNThiNThlYmZmNTI3MDFmZTA0MzljNWM5Njg1ZWNmYjhhNiIsInRhZyI6IiJ9)

A BIS formulation record's indexed title and amendment-number field differ. Its direct
retrieval also returned HTTP 500. A development/work-item record must not be substituted
for the published standard's amendment record.
[1](https://www.services.bis.gov.in/php/BIS_2.0/StandardsFormulationV2/doc_details_outside.php?ID=MTM4MDQ%3D)

### IIT Kharagpur / NPTEL — secondary teaching references

The returned text of these four lessons was read through the fetch tool's final chunk.
This was **parsed-text review, not visual verification of PDF figures or original PDF bytes**.
Their attribution to IS 456:2000 does not establish incorporation of later amendments.

| ID | Directly retrieved source | Potential role, subject to review |
|---|---|---|
| N04 | <https://archive.nptel.ac.in/content/storage2/courses/105105104/pdf/m3l4.pdf> | Flexural assumptions, section equilibrium, compression resultant and lever-arm derivation; steel-curve references. |
| N05 | <https://archive.nptel.ac.in/content/storage2/courses/105105104/pdf/m3l5.pdf> | Neutral-axis limits and limiting moment derivation; distinction between design rejection and an existing-section assessment convention. |
| N08 | <https://archive.nptel.ac.in/content/storage2/courses/105105104/pdf/m4l8.pdf> | Compression-steel strain/stress, displaced-concrete correction, and longitudinal reinforcement provisions. |
| N10 | <https://archive.nptel.ac.in/content/storage2/courses/105105104/pdf/m5l10.pdf> | Flange coupling, effective widths, compression-side geometry and flange/web cases. |

N10's retrieved text explicitly references Clause 23.1.2 and Annex G; these remain
secondary attributions requiring controlled-code checks.
[2](https://archive.nptel.ac.in/content/storage2/courses/105105104/pdf/m5l10.pdf)

**Do not extend this approval to the whole course.** The indexed earthquake-design lesson
uses IS 13920:1993, not the project's requested 2016 edition. It is not an accepted source
for M4 detailing; its full text was not reviewed here.
[1](https://archive.nptel.ac.in/content/storage2/courses/105105104/pdf/m16l40.pdf)

## 2. Review issues found — why automatic transcription is unsafe

- **N04, sections 3.4.2 and 3.4.8:** the retrieved assumption and a multiple-choice answer
  appear inconsistent about the direction of a strain inequality. This may involve source
  or extraction errors; check the original figure/text and controlled code. Do not turn the
  answer key into a test oracle. Its stress-block derivation also distinguishes resultant
  location from the depth of the constant-stress region; those are not interchangeable.
- **N05, sections 3.5.2–3.5.6:** the lesson includes rounded limits and a simplified lever-arm
  expression. The project must choose and document one sourced precision convention, not
  mix rounded tables with a different constitutive model to force a round-trip test to pass.
- **N08, sections 4.8.3–4.8.6:** compression-steel stress is strain-dependent and displaced
  concrete is accounted for. Some tabulated stresses are explicitly attributed to SP-16;
  they are not a substitute for an approved constitutive curve. The retrieved analysis-type
  classification sentence needs checking. Its maximum-steel reference distinguishes overall
  depth from effective depth; its practical compression-steel suggestions must not be
  promoted into mandatory code limits.
- **N10, sections 5.10.2–5.10.4:** coupling, actual-width restrictions, the compression face,
  and branch-dependent flange treatment matter. Some parsed equations lose primes or split
  denominators across lines. Do not implement from that OCR. Teaching cases that restrict a
  neutral axis to a limiting value are not permission for this application's prohibited
  silent clamping of an invalid design into a PASS.

These are **review flags**, not verified errata or replacement code provisions. The URLs
and exact lesson sections above make the concerns inspectable. No numerical correction
has been silently substituted.

## 3. Data required before the M1 service can consume anything

The following is an intake checklist, **not a data catalogue**. Numerical values and exact
record-level citations remain unresolved until transcription/review. Where a primary
reference is not established, use `TODO_VERIFY`; do not infer a clause from memory.

| Required group | Units | Candidate source locations to check | Still required |
|---|---|---|---|
| Concrete constitutive model and limiting strains | N/mm²; dimensionless strain | N04 §3.4.2, §3.4.5; referenced IS figures | Controlled equations, bounds, exact clauses and rounding convention |
| Steel curves and elastic modulus for each admitted grade/type | N/mm²; dimensionless strain | N04 §3.4.2; N08 §4.8.4; referenced IS Figure 23 | Actual applicable curve points/equations, modulus source, interpolation and range rules |
| Material factors and tensile-strain/neutral-axis limits | dimensionless | N04/N05; N08 cites Clause 38.1 Note | Exact primary references; consistent derived versus prescribed precision |
| Minimum/maximum longitudinal steel | mm²; dimensionless coefficients | N08 §4.8.5 cites 26.5.1.1(a)/(b), 26.5.1.2 | Amended provisions; correct overall/effective-depth roles |
| Flange participation requirements | geometry and reinforcement-specific | N10 §5.10.2.1 cites 23.1.1 | Evidence that the assumed composite action is applicable |
| Effective flange width | mm; dimensionless coefficients | N10 §5.10.2.2 cites 23.1.2 | Actual-width limits and explicit zero-moment-distance input/derivation |
| Flanged compression model and case boundaries | N/mm²; mm; dimensionless ratios | N10 §5.10.4 cites G-2.2 | Full applicable Annex G branches, boundaries and limits |
| Compression-steel/concrete interaction | N/mm²; mm² | N08 §4.8.3–4.8.4 | Primary-model correspondence and independent force-equilibrium verification |
| Applicability and amendments | documentary | Controlled IS 456:2000 publication and adopted amendment set | Responsible engineer's edition/amendment selection and scope review |

Any later adopted numerical record belongs in `struct_ai/codes/is456_2000/data/*.json`,
with explicit value, units, clause, code edition, source, `verified:false` and
`verified_by:null`. Missing information stays null/`TODO_VERIFY`; required missing values
must raise `MissingCodeValue`. Review-only bibliography entries are not consumable constants.

## 4. Proposed verification work after the acceptance/data gates

This is a plan, not a claim that these functions or tests exist:

1. Derive limiting moment coefficients from the accepted primitive data; do not store a
   remembered coefficient as an independent authority.
2. Use separate forward capacity and inverse steel-area checks, retaining the user-required
   round-trip tolerance and independent analytical derivations.
3. For doubly reinforced sections, solve actual strain compatibility; test cases where
   compression steel has not reached the design plateau.
4. Exercise both bending signs, flange-in-compression versus flange-in-tension, branch
   transitions, and the rectangular limiting geometry.
5. Check maximum steel against overall depth; reject invalid geometry, unsupported material
   domains and over-limit designs with typed clause/value/limit context.
6. Add monotonicity/property tests and independent hand/reference checks without changing
   expected results to fit the implementation or digitising SP-16 column charts.

## 5. What this research does and does not unblock

**Completed:** a traceable public-reference shortlist, explicit retrieval limitations,
source-specific review flags, and a bounded intake checklist. Machine-readable metadata:
`M1_SOURCE_REGISTER.json` beside this document. All entries are unverified and not adopted.

**Not completed:** controlled-code reconciliation, numerical transcription approval,
M0b clean-Windows acceptance, or any M1 engineering implementation. Public availability
alone does not grant redistribution rights. Only our own review notes and links are stored;
no copyrighted standard prose or source PDFs are bundled. A licensed structural engineer
must review the eventual design basis and every production design.
