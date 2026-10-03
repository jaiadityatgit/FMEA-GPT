# FMEA-GPT Phase 5A: Engineering Data Model & Criticality Methodology Redesign Specification

**Document ID:** FMEA-GPT-SPEC-PHASE5A  
**Date:** October 2, 2026  
**Status:** Approved for Implementation  
**Standard Baselines:** MIL-STD-1629A (Task 101/102), NASA-STD-8729.1A, FAA AC 33.75-1A, FAA AC 25.1309-1B, EASA CS-E 510  

---

## 1. Architectural Philosophy: Separating Evidence, Inference, and Scoring

The fundamental defect identified in Phase 4 was **epistemic conflation**:
* Pre-written python string literals were presented as RAG discoveries.
* Unrelated RAG chunks were attached indiscriminately as citations.
* Automotive Risk Priority Numbers ($RPN = S \times O \times D$, 1–1000 scale) were passed off as "MIL-STD-1629A compliance".
* The system was incapable of representing uncertainty or stating that evidence was missing.

Phase 5A establishes a strict separation of concerns across five core layers:

```
[Layer 1: Empirical / Regulatory Evidence]
   ChromaDB Chunks, Document Passages, Standards Clauses (Document, Page, Section, Excerpt)
                     │
                     ▼
[Layer 2: Epistemic Claim & Provenance Layer]
   Claim Type, Support Level (Direct / Inferred / Heuristic / Unsupported), Linked Evidence, Assumptions
                     │
                     ▼
[Layer 3: Physical Degradation & Causal Chain]
   Component Function ──► Physical Mechanism ──► Failure Mode ──► Local Effect ──► Next Effect ──► End Hazard
                     │
                     ▼
[Layer 4: Rigorous Airworthiness Scoring]
   Severity Classification (Cat I–IV / Unknown) ──► Criticality Analysis (Qualitative Matrix / Quantitative Cm)
                     │
                     ▼
[Layer 5: Action, Controls & Critical Item Determination]
   Detection / Observability Means ──► Action / Limits ──► CIL Retention Rationale (NASA / DoD criteria)
```

---

## 2. Core Epistemic Foundations: Support Levels & Evidence Records

Every engineering claim in the new architecture must declare its **support level**:

```python
class SupportLevel(str, Enum):
    DIRECT_SOURCE = "direct_source"          # Verifiable quote/fact directly in cited standard/document
    SUPPORTING_SOURCE = "supporting_source"  # Cited document provides strong context/principles
    ENGINEERING_INFERENCE = "inference"      # Technical deduction from engineering physics or operational rules
    DOMAIN_HEURISTIC = "domain_heuristic"    # Expert rules-of-thumb, baseline templates, or unverified presets
    UNSUPPORTED = "unsupported"              # Claim made with zero documentary backing
    INSUFFICIENT_EVIDENCE = "insufficient_evidence" # Explicit absence of data in corpus
```

### 2.1 The `EvidenceRecord` Model
Replaces the flat, uncalibrated `Citation` model.

```text
EvidenceRecord:
  ├── evidence_id: str                      # Unique ID, e.g. "EVID-FAA-33.75-P11-01"
  ├── source_document: str                  # e.g. "FAA_AC_33.75-1A.pdf"
  ├── document_title: str                   # e.g. "Guidance Material for 14 CFR 33.75, Safety Analysis"
  ├── publisher: str                        # "FAA", "EASA", "DoD", "NASA"
  ├── page_number: int                      # Exact 1-indexed PDF page
  ├── section: Optional[str]                # e.g. "§ 7.b Shedding of Blades"
  ├── excerpt: str                          # Verbatim quoted passage text
  ├── retrieval_query: Optional[str]        # The query that retrieved this chunk
  ├── retrieval_score: Optional[float]      # Raw vector distance / similarity (uncalibrated)
  ├── evidence_type: str                    # "regulatory_standard", "service_bulletin", "accident_report"
  └── support_level: SupportLevel           # direct_source vs supporting_source
```

### 2.2 The `EngineeringAssumption` Model
Engineering analyses necessarily make assumptions. Rather than embedding assumptions invisibly in text, they must be explicit:

```text
EngineeringAssumption:
  ├── assumption_id: str                    # e.g. "ASM-001"
  ├── statement: str                        # What is assumed (e.g. "Turbine casing meets containment rating")
  ├── engineering_rationale: str            # Why this assumption is technically justified
  ├── risk_impact: str                      # Consequence if assumption is violated
  └── verification_required: bool           # Whether physical test or cert review is required
```

