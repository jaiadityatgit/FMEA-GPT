"""Node 2: Targeted RAG context retrieval from the local aerospace knowledge base."""
from typing import Dict, Any, List
from ..state import FMEAState
from ...rag.retriever import AerospaceRetriever, RetrievalResult


def retrieve_standards_node(
    state: FMEAState,
    retriever: AerospaceRetriever
) -> Dict[str, Any]:
    """Execute domain-focused semantic queries to ground FMEA generation in FAA/EASA/DoD literature."""
    component = state.get("component")
    comp_name = component.component_name if component else state.get("component_input", "")

    # Define key queries covering regulatory requirements, failure physics, and inspection
    queries = {
        "engine_safety_clauses": f"{comp_name} 14 CFR 33.75 safety analysis hazardous engine effect blade uncontained",
        "failure_modes_physics": f"{comp_name} thermal mechanical fatigue creep oxidation cracking",
        "inspection_and_maintenance": f"{comp_name} borescope inspection interval crack limit maintenance errors",
        "fmeca_methodology": "MIL-STD-1629A failure mode effects severity categories criticality analysis"
    }

    retrieved_context: Dict[str, List[Dict[str, Any]]] = {}
    flattened_passages: List[Dict[str, Any]] = []

    for category, q in queries.items():
        results = retriever.retrieve(query=q, top_k=2)
        serialized = [r.to_dict() for r in results]
        retrieved_context[category] = serialized
        flattened_passages.extend(serialized)

    return {
        "retrieved_context": retrieved_context,
        "_flattened_passages": flattened_passages
    }
