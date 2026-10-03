"""Node 1: Evidence-Aware Component Classification.

Identifies component type, system hierarchy, operating environment, and regulatory tier.
Capable of yielding UNKNOWN or INSUFFICIENT_EVIDENCE when the component falls outside
the validated aerospace knowledge base or when the corpus lacks grounding data.
"""
from typing import Dict, Any
from ..state import FMEAState, ComponentInfo, AnalysisStatus, ReasoningTrace
from ..providers.base import LLMProvider


def classify_component_node(state: FMEAState, provider: LLMProvider) -> Dict[str, Any]:
    """Identify component type, system hierarchy, operating environment, and regulatory tier."""
    comp_input = state.get("component_input", "")
    part_num = state.get("target_part_number")
    notes = state.get("operating_notes")

    prompt = (
        f"Classify the following aerospace component into its system, subsystem, regulatory airworthiness "
        f"category (FAA 14 CFR / EASA CS-25 / CS-E), operating environment, and primary function.\n\n"
        f"Component: {comp_input}\n"
        f"Part Number: {part_num or 'Unknown'}\n"
        f"Operating Notes: {notes or 'Standard aerospace mission profile'}\n"
    )

    component_info: ComponentInfo = provider.generate_structured(
        prompt=prompt,
        response_model=ComponentInfo,
        context={"component_input": comp_input, "part_number": part_num, "operating_notes": notes}
    )

    status_str = (
        component_info.analysis_status.value
        if hasattr(component_info.analysis_status, "value")
        else str(component_info.analysis_status)
    )

    coverage_adequate = component_info.analysis_status != AnalysisStatus.INSUFFICIENT_EVIDENCE

    # Initialize reasoning trace
    trace = ReasoningTrace(
        input_component=comp_input,
        target_part_number=part_num,
        classification_status=status_str,
        execution_route=["classify"],
        candidate_modes_discovered=[],
        accepted_modes=[],
        rejected_candidates=[]
    )

    return {
        "component": component_info,
        "coverage_adequate": coverage_adequate,
        "reasoning_trace": trace
    }
