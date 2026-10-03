"""Pydantic data models and TypedDict state definitions for FMEA-GPT LangGraph agent.

Redesigned in Phase 5A to adhere strictly to:
- MIL-STD-1629A (Task 101 Failure Mode and Effects Analysis, Task 102 Criticality Analysis)
- NASA-STD-8729.1A (Critical Items List & Single Point Failure methodology)
- FAA AC 33.75-1A / EASA CS-E 510 (Airworthiness hazardous engine effects)

Distinguishes empirical evidence from engineering inference and isolates legacy automotive RPN.
"""
from enum import Enum
from typing import List, Dict, Any, Optional, TypedDict
from pydantic import BaseModel, Field


# ============================================================================
# 1. Epistemic Support Levels and Analysis Status
# ============================================================================

class SupportLevel(str, Enum):
    """Epistemic support level classifying the evidentiary basis of an engineering claim."""
    DIRECT_SOURCE = "direct_source"          # Verifiable fact/clause directly in cited source document
    SUPPORTING_SOURCE = "supporting_source"  # Cited source provides relevant technical context/principles
    ENGINEERING_INFERENCE = "inference"      # Technical deduction derived from physical laws or failure records
    DOMAIN_HEURISTIC = "domain_heuristic"    # Expert rules-of-thumb, baseline templates, or unverified presets
    UNSUPPORTED = "unsupported"              # Claim made with zero documentary or physical evidence
    INSUFFICIENT_EVIDENCE = "insufficient_evidence" # Explicit absence of data in knowledge corpus


class AnalysisStatus(str, Enum):
    """Analysis grounding status for an entity, failure mode, or overall analysis."""
    SUPPORTED = "supported"                  # Fully substantiated by direct/supporting evidence
    PARTIALLY_SUPPORTED = "partially_supported" # Some fields grounded; others inferred
    INFERRED = "inferred"                    # Logically inferred from domain physics without direct citation
    INSUFFICIENT_EVIDENCE = "insufficient_evidence" # Corpus cannot substantiate analysis; uncertainty flagged


# ============================================================================
# 2. Standards-Compliant Severity & Criticality Classifications
# ============================================================================

class SeverityCategory(str, Enum):
    """MIL-STD-1629A § 4.4.3 / MIL-STD-882 Severity Classification Categories."""
    CATEGORY_I = "Category I - Catastrophic"   # Failure may cause death or weapon system loss
    CATEGORY_II = "Category II - Critical"     # Severe injury, major property damage, or mission loss
    CATEGORY_III = "Category III - Marginal"   # Minor injury, minor property damage, or mission degradation
    CATEGORY_IV = "Category IV - Minor"       # Unscheduled maintenance or repair; no injury or system damage
    UNKNOWN = "Unknown / Insufficient Evidence" # Evidence does not support classification


class ProbabilityLevel(str, Enum):
    """MIL-STD-1629A Task 102 § 3.1 Qualitative Failure Probability Levels."""
    LEVEL_A = "Level A - Frequent (>0.20)"               # Single failure mode prob > 0.20 of overall failure prob
    LEVEL_B = "Level B - Reasonably Probable (0.10-0.20)"# Single failure mode prob 0.10 to 0.20
    LEVEL_C = "Level C - Occasional (0.01-0.10)"         # Single failure mode prob 0.01 to 0.10
    LEVEL_D = "Level D - Remote (0.001-0.01)"            # Single failure mode prob 0.001 to 0.01
    LEVEL_E = "Level E - Extremely Unlikely (<0.001)"    # Single failure mode prob < 0.001
    UNKNOWN = "Unknown / Unquantified"                   # Insufficient data to evaluate probability level


class CriticalityMethodology(str, Enum):
    """MIL-STD-1629A Task 102 Analysis Approach."""
    QUALITATIVE_MATRIX = "qualitative_matrix"           # Task 102 § 3.1 (4x5 Criticality Matrix)
    QUANTITATIVE_CALCULATION = "quantitative_calculation"# Task 102 § 3.2 (Cm = beta * alpha * lambda_p * t)
    UNKNOWN = "unknown"                                  # Criticality approach unassigned