### 2.3 The `EngineeringClaim` Model
A reusable claim wrapper ensuring every substantive statement tracks its own provenance:

```text
EngineeringClaim:
  ├── claim_id: str                         # e.g. "CLM-FM001-CAUSE"
  ├── statement: str                        # The claim text
  ├── claim_type: str                       # "cause", "local_effect", "end_effect", "action", etc.
  ├── support_level: SupportLevel           # Direct, inferred, heuristic, unsupported
  ├── evidence: List[EvidenceRecord]        # Specific evidence items supporting THIS claim
  ├── assumptions: List[EngineeringAssumption] # Assumptions underpinning this claim
  └── verification_notes: Optional[str]     # Technical notes on confidence or limitations
```

---

## 3. Redesigned Component Model

The component model must not assign airworthiness categories based on naive substring matching (e.g., classifying a lavatory valve as a critical flight control actuator).

```text
ComponentInfo:
  ├── component_id: str                     # e.g. "COMP-CFM56-HPT-S1-BLADE"
  ├── component_name: str                   # Name of component
  ├── part_number: Optional[str]            # OEM part number
  ├── system: str                           # Primary ATA system (e.g. "ATA 72 - Engine")
  ├── subsystem: str                        # Subsystem (e.g. "High Pressure Turbine")
  ├── primary_function: EngineeringClaim    # What it does, with supporting evidence
  ├── operating_environment: EngineeringClaim # Temperatures, RPM, chemical, vibration
  ├── analysis_scope: str                   # Boundary conditions of FMEA (Indenture Level per MIL-STD-1629A § 3.1.17)
  ├── regulatory_classification: str        # e.g. "Engine Critical Part (14 CFR § 33.75)"
  ├── classification_basis: EngineeringClaim # Why it receives this airworthiness classification
  └── analysis_status: AnalysisStatus       # SUPPORTED, PARTIALLY_SUPPORTED, INSUFFICIENT_EVIDENCE
```

---

## 4. Physical Failure Mechanism vs. Failure Mode

Per aerospace failure analysis standards, physical degradation mechanisms must be decoupled from failure mode descriptions:

* **Failure Mode:** The observable manner in which an item fails to deliver its intended function (e.g., *Airfoil structural cracking*, *Blade tip clearance loss*, *Cooling airflow starvation*).
* **Physical Failure Mechanism:** The physical, chemical, metallurgical, or thermal process causing the failure (e.g., *Thermal Mechanical Fatigue (TMF)*, *High-Temperature Creep*, *CMAS Silicate Vitrification*, *Dovetail Fretting*).
* **Root Cause:** The fundamental design, environmental, or operational agent that triggered the mechanism (e.g., *Idle-to-takeoff thermal transients creating cyclic thermal strains at cooling holes*).

---

## 5. Severity Representation (MIL-STD-1629A Task 101 § 4.4)

Severity must **not** be an arbitrary 1–10 integer. It must adhere to the four qualitative Roman numeral categories established by MIL-STD-1629A and aligned with MIL-STD-882:

```python
class SeverityCategory(str, Enum):
    CATEGORY_I = "Category I - Catastrophic"   # May cause death or weapon system loss (e.g., uncontained blade)
    CATEGORY_II = "Category II - Critical"     # Severe injury, major property damage, or mission loss
    CATEGORY_III = "Category III - Marginal"   # Minor injury, minor property damage, mission degradation
    CATEGORY_IV = "Category IV - Minor"       # Unscheduled maintenance/repair; no injury or system damage
    UNKNOWN = "Unknown / Insufficient Evidence" # Evidence does not support classification
```

### Dedicated `SeverityClassification` Object:
```text
SeverityClassification:
  ├── category: SeverityCategory            # Category I, II, III, IV, or UNKNOWN
  ├── definition: str                       # Verbatim definition from MIL-STD-1629A § 4.4.3
  ├── justification: EngineeringClaim       # Claim explaining why the End Effect falls in this category
  ├── regulatory_hazard_tier: Optional[str] # 14 CFR § 33.75 / CS-E 510 alignment (Hazardous / Major / Minor)
  └── classification_confidence: str        # HIGH, MEDIUM, LOW, UNVERIFIED
```

---

## 6. Criticality Methodology (MIL-STD-1629A Task 102)

Criticality Analysis (CA) is **completely decoupled from Severity**. It represents the probability/rate of the failure mode occurring combined with its severity.

