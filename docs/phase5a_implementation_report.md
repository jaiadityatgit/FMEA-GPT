# FMEA-GPT Phase 5A: Engineering Data Model & Criticality Methodology Redesign Implementation Report

**Document ID:** FMEA-GPT-REPORT-PHASE5A  
**Date:** October 2, 2026  
**Audited Target:** `C:\fmeagpt`  
**Status:** Completed & Validated  
**Standard Baselines:** MIL-STD-1629A (Task 101/102), NASA-STD-8729.1A § 13, FAA AC 33.75-1A, FAA AC 25.1309-1B, EASA CS-E 510  

---

## A. Previous Architecture

Prior to Phase 5A, the data models in `src/agents/state.py` suffered from severe architectural, epistemic, and methodological conflations:

1. **Automotive S/O/D/RPN Coupling:** The core failure mode schema was built around four integer fields: `severity` (1–10), `occurrence` (1–10), `detection` (1–10), and `rpn = severity * occurrence * detection` (1–1000). This automotive construct (SAE J1739 / AIAG-VDA) was presented to users with "MIL-STD-1629A FMEA Worksheet" compliance headers.
2. **Conflated Failure Mode & Physical Mechanism:** Observable failure effects were combined into single verbose phrases (e.g., *"Thermal Mechanical Fatigue (TMF) Cracking at Airfoil Leading Edge and Cooling Holes"*), obscuring whether the engineering statement addressed the observable structural symptom or the metallographic degradation mechanism.
3. **Indiscriminate Citation Attachment:** The generator sliced `retrieved_passages[:4]` from general RAG queries and copied the exact same 4 citations into every single failure mode. A passage regarding fan blade bird ingestion mass (EASA CS-E p. 192) was attached equally to TMF, Creep, Blockage, Dovetail Fretting, FOD, and Hot Corrosion.
4. **Arbitrary Critical Items List Logic:** In `cil_exporter.py`, modes were flagged as critical if `fm.single_point_failure or fm.severity >= 9 or fm.rpn >= 100`. The threshold $\text{RPN} \ge 100$ was an arbitrary heuristic with zero foundation in MIL-STD-1629A or NASA-STD-8729.1A.
5. **Epistemic Inability to Represent Uncertainty:** When given an uncataloged or out-of-domain part (e.g., *"Commercial Aircraft Lavatory Flush Valve"*), the keyword `"valve"` caused the system to classify it as a `Critical Flight Control Component (14 CFR § 25.1309)` with attached FAA AC 25.1309-1B citations. The schema had no way to express `UNKNOWN`, `INSUFFICIENT_EVIDENCE`, or unverified assumptions.
6. **Stripping of Citations in Binary Exports:** Binary Excel (`.xlsx`) and PDF (`.pdf`) deliverables completely dropped all citations, source files, and page numbers.

---

## B. Problems Removed in Phase 5A

| Problem in Phase 4 Baseline | Root Cause in Code | Resolution in Phase 5A |
| :--- | :--- | :--- |
| **S/O/D/RPN Falsely Claimed as MIL-STD-1629A** | Integers 1–10 multiplied into RPN in `state.py:46-49` | Severity decoupled into `SeverityClassification` (Categories I–IV); Criticality decoupled into `CriticalityAnalysis` (Qualitative Matrix or $C_m = \beta \alpha \lambda_p t$). RPN quarantined in `LegacyRPN`. |
| **Indiscriminate Citation Copying** | Slicing `retrieved_passages[:4]` in `local_synthesizer.py:123` | Granular `EvidenceRecord` and `EngineeringClaim` models implemented. Support levels explicitly tagged (`DIRECT_SOURCE`, `SUPPORTING_SOURCE`, `DOMAIN_HEURISTIC`, `UNSUPPORTED`). |
| **Arbitrary CIL Threshold ($\text{RPN} \ge 100$)** | Arbitrary filter in `cil_exporter.py:10` | Filter replaced with MIL-STD-1629A § 4.5.2.1 / NASA-STD-8729.1A § 13 criteria: Category I, Category II, or Single Failure Point. |
| **Conflation of Mode & Mechanism** | Single text field in `FailureModeEntry.failure_mode` | Decoupled into `failure_mode` (observable symptom) and `physical_mechanism` (physics/metallurgy process). |
| **Lavatory Valve Misclassification** | Keyword substring match in `_classify_component` | Naive substring matching removed for utility parts. Out-of-domain components assigned `AnalysisStatus.INSUFFICIENT_EVIDENCE` and `SeverityCategory.UNKNOWN`. |
| **Stripping of Citations in Excel / PDF** | Omission of citation tables in `exporters_binary.py` | Added dedicated `"Evidence & Citations"` worksheet in Excel and `"Airworthiness Evidence & Regulatory Provenance Appendix"` in PDF. |

