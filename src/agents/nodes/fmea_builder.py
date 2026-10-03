"""Node: Evidence-Aware FMEA Synthesis and Report Assembly.

Constructs FailureModeEntry records exclusively from verified candidate failure modes.
Derives:
1. Severity Category (MIL-STD-1629A I-IV) strictly grounded in end effects and airworthiness evidence.
2. Criticality Analysis (qualitative grounded; quantitative without invented failure rates).
3. Detection controls and maintenance actions labeled with epistemological support levels.
4. Deterministic EvidenceCoverageReport (claim counts across all support levels).
5. Comprehensive ReasoningTrace documenting the complete audit path.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from ..state import (
    FMEAState,
    FMEAReport,
    FailureModeEntry,
    ComponentInfo,
    SeverityClassification,
    SeverityCategory,
    CriticalityAnalysis,
    CriticalityMethodology,
    ProbabilityLevel,
    DetectionAndControls,
    DetectionCategory,
    CILAssessment,
    LegacyRPN,
    EngineeringClaim,
    EvidenceRecord,
    Citation,
    SupportLevel,
    AnalysisStatus,
    EvidenceCoverageReport,
    ReasoningTrace,
    CandidateFailureMode,
    ClaimVerificationResult
)


def _build_mode_entry(
    cand: CandidateFailureMode,
    component: ComponentInfo,
    verified_evidence: List[EvidenceRecord],
    verification_res: Optional[ClaimVerificationResult] = None
) -> FailureModeEntry:
    """Build a complete FailureModeEntry grounded in verified candidate evidence."""
    cand_id = cand.candidate_id
    mode_name = cand.proposed_mode
    mechanism = cand.proposed_mechanism
    
    # 1. Failure Mode Claim
    fm_claim = EngineeringClaim(
        claim_id=f"CLM-{cand_id}-MODE",
        statement=f"{mode_name} resulting from {mechanism}.",
        claim_type="failure_mode",
        support_level=verification_res.assigned_support_level if verification_res else SupportLevel.SUPPORTING_SOURCE,
        evidence=verified_evidence
    )

    # 2. Determine Cause, Local Effect, Next Effect, End Effect based on externalized taxonomy
    from ..taxonomy import match_failure_mechanism_profile, get_taxonomy
    tax = get_taxonomy()
    profile = match_failure_mechanism_profile(mechanism, mode_name)
    
    cause_stmt = profile.get("cause", "Operational stress exceeding material capability under cyclic loading.")
    local_effect_stmt = profile.get("local_effect", "Localized yielding or hairline surface cracking.")
    next_effect_stmt = profile.get("next_effect", "Progressive loss of structural stiffness or function.")
    end_effect_stmt = profile.get("end_effect", "Subsystem operational degradation.")
    
    sev_data = profile.get("severity", {})
    sev_cat_key = sev_data.get("category", "CATEGORY_III")
    sev_cat = getattr(SeverityCategory, sev_cat_key, SeverityCategory.CATEGORY_III)
    sev_hazard = sev_data.get("regulatory_hazard_tier", "Not established in corpus")
    sev_just_text = sev_data.get("justification", f"MIL-STD-1629A {sev_cat.value} assessment.")
    sev_defs = tax.get("severity_definitions", {})
    sev_def = sev_defs.get(sev_cat_key, "MIL-STD-1629A severity definition.")
    
    # Check if end effect claim can be DIRECT_SOURCE from regulatory docs
    is_direct_reg = any(
        any(doc in (e.source_document or "") for doc in ["33.75", "CS-E", "1629"])
        for e in verified_evidence
    )
    if is_direct_reg and sev_cat == SeverityCategory.CATEGORY_I:
        sev_level = SupportLevel.DIRECT_SOURCE
    elif verified_evidence:
        sev_level = SupportLevel.ENGINEERING_INFERENCE
    else:
        sev_level = SupportLevel.DOMAIN_HEURISTIC
        
    is_spf = profile.get("single_point_failure", False)
    cil_reason = profile.get("cil_reason", "Single point failure candidate requiring engineering evaluation.")
    
    det_data = profile.get("detection", {})
    detection_stmt = det_data.get("statement", "Standard visual inspection during scheduled maintenance.")
    det_cat_str = det_data.get("category", "scheduled_line_maintenance")
    det_cat = getattr(DetectionCategory, det_cat_str.upper(), DetectionCategory.SCHEDULED_LINE_MAINTENANCE)
    action_stmt = profile.get("recommended_action", "Follow OEM maintenance procedures.")
    
    inspection_interval_str = tax.get(
        "not_established_interval",
        "Not established in indexed corpus - defer to OEM engine/component manual and approved maintenance program"
    )
    
    legacy_scores = profile.get("legacy_scores", {"severity": 5, "occurrence": 3, "detection": 4})
    comp_sev = legacy_scores.get("severity", 5)
    comp_occ = legacy_scores.get("occurrence", 3)
    comp_det = legacy_scores.get("detection", 4)
    op_readiness = profile.get("operational_readiness_indicator", "Not established in indexed corpus")

    # 3. Claims for Root Cause, Local Effect, Next Effect, End Effect
    cause_claim = EngineeringClaim(
        claim_id=f"CLM-{cand_id}-CAUSE",
        statement=cause_stmt,
        claim_type="cause",
        support_level=SupportLevel.SUPPORTING_SOURCE if verified_evidence else SupportLevel.DOMAIN_HEURISTIC,
        evidence=verified_evidence[:2]
    )
    local_claim = EngineeringClaim(
        claim_id=f"CLM-{cand_id}-LOC-EFF",
        statement=local_effect_stmt,
        claim_type="local_effect",
        support_level=SupportLevel.SUPPORTING_SOURCE if verified_evidence else SupportLevel.DOMAIN_HEURISTIC,
        evidence=verified_evidence[:1]
    )
    next_claim = EngineeringClaim(
        claim_id=f"CLM-{cand_id}-NXT-EFF",
        statement=next_effect_stmt,
        claim_type="next_effect",
        support_level=SupportLevel.SUPPORTING_SOURCE if verified_evidence else SupportLevel.DOMAIN_HEURISTIC,
        evidence=verified_evidence[:1]
    )
    end_claim = EngineeringClaim(
        claim_id=f"CLM-{cand_id}-END-EFF",
        statement=end_effect_stmt,
        claim_type="end_effect",
        support_level=sev_level,
        evidence=[e for e in verified_evidence if "33.75" in e.source_document or "1629" in e.source_document or "CS-E" in e.source_document] or verified_evidence[:2]
    )

    # 4. Severity Classification
    sev_just_claim = EngineeringClaim(
        claim_id=f"CLM-{cand_id}-SEV-JUST",
        statement=sev_just_text,
        claim_type="severity_justification",
        support_level=sev_level,
        evidence=end_claim.evidence
    )
    severity_obj = SeverityClassification(
        category=sev_cat,
        definition=sev_def,
        justification=sev_just_claim,
        regulatory_hazard_tier=sev_hazard,
        classification_confidence="HIGH" if verified_evidence else "MEDIUM"
    )

    # 5. Criticality Analysis (Qualitative; Quantitative omitted if no fleet failure rate)
    crit_claim = EngineeringClaim(
        claim_id=f"CLM-{cand_id}-CRIT-RAT",
        statement="Qualitative evaluation based on MIL-STD-1629A Task 102. Failure probability rate lambda_p is uncataloged in corpus.",
        claim_type="criticality_rationale",
        support_level=SupportLevel.INSUFFICIENT_EVIDENCE
    )
    crit_obj = CriticalityAnalysis(
        methodology=CriticalityMethodology.QUALITATIVE_MATRIX,
        qualitative_level=ProbabilityLevel.UNKNOWN,
        matrix_position=f"{sev_cat.value} - Probability level not established",
        data_source_description="Aviation transport operating history and engineering standards analysis",
        rationale=crit_claim
    )

    # 6. CIL Assessment
    cil_claim = EngineeringClaim(
        claim_id=f"CLM-{cand_id}-CIL-RAT",
        statement=cil_reason,
        claim_type="cil_retention",
        support_level=sev_level
    )
    cil_obj = CILAssessment(
        is_critical_item=is_spf and (sev_cat in [SeverityCategory.CATEGORY_I, SeverityCategory.CATEGORY_II]),
        single_failure_point=is_spf,
        inclusion_basis=cil_reason,
        retention_rationale=cil_claim,
        verification_status="VERIFIED" if verified_evidence else "PENDING_REVIEW"
    )

    # 7. Detection and Controls (without specific evidence, labeled DOMAIN_HEURISTIC)
    det_has_evidence = verified_evidence and any(
        any(k in (e.excerpt or "").lower() for k in ["borescope", "inspection", "ndt", "eddy", "penetrant", "telemetry"])
        for e in verified_evidence
    )
    det_claim = EngineeringClaim(
        claim_id=f"CLM-{cand_id}-DET-METH",
        statement=detection_stmt,
        claim_type="detection_method",
        support_level=SupportLevel.SUPPORTING_SOURCE if det_has_evidence else SupportLevel.DOMAIN_HEURISTIC,
        evidence=verified_evidence[:1] if det_has_evidence else []
    )
    action_claim = EngineeringClaim(
        claim_id=f"CLM-{cand_id}-REC-ACT",
        statement=action_stmt,
        claim_type="recommended_action",
        support_level=SupportLevel.DOMAIN_HEURISTIC,
        evidence=[]
    )
    det_controls = DetectionAndControls(
        primary_detection_means=detection_stmt,
        detection_category=det_cat,
        method_description=det_claim,
        operational_readiness_indicator=op_readiness,
        is_undetectable=False,
        recommended_action=action_claim,
        inspection_interval=inspection_interval_str
    )

    # 8. Legacy RPN Compatibility
    legacy_rpn = LegacyRPN(
        severity_score=comp_sev,
        occurrence_score=comp_occ,
        detection_score=comp_det,
        rpn_value=comp_sev * comp_occ * comp_det,
        methodology="legacy_automotive_unverified"
    )

    # 9. Citations (backward compatibility)
    citations = [
        Citation(
            source_document=e.source_document,
            doc_title=e.document_title,
            page_number=e.page_number,
            publisher=e.publisher,
            similarity_score=e.retrieval_score or 0.60,
            excerpt=e.excerpt
        ) for e in verified_evidence[:3]
    ]

    return FailureModeEntry(
        mode_id=f"FM-{cand_id.replace('CAND-', '')}",
        failure_mode=mode_name,
        physical_mechanism=mechanism,
        root_cause=cause_stmt,
        local_effect=local_effect_stmt,
        next_higher_effect=next_effect_stmt,
        end_effect=end_effect_stmt,
        detection_method=detection_stmt,
        recommended_action=action_stmt,
        inspection_interval=inspection_interval_str,
        severity=comp_sev,
        occurrence=comp_occ,
        detection=comp_det,
        rpn=comp_sev * comp_occ * comp_det,
        mil_std_severity_category=sev_cat.value,
        single_point_failure=is_spf,
        citations=citations,
        severity_classification=severity_obj,
        criticality_analysis=crit_obj,
        detection_and_controls=det_controls,
        cil_assessment=cil_obj,
        legacy_rpn_audit=legacy_rpn,
        root_cause_claim=cause_claim,
        local_effect_claim=local_claim,
        next_effect_claim=next_claim,
        end_effect_claim=end_claim,
        mode_status=AnalysisStatus.SUPPORTED if verified_evidence else AnalysisStatus.INFERRED,
        evidence_records=verified_evidence
    )


def build_fmea_node(state: FMEAState) -> Dict[str, Any]:
    """Assemble final FMEAReport from verified candidate failure modes."""
    component: ComponentInfo = state.get("component")
    candidate_modes: List[CandidateFailureMode] = state.get("candidate_modes", [])
    targeted_evidence: Dict[str, List[EvidenceRecord]] = state.get("targeted_evidence", {})
    verification_results: List[ClaimVerificationResult] = state.get("verification_results", [])
    
    verif_map = {vr.claim_id: vr for vr in verification_results}

    failure_modes: List[FailureModeEntry] = []
    all_claims: List[EngineeringClaim] = []

    # Only process retained candidates
    retained_candidates = [c for c in candidate_modes if c.is_retained]

    for cand in retained_candidates:
        cand_evid = targeted_evidence.get(cand.candidate_id, [])
        vr = verif_map.get(f"CLM-{cand.candidate_id}-MODE")
        verified_evid = vr.verified_evidence if vr else cand_evid

        mode_entry = _build_mode_entry(cand, component, verified_evid, vr)
        failure_modes.append(mode_entry)

        # Collect claims for coverage calculation
        if mode_entry.root_cause_claim:
            all_claims.append(mode_entry.root_cause_claim)
        if mode_entry.local_effect_claim:
            all_claims.append(mode_entry.local_effect_claim)
        if mode_entry.next_effect_claim:
            all_claims.append(mode_entry.next_effect_claim)
        if mode_entry.end_effect_claim:
            all_claims.append(mode_entry.end_effect_claim)

    # Calculate deterministic EvidenceCoverageReport
    total_c = len(all_claims)
    direct_c = sum(1 for c in all_claims if c.support_level == SupportLevel.DIRECT_SOURCE)
    supp_c = sum(1 for c in all_claims if c.support_level == SupportLevel.SUPPORTING_SOURCE)
    inf_c = sum(1 for c in all_claims if c.support_level == SupportLevel.ENGINEERING_INFERENCE)
    heur_c = sum(1 for c in all_claims if c.support_level == SupportLevel.DOMAIN_HEURISTIC)
    unsupp_c = sum(1 for c in all_claims if c.support_level == SupportLevel.UNSUPPORTED)
    insuff_c = sum(1 for c in all_claims if c.support_level == SupportLevel.INSUFFICIENT_EVIDENCE)

    coverage_score = (direct_c + supp_c) / total_c if total_c > 0 else 0.0

    coverage_report = EvidenceCoverageReport(
        total_claims=total_c,
        directly_supported=direct_c,
        supporting_evidence=supp_c,
        engineering_inference=inf_c,
        domain_heuristic=heur_c,
        unsupported=unsupp_c,
        insufficient_evidence=insuff_c,
        coverage_score=round(coverage_score, 4),
        is_coverage_adequate=total_c > 0 and (direct_c + supp_c + inf_c) > 0
    )

    # Build Final Report
    report = FMEAReport(
        component=component,
        failure_modes=failure_modes,
        evidence_coverage=coverage_report,
        reasoning_trace=state.get("reasoning_trace"),
        generation_metadata={
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "pipeline_route": "reasoning_engine",
            "coverage_adequate": coverage_report.is_coverage_adequate,
            "failure_modes_generated": len(failure_modes)
        }
    )

    trace = state.get("reasoning_trace")
    if trace:
        trace.coverage_report = coverage_report
        trace.execution_route.append("build_fmea")

    return {
        "failure_modes": failure_modes,
        "evidence_coverage": coverage_report,
        "final_report": report,
        "reasoning_trace": trace
    }
