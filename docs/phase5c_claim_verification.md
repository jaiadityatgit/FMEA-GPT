# FMEA-GPT Phase 5C — Claim Verification Report

**Document ID:** DOC-PHASE5C-VERIFY-001  
**Repository:** `C:\fmeagpt`  
**Evaluation Date:** October 2026  
**Status:** Architecture Specification & Benchmark Performance  

---

## 1. Executive Summary

Phase 5C transitions the FMEA-GPT claim verification subsystem from a single-stage keyword overlap heuristic into a **two-layer semantic entailment and invariant checking architecture**.

The hardened claim verifier operates locally and deterministically without external LLM dependencies, combining:
1. **Layer 1:** A symmetric, cross-domain thematic pre-filter that blocks incompatible physical regimes (e.g., TMF vs. FOD, high-temperature gas path vs. hydraulic actuation).
2. **Layer 2:** Dense semantic ONNX embedding cosine similarity (`all-MiniLM-L6-v2`) coupled with deterministic invariant checks for **scope overreach**, **unbacked quantitative intervals**, and **unsubstantiated causal assertions**.

### Benchmark Performance Highlights (40 Ground-Truth Pairs)
* **Exact Multi-Class Accuracy:** 82.5% (33 / 40)
* **Binary Decision Accuracy (Supported vs. Rejected):** 95.0% (38 / 40)
* **Binary Precision:** 95.2%
* **Binary Recall:** 95.2%
* **Binary F1 Score:** 95.2%
* **Adversarial Unsupported Precision:** **100.0%** (14 / 14 correctly rejected with zero false positives)
* **Adversarial Unsupported Recall:** **100.0%** (14 / 14)

---

## 2. Claim Verifier Architecture & Decision Flow

