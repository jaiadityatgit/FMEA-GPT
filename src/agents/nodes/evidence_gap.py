"""Node: Evidence-Gap Branch for Inadequate Corpus Coverage.

Activated when:
1. Component classification is INSUFFICIENT_EVIDENCE or UNKNOWN.
2. Retrieved passages contain zero relevant engineering content.
3. Component is outside the civil aerospace turbomachinery / flight-control corpus.

Strict Rule:
Does NOT manufacture aerospace failure modes or invent evidence.
Produces an explicit EvidenceCoverageReport and honest FMEAReport declaring the gap.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List
from ..state import (
    FMEAState,
    FMEAReport,
    ComponentInfo,
    ValidationReport,
    ValidationIssue,
    EvidenceCoverageReport,
    AnalysisStatus,
    EngineeringAssumption
)


def evidence_gap_node(state: FMEAState) -> Dict[str, Any]:
    """Build an evidence-gap analysis package when corpus coverage is insufficient."""
    component: ComponentInfo = state.get("component")
    if not component:
        component = ComponentInfo(
            component_id="COMP-UNKNOWN-001",
            component_name=state.get("component_input", "Unknown Component"),
            system="Unknown / Out of Scope",
            subsystem="Uncataloged",
            regulatory_class="Unclassified (Corpus Lacks Documentation)",
            operating_environment="Unknown operating conditions.",
            primary_function="Function cannot be reliably established from available regulatory corpus.",
            analysis_status=AnalysisStatus.INSUFFICIENT_EVIDENCE
        )

    # 1. Deterministic zero-coverage report
    coverage = EvidenceCoverageReport(
        total_claims=1,
        directly_supported=0,
        supporting_evidence=0,
        engineering_inference=0,
        domain_heuristic=0,
        unsupported=0,
        insufficient_evidence=1,
        coverage_score=0.0,
        is_coverage_adequate=False
    )

    # 2. Honest validation report flagging the gap
    validation = ValidationReport(
        is_compliant=False,
        compliance_standard="MIL-STD-1629A / Corpus Evidence Audit",
        total_modes_evaluated=0,
        single_point_failures_count=0,
        critical_items_count=0,
        unverified_claims_count=1,
        issues=[
            ValidationIssue(
                severity_level="ERROR",
                rule="EVIDENCE_GROUNDING_MANDATE",
                description=(
                    f"Component '{component.component_name}' lacks technical baseline documentation "
                    f"in the ingested aerospace corpus. FMEA generation halted to prevent hallucination."
                ),
                resolution_recommendation="Ingest OEM engineering manuals, CS-25/FAR 25/33 standards, or component specification sheets."
            )
        ],
        compliance_summary=(
            f"Evidence-Gap Branch Executed: Corpus lacks sufficient engineering literature to analyze '{component.component_name}'. "
            f"Zero failure modes manufactured."
        )
    )

    # 3. Global assumption explaining the gap
    assumptions = [
        EngineeringAssumption(
            assumption_id="ASSUMP-GAP-001",
            statement=(
                f"The available local corpus (MIL-STD-1629A, FAA AC 33.75-1A, FAA AC 25.1309-1B, "
                f"EASA CS-E, NASA-STD-8729.1A) does not contain design specifications or failure "
                f"physics for '{component.component_name}'. No speculative failure modes generated."
            ),
            engineering_rationale="Anti-hallucination constraint strictly enforced per Phase 5B architecture.",
            risk_impact="No safety-critical propulsion authority can be assumed without OEM engineering data.",
            validation_required=True
        )
    ]

    # 4. Final Report Package
    report = FMEAReport(
        component=component,
        failure_modes=[],
        global_assumptions=assumptions,
        validation=validation,
        evidence_coverage=coverage,
        reasoning_trace=state.get("reasoning_trace"),
        generation_metadata={
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "pipeline_route": "evidence_gap_branch",
            "coverage_adequate": False,
            "failure_modes_generated": 0
        }
    )

    trace = state.get("reasoning_trace")
    if trace:
        trace.coverage_report = coverage
        trace.execution_route.append("evidence_gap")

    return {
        "failure_modes": [],
        "validation": validation,
        "evidence_coverage": coverage,
        "final_report": report,
        "branch_taken": "evidence_gap",
        "reasoning_trace": trace
    }
