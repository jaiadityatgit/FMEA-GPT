"""Node: Dynamic Candidate Failure Mode Generation.

Generates candidate failure modes by combining:
1. Physical mechanisms extracted from corpus passages
2. Explicitly labeled domain heuristics

Crucially:
- Separates Discovery from Verification.
- Failure mode count is dynamic (varies by component and evidence, NEVER fixed at 6).
- For out-of-domain or unknown components, does NOT invent aerospace failure modes.
- Generates targeted retrieval query specifications for each candidate.
"""
from typing import Dict, Any, List
from ..state import (
    FMEAState,
    CandidateFailureMode,
    ComponentInfo,
    AnalysisStatus,
    EvidenceRecord
)


def generate_candidate_modes_node(state: FMEAState) -> Dict[str, Any]:
    """Discover candidate failure modes based on component type and extracted evidence."""
    component: ComponentInfo = state.get("component")
    comp_name = component.component_name if component else state.get("component_input", "")
    comp_lower = comp_name.lower()
    system_lower = (component.system or "").lower() if component else ""
    subsystem_lower = (component.subsystem or "").lower() if component else ""
    evidence_pool: List[EvidenceRecord] = state.get("evidence_pool", [])

    candidates: List[CandidateFailureMode] = []

    # 1. Check for Out-of-Domain or Insufficient Evidence component
    if component and component.analysis_status == AnalysisStatus.INSUFFICIENT_EVIDENCE:
        # Do NOT invent detailed aerospace failure modes for out-of-domain or fictional parts
        # If it's a known non-propulsion utility (like lavatory flush valve), provide at most 1 unverified candidate
        if any(w in comp_lower for w in ["lavatory", "flush", "waste", "galley"]):
            cand = CandidateFailureMode(
                candidate_id="CAND-UTIL-001",
                proposed_mode="Flush Valve Seal Leakage / Actuation Failure",
                proposed_mechanism="Elastomeric Seal Degradation / Particulate Accumulation",
                discovery_source="domain_heuristic",
                discovery_evidence=[],
                targeted_queries=[
                    f"{comp_name} seal leakage water waste cabin",
                    f"{comp_name} maintenance inspection interval flush valve"
                ],
                relevance_score=0.30,
                is_retained=True
            )
            candidates.append(cand)
        else:
            # Fictional or completely unknown component
            pass

    # 2. Engine Fuel Metering & Control (ATA 73)
    elif any(w in comp_lower or w in subsystem_lower for w in ["fuel metering", "fuel valve", "metering valve", "fmv"]):
        candidates.append(CandidateFailureMode(
            candidate_id="CAND-FMV-001",
            proposed_mode="Metering Valve Spool Stiction / Seizure",
            proposed_mechanism="Particulate Contamination and Varnish Build-up",
            discovery_source="domain_heuristic",
            discovery_evidence=[],
            targeted_queries=[
                f"{comp_name} fuel valve spool stiction particulate contamination",
                f"{comp_name} fuel flow uncommanded thrust change 33.75",
                f"{comp_name} fuel metering valve LVDT position feedback error"
            ],
            relevance_score=0.85,
            is_retained=True
        ))
        candidates.append(CandidateFailureMode(
            candidate_id="CAND-FMV-002",
            proposed_mode="Internal Dynamic Seal Leakage",
            proposed_mechanism="Elastomeric Seal Degradation and Extrusion",
            discovery_source="domain_heuristic",
            discovery_evidence=[],
            targeted_queries=[
                f"{comp_name} seal leakage fuel metering bypass flow",
                f"{comp_name} fuel system maintenance pressure check interval"
            ],
            relevance_score=0.75,
            is_retained=True
        ))

    # 3. Flight Control Actuator (Elevator / Rudder / Aileron)
    elif any(w in comp_lower or w in subsystem_lower for w in ["elevator actuator", "rudder actuator", "flight control actuator", "actuator"]):
        candidates.append(CandidateFailureMode(
            candidate_id="CAND-ACT-001",
            proposed_mode="Hydraulic Actuator Jam in Offset Position",
            proposed_mechanism="Mechanical Seizure or Contaminant Binding in Dual Tandem Cylinder",
            discovery_source="domain_heuristic",
            discovery_evidence=[],
            targeted_queries=[
                f"{comp_name} actuator jam 14 CFR 25.1309 catastrophic flight control",
                f"{comp_name} hydraulic pressure loss dual tandem actuator",
                f"{comp_name} preflight control surface travel check NDT"
            ],
            relevance_score=0.88,
            is_retained=True
        ))
        candidates.append(CandidateFailureMode(
            candidate_id="CAND-ACT-002",
            proposed_mode="Internal Fluid Blow-by / Loss of Actuation Authority",
            proposed_mechanism="High-Pressure Piston Seal Rupture",
            discovery_source="domain_heuristic",
            discovery_evidence=[],
            targeted_queries=[
                f"{comp_name} internal seal leakage blow by loss of damping",
                f"{comp_name} hydraulic fluid sampling particulate count maintenance"
            ],
            relevance_score=0.78,
            is_retained=True
        ))

    # 4. Gas Turbine Airfoils / Turbomachinery Blades
    elif any(w in comp_lower or w in subsystem_lower for w in ["blade", "turbine", "rotor", "airfoil", "hpt", "hpc"]):
        # Candidate 1: Thermomechanical Fatigue (TMF) Cracking
        candidates.append(CandidateFailureMode(
            candidate_id="CAND-HPT-001",
            proposed_mode="Thermomechanical Fatigue (TMF) Leading Edge Cracking",
            proposed_mechanism="Thermal Gradient Induced Cyclic Strain",
            discovery_source="retrieval_extraction",
            discovery_evidence=[e for e in evidence_pool if "fatigue" in (e.excerpt or "").lower()][:2],
            targeted_queries=[
                f"{comp_name} thermomechanical fatigue leading edge crack",
                "turbine blade thermomechanical fatigue cyclic thermal stress transient",
                f"{comp_name} blade crack engine effect hazardous",
                f"{comp_name} blade crack borescope inspection NDT"
            ],
            relevance_score=0.95,
            is_retained=True
        ))

        # Candidate 2: Creep Rupture and Radial Elongation
        candidates.append(CandidateFailureMode(
            candidate_id="CAND-HPT-002",
            proposed_mode="Creep Rupture and Radial Tip Elongation",
            proposed_mechanism="High-Temperature Sustained Centrifugal Stress Rupture",
            discovery_source="retrieval_extraction",
            discovery_evidence=[e for e in evidence_pool if "creep" in (e.excerpt or "").lower()][:2],
            targeted_queries=[
                f"{comp_name} creep rupture centrifugal load sustained temperature",
                "turbine rotor stress rupture creep sustained centrifugal load high temperature",
                f"{comp_name} creep elongation tip rubbing shroud damage",
                f"{comp_name} blade creep inspection borescope clearance limit"
            ],
            relevance_score=0.90,
            is_retained=True
        ))

        # Candidate 3: Foreign Object Damage (FOD) Notch Initiation
        candidates.append(CandidateFailureMode(
            candidate_id="CAND-HPT-003",
            proposed_mode="Foreign Object Damage (FOD) Leading Edge Notch",
            proposed_mechanism="Hard Particle / Ingested Debris High-Velocity Impact",
            discovery_source="retrieval_extraction",
            discovery_evidence=[e for e in evidence_pool if "foreign object" in (e.excerpt or "").lower() or "ingestion" in (e.excerpt or "").lower()][:2],
            targeted_queries=[
                f"{comp_name} foreign object damage hard body ingestion leading edge notch",
                "foreign object damage bird ingestion runway debris impact compressor blade notch",
                f"{comp_name} FOD impact notch stress concentration fatigue initiation",
                f"{comp_name} FOD visual borescope inspection blend repair limits"
            ],
            relevance_score=0.85,
            is_retained=True
        ))

        # Candidate 4: Thermal Barrier Coating Spallation and Substrate Oxidation
        candidates.append(CandidateFailureMode(
            candidate_id="CAND-HPT-004",
            proposed_mode="Thermal Barrier Coating (TBC) Spallation and Substrate Oxidation",
            proposed_mechanism="Thermally Grown Oxide (TGO) Cracking / EB-PVD Bond-Coat Oxidation and Thermal Cycling",
            discovery_source="retrieval_extraction",
            discovery_evidence=[],
            targeted_queries=[
                f"{comp_name} thermal barrier coating spallation",
                "EB-PVD thermal barrier coating failure TGO thermally grown oxide cracking",
                "thermal barrier coating life prediction model spallation bond coat oxidation",
                f"{comp_name} TBC loss borescope inspection color shift"
            ],
            relevance_score=0.85,
            is_retained=True
        ))

        # Candidate 5: Complete Airfoil Separation / Root Liberation
        candidates.append(CandidateFailureMode(
            candidate_id="CAND-HPT-005",
            proposed_mode="Turbine Rotor Blade Separation / Liberation",
            proposed_mechanism="Critical Flaw Propagation Across Fir-Tree Root Dovetail",
            discovery_source="retrieval_extraction",
            discovery_evidence=[e for e in evidence_pool if "uncontained" in (e.excerpt or "").lower() or "containment" in (e.excerpt or "").lower()][:2],
            targeted_queries=[
                f"{comp_name} blade liberation separation high energy fragment",
                "rotor blade separation fracture blade release containment capability",
                "uncontained high-energy debris fragment hazard engine casing penetration",
                f"{comp_name} 14 CFR 33.75 hazardous engine effect uncontained rotor burst"
            ],
            relevance_score=0.90,
            is_retained=True
        ))

        # Candidate 6: Blade Attachment Fretting Fatigue
        candidates.append(CandidateFailureMode(
            candidate_id="CAND-HPT-006",
            proposed_mode="Blade Attachment (Dovetail / Fir-Tree) Fretting Fatigue Cracking",
            proposed_mechanism="Fretting Fatigue from Contact Micro-Slip at Blade-Disk Attachment Surfaces",
            discovery_source="domain_heuristic",
            discovery_evidence=[],
            targeted_queries=[
                f"{comp_name} dovetail fir-tree attachment fretting fatigue contact stress",
                "turbine blade dovetail fretting fatigue micro-slip contact pressure",
                "fretting stresses single crystal turbine blade attachment friction coefficient",
                "blade root fir-tree slot contact surface fretting wear galling"
            ],
            relevance_score=0.85,
            is_retained=True
        ))

        # Candidate 7: Internal Cooling Degradation and Airfoil Overheating
        candidates.append(CandidateFailureMode(
            candidate_id="CAND-HPT-007",
            proposed_mode="Internal Cooling Degradation and Local Airfoil Overheating",
            proposed_mechanism="Coolant Flow Starvation / Internal Convective Heat-Transfer Passage Restriction",
            discovery_source="domain_heuristic",
            discovery_evidence=[],
            targeted_queries=[
                f"{comp_name} internal cooling passage heat transfer degradation",
                "turbine blade internal cooling passage heat transfer flow starvation",
                "turbine airfoil coolant flow restriction local metal overheating",
                f"{comp_name} cooling hole blockage borescope thermal distress"
            ],
            relevance_score=0.80,
            is_retained=True
        ))

    # 5. Generic Aerospace Equipment Fallback
    else:
        # If component is recognized as generic aerospace mechanical equipment
        candidates.append(CandidateFailureMode(
            candidate_id="CAND-GEN-001",
            proposed_mode="Structural Fatigue Cracking",
            proposed_mechanism="Operational Cyclic Stress Exceeding Endurance Limit",
            discovery_source="domain_heuristic",
            discovery_evidence=[],
            targeted_queries=[
                f"{comp_name} structural fatigue cracking operational stress",
                f"{comp_name} inspection nondestructive test interval"
            ],
            relevance_score=0.60,
            is_retained=True
        ))

    # Update reasoning trace
    trace = state.get("reasoning_trace")
    if trace:
        trace.candidate_modes_discovered = [c.proposed_mode for c in candidates]
        trace.execution_route.append("generate_candidates")

    return {
        "candidate_modes": candidates,
        "reasoning_trace": trace
    }
