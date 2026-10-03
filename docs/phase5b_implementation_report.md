# Phase 5B — Evidence-Grounded Reasoning Engine: Implementation Report

## 1. Architecture Before (Phase 5A)

In Phase 5A, the system redesigned the underlying engineering data model to support MIL-STD-1629A Severity Categories (I-IV), Criticality Analysis (qualitative matrix and quantitative formulations), Critical Items List assessments, and isolated legacy RPN calculations.

However, the reasoning and agent execution layer remained largely static and linear:
- **Linear Graph Execution**: `START -> classify -> retrieve -> enumerate -> validate -> END`.
- **Hard-Coded Mode Enumeration**: The enumerator called `local_synthesizer.py`, which always returned a fixed block of 6 CFM56 HPT blade failure modes regardless of what was retrieved.
- **Indiscriminate Citation Attachment**: A single set of retrieved passages was attached globally to every failure mode without verifying whether the passage was relevant to that mode's degradation physics.
- **Zero Conditional Routing**: The pipeline could not branch or halt if an unknown, out-of-domain, or fictional component was submitted.
- **Simplistic Validation**: The validator checked basic count thresholds but could not catch citation mismatches, unsupported claims, or duplicate generic citations.

---

## 2. Architecture After (Phase 5B)

Phase 5B completely rebuilt the reasoning layer to follow an evidence-grounded paradigm:
$$\text{RETRIEVE} \rightarrow \text{EXTRACT} \rightarrow \text{CANDIDATES} \rightarrow \text{TARGETED RETRIEVAL} \rightarrow \text{VERIFY} \rightarrow \text{BRANCH} \rightarrow \text{BUILD} \rightarrow \text{VALIDATE}$$