class ReliabilityScope(str, Enum):
    """Scope of applicability for quantitative reliability inputs."""
    PART_SPECIFIC_MEASURED = "part_specific_measured"       # Empirically measured on exact Part Number
    FLEET_OBSERVED_SURROGATE = "fleet_observed_surrogate"   # Observed in fleet on same family/stage
    GENERIC_TURBINE_BENCHMARK = "generic_turbine_benchmark" # Literature / handbook reference value
    WORST_CASE_BOUND = "worst_case_bound"                   # Conservative standard bound (e.g. beta=1.0)
    UNVERIFIED_ASSUMPTION = "unverified_assumption"         # Unverified analyst assumption


class DetectionCategory(str, Enum):
    """Operational detection category per MIL-STD-1629A Task 101 § 5.7."""
    REAL_TIME_COCKPIT = "real_time_cockpit_alert"       # Annunciator, master caution, EICAS/ECAM
    SCHEDULED_LINE_MAINTENANCE = "scheduled_line_maintenance" # Routine borescope, walkaround, line check
    SHOP_DEPOT_OVERHAUL = "shop_depot_overhaul"         # Shop visit, NDT (FPI, Eddy Current), full disassembly
    PRE_FLIGHT_WALKAROUND = "pre_flight_walkaround"     # Visual inspection by crew/mechanic
    UNDETECTABLE = "undetectable"                       # MIL-STD-1629A § 3.1.21 undetectable failure


# ============================================================================
# 3. Evidence, Assumption, and Claim Models
# ============================================================================

class EvidenceRecord(BaseModel):
    """Robust provenance record linking a specific passage to an engineering claim."""
    evidence_id: str = Field(description="Unique identifier for this evidence record")
    source_document: str = Field(description="Source PDF filename, e.g. MIL-STD-1629A.pdf")
    document_title: str = Field(description="Formal title of source standard or publication")
    publisher: str = Field(description="Publishing authority (DoD, FAA, EASA, NASA)")
    page_number: int = Field(description="1-indexed PDF page number containing the citation")
    section: Optional[str] = Field(default=None, description="Clause or paragraph reference, e.g. Task 101 § 4.3")
    excerpt: str = Field(description="Exact verbatim excerpt from the document")
    retrieval_query: Optional[str] = Field(default=None, description="Semantic search query used to retrieve chunk")
    retrieval_score: Optional[float] = Field(default=None, description="Raw uncalibrated retrieval distance/score")
    evidence_type: str = Field(default="regulatory_standard", description="standard, regulation, manual, bulletin")
    support_level: SupportLevel = Field(default=SupportLevel.SUPPORTING_SOURCE)
    official_report_number: Optional[str] = Field(default=None, description="Official report number, e.g. NASA-CR-189111")
    publication_year: Optional[int] = Field(default=None, description="Year of publication")
    evidence_category: Optional[str] = Field(default=None, description="Methodology, field study, experiment, regulation, etc.")
    technical_domain: Optional[str] = Field(default=None, description="Domain classification of source")
    applicability_scope: Optional[str] = Field(default=None, description="Generalization constraint / test population audit")

    def to_citation_str(self) -> str:
        sec = f" § {self.section}" if self.section else ""
        return f"{self.document_title} ({self.publisher}){sec}, Page {self.page_number} [{self.source_document}]"


class EngineeringAssumption(BaseModel):
    """Explicitly documented engineering assumption underpinning an analysis."""
    assumption_id: str = Field(description="Unique assumption ID, e.g. ASM-001")
    statement: str = Field(description="Exact statement of what is assumed")
    engineering_rationale: str = Field(description="Physical or operational justification for assumption")
    risk_impact: str = Field(description="Potential consequence if assumption is invalidated")
    verification_required: bool = Field(default=True, description="Whether physical test/review is mandatory")