---

## C. New Architecture: Redesigned Engineering Schema

The revised schema in `src/agents/state.py` establishes a clean, 5-layer engineering model:

```
[Layer 1: Empirical / Regulatory Evidence]
   EvidenceRecord (evidence_id, source_document, document_title, publisher, page_number, section, excerpt, retrieval_score)
                     │
                     ▼
[Layer 2: Epistemic Claim & Provenance Layer]
   EngineeringClaim (claim_id, statement, claim_type, support_level, evidence[], assumptions[], verification_notes)
   EngineeringAssumption (assumption_id, statement, engineering_rationale, risk_impact, verification_required)
                     │
                     ▼
[Layer 3: Physical Degradation & Causal Chain]
   ComponentInfo ──► physical_mechanism ──► failure_mode ──► local_effect ──► next_higher_effect ──► end_effect
                     │
                     ▼
[Layer 4: Rigorous Airworthiness Scoring]
   SeverityClassification (category: Category I–IV / UNKNOWN, definition, justification, regulatory_hazard_tier)
   CriticalityAnalysis (methodology: Qualitative Matrix [Levels A–E] vs Quantitative [Cm = beta * alpha * lambda_p * t])
   LegacyRPN (severity_score, occurrence_score, detection_score, rpn_value, methodology="legacy_automotive_unverified")
                     │
                     ▼
[Layer 5: Detection, Controls & CIL Determination]
   DetectionAndControls (primary_detection_means, detection_category, method_description, recommended_action, interval)
   CILAssessment (is_critical_item, single_failure_point, inclusion_basis, retention_rationale)
```

### Complete Class Inventory in `src/agents/state.py`

