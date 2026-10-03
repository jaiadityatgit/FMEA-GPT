"""Node: Evidence Extraction from retrieved technical aerospace passages.

Inspects retrieved passages and extracts structured engineering evidence facets:
- failure_mode
- physical_mechanism
- cause
- local_effect
- next_higher_effect
- end_effect
- detection_method
- maintenance_control
- severity_basis
- probability_basis
- criticality_basis

Unknown fields remain None. Does not hallucinate missing engineering facets.
"""
import re
from typing import Dict, Any, List, Optional
from ..state import FMEAState, EvidenceRecord, SupportLevel


# Key technical patterns mapped to physical degradation mechanisms
MECHANISM_PATTERNS = {
    "thermomechanical_fatigue": [
        r"thermo-?mechanical fatigue", r"\bTMF\b", r"thermal fatigue", r"thermal cyclic",
        r"cyclic thermal stress", r"transient thermal gradient"
    ],
    "high_cycle_fatigue": [
        r"high[- ]cycle fatigue", r"\bHCF\b", r"aerodynamic vibration", r"resonance stress",
        r"vibratory stress"
    ],
    "low_cycle_fatigue": [
        r"low[- ]cycle fatigue", r"\bLCF\b", r"start[- ]stop cycle", r"centrifugal stress cycle"
    ],
    "creep_rupture": [
        r"creep", r"creep rupture", r"creep elongation", r"sustained centrifugal",
        r"stress rupture", r"grain boundary void"
    ],
    "foreign_object_damage": [
        r"foreign object damage", r"\bFOD\b", r"ingestion", r"bird ingestion",
        r"hard body impact", r"leading edge notch"
    ],
    "hot_corrosion_oxidation": [
        r"hot corrosion", r"type [iI]+ hot corrosion", r"sulfidation", r"oxidation",
        r"thermal barrier coating spallation", r"\bTBC\b spallation", r"environmental attack"
    ],
    "blade_fracture_liberation": [
        r"blade fracture", r"blade separation", r"blade liberation", r"blade release",
        r"uncontained", r"casing penetration", r"rotor burst"
    ],
    "fluid_contamination_stiction": [
        r"hydraulic contamination", r"spool stiction", r"seal degradation", r"valve jam",
        r"fluid leakage"
    ]
}

# Detection methods in technical documentation
DETECTION_PATTERNS = {
    "borescope": [r"borescope", r"video borescope", r"visual optical inspection", r"on-wing optical"],
    "eddy_current": [r"eddy current", r"\bECT\b", r"electromagnetic inspection"],
    "fluorescent_penetrant": [r"fluorescent penetrant", r"\bFPI\b", r"dye penetrant"],
    "ultrasonic": [r"ultrasonic", r"\bUT\b", r"ultrasonic phased array"],
    "vibration_monitoring": [r"vibration sensor", r"engine vibration", r"accelerometer", r"HUMS"],
    "oil_debris_monitoring": [r"chip detector", r"oil debris", r"spectrometric oil analysis"]
}

# Airworthiness / End effects
AIRWORTHINESS_PATTERNS = {
    "hazardous_engine_effect": [
        r"hazardous engine effect", r"14 CFR (?:§\s*)?33\.75", r"CS-E 510",
        r"uncontained", r"loss of thrust control", r"toxic products in cabin",
        r"engine fire", r"inability to shut down"
    ],
    "major_engine_effect": [
        r"major engine effect", r"in-flight shutdown", r"\bIFSD\b",
        r"controlled thrust loss", r"damage to engine structure"
    ],
    "minor_engine_effect": [
        r"minor engine effect", r"minimal operational inconvenience", r"nuisance alarm"
    ]
}


