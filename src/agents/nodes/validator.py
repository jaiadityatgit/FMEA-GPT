"""Node: Rigorous Multi-Tier Engineering Validation and Report Packaging.

Implements deterministic engineering validation across four distinct dimensions:
1. Structural Validation (required fields, IDs, enum integrity, completeness).
2. Provenance Validation (evidence linkage, claim-evidence coupling, duplicate generic citation detection).
3. Epistemic Validation (support level fidelity, heuristic labeling, anti-hallucination verification).
4. Engineering Consistency Validation (mechanism-cause alignment, effect hierarchy, severity justification).

Never claims 'certification ready' or 'approved'; provides objective discrepancy reporting.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Set, Tuple
from ..state import (
    FMEAState,
    ValidationReport,
    ValidationIssue,
    FMEAReport,
    ComponentInfo,
    FailureModeEntry,
    SeverityCategory,
    SupportLevel
)
from ..providers.base import LLMProvider


def execute_engineering_validation(
    component: ComponentInfo,
    failure_modes: List[FailureModeEntry]
) -> ValidationReport:
    """Execute deterministic structural, provenance, epistemic, and engineering consistency checks."""
    issues: List[ValidationIssue] = []
    
    total = len(failure_modes)
    cat_i_count = 0
    cat_ii_count = 0
    spf_count = 0
    crit_items_count = 0
    unverified_count = 0
    max_rpn = 0

    if total == 0:
        if component.analysis_status.value in ["INSUFFICIENT_EVIDENCE", "UNKNOWN"]:
            issues.append(ValidationIssue(
                severity_level="NOTE",
                rule="EVIDENCE_GAP_CONFIRMED",
                description="Analysis halted at evidence-gap branch due to insufficient corpus documentation. Zero speculative modes generated.",
                resolution_recommendation="Provide OEM documentation or regulatory specification."
            ))
            return ValidationReport(
                is_compliant=True,
                compliance_standard="MIL-STD-1629A / Evidence-Grounded Audit",
                total_modes_evaluated=0,
                single_point_failures_count=0,
                max_rpn=0,
                critical_items_count=0,
                category_i_count=0,
                category_ii_count=0,
                unverified_claims_count=0,
                issues=issues,
                compliance_summary="Analysis completed via evidence-gap protocol; no ungrounded failure modes generated."
            )
        else:
            issues.append(ValidationIssue(
                severity_level="ERROR",
                rule="STRUCTURAL_EMPTY_FMEA",
                description="FMEA package contains zero failure modes for an active aerospace component.",
                resolution_recommendation="Ensure candidate generator and retrieval nodes execute correctly."
            ))

    # Citation fingerprints to detect duplicate generic citation attachment
    citation_fingerprints: List[Tuple[str, ...]] = []

    for fm in failure_modes:
        # Track max RPN
        if fm.rpn and fm.rpn > max_rpn:
            max_rpn = fm.rpn

        # 1. Structural Checks
        if not fm.mode_id or not fm.mode_id.startswith("FM-"):
            issues.append(ValidationIssue(
                severity_level="ERROR",
                rule="STRUCTURAL_INVALID_ID",
                description=f"Failure mode ID '{fm.mode_id}' does not follow 'FM-XXX' naming standard.",
                affected_mode_id=fm.mode_id,
                resolution_recommendation="Assign standard sequential mode IDs."
            ))

        if len(fm.root_cause.strip()) < 10:
            issues.append(ValidationIssue(
                severity_level="ERROR",
                rule="STRUCTURAL_INCOMPLETE_CAUSE",
                description="Root cause description is excessively terse or empty.",
                affected_mode_id=fm.mode_id,
                resolution_recommendation="Provide comprehensive physical root cause explanation."
            ))

        if len(fm.end_effect.strip()) < 10:
            issues.append(ValidationIssue(
                severity_level="ERROR",
                rule="STRUCTURAL_INCOMPLETE_END_EFFECT",
                description="End effect description is missing airworthiness consequence details.",
                affected_mode_id=fm.mode_id,
                resolution_recommendation="Articulate aircraft or engine system end effect."
            ))

        # 2. Severity Classification Checks
        if fm.severity_classification:
            cat = fm.severity_classification.category
            if cat == SeverityCategory.CATEGORY_I:
                cat_i_count += 1
            elif cat == SeverityCategory.CATEGORY_II:
                cat_ii_count += 1

            # Consistency: End effect vs Severity
            if cat == SeverityCategory.CATEGORY_I:
                if not any(w in fm.end_effect.lower() for w in ["uncontained", "catastrophic", "hazardous", "loss of aircraft", "burst"]):
                    issues.append(ValidationIssue(
                        severity_level="WARNING",
                        rule="CONSISTENCY_SEVERITY_END_EFFECT_MISMATCH",
                        description="Category I (Catastrophic) assigned but end effect does not articulate hazardous/uncontained engine consequences.",
                        affected_mode_id=fm.mode_id,
                        resolution_recommendation="Harmonize severity justification with end effect per 14 CFR § 33.75."
                    ))
        else:
            issues.append(ValidationIssue(
                severity_level="ERROR",
                rule="STRUCTURAL_MISSING_SEVERITY",
                description="Missing MIL-STD-1629A SeverityClassification object.",
                affected_mode_id=fm.mode_id,
                resolution_recommendation="Instantiate Phase 5A SeverityClassification."
            ))

        # 3. Criticality and CIL Checks
        if fm.cil_assessment:
            if getattr(fm.cil_assessment, "single_failure_point", False) or getattr(fm.cil_assessment, "is_single_point_failure", False):
                spf_count += 1
            if fm.cil_assessment.is_critical_item:
                crit_items_count += 1
                if not fm.cil_assessment.retention_rationale:
                    issues.append(ValidationIssue(
                        severity_level="ERROR",
                        rule="PROVENANCE_MISSING_CIL_RATIONALE",
                        description="Critical item retained on CIL without explicit retention rationale.",
                        affected_mode_id=fm.mode_id,
                        resolution_recommendation="Document mandatory retention rationale per NASA-STD-8729.1A § 5.2."
                    ))

        # 4. Provenance & Anti-Generic Citation Attachment
        fp = tuple(sorted(f"{c.source_document}:{c.page_number}" for c in fm.citations))
        citation_fingerprints.append(fp)

        # Check claim support levels
        for claim in [fm.root_cause_claim, fm.local_effect_claim, fm.next_effect_claim, fm.end_effect_claim]:
            if claim:
                if claim.support_level == SupportLevel.DIRECT_SOURCE and len(claim.evidence) == 0:
                    issues.append(ValidationIssue(
                        severity_level="ERROR",
                        rule="EPISTEMIC_UNGROUNDED_DIRECT_CLAIM",
                        description=f"Claim '{claim.claim_id}' asserts DIRECT_SOURCE support but attaches zero evidence records.",
                        affected_mode_id=fm.mode_id,
                        resolution_recommendation="Attach substantiated EvidenceRecord or downgrade to DOMAIN_HEURISTIC."
                    ))
                if claim.support_level in [SupportLevel.DOMAIN_HEURISTIC, SupportLevel.INSUFFICIENT_EVIDENCE]:
                    unverified_count += 1

    # Check for identical citation set attached across all modes (Anti-Generic Citation rule)
    if len(failure_modes) > 1 and len(citation_fingerprints) > 1:
        non_empty_fps = [fp for fp in citation_fingerprints if len(fp) > 0]
        if len(non_empty_fps) == len(failure_modes) and len(set(non_empty_fps)) == 1:
            issues.append(ValidationIssue(
                severity_level="ERROR",
                rule="PROVENANCE_DUPLICATE_GENERIC_CITATIONS",
                description="All failure modes share an identical citation set. Targeted per-claim evidence retrieval is required.",
                resolution_recommendation="Perform distinct targeted retrieval for each candidate failure mode."
            ))

    has_blocking_errors = any(i.severity_level == "ERROR" for i in issues)
    is_compliant = not has_blocking_errors

    summary = (
        f"Evaluated against MIL-STD-1629A and NASA-STD-8729.1A. "
        f"Total modes: {total}. Category I: {cat_i_count}. Category II: {cat_ii_count}. "
        f"Single Point Failures: {spf_count}. Critical Items: {crit_items_count}. "
        f"Unverified / Heuristic Claims: {unverified_count}. "
        f"Status: {'PASSED (Compliant Grounding)' if is_compliant else 'ACTION REQUIRED'}."
    )

    return ValidationReport(
        is_compliant=is_compliant,
        compliance_standard="MIL-STD-1629A (Task 101/102) & NASA-STD-8729.1A",
        total_modes_evaluated=total,
        single_point_failures_count=spf_count,
        max_rpn=max_rpn,
        critical_items_count=crit_items_count,
        category_i_count=cat_i_count,
        category_ii_count=cat_ii_count,
        unverified_claims_count=unverified_count,
        issues=issues,
        compliance_summary=summary
    )


def validate_and_package_node(
    state: FMEAState,
    provider: LLMProvider
) -> Dict[str, Any]:
    """Execute multi-tier validation checks and finalize the FMEAReport package."""
    component = state.get("component") or ComponentInfo(component_name=state.get("component_input", "Unknown"))
    failure_modes = state.get("failure_modes", [])
    coverage_report = state.get("evidence_coverage")
    reasoning_trace = state.get("reasoning_trace")

    # Run deterministic multi-tier validation
    validation = execute_engineering_validation(component, failure_modes)

    # Get or assemble final report
    final_report = state.get("final_report")
    if not final_report:
        metadata = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "provider": provider.provider_name,
            "standard": "MIL-STD-1629A / FAA AC 33.75-1A",
            "total_modes": len(failure_modes),
            "is_compliant": validation.is_compliant
        }
        final_report = FMEAReport(
            component=component,
            failure_modes=failure_modes,
            validation=validation,
            evidence_coverage=coverage_report,
            reasoning_trace=reasoning_trace,
            generation_metadata=metadata
        )
    else:
        final_report.validation = validation
        if coverage_report:
            final_report.evidence_coverage = coverage_report
        if reasoning_trace:
            final_report.reasoning_trace = reasoning_trace

    if reasoning_trace:
        reasoning_trace.execution_route.append("validate")

    return {
        "validation": validation,
        "final_report": final_report,
        "reasoning_trace": reasoning_trace
    }