class EngineeringClaim(BaseModel):
    """Granular engineering claim with explicit evidence grounding and assumptions."""
    claim_id: str = Field(description="Unique claim identifier, e.g. CLM-CAUSE-001")
    statement: str = Field(description="The technical statement or assertion")
    claim_type: str = Field(default="general", description="cause, local_effect, end_effect, action, etc.")
    support_level: SupportLevel = Field(default=SupportLevel.DOMAIN_HEURISTIC)
    evidence: List[EvidenceRecord] = Field(default_factory=list, description="Grounding evidence records")
    assumptions: List[EngineeringAssumption] = Field(default_factory=list, description="Associated assumptions")
    verification_notes: Optional[str] = Field(default=None, description="Caveats, margins, or review notes")

    @property
    def is_evidence_backed(self) -> bool:
        return len(self.evidence) > 0 and self.support_level in [
            SupportLevel.DIRECT_SOURCE, SupportLevel.SUPPORTING_SOURCE
        ]


# ============================================================================
# 4. Backward Compatibility Citation Wrapper
# ============================================================================

class Citation(BaseModel):
    """Legacy citation model preserved for backward compatibility with Phase 1-3 exporters."""
    source_document: str = Field(description="Source PDF filename")
    doc_title: str = Field(description="Title of the source document")
    page_number: int = Field(description="1-indexed page number in the original PDF")
    publisher: str = Field(description="Publishing authority (DoD, FAA, EASA, NASA)")
    similarity_score: float = Field(default=0.0, description="Semantic similarity percentage (uncalibrated)")
    excerpt: Optional[str] = Field(default=None, description="Relevant excerpt text")

    def to_evidence_record(self, evidence_id: Optional[str] = None) -> EvidenceRecord:
        """Convert legacy citation to rich EvidenceRecord."""
        return EvidenceRecord(
            evidence_id=evidence_id or f"EVID-{self.source_document}-P{self.page_number}",
            source_document=self.source_document,
            document_title=self.doc_title,
            publisher=self.publisher,
            page_number=self.page_number,
            excerpt=self.excerpt or "",
            retrieval_score=self.similarity_score,
            support_level=SupportLevel.SUPPORTING_SOURCE
        )


# ============================================================================
# 5. Severity, Criticality, Controls, and CIL Subsystems
# ============================================================================

class SeverityClassification(BaseModel):
    """Standards-compliant severity representation per MIL-STD-1629A § 4.4.3."""
    category: SeverityCategory = Field(
        default=SeverityCategory.UNKNOWN,
        description="MIL-STD-1629A Severity Category (Category I, II, III, IV, or UNKNOWN)"
    )
    definition: str = Field(default="", description="Verbatim definition from MIL-STD-1629A § 4.4.3")
    justification: EngineeringClaim = Field(description="Technical claim justifying the severity category")
    regulatory_hazard_tier: Optional[str] = Field(
        default=None,
        description="FAA AC 33.75-1A / EASA CS-E 510 airworthiness hazard tier (Hazardous / Major / Minor)"
    )
    classification_confidence: str = Field(default="UNVERIFIED", description="HIGH, MEDIUM, LOW, UNVERIFIED")


class CriticalityInputParameter(BaseModel):
    """Independent structured parameter record for MIL-STD-1629A criticality calculation (Cm = beta * alpha * lambda_p * t)."""
    parameter_name: str = Field(description="Parameter name (beta, alpha, lambda_p, t)")
    symbol: str = Field(description="Mathematical symbol (β, α, λp, t)")
    value: Optional[float] = Field(default=None, description="Assigned numerical value")
    unit: str = Field(default="dimensionless", description="Unit of measurement (dimensionless, failures/hr, hours)")
    source: str = Field(default="MIL-STD-1629A Table 102.1 / Engineering Assessment", description="Reference document or authoritative source")
    scope: ReliabilityScope = Field(default=ReliabilityScope.WORST_CASE_BOUND, description="Applicability scope")
    is_measured: bool = Field(default=False, description="True if empirically measured from field/test data, False if assumed")
    assumption_status: str = Field(default="ASSUMPTION", description="'SOURCE-DERIVED' or 'ASSUMPTION'")
    rationale: str = Field(default="", description="Detailed rationale explaining origin, limits, and justification of value")