* `SupportLevel(str, Enum)`: `DIRECT_SOURCE`, `SUPPORTING_SOURCE`, `ENGINEERING_INFERENCE`, `DOMAIN_HEURISTIC`, `UNSUPPORTED`, `INSUFFICIENT_EVIDENCE`.
* `AnalysisStatus(str, Enum)`: `SUPPORTED`, `PARTIALLY_SUPPORTED`, `INFERRED`, `INSUFFICIENT_EVIDENCE`.
* `SeverityCategory(str, Enum)`: `CATEGORY_I`, `CATEGORY_II`, `CATEGORY_III`, `CATEGORY_IV`, `UNKNOWN`.
* `ProbabilityLevel(str, Enum)`: `LEVEL_A` ($>0.20$), `LEVEL_B` ($0.10-0.20$), `LEVEL_C` ($0.01-0.10$), `LEVEL_D` ($0.001-0.01$), `LEVEL_E` ($<0.001$), `UNKNOWN`.
* `CriticalityMethodology(str, Enum)`: `QUALITATIVE_MATRIX`, `QUANTITATIVE_CALCULATION`, `UNKNOWN`.
* `DetectionCategory(str, Enum)`: `REAL_TIME_COCKPIT`, `SCHEDULED_LINE_MAINTENANCE`, `SHOP_DEPOT_OVERHAUL`, `PRE_FLIGHT_WALKAROUND`, `UNDETECTABLE`.
* `EvidenceRecord(BaseModel)`: Tracks document, page, section, verbatim excerpt, and query score.
* `EngineeringAssumption(BaseModel)`: Formal assumption tracking with rationale, risk impact, and verification flag.
* `EngineeringClaim(BaseModel)`: Claims tracking their own supporting evidence records and assumptions.
* `SeverityClassification(BaseModel)`: Standard-grounded categorical severity with verbatim definitions and justification claims.
* `CriticalityAnalysis(BaseModel)`: Decoupled criticality analysis with full qualitative matrix and quantitative formula parameters.
* `DetectionAndControls(BaseModel)`: Diagnostic and maintenance observability model per MIL-STD-1629A § 5.7.
* `CILAssessment(BaseModel)`: NASA/DoD Critical Items List and Single Failure Point assessment with retention rationales.
* `LegacyRPN(BaseModel)`: Quarantined automotive RPN with explicit disclaimers.
* `ComponentInfo(BaseModel)`: Hardware tree node with analysis scope, classification basis claim, and confidence tier.
* `FailureModeEntry(BaseModel)`: Complete FMEA record binding physical mechanism, causal claims, severity, criticality, and CIL.
* `ValidationReport(BaseModel)`: Structural and airworthiness self-review tracking Cat I/II counts and unverified claims.
* `FMEAReport(BaseModel)`: Comprehensive output package.
* `FMEAState(TypedDict)`: State container for LangGraph reasoning workflow.

---

## D. Standards Traceability Summary

All fields in the revised models were traced directly to the five local standards in `data/raw/`:

1. **MIL-STD-1629A:**
   * **Task 101 § 4.3 (Pages 18–19):** Item Identification, Function, Failure Mode, and Probable Causes.
   * **Task 101 § 4.4.3 (Pages 15–16):** Categories I (Catastrophic), II (Critical), III (Marginal), IV (Minor).
   * **Task 101 § 5.6 (Page 23):** Local, Next Higher Level, and End Effects.
   * **Task 101 § 5.7 (Pages 23–24):** Failure Detection Methods.
   * **Task 101 § 4.5.2.1 (Pages 16–17):** Critical Items List (All Category I and II modes).
   * **Task 102 § 3.1 (Pages 29–30):** Qualitative Failure Probability Levels A, B, C, D, E.
   * **Task 102 § 3.2 (Pages 30–33):** Quantitative Criticality Number $C_m = \beta \cdot \alpha \cdot \lambda_p \cdot t$.
   * **General Requirements § 3.1.19 & § 3.1.21 (Page 11):** Single Failure Point (SFP) and Undetectable Failure.
2. **FAA AC 33.75-1A & EASA CS-E 510:**
   * **§ 4 & § 6 (Pages 4, 10–14):** Engine Critical Part designation; Hazardous Engine Effects ($p < 10^{-7}$) vs. Major Engine Effects ($p < 10^{-5}$) vs. Minor Engine Effects.
3. **NASA-STD-8729.1A:**
   * **§ 12 & § 13 (Pages 13, 16):** Single Point Failure definitions, CIL retention rationales, and damage-tolerant verification.

---

## E. Files Changed