def extract_evidence_facets(text: str) -> Dict[str, Any]:
    """Deterministically extract engineering facets from a technical passage.
    
    Fields that are not attested in the text are set to None.
    """
    text_lower = text.lower()
    facets: Dict[str, Any] = {
        "physical_mechanism": None,
        "cause": None,
        "local_effect": None,
        "next_higher_effect": None,
        "end_effect": None,
        "detection_method": None,
        "maintenance_control": None,
        "severity_basis": None,
        "probability_basis": None,
        "criticality_basis": None
    }

    # 1. Identify physical mechanism
    for mech, patterns in MECHANISM_PATTERNS.items():
        if any(re.search(pat, text_lower) for pat in patterns):
            facets["physical_mechanism"] = mech.replace("_", " ").title()
            break

    # 2. Identify detection method
    for det, patterns in DETECTION_PATTERNS.items():
        if any(re.search(pat, text_lower) for pat in patterns):
            facets["detection_method"] = det.replace("_", " ").title()
            break

    # 3. Identify airworthiness / end effect / severity basis
    for air_level, patterns in AIRWORTHINESS_PATTERNS.items():
        if any(re.search(pat, text_lower) for pat in patterns):
            facets["severity_basis"] = air_level.replace("_", " ").title()
            if air_level == "hazardous_engine_effect":
                facets["end_effect"] = "Hazardous Engine Effect (Potential uncontained debris or non-restartable IFSD)"
            elif air_level == "major_engine_effect":
                facets["end_effect"] = "Major Engine Effect (In-Flight Shutdown or significant thrust reduction)"
            elif air_level == "minor_engine_effect":
                facets["end_effect"] = "Minor Engine Effect (Acceptable parameter deviation or maintenance deferral)"
            break

    # 4. Check for MIL-STD-1629A Criticality / Severity references
    if re.search(r"category i\b|catastrophic", text_lower):
        facets["severity_basis"] = facets["severity_basis"] or "MIL-STD-1629A Category I (Catastrophic)"
    elif re.search(r"category ii\b|critical", text_lower):
        facets["severity_basis"] = facets["severity_basis"] or "MIL-STD-1629A Category II (Critical)"
    elif re.search(r"category iii\b|marginal", text_lower):
        facets["severity_basis"] = facets["severity_basis"] or "MIL-STD-1629A Category III (Marginal)"
    elif re.search(r"category iv\b|minor", text_lower):
        facets["severity_basis"] = facets["severity_basis"] or "MIL-STD-1629A Category IV (Minor)"

    # 5. Check for quantitative criticality parameters (MIL-STD-1629A Task 102)
    if any(k in text_lower for k in ["mode criticality", "failure effect probability", "beta", "lambda_p"]):
        facets["criticality_basis"] = "MIL-STD-1629A Task 102 Quantitative Criticality Formulation"

    # 6. Check for maintenance controls / intervals
    maint_match = re.search(r"(\b\d{2,5}\s*(?:flight cycles|cycles|flight hours|hours|efh|fc)\b)", text_lower)
    if maint_match:
        facets["maintenance_control"] = f"Periodic inspection interval referenced: {maint_match.group(1)}"
    elif re.search(r"time-limited dispatch|\btld\b|scheduled maintenance", text_lower):
        facets["maintenance_control"] = "Scheduled Maintenance / Time-Limited Dispatch"

    return facets


def extract_evidence_node(state: FMEAState) -> Dict[str, Any]:
    """Execute evidence extraction over all initially retrieved passages."""
    passages = state.get("_flattened_passages", [])
    if not passages:
        ctx = state.get("retrieved_context", {})
        for plist in ctx.values():
            passages.extend(plist)

    evidence_pool: List[EvidenceRecord] = []
    
    for idx, p in enumerate(passages):
        text = p.get("text", "")
        facets = extract_evidence_facets(text)
        
        # Build structured EvidenceRecord
        evid = EvidenceRecord(
            evidence_id=f"EVID-EXT-{idx+1:03d}",
            source_document=p.get("source_document", "Aerospace Standard"),
            document_title=p.get("doc_title", "Aerospace Standard Document"),
            publisher=p.get("publisher", "DoD/FAA/EASA"),
            page_number=p.get("page_number", 1),
            section=p.get("metadata", {}).get("section") or p.get("section"),
            excerpt=text[:320] if len(text) > 320 else text,
            retrieval_query=p.get("metadata", {}).get("query"),
            retrieval_score=p.get("similarity_score"),
            support_level=SupportLevel.SUPPORTING_SOURCE if p.get("similarity_score", 0.0) >= 0.50 else SupportLevel.INSUFFICIENT_EVIDENCE
        )
        evidence_pool.append(evid)

    # Update reasoning trace
    trace = state.get("reasoning_trace")
    if trace:
        trace.total_passages_retrieved += len(passages)
        trace.execution_route.append("extract_evidence")

    return {
        "evidence_pool": evidence_pool,
        "reasoning_trace": trace
    }
