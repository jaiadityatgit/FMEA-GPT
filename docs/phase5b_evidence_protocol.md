# Phase 5B — Evidence Verification Protocol & Epistemic Specification

## 1. Core Principles

FMEA-GPT Phase 5B enforces strict epistemological boundaries across all generated failure modes, effects, causes, severity classifications, and maintenance actions.

The system adheres to three mandatory rules:
1. **No Evidence Manufacture**: A claim is never labeled as evidence-backed simply because it is physically plausible or part of the model's pre-trained weights.
2. **Claim-Specific Provenance**: A failure mode or claim must only retain citations that directly substantiate its specific topics. Universal citation attachment is forbidden.
3. **Discrete Support Tiers**: Confidence is represented as discrete, audit-ready support categories, not arbitrary uncalibrated percentages (e.g. "87% confidence").

---

## 2. The Six Epistemological Support Levels

Every `EngineeringClaim` and `EvidenceRecord` is assigned one of six mutually exclusive support levels:

| Support Level | Strict Definition | Qualification Criteria | Example |
| :--- | :--- | :--- | :--- |
| `DIRECT_SOURCE` | Source explicitly states the claim or key technical assertion verbatim or in near-verbatim conceptual form. | Retrieved passage contains both component/failure mode concepts and explicit consequence or criteria. | FAA AC 33.75-1A § 4.b explicitly defining uncontained rotor burst as a hazardous engine effect. |
| `SUPPORTING_SOURCE` | Source materially supports the physical degradation principle, regulatory standard, or test procedure. | Passage provides standard definitions (MIL-STD-1629A, CS-E) that directly underpin the claim logic. | MIL-STD-1629A § 4.4.3 defining Category II Critical severity thresholds. |
| `ENGINEERING_INFERENCE` | Claim is a deduction synthesized across multiple verified passages and established physical laws. | Requires at least one verified source passage plus a documented engineering rationale linking cause to effect. | Inferring blade root cyclic strain from temperature transients and rotational speed. |
| `DOMAIN_HEURISTIC` | Claim originates from baseline engineering design rules of thumb without direct textual corpus evidence. | Explicitly flagged with `verification_required = True`. Never presented as an official regulatory requirement. | Standard recommended borescope inspection interval (e.g. 500 cycles) derived from airline fleet experience. |
| `UNSUPPORTED` | The claim is contradicted by, unrelated to, or mismatched with the attached evidence. | Retained evidence does not match the thematic domain concepts of the claim. | Bird ingestion passage attached to a thermal fatigue cracking claim. |
| `INSUFFICIENT_EVIDENCE` | The corpus contains no relevant technical literature to evaluate or substantiate the claim. | Zero passages retrieved or passage similarity score falls below relevance threshold (< 0.50). | Fictional aerospace components or uncataloged commercial cabin utility parts. |

---

## 3. Claim Verification Algorithm

Verification is executed deterministically in [claim_verifier.py](file:///C:/fmeagpt/src/agents/nodes/claim_verifier.py) through thematic analysis:

### 3.1. Thematic Concept Vocabulary
The verification engine indexes key concept vocabularies:
- **Thermal Fatigue**: `{"thermal", "fatigue", "tmf", "cyclic", "gradient", "transient", "temperature", "cracking"}`
- **Creep**: `{"creep", "rupture", "elongation", "centrifugal", "sustained", "shroud", "radial"}`
- **FOD**: `{"foreign", "object", "fod", "bird", "ingestion", "impact", "debris", "notch", "stone"}`
- **Oxidation/Corrosion**: `{"oxidation", "corrosion", "sulfidation", "tbc", "coating", "spallation", "environmental"}`
- **Blade Release**: `{"uncontained", "liberation", "separation", "fracture", "burst", "containment", "debris"}`
- **Actuator Jam**: `{"actuator", "jam", "hydraulic", "pressure", "cylinder", "stiction", "flight control"}`
- **Valve Stiction**: `{"valve", "metering", "spool", "stiction", "particulate", "contamination", "seal"}`
- **Airworthiness**: `{"hazardous", "33.75", "25.1309", "cs-e", "catastrophic", "effect", "critical part"}`
- **NDT/Inspection**: `{"borescope", "eddy current", "fpi", "penetrant", "ultrasonic", "ndt", "inspection"}`

### 3.2. Evaluation Rules
1. **Empty Candidate Evidence**:
   - If claim is a known domain heuristic -> `DOMAIN_HEURISTIC`.
   - Else -> `INSUFFICIENT_EVIDENCE`.
2. **Thematic Intersection**:
   - Identify themes in `claim.statement`.
   - Identify themes in `evidence.excerpt`.
   - Detect **hard mismatches** (e.g. claim is `thermal_fatigue`, but excerpt is `fod`/`bird`): If hard mismatch occurs, passage is quarantined and excluded.
3. **Direct Phrase Checking**:
   - If excerpt contains verbatim standard phrases (`"hazardous engine effect"`, `"thermomechanical fatigue"`, `"creep rupture"`), mark record as `DIRECT_SOURCE`.
   - If excerpt contains broader conceptual backing, mark record as `SUPPORTING_SOURCE`.
4. **Outcome Assignment**:
   - If verified evidence records survive -> assign `DIRECT_SOURCE` or `SUPPORTING_SOURCE`.
   - If all candidate passages were rejected due to mismatch -> assign `UNSUPPORTED`.
   - If no candidate passages matched -> assign `INSUFFICIENT_EVIDENCE`.

---

## 4. Anti-Cheating & Provenance Enforcement

### 4.1. Anti-Sabotage Test (Irrelevant Evidence)
If a plausible engineering claim is paired with irrelevant evidence (e.g. bird strike passage attached to a TMF claim), the verifier is forbidden from confirming the claim based on pre-trained scientific plausibility:
```python
result = verify_claim_against_evidence(tmf_claim, bird_strike_evidence)
assert result.assigned_support_level == SupportLevel.UNSUPPORTED
assert not result.is_verified
```

### 4.2. Swapped Evidence Detection
If evidence is swapped between failure modes, the system rejects the swapped evidence and downgrades the claim.

### 4.3. Anti-Generic Citation Rule
The validator inspects citation fingerprints across all failure modes:
```python
citation_fingerprints = [tuple(sorted(f"{c.source_document}:{c.page_number}" for c in fm.citations)) for fm in failure_modes]
if len(set(citation_fingerprints)) == 1 and len(failure_modes) > 1:
    # Trigger ERROR: PROVENANCE_DUPLICATE_GENERIC_CITATIONS
```
This guarantees that failure modes must undergo distinct, targeted retrieval.

---

## 5. Deterministic Evidence Coverage Formulation

The reasoning engine computes an `EvidenceCoverageReport` based on **integer counts**, never uncalibrated probability percentages:

$$\text{Total Claims} = N_{\text{direct}} + N_{\text{supporting}} + N_{\text{inferred}} + N_{\text{heuristic}} + N_{\text{unsupported}} + N_{\text{insufficient}}$$

$$\text{Coverage Score} = \frac{N_{\text{direct}} + N_{\text{supporting}}}{\text{Total Claims}}$$

Example Report:
```text
Total claims: 20
Directly supported: 5
Supporting evidence: 10
Engineering inference: 5
Domain heuristic: 0
Unsupported: 0
Insufficient evidence: 0
Coverage score: 75.0%
Adequacy flag: TRUE
```