class CriticalityAnalysis(BaseModel):
    """MIL-STD-1629A Task 102 Criticality Analysis data model."""
    methodology: CriticalityMethodology = Field(
        default=CriticalityMethodology.QUALITATIVE_MATRIX,
        description="Task 102 Approach: Qualitative Matrix (§ 3.1) or Quantitative Calculation (§ 3.2)"
    )
    
    # Qualitative approach fields (Task 102 § 3.1 & Figure 102.2)
    qualitative_level: Optional[ProbabilityLevel] = Field(
        default=None,
        description="Failure mode probability of occurrence level (Level A through E)"
    )
    matrix_position: Optional[str] = Field(
        default=None,
        description="Grid position on MIL-STD-1629A Figure 102.2 matrix, e.g. 'Cat I - Level D'"
    )
    
    # Quantitative calculation fields (Task 102 § 3.2.1: Cm = beta * alpha * lambda_p * t)
    beta_conditional_probability: Optional[float] = Field(
        default=None,
        ge=0.0, le=1.0,
        description="Conditional probability that failure mode results in listed severity effect (Table 102.1)"
    )
    alpha_failure_mode_ratio: Optional[float] = Field(
        default=None,
        ge=0.0, le=1.0,
        description="Fraction of part failure rate attributed to this failure mode"
    )
    part_failure_rate_lambda_p: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Part failure rate (failures per operating hour or 10^6 hours)"
    )
    operating_time_t: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Operating time in hours or mission operating cycles"
    )
    failure_mode_criticality_cm: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Calculated Failure Mode Criticality Number: Cm = beta * alpha * lambda_p * t"
    )
    
    # Independent parameter representation and scope protection
    input_parameters: Optional[Dict[str, CriticalityInputParameter]] = Field(
        default=None,
        description="Independent inputs for beta, alpha, lambda_p, t with full provenance and assumption tracking"
    )
    reliability_scope: Optional[ReliabilityScope] = Field(
        default=None,
        description="Overall reliability scope preventing generic turbine data from silent assignment to specific part numbers"
    )

    data_source_description: str = Field(
        default="Qualitative engineering assessment",
        description="Source of failure rates or qualitative probability assignment"
    )
    rationale: EngineeringClaim = Field(description="Engineering rationale underpinning criticality evaluation")
    assumptions: List[EngineeringAssumption] = Field(default_factory=list)


def create_criticality_input_parameters(
    beta: Optional[float] = None,
    beta_status: str = "ASSUMPTION",
    beta_rationale: str = "MIL-STD-1629A Table 102.1 conditional probability bound for actual loss given mode occurrence (not empirical fleet probability)",
    alpha: Optional[float] = None,
    alpha_status: str = "ASSUMPTION",
    alpha_rationale: str = "Failure mode ratio estimate based on engineering failure mode distribution",
    lambda_p: Optional[float] = None,
    lambda_p_status: str = "ASSUMPTION",
    lambda_p_source: str = "Proprietary fleet/engine records (uncataloged in open regulatory corpus)",
    lambda_p_scope: ReliabilityScope = ReliabilityScope.GENERIC_TURBINE_BENCHMARK,
    t: Optional[float] = None,
    t_status: str = "ASSUMPTION",
    t_rationale: str = "Operating time or mission duration interval"
) -> Dict[str, CriticalityInputParameter]:
    """Build structured input parameter records for Cm = beta * alpha * lambda_p * t."""
    params = {}
    if beta is not None:
        params["beta"] = CriticalityInputParameter(
            parameter_name="conditional_probability_beta",
            symbol="β",
            value=beta,
            unit="dimensionless",
            source="MIL-STD-1629A Table 102.1",
            scope=ReliabilityScope.WORST_CASE_BOUND if beta == 1.0 else ReliabilityScope.UNVERIFIED_ASSUMPTION,
            is_measured=False,
            assumption_status="ASSUMPTION" if beta == 1.0 and beta_status != "SOURCE-DERIVED" else beta_status,
            rationale=beta_rationale
        )
    if alpha is not None:
        params["alpha"] = CriticalityInputParameter(
            parameter_name="failure_mode_ratio_alpha",
            symbol="α",
            value=alpha,
            unit="dimensionless",
            source="Engineering Failure Mode Distribution Analysis",
            scope=ReliabilityScope.GENERIC_TURBINE_BENCHMARK,
            is_measured=False,
            assumption_status=alpha_status,
            rationale=alpha_rationale
        )
    if lambda_p is not None:
        params["lambda_p"] = CriticalityInputParameter(
            parameter_name="part_failure_rate_lambda_p",
            symbol="λp",
            value=lambda_p,
            unit="failures/operating_hour",
            source=lambda_p_source,
            scope=lambda_p_scope,
            is_measured=False,
            assumption_status=lambda_p_status,
            rationale="Part failure rate per operating hour"
        )
    if t is not None:
        params["t"] = CriticalityInputParameter(
            parameter_name="operating_time_t",
            symbol="t",
            value=t,
            unit="operating_hours",
            source="Flight Mission Profile / Maintenance Interval Specification",
            scope=ReliabilityScope.WORST_CASE_BOUND,
            is_measured=False,
            assumption_status=t_status,
            rationale=t_rationale
        )
    return params


