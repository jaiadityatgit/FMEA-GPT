"""Taxonomy loader and matching logic for FMEA-GPT.

Externalizes engineering taxonomy, ATA chapters, component profiles,
and failure mechanism narrative templates from code to data/metadata/subsystem_taxonomy.json.
Every engineering statement carries an explicit provenance status.
"""
from functools import lru_cache
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .state import (
    ComponentInfo,
    EngineeringClaim,
    EvidenceRecord,
    SupportLevel,
    AnalysisStatus,
)

TAXONOMY_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "metadata" / "subsystem_taxonomy.json"


@lru_cache(maxsize=1)
def get_taxonomy() -> Dict[str, Any]:
    """Load and cache the externalized subsystem taxonomy."""
    with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def classify_component_from_taxonomy(text: str, context: Optional[Dict[str, Any]] = None) -> ComponentInfo:
    """Classify a component into ComponentInfo using externalized taxonomy rules."""
    ctx = context or {}
    comp_target = ctx.get("component_input", "")
    if not comp_target:
        for line in text.splitlines():
            line_stripped = line.strip()
            if line_stripped.lower().startswith("component:"):
                comp_target = line_stripped.split(":", 1)[1].strip()
                break
    if not comp_target:
        comp_target = text.strip()
    comp_lower = comp_target.lower()
    part_num = ctx.get("part_number")

    tax = get_taxonomy()
    profiles = tax.get("component_profiles", [])
    default_pn = tax.get("default_part_number", {}).get("value", "UNSPECIFIED")

    # Match profile in order
    selected_profile = None
    for p in profiles:
        match_any = p.get("match_any", [])
        if not match_any:  # Fallback profile
            selected_profile = p
            break
        if any(term in comp_lower for term in match_any):
            selected_profile = p
            break

    if not selected_profile:
        selected_profile = profiles[-1]

    # Resolve subsystem rules if any
    subsystem = selected_profile.get("default_subsystem", "General Assembly")
    for s_rule in selected_profile.get("subsystem_rules", []):
        if any(term in comp_lower for term in s_rule.get("match_any", [])):
            subsystem = s_rule.get("subsystem", subsystem)
            break

    # Preserve user's component name
    comp_name = comp_target or "Unclassified Component"

    # Build classification claim
    claim_dict = selected_profile.get("classification_claim", {})
    ev_records = []
    for ev_data in claim_dict.get("evidence", []):
        ev_records.append(
            EvidenceRecord(
                evidence_id=ev_data.get("evidence_id", "EVID-CLASS-001"),
                source_document=ev_data.get("source_document", ""),
                document_title=ev_data.get("document_title", ""),
                publisher=ev_data.get("publisher", ""),
                page_number=int(ev_data.get("page_number", 1)),
                section=ev_data.get("section"),
                excerpt=ev_data.get("excerpt", ""),
                support_level=SupportLevel(ev_data.get("support_level", "supporting_source")),
                evidence_type=ev_data.get("evidence_type", "regulatory_requirement"),
            )
        )

    stmt_template = claim_dict.get("statement", "")
    stmt = stmt_template.format(component=comp_target[:60]) if "{component}" in stmt_template else stmt_template

    basis_claim = EngineeringClaim(
        claim_id=claim_dict.get("claim_id", "CLM-COMP-CLASS"),
        statement=stmt,
        claim_type="classification",
        support_level=SupportLevel(claim_dict.get("support_level", "domain_heuristic")),
        evidence=ev_records,
        verification_notes=claim_dict.get("verification_notes"),
    )

    sys_obj = selected_profile.get("system", {})
    sys_str = sys_obj.get("text", "General Aerospace Equipment") if isinstance(sys_obj, dict) else str(sys_obj)

    reg_obj = selected_profile.get("regulatory_class", {})
    reg_str = reg_obj.get("text", "Standard Airborne Equipment") if isinstance(reg_obj, dict) else str(reg_obj)

    op_obj = selected_profile.get("operating_environment", {})
    op_str = op_obj.get("text", "Operating envelope not established in indexed corpus.") if isinstance(op_obj, dict) else str(op_obj)

    fn_obj = selected_profile.get("primary_function", {})
    fn_str = fn_obj.get("text", "Function not established in indexed corpus.") if isinstance(fn_obj, dict) else str(fn_obj)

    status_str = selected_profile.get("analysis_status", "insufficient_evidence")
    try:
        status_enum = AnalysisStatus(status_str)
    except Exception:
        status_enum = AnalysisStatus.INSUFFICIENT_EVIDENCE

    return ComponentInfo(
        component_id=selected_profile.get("component_id", "COMP-001"),
        component_name=comp_name,
        part_number=part_num or default_pn,
        system=sys_str,
        subsystem=subsystem,
        regulatory_class=reg_str,
        operating_environment=op_str,
        primary_function=fn_str,
        analysis_scope=selected_profile.get("analysis_scope", "Indenture Level 3"),
        classification_basis=basis_claim,
        classification_confidence=selected_profile.get("classification_confidence", "LOW"),
        analysis_status=status_enum,
    )


def match_failure_mechanism_profile(mechanism: str, mode_name: str) -> Dict[str, Any]:
    """Match a candidate's mechanism and mode name to an externalized narrative profile."""
    tax = get_taxonomy()
    profiles = tax.get("failure_mechanism_profiles", [])
    mech_lower = mechanism.lower()
    mode_lower = mode_name.lower()

    for p in profiles:
        m_mechs = p.get("match_mechanism", [])
        m_modes = p.get("match_mode", [])
        if not m_mechs and not m_modes:
            # Fallback generic profile
            return p
        match_mech = any(term in mech_lower for term in m_mechs) if m_mechs else False
        match_mode = any(term in mode_lower for term in m_modes) if m_modes else False
        if match_mech or match_mode:
            return p

    # Fallback to last profile
    return profiles[-1] if profiles else {}
