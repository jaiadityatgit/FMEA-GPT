# Phase 5E — Knowledge Gap Analysis

## Methodology

Gaps identified exclusively from verified Phase 5D benchmark failures in `tests/retrieval_ground_truth.json` and documented root-cause analysis in `docs/phase5d_failure_analysis.md`. No gaps are invented.

---

## 1. Verified Knowledge Gaps (Ranked by Benchmark Impact)

### Gap 1: Thermal Fatigue / Thermomechanical Fatigue (TMF)

| Field | Value |
| :--- | :--- |
| **Gap** | Thermal fatigue mechanisms, cyclic thermal strain, TMF crack initiation |
| **Affected Benchmark Queries** | RET-01 (`thermal stress cyclic gradients transient temperatures structural fatigue`), RET-02 (`high pressure turbine blade thermomechanical fatigue TMF cracking start stop cycles`) |
| **Engineering Capability Affected** | Cannot generate evidence-grounded failure modes for HPT blade thermal fatigue — the single most common life-limiting mechanism for turbine airfoils |
| **Current Corpus Limitation** | The 8 indexed documents (MIL-STD-1629A, MIL-HDBK-338B, FAA AC 33.75, CS-E, NASA standards) are regulatory/procedural standards. They mention "thermal stress" in passing but contain no textbook-level descriptions of cyclic thermal strain hysteresis, transient temperature gradients, or TMF crack nucleation. |
| **Source Type Needed** | NASA technical report or handbook on gas turbine engine failure modes, turbine blade materials degradation, or engine durability |
| **Phase 5D Metrics** | P@1: 0.0%, R@5: 0.0%, MRR: 0.0000 across ALL configurations |
| **Corpus Gap Confirmed** | Yes — Phase 5C manual grep found zero occurrences of "transient thermal strain" in `data/raw/` |

### Gap 2: Cooling System / Internal Cooling Passage Physics

| Field | Value |
| :--- | :--- |
| **Gap** | Internal turbine blade cooling passage blockage, film cooling degradation, heat transfer loss |
| **Affected Benchmark Queries** | RET-11 (`compressor bleed air cooling airflow turbine casing temperature management`), RET-12 (`turbine blade internal cooling passage blockage particulate clogging heat transfer loss`) |
| **Engineering Capability Affected** | Cannot reason about cooling system failure modes. RET-12 is a confirmed corpus gap with `corpus_gap: true` in ground truth. RET-11 fails because CS-E and AC 33.75 discuss "bleed air" only in the context of customer power extraction, not internal blade cooling aerothermodynamics. |
| **Current Corpus Limitation** | No text in the corpus describes serpentine cooling passages, film cooling effectiveness, or thermal management of individual blade internal channels. |
| **Source Type Needed** | NASA technical report on turbine blade cooling, engine thermal management, or gas turbine heat transfer |
| **Phase 5D Metrics** | P@1: 0.0%, R@5: 0.0%, MRR: 0.0000 across ALL configurations |
| **Corpus Gap Confirmed** | Yes (RET-12 explicitly marked `corpus_gap: true`) |

### Gap 3: Fretting Fatigue / Contact Mechanics

| Field | Value |
| :--- | :--- |
| **Gap** | Fretting fatigue at blade root dovetail/fir-tree contacts, micro-motion wear, galling |
| **Affected Benchmark Queries** | RET-13 (`fretting fatigue micro-motion dovetail root contact stress crack initiation`), RET-14 (`blade root fir-tree slot contact surface fretting wear galling`) |
| **Engineering Capability Affected** | Cannot generate evidence-grounded fretting fatigue failure modes for blade-disk attachment joints |
| **Current Corpus Limitation** | Both RET-13 and RET-14 are confirmed corpus gaps with `corpus_gap: true`. No document in the current corpus discusses contact mechanics, fretting, or micro-motion at blade root interfaces. |
| **Source Type Needed** | NASA or FAA technical report on turbine engine component failure modes covering fretting, wear, or blade attachment failures |
| **Phase 5D Metrics** | Not separately benchmarked in Phase 5D ablation (queries added in Phase 5C ground truth) |
| **Corpus Gap Confirmed** | Yes (RET-13, RET-14 both marked `corpus_gap: true`) |