### 6.1 Analysis Approach (Task 102 § 3)
MIL-STD-1629A defines two mutually exclusive approaches:
1. **Qualitative Approach (Task 102 § 3.1):** Used when failure rate data ($\lambda_p$) is not available. Evaluates failure modes against five probability levels:
   * **Level A – Frequent:** Probability $> 0.20$ of overall failure probability.
   * **Level B – Reasonably Probable:** Probability $0.10$ to $0.20$.
   * **Level C – Occasional:** Probability $0.01$ to $0.10$.
   * **Level D – Remote:** Probability $0.001$ to $0.01$.
   * **Level E – Extremely Unlikely:** Probability $< 0.001$.
   * **Criticality Matrix Display:** $4 \times 5$ grid (Severity Categories I–IV vs. Probability Levels A–E, Task 102 § 4 & Figure 102.2).
2. **Quantitative Approach (Task 102 § 3.2):** Used when part failure rate ($\lambda_p$) is available.
   * **Failure Mode Criticality Number ($C_m$):**
     $$C_m = \beta \cdot \alpha \cdot \lambda_p \cdot t$$
     Where:
     * $\beta$ = Conditional probability of the failure effect (Table 102.1).
     * $\alpha$ = Failure mode ratio (fraction of part failure rate attributed to this mode, $\sum \alpha = 1.0$).
     * $\lambda_p$ = Part failure rate (from MIL-HDBK-217 or airline fleet flight-hour tracking).
     * $t$ = Operating time (mission duration or flight cycle duration in hours).
   * **Item Criticality Number ($C_r$):**
     $$C_r = \sum_{j=1}^n (C_m)_j$$

### 6.2 Dedicated `CriticalityAnalysis` Object:
```text
CriticalityAnalysis:
  ├── methodology: CriticalityMethodology   # QUALITATIVE_MATRIX vs QUANTITATIVE_CALCULATION vs UNKNOWN
  │
  │── # Qualitative Fields (Task 102 § 3.1)
  ├── qualitative_level: Optional[ProbabilityLevel] # Level A through E
  ├── matrix_position: Optional[str]        # e.g. "Cat II - Level C"
  │
  │── # Quantitative Fields (Task 102 § 3.2)
  ├── beta_conditional_probability: Optional[float] # Beta (0.0 to 1.0)
  ├── alpha_failure_mode_ratio: Optional[float]     # Alpha (0.0 to 1.0)
  ├── part_failure_rate_lambda_p: Optional[float]   # Lambda_p (failures per 10^6 hours)
  ├── operating_time_t: Optional[float]             # Operating hours or cycles
  ├── failure_mode_criticality_cm: Optional[float]  # Calculated Cm
  │
  ├── data_source_description: str          # Where lambda_p or qualitative level was obtained
  ├── rationale: EngineeringClaim           # Justification with supporting evidence
  └── assumptions: List[EngineeringAssumption] # Assumptions made during analysis
```

---

## 7. Detection & Controls Model

Per MIL-STD-1629A Task 101 § 5.7, detection is a **qualitative description of operator and maintenance detection means**. It is **not** an integer 1–10 multiplied into an RPN.

```text
DetectionAndControls:
  ├── primary_detection_means: str          # Visual / Borescope / Vibration / EGT / NDT / None
  ├── detection_category: DetectionCategory # REAL_TIME_COCKPIT, SCHEDULED_LINE_MAINTENANCE, DEPOT_OVERHAUL, UNDETECTABLE
  ├── method_description: EngineeringClaim  # Full description of method with evidence
  ├── operational_readiness_indicator: str  # Annunciation, warning light, telemetry parameter
  ├── is_undetectable: bool                 # True if undetectable failure under MIL-STD-1629A § 3.1.21
  └── recommended_action: EngineeringClaim  # Specific maintenance action, limit, or interval
```

---

## 8. Legacy RPN Isolation

To maintain compatibility with existing downstream consumers without propagating false compliance claims:
* RPN is moved into an explicit `LegacyRPN` object.
* It is marked with `methodology = "legacy_automotive_unverified"`.
* It is marked with `is_mil_std_1629a_standard = False`.
* It is **quarantined** from the core aerospace airworthiness evaluation.

```text
LegacyRPN:
  ├── severity_score: int                   # 1 to 10
  ├── occurrence_score: int                 # 1 to 10
  ├── detection_score: int                  # 1 to 10
  ├── rpn_value: int                        # S * O * D (1 to 1000)
  ├── methodology: str = "legacy_automotive_unverified"
  ├── is_mil_std_1629a_standard: bool = False
  └── disclaimer: str = "RPN is an automotive prioritization metric (SAE J1739/AIAG) and is NOT part of MIL-STD-1629A."
```

---

## 9. Critical Items List (CIL) & Single Failure Point Architecture