def enforce_reliability_scope(
    target_part_number: str,
    source_part_number: Optional[str],
    data_scope: ReliabilityScope
) -> ReliabilityScope:
    """Enforces reliability scope protection.
    
    Prevents general turbine reliability data from silently being assigned
    to specific part numbers (e.g. CFM56 P/N 301-789-204-0) as PART_SPECIFIC_MEASURED.
    """
    if not source_part_number or source_part_number.strip() != target_part_number.strip():
        if data_scope == ReliabilityScope.PART_SPECIFIC_MEASURED:
            return ReliabilityScope.GENERIC_TURBINE_BENCHMARK
    return data_scope



class DetectionAndControls(BaseModel):
    """Failure detection methods and compensating provisions per MIL-STD-1629A Task 101 § 5.7 & § 5.8."""
    primary_detection_means: str = Field(description="Primary instrument, sensor, or visual inspection means")
    detection_category: DetectionCategory = Field(default=DetectionCategory.SCHEDULED_LINE_MAINTENANCE)
    method_description: EngineeringClaim = Field(description="Detailed procedure with supporting evidence")
    operational_readiness_indicator: str = Field(default="None", description="Cockpit or maintenance indicator")
    is_undetectable: bool = Field(default=False, description="True if undetectable failure per MIL-STD-1629A § 3.1.21")
    recommended_action: EngineeringClaim = Field(description="Actionable maintenance limit or design mitigation")
    inspection_interval: str = Field(default="Unspecified", description="Interval, e.g. 500 Flight Cycles")


class CILAssessment(BaseModel):
    """Critical Items List assessment per MIL-STD-1629A § 4.5.2.1 and NASA-STD-8729.1A § 13."""
    is_critical_item: bool = Field(default=False, description="True if Category I, Category II, or SFP")
    single_failure_point: bool = Field(
        default=False,
        description="True if Single Failure Point under MIL-STD-1629A § 3.1.19 / NASA-STD-8729.1A"
    )
    inclusion_basis: str = Field(
        default="",
        description="Reason for CIL inclusion: Category I, Category II, or Single Point Failure"
    )
    retention_rationale: EngineeringClaim = Field(
        description="Design features, inspections, and service history justifying retaining the item"
    )
    verification_status: str = Field(default="PENDING_REVIEW", description="VERIFIED, UNVERIFIED, PENDING_REVIEW")

    @property
    def is_single_point_failure(self) -> bool:
        return self.single_failure_point


class LegacyRPN(BaseModel):
    """Quarantined legacy automotive RPN representation.
    
    Explicitly decoupled from MIL-STD-1629A core airworthiness representation.
    """
    severity_score: int = Field(ge=1, le=10, description="Automotive ordinal severity (1-10)")
    occurrence_score: int = Field(ge=1, le=10, description="Automotive ordinal occurrence (1-10)")
    detection_score: int = Field(ge=1, le=10, description="Automotive ordinal detection (1-10)")
    rpn_value: int = Field(ge=1, le=1000, description="RPN = S * O * D (1 to 1000)")
    methodology: str = Field(default="legacy_automotive_unverified")
    is_mil_std_1629a_standard: bool = Field(default=False)
    disclaimer: str = Field(
        default="RPN is an automotive prioritization metric (SAE J1739/AIAG) and is NOT part of MIL-STD-1629A."
    )