| File Path | Component / Layer | Nature of Change |
| :--- | :--- | :--- |
| `src/agents/state.py` | Core Data Model | Replaced legacy S/O/D/RPN schemas with full Phase 5A epistemic models (`SupportLevel`, `EvidenceRecord`, `EngineeringClaim`, `SeverityClassification`, `CriticalityAnalysis`, `CILAssessment`, `LegacyRPN`). |
| `src/agents/providers/local_synthesizer.py` | Reasoning Provider | Refactored to populate rich models; hard-coded knowledge explicitly marked as `SupportLevel.DOMAIN_HEURISTIC`; lavatory valve keyword trap removed; CIL logic realigned with Cat I/II/SFP. |
| `src/agents/exporters/cil_exporter.py` | Exporter | Removed arbitrary `if rpn >= 100` condition; CIL inclusion now determined strictly by `CILAssessment` (Category I, Category II, or SFP). |
| `src/agents/exporters/fmea_table.py` | Exporter | Added Physical Mechanism, Task 102 Criticality column, epistemic support level tags, and explicit legacy RPN disclaimer. |
| `src/server/exporters_binary.py` | Binary Exporters | Added dedicated `"Evidence & Citations"` worksheet in Excel and `"Airworthiness Evidence & Regulatory Provenance Appendix"` in PDF export. |
| `tests/test_phase5a_schema.py` | Test Suite | New test suite verifying all 10 required schema capabilities (unknown severity, unknown criticality, claim-specific evidence, RPN isolation, etc.). |

---

## F. Test Suite Results

```text
Old tests passing:  24 / 24
New tests added:    10
Total tests:        34
Tests Passed:       34 / 34 (100%)
Tests Failed:        0
Execution Time:     12.780 seconds
```

### Breakdown by Test Module:
* `tests/test_rag.py`: 9 tests (Chunking, metadata, citation format, ChromaDB persistence) $\rightarrow$ **ALL PASS**
* `tests/test_fmea_agent.py`: 7 tests (Graph execution, classification, exporters, CIL format) $\rightarrow$ **ALL PASS**
* `tests/test_server.py`: 8 tests (FastAPI endpoints, sample, generate, Excel, PDF, Digital Twin) $\rightarrow$ **ALL PASS**
* `tests/test_phase5a_schema.py`: 10 tests (Unknown severity, unknown criticality, evidence claims, unsupported claims, inferred claims, assumptions, multiple evidence records, claim-level citations, severity/criticality separation, legacy RPN isolation) $\rightarrow$ **ALL PASS**

---

## G. Remaining Limitations

While the data models, state representations, exporters, and validation schemas are now rigorously grounded, the following limitations remain in the codebase:

1. **Reasoning Engine Still Relies on Heuristics in Offline Mode:** In `LocalAerospaceSynthesizer`, the CFM56 failure modes are now properly tagged as `SupportLevel.DOMAIN_HEURISTIC`, but they remain pre-written templates. Dynamic RAG-based failure mode discovery has not yet been built.
2. **LangGraph Pipeline Remains Sequential:** `src/agents/graph.py` still runs a linear 4-node pipeline. It does not yet include dynamic routing, self-correction loops, or an automated "insufficient evidence" branch.
3. **Corpus Lacks Component Maintenance Manuals:** The ingested vector database contains high-level certification regulations (CS-E, AC 33.75, AC 25.1309) but lacks specific CFM56 Engine Maintenance Manuals (EMM Chapter 72) or Airworthiness Directives (ADs).

---

## H. Recommended Phase 5B: Reasoning Loop & Dynamic Evidence Extraction

**Do NOT implement Phase 5B yet.** When authorized, Phase 5B should address:

1. **Dynamic LLM / RAG Failure Mode Extraction:** Replace static template selection with an extraction prompt that parses retrieved engine maintenance texts and instantiates `FailureModeEntry` objects directly from evidence passages.
2. **True Claim-Level RAG Routing:** Implement per-field semantic search (e.g., dedicated queries for physical root causes, separate queries for inspection limits) rather than copying 4 general queries.
3. **LangGraph Branching with Early Exit on Insufficient Evidence:** Add conditional edges: if component corpus coverage score $< \text{threshold}$, branch immediately to an `unsupported_component_node` that generates a formal gap report rather than proceeding to synthesis.
4. **Automated Cross-Encoder Citation Verification:** Implement a lightweight verification pass to verify that cited passages actually contain the technical concepts asserted in the claim before attaching them.
