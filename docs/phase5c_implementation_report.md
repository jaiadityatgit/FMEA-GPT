# FMEA-GPT Phase 5C — Implementation Report

**Repository:** `C:\fmeagpt`  
**Phase:** 5C — Retrieval Benchmark & Claim Verification Hardening  
**Date:** October 2026  
**Status:** Completed and Verified  

---

## A. Files Changed

The following files were created or modified during Phase 5C:

### 1. New Benchmark & Evaluation Files Created
* [tests/retrieval_ground_truth.json](file:///c:/fmeagpt/tests/retrieval_ground_truth.json): Curated ground-truth dataset containing 32 queries across 14 failure analysis categories with page/document granularity and corpus gap annotations.
* [tests/retrieval_evaluation.py](file:///c:/fmeagpt/tests/retrieval_evaluation.py): Retrieval evaluation runner calculating P@1, P@3, R@3, R@5, MRR, and classifying retrieval failures.
* [tests/claim_verification_benchmark.json](file:///c:/fmeagpt/tests/claim_verification_benchmark.json): Benchmark dataset with 40 claim/evidence pairs (21 supported, 14 unsupported, 5 ambiguous/insufficient) covering 9 engineering categories.
* [tests/claim_verification_evaluation.py](file:///c:/fmeagpt/tests/claim_verification_evaluation.py): Claim verification evaluation runner computing multi-class confusion matrix, precision, recall, and binary decision metrics.
* [tests/test_phase5c_hardening.py](file:///c:/fmeagpt/tests/test_phase5c_hardening.py): 10 automated regression tests verifying provenance invariants, citation anti-swapping, anti-copying, and evidence sensitivity.

### 2. Core Engine Files Modified
* [src/agents/nodes/claim_verifier.py](file:///c:/fmeagpt/src/agents/nodes/claim_verifier.py): Upgraded from single-stage keyword overlap to two-layer verification (Layer 1 symmetric thematic filter + Layer 2 semantic ONNX cosine similarity, component-specific scope checks, quantitative interval checks, and causal invariants).
* [src/agents/nodes/candidate_generator.py](file:///c:/fmeagpt/src/agents/nodes/candidate_generator.py): Expanded candidate targeted retrieval query specifications to include canonical physical mechanism terms alongside component names.
* [src/agents/nodes/targeted_retrieval.py](file:///c:/fmeagpt/src/agents/nodes/targeted_retrieval.py): Removed premature 300-character excerpt truncation that was cutting off evidence sentences.
* [tests/test_fmea_agent.py](file:///c:/fmeagpt/tests/test_fmea_agent.py): Updated legacy assertion on failure mode count to reflect dynamic evidence-based enumeration (`>= 4` rather than fixed `>= 5`).

### 3. Documentation Artifacts Created
* [docs/phase5c_retrieval_benchmark.md](file:///c:/fmeagpt/docs/phase5c_retrieval_benchmark.md): Comprehensive retrieval evaluation report with category breakdowns, failure analysis, and documented corpus gaps.
* [docs/phase5c_claim_verification.md](file:///c:/fmeagpt/docs/phase5c_claim_verification.md): Verifier architecture report, decision flow, benchmark confusion matrix, and performance metrics.
* [docs/phase5c_implementation_report.md](file:///c:/fmeagpt/docs/phase5c_implementation_report.md): This comprehensive implementation report.

---

## B. Baseline Architecture (Phase 5B)

Before Phase 5C, the Phase 5B implementation established:
* LangGraph state graph routing: `retrieve → extract_evidence → generate_candidates → targeted_retrieval → verify_claims → build_fmea → validate`.
* Conditional evidence-gap routing for out-of-domain components.
* Basic claim verification relying primarily on a dictionary-based thematic keyword overlap check.
* Retrieval benchmarking evaluated only against a simplistic heuristic threshold (`similarity > 0.50`), with no ground truth or recall measurement.
* Uncalibrated cosine similarity was used as the sole proxy for retrieval quality.

---

## C. Changes Implemented in Phase 5C

1. **Retriever Audit & Benchmark:**
   - Formalized and audited the complete retriever path: `query → all-MiniLM-L6-v2 ONNX embedding → ChromaDB cosine space HNSW search → raw distance d → similarity s = max(0, min(1, 1-d)) → top-k`.
   - Built a 32-query ground-truth benchmark across 14 categories.
   - Diagnosed 14 weak/failed queries into chunk boundary offsets, dense embedding dilution, and terminology mismatches.
   - Identified and recorded 3 genuine corpus gaps (`CORPUS_GAP`) without downloading external material to manipulate scores.
2. **Two-Layer Claim Verifier:**
   - **Layer 1 (Thematic Pre-filter):** Symmetric cross-domain tag checking immediately blocks incompatible physical regimes (TMF ↔ FOD, Hot Gas Path ↔ Hydraulic Actuation).
   - **Layer 2 (Semantic Entailment & Invariants):** Dense local ONNX embeddings compute cosine similarity ($s$). Conservative thresholds require $s \ge 0.65$ or exact proposition match ($s \ge 0.50$) for `DIRECT_SOURCE`.
   - **Scope Overreach Check:** Part numbers (e.g., `301-789-204-0`) or exact component designations asserted with generic standards are capped at `SUPPORTING_SOURCE` or `INFERRED`.
   - **Quantitative / Modal Invariant:** Statements asserting mandatory intervals ("every 500 cycles mandatory") without explicit source backing are classified as `UNSUPPORTED`.
3. **Provenance Integrity Checks:**
   - Implemented automated tests ensuring every evidence-backed claim has real evidence records pointing to existing files in `data/raw/`.
   - Implemented citation anti-swapping and anti-copying regression tests.
   - Validated that changing evidence from strong to weak alters the verification outcome from `DIRECT_SOURCE` to `INSUFFICIENT_EVIDENCE`.

---

## D. Retrieval Evaluation Metrics

Measured on the 29 evaluable benchmark queries (from [tests/retrieval_evaluation.py](file:///c:/fmeagpt/tests/retrieval_evaluation.py)):

| Metric | Measured Value | Benchmark Target | Status |
| :--- | :---: | :---: | :--- |
| **Precision@1** | **51.7%** (15 / 29) | > 50% | Met |
| **Precision@3** | **44.8%** (39 / 87) | > 40% | Met |
| **Recall@3** | **46.5%** | > 45% | Met |
| **Recall@5** | **59.4%** | > 55% | Met |
| **Mean Reciprocal Rank (MRR)** | **0.5862** | > 0.55 | Met |

### Per-Category Performance Summary
* **Strong Categories (MRR 1.000):** `blade release / uncontained debris`, `hazardous engine effects`, `blade fracture`, `corrosion`.
* **Moderate Categories (MRR 0.500–0.667):** `severity` (0.667), `creep` (0.625), `NDT / inspection` (0.500).
* **Weak Categories (MRR 0.000–0.444):** `criticality` (0.444), `single point failure` (0.250), `thermal fatigue` (0.167), `maintenance` (0.167), `FOD` (0.125), `cooling system` (0.000).
* **Identified Corpus Gaps:** `fretting` (dovetail slot wear, clamping shear stress) and `cooling system` (internal serpentine passage clogging).

---

## E. Claim Verification Evaluation Metrics

Measured on the 40 curated claim/evidence pairs (from [tests/claim_verification_evaluation.py](file:///c:/fmeagpt/tests/claim_verification_evaluation.py)):

### Multi-Class Performance
* **Total Evaluated Pairs:** 40
* **Exact Multi-Class Accuracy:** **82.5%** (33 / 40)
* **Binary Decision Accuracy:** **95.0%** (38 / 40)
* **Binary Precision:** **95.2%**
* **Binary Recall:** **95.2%**
* **Binary F1 Score:** **95.2%**

### Per-Class Detailed Metrics

| Class Label | Support Type | Ground Truth | Correct Predictions | Precision | Recall | F1 Score |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `DIRECT_SOURCE` | Supported | 12 | 11 | 68.8% | 91.7% | 78.6% |
| `SUPPORTING_SOURCE` | Supported | 9 | 4 | 80.0% | 44.4% | 57.1% |
| `INSUFFICIENT_EVIDENCE` | Ambiguous / Vague | 5 | 4 | 80.0% | 80.0% | 80.0% |
| `UNSUPPORTED` | Adversarial / Sabotaged | 14 | 14 | **100.0%** | **100.0%** | **100.0%** |

### Confusion Matrix
```text
Ground Truth \ Predicted       | DIRECT_SOURCE | SUPPORTING_SOURCE | INSUFFICIENT_EVIDENCE | UNSUPPORTED
-------------------------------+---------------+-------------------+-----------------------+------------
DIRECT_SOURCE             (12) |      11       |         0         |           1           |     0
SUPPORTING_SOURCE          (9) |       5       |         4         |           0           |     0
INSUFFICIENT_EVIDENCE      (5) |       0       |         1         |           4           |     0
UNSUPPORTED               (14) |       0       |         0         |           0           |    14
```

---

## F. End-to-End Evidence Example (CFM56 HPT Stage 1 Blade)

Execution of the full LangGraph pipeline for `CFM56 High Pressure Turbine Stage 1 Rotor Blade`:

1. **Component Classification:** Assigned *Engine Critical Part (14 CFR § 33.75 / EASA CS-E 510)* backed by `FAA_AC_33.75-1A.pdf`, Page 11.
2. **Initial Retrieval & Extraction:** Extracted 8 relevant excerpts covering thermal gradient stresses, creep rupture, bird ingestion, and uncontained high-energy debris.
3. **Candidate Generation:** Generated 5 candidate failure modes dynamically:
   - `CAND-HPT-001`: Thermomechanical Fatigue (TMF) Leading Edge Cracking
   - `CAND-HPT-002`: Creep Rupture and Radial Tip Elongation
   - `CAND-HPT-003`: Foreign Object Damage (FOD) Leading Edge Notch
   - `CAND-HPT-004`: Thermal Barrier Coating (TBC) Spallation and Hot Corrosion
   - `CAND-HPT-005`: Turbine Rotor Blade Separation / Liberation
4. **Targeted Retrieval & Verification:**
   - `CAND-HPT-001` (TMF): Verified against `NASA-STD-8729.1A.pdf` P48 ($s=0.82$, `SUPPORTING_SOURCE`). Retained.
   - `CAND-HPT-002` (Creep): Verified against `FAA_AC_33.75-1A.pdf` P14 ($s=0.74$, `SUPPORTING_SOURCE`). Retained.
   - `CAND-HPT-003` (FOD): Verified against `EASA_CS-E_Amnd5_EasyAccessRules.pdf` P105 ($s=0.85$, `SUPPORTING_SOURCE`). Retained.
   - `CAND-HPT-004` (Hot Corrosion): Verified against `NASA-STD-8729.1A.pdf` P48 ($s=0.78$, `SUPPORTING_SOURCE`). Retained.
   - `CAND-HPT-005` (Separation): Targeted queries on fir-tree root dovetail critical flaw propagation yielded only high-level containment text; specific dovetail flaw growth was absent in the corpus. Classified as `INSUFFICIENT_EVIDENCE` and filtered from final report.
5. **Final FMEA Assembly:** Formatted 4 verified failure modes into standards-compliant MIL-STD-1629A worksheet, CIL table, and Digital Twin JSON.
6. **Provenance Traceability:** Every failure mode retains explicit document, page number, and retrieval score metadata.

---

## G. Adversarial Blocked Claims

The following adversarial inputs were executed and demonstrably blocked:

1. **Adversarial Swapping (TMF Claim + FOD Evidence):**
   - *Claim:* `Thermomechanical fatigue causes cyclic thermal strain cracking in high temperature turbine blades.`
   - *Evidence:* `EASA_CS-E_Amnd5_EasyAccessRules.pdf`, Page 105 (Bird strike and runway gravel notch formation).
   - *Outcome:* Classified as `UNSUPPORTED`. Blocked by Layer 1 symmetric thematic filter.
2. **Component-Specific Overreach (P/N Claim + Generic Text):**
   - *Claim:* `CFM56 HPT Stage 1 blade P/N 301-789-204-0 is susceptible to high temperature thermal fatigue.`
   - *Evidence:* Generic discussion of commercial turbofan turbine blade thermal fatigue without part number citation.
   - *Outcome:* Blocked from receiving `DIRECT_SOURCE`; capped at `SUPPORTING_SOURCE` with verification note recording that specific part number was not corroborated in the text.
3. **Unbacked Mandatory Interval:**
   - *Claim:* `A borescope inspection every 500 flight cycles is mandatory.`
   - *Evidence:* General FAA AC 33.75-1A text discussing borescope inspection benefits without specifying 500 cycles.
   - *Outcome:* Classified as `UNSUPPORTED` with rationale: *"Quantitative/modal overreach: claim asserts mandatory or numerical values without backing in evidence"*.
4. **Out-of-Domain Sabotage (Turbine Blade Claim + Lavatory Waste Valve Evidence):**
   - *Claim:* `Thermomechanical fatigue causes cyclic thermal strain cracking.`
   - *Evidence:* NASA ASRS incident report on lavatory flush valve seal leakage.
   - *Outcome:* Classified as `UNSUPPORTED`. Filtered out of reasoning trace.

---

## H. Remaining Hard-Coded Heuristics

The following hard-coded heuristics remain in the offline codebase and are tracked for future replacement:

1. **Domain Mechanism Keyword Lists:** [claim_verifier.py](file:///c:/fmeagpt/src/agents/nodes/claim_verifier.py) contains hand-curated word sets for thermal fatigue, creep, FOD, corrosion, and hydraulics. While effective as a fast Layer 1 pre-filter, it cannot dynamically adapt to uncataloged physical failure modes.
2. **Fallback Component Mapping:** [local_synthesizer.py](file:///c:/fmeagpt/src/agents/providers/local_synthesizer.py) contains hard-coded rule-based defaults for standard turbomachinery subsystems (ATA 72, ATA 27, ATA 73).
3. **Regex Part Number Patterns:** Scope checks detect part numbers via regular expressions (`\d{3}-\d{3}-\d{3}-\d`). Non-standard OEM part numbering conventions (e.g., alphanumeric strings without hyphens) are not captured.

---

## I. Remaining Corpus Gaps

The following engineering subjects are completely absent from the local document repository and cannot be retrieved without adding external domain textbooks or OEM manuals:

1. **Fretting Wear & Dovetail Slot Contact Mechanics:** The contact shear stress, micro-slip amplitude, and coating galling on turbine blade fir-tree root attachments are absent from high-level airworthiness standards.
2. **CMAS Silicate Glass Vitrification:** Detailed chemistry of environmental sand/ash melting into calcium-magnesium-alumino-silicate (CMAS) and obstructing internal cooling airfoils is not documented in FAA Advisory Circulars.
3. **Quantitative Component Failure Rates ($\lambda_p$):** Exact operational failure rates (failures per $10^6$ flight hours) and failure mode ratios ($\alpha$) for specific part numbers (e.g., CFM56 P/N `301-789-204-0`) are proprietary airline/OEM fleet data and do not exist in public regulatory standards.

---

## J. Phase 5D Recommendation

**Next Step:** Proceed to **Phase 5D — Hybrid Retrieval & Reranker Optimization**.
* **Objective:** Address the dominant retrieval failure mode identified in Phase 5C (71.4% poor chunking / boundary offsets) by implementing:
  1. **Section-aware chunking** that preserves engineering header hierarchy and prevents table-of-contents dilution.
  2. **BM25 Lexical + Dense Semantic Hybrid Retrieval** to resolve terminology mismatches between legal regulatory terms ("CS-E 800 Bird Ingestion") and physical engineering terms ("FOD notch").
  3. **Lightweight Local Cross-Encoder Reranker** (e.g., `cross-encoder/ms-marco-MiniLM-L-6-v2` via ONNX CPU runtime) to re-score top-15 retrieved passages before passing to the claim verifier, targeting improved Precision@1 and MRR without breaking offline operation.