# ============================================================================
# 6. Component and Failure Mode Models
# ============================================================================

class ComponentInfo(BaseModel):
    """Component classification, operational boundary, and airworthiness tier."""
    component_id: str = Field(default="COMP-001", description="Unique component identifier")
    component_name: str = Field(description="Name or designation of the component")
    part_number: Optional[str] = Field(default=None, description="Part number if available")
    system: str = Field(default="Propulsion", description="Primary ATA system (e.g. ATA 72 - Propulsion)")
    subsystem: str = Field(default="High Pressure Turbine", description="Subsystem or module")
    regulatory_class: str = Field(
        default="Engine Critical Part (14 CFR § 33.75 / EASA CS-E 510)",
        description="Airworthiness regulatory classification"
    )
    operating_environment: str = Field(
        default="High temperature, high centrifugal stress, thermal cycling, corrosive gas flow",
        description="Operating conditions and physical stresses"
    )
    primary_function: str = Field(
        default="Extract thermal and kinetic energy from high-pressure combustion gas",
        description="Primary functional definition"
    )
    analysis_scope: str = Field(
        default="Indenture Level 3 (Turbomachinery Airfoil Assembly)",
        description="Indenture level and boundary conditions per MIL-STD-1629A § 3.1.17"
    )
    classification_basis: Optional[EngineeringClaim] = Field(
        default=None,
        description="Evidentiary justification for the assigned airworthiness regulatory tier"
    )
    classification_confidence: str = Field(default="UNVERIFIED", description="HIGH, MEDIUM, LOW, UNVERIFIED")
    analysis_status: AnalysisStatus = Field(default=AnalysisStatus.INFERRED)


class FailureModeEntry(BaseModel):
    """Failure Mode and Effects record conforming to MIL-STD-1629A Task 101/102.
    
    Retains backward-compatible string/integer accessors while embedding full claim-level provenance.
    """
    mode_id: str = Field(description="Unique failure mode ID, e.g. FM-HPT-001")
    failure_mode: str = Field(description="Observable physical failure mode description")
    physical_mechanism: str = Field(default="", description="Degradation physics (TMF, Creep, CMAS, Fretting)")
    root_cause: str = Field(description="Primary engineering root cause of the failure")
    local_effect: str = Field(description="Immediate local consequence on the component")
    next_higher_effect: str = Field(description="Consequence on the engine module/assembly")
    end_effect: str = Field(description="Aircraft-level safety consequence per FAA/EASA")
    
    # Legacy quantitative scoring fields preserved for downstream UI/exporter compatibility
    severity: int = Field(ge=1, le=10, default=5, description="Legacy ordinal severity score (1-10)")
    occurrence: int = Field(ge=1, le=10, default=3, description="Legacy ordinal occurrence score (1-10)")
    detection: int = Field(ge=1, le=10, default=3, description="Legacy ordinal detection score (1-10)")
    rpn: int = Field(ge=1, le=1000, default=45, description="Legacy RPN: S * O * D (Quarantined)")
    
    # MIL-STD-1629A Categorical Classification
    mil_std_severity_category: str = Field(
        default="Category II - Critical",
        description="MIL-STD-1629A Severity Category (Category I, II, III, IV, or UNKNOWN)"
    )
    single_point_failure: bool = Field(
        default=False,
        description="Single Point Failure per MIL-STD-1629A § 3.1.19 / NASA-STD-8729.1A"
    )
    
    # Mitigation and Maintenance fields
    detection_method: str = Field(default="", description="Diagnostic or inspection method")
    recommended_action: str = Field(default="", description="Mitigating action or design change")
    inspection_interval: str = Field(default="", description="Recommended maintenance inspection interval")
    compliance_reference: str = Field(default="", description="Applicable aerospace standard reference")
    citations: List[Citation] = Field(default_factory=list, description="Legacy citation list for backward compatibility")
    
    # --- PHASE 5A RICH AIRWORTHINESS ENGINEERING EXTENSIONS ---
    severity_classification: Optional[SeverityClassification] = Field(
        default=None,
        description="Rigorous MIL-STD-1629A § 4.4.3 severity model with justification and evidence"
    )
    criticality_analysis: Optional[CriticalityAnalysis] = Field(
        default=None,
        description="Dedicated MIL-STD-1629A Task 102 criticality model (Qualitative Matrix or Quantitative Cm)"
    )
    detection_and_controls: Optional[DetectionAndControls] = Field(
        default=None,
        description="MIL-STD-1629A Task 101 § 5.7 detection & maintenance model"
    )
    cil_assessment: Optional[CILAssessment] = Field(
        default=None,
        description="NASA-STD-8729.1A / MIL-STD-1629A Critical Items List determination"
    )
    legacy_rpn_audit: Optional[LegacyRPN] = Field(
        default=None,
        description="Isolated legacy automotive RPN with explicit disclaimers"
    )
    
    # Claim-level provenance objects for individual fields
    root_cause_claim: Optional[EngineeringClaim] = Field(default=None)
    local_effect_claim: Optional[EngineeringClaim] = Field(default=None)
    next_effect_claim: Optional[EngineeringClaim] = Field(default=None)
    end_effect_claim: Optional[EngineeringClaim] = Field(default=None)
    mode_status: AnalysisStatus = Field(default=AnalysisStatus.INFERRED)
    evidence_records: List[EvidenceRecord] = Field(
        default_factory=list,
        description="Granular evidence records linked specifically to this failure mode"
    )


