"""Critical Items List (CIL) and Single Point Failure (SPF) Exporter per NASA-STD-8729.1A and MIL-STD-1629A."""
from typing import List
from ..state import FMEAReport, FailureModeEntry, SeverityCategory


def format_critical_items_list_markdown(report: FMEAReport) -> str:
    """Format Critical Items List (CIL) highlighting single-point failures and Cat I/II modes per MIL-STD-1629A / NASA-STD-8729.1A."""
    comp = report.component
    
    # Standard-grounded CIL filter: Category I, Category II, or Single Point Failure
    # Arbitrary threshold 'rpn >= 100' has been removed
    critical_modes: List[FailureModeEntry] = []
    for fm in report.failure_modes:
        is_cil = False
        if fm.cil_assessment and fm.cil_assessment.is_critical_item:
            is_cil = True
        elif fm.single_point_failure:
            is_cil = True
        elif fm.severity_classification and fm.severity_classification.category in [
            SeverityCategory.CATEGORY_I, SeverityCategory.CATEGORY_II
        ]:
            is_cil = True
        elif fm.mil_std_severity_category.startswith("Category I") or fm.mil_std_severity_category.startswith("Category II"):
            is_cil = True

        if is_cil:
            critical_modes.append(fm)

    md = []
    md.append("# CRITICAL ITEMS LIST (CIL) & SINGLE POINT FAILURE REPORT")
    md.append("**Governing Standard:** NASA-STD-8729.1A § 13 / MIL-STD-1629A § 4.5.2.1  ")
    md.append(f"**Component:** {comp.component_name} (P/N: {comp.part_number})  ")
    md.append(f"**Airworthiness Status:** {comp.regulatory_class}  ")
    md.append(f"**Total Critical Items Flagged:** {len(critical_modes)}  ")
    md.append("\n---\n")

    if not critical_modes:
        md.append("No critical items or Single Point Failures met CIL inclusion criteria.")
        return "\n".join(md)

    for idx, cm in enumerate(critical_modes, start=1):
        is_spf = cm.single_point_failure or (cm.cil_assessment and cm.cil_assessment.single_failure_point)
        spf_badge = "[SINGLE POINT FAILURE (SPF)]" if is_spf else "[CATEGORY I/II CRITICAL ITEM]"
        
        inclusion_basis = (
            cm.cil_assessment.inclusion_basis if cm.cil_assessment and cm.cil_assessment.inclusion_basis
            else ("Single Point Failure" if is_spf else f"{cm.mil_std_severity_category}")
        )
        
        retention = (
            cm.cil_assessment.retention_rationale.statement if cm.cil_assessment and cm.cil_assessment.retention_rationale
            else cm.recommended_action
        )

        md.append(f"## {idx}. {cm.mode_id} {spf_badge}: {cm.failure_mode}")
        if cm.physical_mechanism:
            md.append(f"- **Physical Failure Mechanism:** {cm.physical_mechanism}")
        md.append(f"- **MIL-STD-1629A Severity:** {cm.mil_std_severity_category}")
        if cm.criticality_analysis and cm.criticality_analysis.matrix_position:
            md.append(f"- **Task 102 Criticality Matrix:** {cm.criticality_analysis.matrix_position}")
        md.append(f"- **CIL Inclusion Basis:** {inclusion_basis}")
        md.append(f"- **Root Cause:** {cm.root_cause}")
        md.append(f"- **End Aircraft Effect:** {cm.end_effect}")
        md.append(f"- **Detection Method:** {cm.detection_method}")
        md.append(f"- **Retention Rationale & Action:** {retention}")
        md.append(f"- **Inspection Interval:** {cm.inspection_interval}")
        if cm.legacy_rpn_audit:
            md.append(f"- **Legacy Automotive Metric:** RPN={cm.legacy_rpn_audit.rpn_value} (Quarantined)")
        md.append(f"- **Airworthiness Citation:** {cm.compliance_reference}")
        md.append("")

    return "\n".join(md)