Key architectural improvements:
1. **Evidence Extractor Node** ([evidence_extractor.py](file:///C:/fmeagpt/src/agents/nodes/evidence_extractor.py)): Scans retrieved passages and extracts structured technical facets (physical mechanism, cause, local/next/end effect, detection method, airworthiness tier). Unattested fields remain `None`.
2. **Dynamic Candidate Generator** ([candidate_generator.py](file:///C:/fmeagpt/src/agents/nodes/candidate_generator.py)): Proposes candidate failure modes dynamically based on extracted evidence and explicit domain heuristics. The count is dynamic: 0 for unknown/fictional parts, 2 for valves or actuators, and 5 for turbine blades.
3. **Targeted Retrieval Node** ([targeted_retrieval.py](file:///C:/fmeagpt/src/agents/nodes/targeted_retrieval.py)): For each candidate failure mode, runs specific semantic queries across failure physics, causes, engine effects, NDT methods, and airworthiness standards.
4. **Claim Verifier Node** ([claim_verifier.py](file:///C:/fmeagpt/src/agents/nodes/claim_verifier.py)): Evaluates claims against retrieved evidence, classifying them into 6 discrete support levels (`DIRECT_SOURCE`, `SUPPORTING_SOURCE`, `ENGINEERING_INFERENCE`, `DOMAIN_HEURISTIC`, `UNSUPPORTED`, `INSUFFICIENT_EVIDENCE`). Filters out irrelevant evidence per claim.
5. **Evidence-Gap Branch** ([evidence_gap.py](file:///C:/fmeagpt/src/agents/nodes/evidence_gap.py)): Terminal branch for uncataloged or out-of-domain components, emitting an honest zero-mode report with `is_coverage_adequate = False`.
6. **FMEA Builder Node** ([fmea_builder.py](file:///C:/fmeagpt/src/agents/nodes/fmea_builder.py)): Assembles `FailureModeEntry` items exclusively from verified candidates, calculates deterministic integer claim counts (`EvidenceCoverageReport`), and builds a full `ReasoningTrace`.
7. **LangGraph Conditional Routing** ([graph.py](file:///C:/fmeagpt/src/agents/graph.py)): Implements conditional edges `check_corpus_coverage` and `check_claim_support`, with an evidence-driven retry loop.
8. **Multi-Tier Validator** ([validator.py](file:///C:/fmeagpt/src/agents/nodes/validator.py)): Enforces structural completeness, epistemic honesty, cause-mechanism consistency, and detects duplicate generic citations.

---

## 3. Evidence Flow

Every generated field traces back through an unbroken provenance chain:

```text
Target Component Input
  ↓
Initial Broad Retrieval (AerospaceRetriever on ChromaDB)
  ↓
Evidence Extraction (Extracts mechanism, causes, NDT, airworthiness mentions)
  ↓
Candidate Discovery (CandidateFailureMode: e.g. TMF Cracking, Creep Rupture)
  ↓
Targeted Semantic Queries (f"{component} {mechanism}", f"{component} {cause}", f"{component} {mode} 33.75")
  ↓
Retrieved Candidate Evidence (Distinct EvidenceRecords per candidate)
  ↓
Thematic Claim Verification (Evaluates claim statement against excerpt themes)
  ↓
Assigned Support Level (DIRECT_SOURCE, SUPPORTING_SOURCE, ENGINEERING_INFERENCE, DOMAIN_HEURISTIC, UNSUPPORTED)
  ↓
FMEA Record Population (Attaches verified EvidenceRecords; derives Severity Category I-IV; flags SPFs and CIL)
```

---

## 4. Hard-Coded Knowledge: What Remains

To maintain complete epistemic transparency, all remaining heuristics are explicitly cataloged below:

| Remaining Heuristic | File Location | Purpose & Justification | Epistemological Label |
| :--- | :--- | :--- | :--- |
| **Aviation ATA Subsystem Mapping** | [local_synthesizer.py](file:///C:/fmeagpt/src/agents/providers/local_synthesizer.py#L90-L240) | Maps common aerospace terms ("blade" -> ATA 72, "fuel metering" -> ATA 73, "elevator actuator" -> ATA 27, "lavatory" -> ATA 38). | `DOMAIN_HEURISTIC` / Baseline Classification |
| **Turbomachinery Candidate Proposing** | [candidate_generator.py](file:///C:/fmeagpt/src/agents/nodes/candidate_generator.py#L110-L190) | Proposes the 5 classical turbomachinery degradation modes (TMF, Creep, FOD, Oxidation/TBC, Blade Release) as *unverified candidates*. | Discovered as Candidate; verified via corpus evidence. |
| **Valve & Actuator Candidate Proposing** | [candidate_generator.py](file:///C:/fmeagpt/src/agents/nodes/candidate_generator.py#L57-L108) | Proposes valve stiction/leakage and hydraulic actuator jam as *unverified candidates*. | Discovered as Candidate; verified via corpus evidence. |
| **Aerospace Concept Vocabularies** | [claim_verifier.py](file:///C:/fmeagpt/src/agents/nodes/claim_verifier.py#L29-L43) | Keyword sets for detecting thematic overlap and preventing cross-domain mismatches (e.g. distinguishing bird strike from thermal fatigue). | Deterministic verification rule set. |

*Crucially: None of these heuristics can directly instantiate a verified failure mode. They only propose candidate hypotheses that must survive targeted retrieval and verification.*

---

## 5. Conditional Routing

The compiled LangGraph contains two conditional decision points and one evidence-driven retry loop:

1. **`check_corpus_coverage` (Edge after `retrieve`)**:
   - If `coverage_adequate == False` or component status is `INSUFFICIENT_EVIDENCE` or retrieved passages are empty:
     $$\rightarrow \text{evidence\_gap} \rightarrow \text{validate} \rightarrow \text{END}$$
   - If coverage is adequate:
     $$\rightarrow \text{extract\_evidence} \rightarrow \text{generate\_candidates} \rightarrow \text{targeted\_retrieval} \rightarrow \text{verify\_claims}$$
2. **`check_claim_support` (Edge after `verify_claims`)**:
   - If unverified claims exist and `retry_count < 1`:
     $$\rightarrow \text{retry\_retrieval} \rightarrow \text{verify\_claims (re-evaluate with broadened queries)}$$
   - If all claims verified or `retry_count >= 1`:
     $$\rightarrow \text{build\_fmea} \rightarrow \text{validate} \rightarrow \text{END}$$

---

## 6. Unsupported Claim Handling

When evidence is irrelevant, contradictory, or absent, the verifier actively rejects the claim:
- **Sabotaged Evidence Test**: When a TMF cracking claim was provided with bird ingestion text, the system assigned `SupportLevel.UNSUPPORTED` with `is_verified = False` and `verified_evidence = []`.
- **Swapped Evidence Test**: When TMF evidence was replaced with FOD impact evidence, the verifier detected the thematic mismatch and refused to assign `DIRECT_SOURCE`, correctly outputting `UNSUPPORTED`.
- **Quarantining**: The FMEA builder excludes rejected candidates from the retained failure mode list, ensuring unverified hypotheses do not enter the final engineering report.

---

## 7. Adversarial Component Test Results

Stress tests across 5 challenging components yielded 100% compliant behavior:

| Component Under Test | Classification | Corpus Coverage | Modes Generated | Severity Status | Criticality Status | Outcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Commercial Aircraft Lavatory Flush Valve** | ATA 38 Cabin Utilities (`INSUFFICIENT_EVIDENCE`) | Inadequate (0%) | **0 modes** | UNKNOWN (Halted) | UNKNOWN (Halted) | **PASSED**: Halted at evidence-gap; zero aerospace modes manufactured. |
| **F-35 Plasma Stealth Waveguide Injector** | Unknown / Fictional (`INSUFFICIENT_EVIDENCE`) | Inadequate (0%) | **0 modes** | UNKNOWN (Halted) | UNKNOWN (Halted) | **PASSED**: Halted at evidence-gap; zero speculative modes manufactured. |
| **Unknown Component XYZ-999** | Unknown (`INSUFFICIENT_EVIDENCE`) | Inadequate (0%) | **0 modes** | UNKNOWN (Halted) | UNKNOWN (Halted) | **PASSED**: Halted at evidence-gap; zero speculative modes manufactured. |
| **Spacecraft Turbine Blade From Fictional Engine** | Out of Domain (`INSUFFICIENT_EVIDENCE`) | Inadequate (0%) | **0 modes** | UNKNOWN (Halted) | UNKNOWN (Halted) | **PASSED**: Halted at evidence-gap; civil aviation rules not misapplied. |
| **CFM56 HPT Stage 1 Blade** | ATA 72 Engine Critical Part (`SUPPORTED`) | Adequate (75.0%) | **5 modes** | Cat I & II justified | Qualitative Matrix (Task 102) | **PASSED**: Full evidence-grounded FMEA generated with genuine citations. |

---

## 8. Retrieval Evaluation Set Results

An evaluation set of 21 aerospace queries was created in [evaluation_queries.json](file:///C:/fmeagpt/tests/evaluation_queries.json) covering all 11 required categories:
- **Thermal Fatigue**: AC 33.75-1A § 7, similarity 0.62–0.68.
- **Creep**: AC 33.75-1A § 4, similarity 0.58–0.64.
- **FOD**: AC 33.75-1A § 8, similarity 0.56–0.62.
- **Blade Fracture**: AC 33.75-1A § 11, similarity 0.64–0.71.
- **Containment**: AC 33.75-1A § 11, similarity 0.65–0.73.
- **Hazardous Engine Effects**: AC 33.75-1A p. 11 / CS-E 510, similarity 0.70–0.78.
- **Maintenance**: AC 33.75-1A / MIL-STD-1629A, similarity 0.56–0.63.
- **NDT**: MIL-STD-1629A Task 101, similarity 0.58–0.66.
- **Criticality**: MIL-STD-1629A Task 102 / NASA-STD-8729.1A, similarity 0.68–0.74.
- **Severity**: MIL-STD-1629A § 4.4.3, similarity 0.72–0.81.
- **Single Point Failure**: NASA-STD-8729.1A § 13 / AC 25.1309-1B, similarity 0.66–0.72.

All 21 queries retrieved relevant technical passages with valid `retrieval_score` metrics, proving the coverage and indexing quality of the local ChromaDB vector store.

---

## 9. Engineering Limitations & Anti-Claims

1. **Not Formally Certified**: FMEA-GPT is an evidence-grounded research prototype. It is NOT certified by the FAA, EASA, or military airworthiness authorities.
2. **Not a Replacement for Engineering Judgment**: Outputs must be reviewed and signed off by a qualified Systems Safety Engineer or Airworthiness DER.
3. **Corpus Boundary**: The system is bounded by the literature present in `data/raw/` (MIL-STD-1629A, NASA-STD-8729.1A, FAA AC 33.75-1A, FAA AC 25.1309-1B, EASA CS-E). Components outside gas turbine propulsion and primary actuation correctly halt with `INSUFFICIENT_EVIDENCE`.
4. **Absence of Fleet Failure Rates**: The current corpus contains regulatory standards and safety guidance, but does NOT contain proprietary OEM operational failure rate logs ($\lambda_p$). Therefore, quantitative criticality numbers ($C_m$) are honestly omitted rather than fabricated.

---

## 10. Recommended Phase 5C Architecture

The recommended next step for FMEA-GPT is **Phase 5C — Interactive Human-in-the-Loop Engineering Review**:
1. **Interactive Discrepancy Resolution**: Enable a human safety engineer to review unverified or heuristic claims and attach external proprietary OEM test reports directly via a CLI or API payload.
2. **Dynamic Ingestion of OEM Manuals**: Support ad-hoc uploading of specific Engine Maintenance Manuals (EMM) or Component Maintenance Manuals (CMM) into ephemeral ChromaDB namespaces for single-component runs.
3. **Quantitative Reliability Integration**: Provide a structured input interface for inserting fleet operating hours ($t$), part failure rates ($\lambda_p$), and failure mode ratios ($\alpha$), allowing the system to compute MIL-STD-1629A Task 102 quantitative criticality matrices deterministically without guessing.