In accordance with MIL-STD-1629A § 4.5.2.1 and NASA-STD-8729.1A:
* **Inclusion Criteria:** An item is classified as a Critical Item if:
  1. It is a **Category I (Catastrophic)** failure mode.
  2. It is a **Category II (Critical)** failure mode.
  3. It is a **Single Failure Point (SFP)** (NASA-STD-8729.1A § 13: failure results in loss of system/crew with no redundancy).
* The arbitrary condition `if rpn >= 100` is **completely eliminated**.

```text
CILAssessment:
  ├── is_critical_item: bool                # True if meets standard criteria
  ├── single_failure_point: bool            # True if SFP under MIL-STD-1629A § 3.1.19
  ├── inclusion_basis: str                  # "MIL-STD-1629A § 4.5.2.1 (Category I / II)"
  ├── retention_rationale: EngineeringClaim # Design features, inspections, history that justify retaining item
  └── verification_status: str              # VERIFIED, UNVERIFIED, PENDING_REVIEW
```

---

## 10. Complete Failure Mode Entry Model

Putting the components together, the redesigned `FailureModeEntry` becomes:

```text
FailureModeEntry:
  ├── mode_id: str                          # e.g. "FM-HPT-001"
  ├── failure_mode: str                     # Observable failure mode wording
  ├── physical_mechanism: str               # Metallurgical / physics mechanism (TMF, Creep)
  ├── root_cause: EngineeringClaim          # Root cause with evidence & assumptions
  ├── local_effect: EngineeringClaim        # Component-level consequence with evidence
  ├── next_higher_effect: EngineeringClaim  # Engine-module consequence with evidence
  ├── end_effect: EngineeringClaim          # Aircraft / airworthiness hazard with evidence
  ├── severity: SeverityClassification      # MIL-STD-1629A Category I–IV + justification
  ├── criticality: CriticalityAnalysis      # Qualitative Matrix or Quantitative Cm
  ├── detection: DetectionAndControls       # Maintenance / diagnostic means
  ├── cil_assessment: CILAssessment         # CIL & Single Failure Point determination
  ├── legacy_rpn: Optional[LegacyRPN]       # Isolated backward-compatibility structure
  ├── mode_status: AnalysisStatus           # SUPPORTED, INFERRED, INSUFFICIENT_EVIDENCE
  └── metadata: Dict[str, Any]              # Extensible attributes
```

---

## 11. Complete FMEA Report & Validation Models

```text
ValidationIssue:
  ├── severity_level: str                   # "ERROR", "WARNING", "NOTE"
  ├── standard_reference: str               # e.g. "MIL-STD-1629A § 4.4.3"
  ├── description: str                      # Exact description of non-compliance
  ├── affected_mode_id: Optional[str]       # Target mode
  └── resolution_recommendation: str        # Required action

ValidationReport:
  ├── is_compliant: bool                    # Overall compliance status
  ├── compliance_standard: str              # "MIL-STD-1629A (Task 101/102)"
  ├── total_modes_evaluated: int
  ├── category_i_count: int                 # Catastrophic modes
  ├── category_ii_count: int                # Critical modes
  ├── single_failure_points_count: int      # SFP modes
  ├── unverified_claims_count: int          # Claims lacking direct evidence
  ├── issues: List[ValidationIssue]
  └── compliance_summary: str

FMEAReport:
  ├── component: ComponentInfo
  ├── failure_modes: List[FailureModeEntry]
  ├── global_assumptions: List[EngineeringAssumption]
  ├── validation: ValidationReport
  └── generation_metadata: Dict[str, Any]
```

---

## 12. Provenance Integrity Rules

To enforce claim-level provenance, the following validation rules are established:

* **Rule A:** Every `EngineeringClaim` marked `DIRECT_SOURCE` must have at least one `EvidenceRecord` containing valid `source_document`, `page_number`, and non-empty `excerpt`.
* **Rule B:** Global copying of citations is disallowed. An evidence record attached to a claim must be verified against the text of that claim.
* **Rule C:** Claims generated from developer knowledge or heuristic fallbacks must be explicitly labeled `SupportLevel.DOMAIN_HEURISTIC`.
* **Rule D:** Any failure mode or field where the RAG corpus contains no evidence must be assigned `SupportLevel.INSUFFICIENT_EVIDENCE` or `SeverityCategory.UNKNOWN`. Fabricating values to satisfy schema constraints is prohibited.
* **Rule E:** Critical Items List determination must be computed strictly from `SeverityCategory.CATEGORY_I`, `SeverityCategory.CATEGORY_II`, or `single_failure_point == True`.