# ============================================================================
# 7. Validation and Reporting Packages
# ============================================================================

class ValidationIssue(BaseModel):
    """Issue, discrepancy, or compliance note identified during engineering self-review."""
    severity_level: str = Field(description="ERROR, WARNING, or NOTE")
    rule: str = Field(description="MIL-STD-1629A or airworthiness requirement rule name")
    description: str = Field(description="Detailed explanation of the issue")
    affected_mode_id: Optional[str] = Field(default=None, description="Affected failure mode ID if specific")
    resolution_recommendation: Optional[str] = Field(default=None, description="Required corrective action")


class ValidationReport(BaseModel):
    """Overall compliance, structural, and evidence validity report."""
    is_compliant: bool = Field(default=True, description="True if no blocking structural or airworthiness errors exist")
    compliance_standard: str = Field(default="MIL-STD-1629A (Task 101/102) & NASA-STD-8729.1A")
    total_modes_evaluated: int = Field(default=0)
    single_point_failures_count: int = Field(default=0)
    max_rpn: Optional[int] = Field(default=None)
    critical_items_count: int = Field(default=0)
    category_i_count: int = Field(default=0)
    category_ii_count: int = Field(default=0)
    unverified_claims_count: int = Field(default=0)
    issues: List[ValidationIssue] = Field(default_factory=list)
    compliance_summary: str = Field(default="")


# ============================================================================
# 8. Phase 5B Reasoning Engine Models
# ============================================================================

class EvidenceCoverageReport(BaseModel):
    """Deterministic count-based quantification of evidence grounding across all claims."""
    total_claims: int = Field(default=0, description="Total number of evaluated engineering claims")
    directly_supported: int = Field(default=0, description="Claims substantiated by direct verbatim source text")
    supporting_evidence: int = Field(default=0, description="Claims materially supported by relevant standard context")
    engineering_inference: int = Field(default=0, description="Claims inferred from physical/metallurgical principles")
    domain_heuristic: int = Field(default=0, description="Claims originating from expert rule-of-thumb baseline")
    unsupported: int = Field(default=0, description="Claims lacking documentary or physical backing")
    insufficient_evidence: int = Field(default=0, description="Claims where evidence is explicitly absent in corpus")
    coverage_score: float = Field(default=0.0, description="Fraction of claims backed by direct or supporting evidence")
    is_coverage_adequate: bool = Field(default=True, description="True if corpus contains sufficient material to proceed")

    def to_summary_str(self) -> str:
        return (
            f"Claims: {self.total_claims} total | "
            f"Direct: {self.directly_supported}, Supporting: {self.supporting_evidence}, "
            f"Inferred: {self.engineering_inference}, Heuristic: {self.domain_heuristic}, "
            f"Unsupported: {self.unsupported}, Insufficient: {self.insufficient_evidence} "
            f"[Coverage: {self.coverage_score*100:.1f}%]"
        )