The verification subsystem is implemented in [src/agents/nodes/claim_verifier.py](file:///c:/fmeagpt/src/agents/nodes/claim_verifier.py). Its architecture follows a staged pipeline:

```text
Claim Statement + Candidate Evidence Excerpts
                       ↓
[ Layer 1: Symmetric Thematic Pre-Filter ]
  - Checks domain dictionary tags
  - Detects hard cross-domain clashes (TMF ↔ FOD, Hot Section ↔ Hydraulic)
  - If mismatch detected: IMMEDIATELY ASSIGN UNSUPPORTED
                       ↓
[ Layer 2: Semantic ONNX Embedding Similarity ]
  - Computes v_claim = E(claim), v_evid = E(excerpt) via local ONNX runtime
  - Calculates cosine similarity s = (v_claim · v_evid) / (||v_claim|| ||v_evid||)
                       ↓
[ Layer 2 Invariant Checks ]
  - Invariant A: Specific Part Number Scope Check
    (If claim cites P/N or exact model not present in evidence → Cannot be DIRECT_SOURCE)
  - Invariant B: Quantitative / Modal Overreach Check
    (If claim asserts mandatory intervals like "every 500 cycles" or "zero failure rate" without evidence → ASSIGN UNSUPPORTED)
  - Invariant C: Causal Mechanism Verification
    (If claim asserts deterministic causation "causes catastrophic liberation" without backing → Downgrade to INSUFFICIENT)
                       ↓
[ Conservative Classification Logic ]
  - DIRECT_SOURCE: High semantic match (s ≥ 0.65) OR exact proposition match (s ≥ 0.50) + Scope Invariants Satisfied
  - SUPPORTING_SOURCE: Moderate semantic match (s ≥ 0.45) OR (s ≥ 0.28 with thematic alignment)
  - INSUFFICIENT_EVIDENCE: Weak semantic match (s < 0.28) or vague background context
  - UNSUPPORTED: Adversarial contradiction, scope violation, or unbacked mandatory interval
```

---

## 3. Support-Level Decision Rules & Invariants

### Rule 1: Preference for Uncertainty (`INSUFFICIENT_EVIDENCE` over False Certainty)
The verifier is strictly conservative:
* When evidence is topically related but fails to prove the specific proposition, the verifier assigns `INSUFFICIENT_EVIDENCE` rather than upgrading to `DIRECT_SOURCE`.
* Reputable source authority (e.g., an official FAA Advisory Circular) does **NOT** automatically prove claim entailment. The text must substantiate the specific physical claim.

### Rule 2: Component Scope Invariant (General Principle vs. Component Overreach)
* **General Principle:** "Turbine blades can experience creep at elevated temperature."
* **Component-Specific Overreach:** "CFM56 HPT Stage 1 blade P/N 301-789-204-0 experiences creep."
* If evidence discusses general turbine creep without naming the CFM56 engine or part number, the claim cannot receive `DIRECT_SOURCE`. The verifier automatically caps the support level at `SUPPORTING_SOURCE` or flags it as an engineering inference.

### Rule 3: Quantitative and Modal Invariant
* Statements asserting mandatory operational rules or exact numerical values (e.g., *"A borescope inspection every 500 flight cycles is mandatory"*) require explicit textual support in the evidence.
* If general FAA guidance mentions that inspections are beneficial, but does not state the exact 500-cycle mandatory interval, the claim is classified as `UNSUPPORTED` due to quantitative/modal overreach.

---

## 4. Benchmark Dataset Composition

The benchmark dataset was authored in [tests/claim_verification_benchmark.json](file:///c:/fmeagpt/tests/claim_verification_benchmark.json) with 40 claim/evidence pairs spanning 9 engineering categories:

| Target Engineering Category | Supported (Direct/Supporting) | Unsupported (Adversarial) | Ambiguous / Insufficient | Total Pairs |
| :--- | :---: | :---: | :---: | :---: |
| **failure_mode** | 5 | 2 | 1 | 8 |
| **cause** | 4 | 2 | 1 | 7 |
| **end_effect** | 4 | 2 | 0 | 6 |
| **component-specific** | 2 | 2 | 1 | 5 |
| **maintenance** | 2 | 2 | 1 | 5 |
| **severity** | 2 | 1 | 0 | 3 |
| **criticality** | 1 | 1 | 1 | 3 |
| **airworthiness** | 1 | 1 | 0 | 2 |
| **quantitative** | 0 | 1 | 0 | 1 |
| **Total** | **21** | **14** | **5** | **40** |

---

## 5. Quantitative Verification Benchmark Results

Evaluation was executed using [tests/claim_verification_evaluation.py](file:///c:/fmeagpt/tests/claim_verification_evaluation.py):

### Multi-Class Performance Metrics

| Classification Label | Ground Truth Count | Predicted Count | Precision | Recall | F1 Score |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **DIRECT_SOURCE** | 12 | 16 | 68.8% | 91.7% | 78.6% |
| **SUPPORTING_SOURCE** | 9 | 5 | 80.0% | 44.4% | 57.1% |
| **INSUFFICIENT_EVIDENCE** | 5 | 5 | 80.0% | 80.0% | 80.0% |
| **UNSUPPORTED** | 14 | 14 | **100.0%** | **100.0%** | **100.0%** |
| **Overall Multi-Class Accuracy** | **40** | **40** | — | — | **82.5%** |

### Confusion Matrix

```text
Expected (Rows) \ Predicted (Cols)   | DIRECT_SOURCE | SUPPORTING_SOURCE | INSUFFICIENT_EVIDENCE | UNSUPPORTED
-------------------------------------+---------------+-------------------+-----------------------+------------
DIRECT_SOURCE                  (12)  |      11       |         0         |           1           |     0
SUPPORTING_SOURCE               (9)  |       5       |         4         |           0           |     0
INSUFFICIENT_EVIDENCE           (5)  |       0       |         1         |           4           |     0
UNSUPPORTED                    (14)  |       0       |         0         |           0           |    14
```

### Binary Decision Metrics (Retain as Supported vs. Reject/Flag)
* **Ground Truth Supported (`DIRECT` or `SUPPORTING`):** 21 pairs
* **Ground Truth Rejected (`UNSUPPORTED` or `INSUFFICIENT`):** 19 pairs
* **True Positives (Correctly Retained):** 20
* **False Positives (Unsupported Retained):** 1 (borderline `INSUFFICIENT` classified as `SUPPORTING`)
* **True Negatives (Correctly Rejected):** 18
* **False Negatives (Supported Incorrectly Rejected):** 1 (`DIRECT_SOURCE` classified as `INSUFFICIENT`)
* **Binary Decision Accuracy:** **95.0%**
* **Binary Precision:** **95.2%**
* **Binary Recall:** **95.2%**
* **Binary F1 Score:** **95.2%**

---

## 6. Failure Modes, False Positives, and False Negatives Analysis

### 1. Zero False Positives for Unsupported Claims
Out of 14 adversarial unsupported claims, exactly 14 were classified as `UNSUPPORTED` ($P=100\%$, $R=100\%$).
* *Example (TMF vs. Bird Strike):* Claim asserting thermomechanical fatigue paired with FAA bird ingestion passage: blocked by Layer 1 symmetric thematic mismatch.
* *Example (Mandatory Interval Overreach):* Claim asserting *"Borescope inspection every 500 cycles is mandatory"* with general FAA inspection guidance: blocked by Layer 2 Quantitative/Modal Invariant check.

### 2. Multi-Class Boundary Migration (`SUPPORTING_SOURCE` vs. `DIRECT_SOURCE`)
In 5 cases, claims intended as `SUPPORTING_SOURCE` scored high semantic similarity ($s \ge 0.65$) and were assigned `DIRECT_SOURCE`.
* *Example:* Claim *"Thermal gradients can contribute to cyclic thermal stresses"* paired with a passage detailing transient temperature gradients producing severe cyclic thermal stress.
* *Diagnosis:* The dense embedding model `all-MiniLM-L6-v2` perceives this passage as a direct proposition match. While technically supporting, the semantic overlap is strong enough that the verifier treats it as direct evidence. This does not harm binary engineering safety, as both labels represent genuine grounding.

### 3. Ambiguous Case / False Negative
* *Query ID `CV-AMB-01`:* Claim regarding secondary stress concentration in notched airfoils paired with general foreign object impact text.
* The verifier assigned `INSUFFICIENT_EVIDENCE` because the excerpt did not explicitly mention "stress concentration factor ($K_t$)". This illustrates the verifier's conservative bias.

---

## 7. Known Limitations of the Offline Verifier

1. **Lack of Symbolic Logic Prover:** The verifier relies on dense vector cosine similarity and pattern invariants. It does not perform formal first-order predicate logic resolution.
2. **Context-Window Chunking:** When an evidence passage is truncated mid-sentence by the chunker, the verifier evaluates only the available excerpt text. If qualifying clauses exist on the next page, the verifier cannot see them.
3. **Single Part Number Recognition:** Part number extraction currently uses alphanumeric regular expressions (e.g., `\d{3}-\d{3}-\d{3}-\d`). Non-standard proprietary OEM naming conventions may require expanded schema patterns.
