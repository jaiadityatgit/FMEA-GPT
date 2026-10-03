"""Node 3: Systematic Failure Mode Enumeration and Root Cause Analysis."""
from typing import Dict, Any, List
from ..state import FMEAState, FailureModeEntry
from ..providers.base import LLMProvider


def enumerate_failure_modes_node(
    state: FMEAState,
    provider: LLMProvider
) -> Dict[str, Any]:
    """Generate comprehensive failure mode records with cause-effect, scoring, and mitigations."""
    component = state.get("component")
    flattened_passages = state.get("_flattened_passages", [])
    if not flattened_passages:
        # Extract from retrieved_context if present
        ctx = state.get("retrieved_context", {})
        for plist in ctx.values():
            flattened_passages.extend(plist)

    prompt = (
        f"Generate a complete, standards-compliant MIL-STD-1629A Failure Mode and Effects Analysis for:\n"
        f"Component: {component.component_name if component else state.get('component_input')}\n"
        f"System: {component.system if component else 'Propulsion'}\n"
        f"Subsystem: {component.subsystem if component else 'High Pressure Turbine'}\n"
        f"Operating Environment: {component.operating_environment if component else 'Aviation transport'}\n\n"
        f"Ground each failure mode in physical degradation mechanisms (fatigue, creep, FOD, corrosion), "
        f"evaluate Severity (S), Occurrence (O), Detection (D), calculate RPN, and assign specific maintenance "
        f"actions (borescope, eddy current, NDT) with intervals."
    )

    context = {
        "component": component,
        "retrieved_passages": flattened_passages
    }

    failure_modes: List[FailureModeEntry] = provider.generate_structured(
        prompt=prompt,
        response_model=List[FailureModeEntry],  # type: ignore
        context=context
    )

    return {"failure_modes": failure_modes}