class CandidateFailureMode(BaseModel):
    """Candidate failure mode discovered during initial evidence extraction or heuristic proposing."""
    candidate_id: str = Field(description="Unique candidate ID, e.g. CAND-001")
    proposed_mode: str = Field(description="Proposed observable failure mode")
    proposed_mechanism: str = Field(description="Proposed physical degradation mechanism")
    discovery_source: str = Field(default="retrieval_extraction", description="retrieval_extraction, domain_heuristic, llm_discovery")
    discovery_evidence: List[EvidenceRecord] = Field(default_factory=list, description="Passages that triggered discovery")
    targeted_queries: List[str] = Field(default_factory=list, description="Targeted retrieval queries generated for candidate")
    relevance_score: float = Field(default=0.5, description="Initial discovery relevance score")
    is_retained: bool = Field(default=True, description="Whether candidate survived verification")


class ClaimVerificationResult(BaseModel):
    """Result of evaluating a specific engineering claim against candidate retrieved evidence."""
    claim_id: str = Field(description="Target claim ID")
    claim_statement: str = Field(description="Statement being verified")
    claim_type: str = Field(description="failure_mode, cause, effect, severity, detection, action")
    assigned_support_level: SupportLevel = Field(description="Evaluated support level")
    verified_evidence: List[EvidenceRecord] = Field(default_factory=list, description="Retained supporting evidence records")
    verification_rationale: str = Field(description="Deterministic rationale explaining verification outcome")
    is_verified: bool = Field(default=True, description="True if support level is direct, supporting, or inference")


class ReasoningTrace(BaseModel):
    """Audit trace documenting why each failure mode and claim was generated or rejected."""
    input_component: str
    target_part_number: Optional[str] = None
    classification_status: str = "INFERRED"
    retrieval_queries: List[str] = Field(default_factory=list)
    total_passages_retrieved: int = 0
    candidate_modes_discovered: List[str] = Field(default_factory=list)
    verification_results: List[ClaimVerificationResult] = Field(default_factory=list)
    rejected_candidates: List[str] = Field(default_factory=list)
    accepted_modes: List[str] = Field(default_factory=list)
    coverage_report: Optional[EvidenceCoverageReport] = None
    execution_route: List[str] = Field(default_factory=list, description="Sequence of graph nodes executed")
    retries_performed: int = 0


class FMEAReport(BaseModel):
    """Complete generated FMEA analysis package containing all engineering artifacts."""
    component: ComponentInfo
    failure_modes: List[FailureModeEntry] = Field(default_factory=list)
    global_assumptions: List[EngineeringAssumption] = Field(
        default_factory=list,
        description="Global engineering assumptions underpinning the entire analysis"
    )
    validation: ValidationReport = Field(default_factory=ValidationReport)
    evidence_coverage: Optional[EvidenceCoverageReport] = Field(
        default=None,
        description="Deterministic evidence coverage summary"
    )
    reasoning_trace: Optional[ReasoningTrace] = Field(
        default=None,
        description="Machine-readable audit trail of reasoning decisions"
    )
    generation_metadata: Dict[str, Any] = Field(default_factory=dict)


class FMEAState(TypedDict, total=False):
    """LangGraph execution state passed between reasoning nodes."""
    component_input: str
    target_part_number: Optional[str]
    operating_notes: Optional[str]
    
    component: ComponentInfo
    retrieved_context: Dict[str, List[Dict[str, Any]]]
    _flattened_passages: List[Dict[str, Any]]
    evidence_pool: List[EvidenceRecord]
    
    # Phase 5B Reasoning Pipeline States
    candidate_modes: List[CandidateFailureMode]
    targeted_evidence: Dict[str, List[EvidenceRecord]]
    claims_pool: List[EngineeringClaim]
    verification_results: List[ClaimVerificationResult]
    evidence_coverage: EvidenceCoverageReport
    reasoning_trace: ReasoningTrace
    
    coverage_adequate: bool
    retry_count: int
    branch_taken: str
    
    failure_modes: List[FailureModeEntry]
    validation: ValidationReport
    final_report: FMEAReport
    errors: List[str]