### Gap 4: Criticality Formula Extraction (Mathematical Representation)

| Field | Value |
| :--- | :--- |
| **Gap** | Mathematical equations for mode criticality ($C_m$) and item criticality ($C_r$) are poorly extracted from PDF text |
| **Affected Benchmark Queries** | RET-25 (`MIL-STD-1629A Task 102 criticality analysis mode criticality number Cm calculation beta alpha lambda`), RET-26 (`item criticality number Cr summation failure mode criticality quantitative matrix`) |
| **Engineering Capability Affected** | Criticality retrieval underperforms because formula text is rendered as single-letter variables (`Cm = a * b * lambda * t`) that cosine and BM25 cannot match |
| **Current Corpus Limitation** | The content EXISTS in MIL-STD-1629A Task 102 but is extracted poorly by pypdf text extraction. This is a formula extraction problem, not a corpus gap. |
| **Source Type Needed** | Formula extraction enhancement (not new corpus) |
| **Phase 5D Metrics** | P@1: 0.0–33.3%, MRR: 0.1333–0.4444 |
| **Corpus Gap Confirmed** | No — this is a text extraction / indexing problem |

### Gap 5: Thermal Barrier Coating (TBC) Degradation

| Field | Value |
| :--- | :--- |
| **Gap** | TBC oxidation, spallation, sintering, thermal cycling degradation |
| **Affected Benchmark Queries** | RET-16 mentions "thermal barrier coating spallation" but is categorized under corrosion and partially served by existing corpus. A deeper physics-level description of TBC degradation mechanisms is absent. |
| **Engineering Capability Affected** | Partially degraded — CS-E and AC 33.75 mention "environmental degradation" generically, but lack TBC-specific spallation physics |
| **Current Corpus Limitation** | No dedicated TBC chapter in current standards |
| **Source Type Needed** | Would be addressed by a gas turbine engine failure modes report that includes coating degradation |
| **Corpus Gap Confirmed** | Partial (RET-16 is not marked `corpus_gap: true` but retrieval is weak) |

---

## 2. Source Requirements Table

| Gap | Required Technical Knowledge | Preferred Source Type | Minimum Evidence Needed |
| :--- | :--- | :--- | :--- |
| **Thermal Fatigue / TMF** | Turbine blade thermal gradients, cyclic stress-strain, crack initiation, TMF hysteresis | NASA/FAA technical report on engine failure modes or turbine blade durability | At least 2-3 pages defining TMF mechanisms, crack nucleation, thermal cycling effects |
| **Cooling System** | Film cooling, serpentine passages, blockage/degradation, heat transfer coefficients | NASA technical report on turbine cooling, gas turbine thermal management | At least 1-2 pages describing internal blade cooling architecture and failure modes |
| **Fretting Fatigue** | Blade root / dovetail contact mechanics, fretting fatigue, micro-motion, galling | NASA/FAA technical report covering blade-disk attachment failures | At least 1-2 pages on fretting wear at blade root interfaces |
| **Criticality Formulas** | Cm = β × α × λp × t, Cr = Σ Cm, variable definitions | Formula extraction enhancement on existing MIL-STD-1629A (not new corpus) | Structured formula records with variable definitions and provenance |
| **TBC Degradation** | Coating oxidation, spallation, sintering mechanisms | Would be addressed by a comprehensive gas turbine failure modes report | At least 1 page describing TBC degradation modes |

---

## 3. Gaps NOT Requiring New Corpus

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| Criticality formula retrieval (RET-25, RET-26) | Formula text parsed as single-letter variables | Formula extraction enhancement for existing MIL-STD-1629A content |
| Maintenance competing passages (RET-19, RET-20) | Ground-truth ambiguity / passage ranking jitter | Not a corpus gap — Phase 5D section chunking partially resolved |
| Single point failure (RET-27, RET-28) | Partially resolved in Phase 5D | Not a corpus gap — NASA-STD-8729.1A and FAA AC 25.1309 contain relevant content |
