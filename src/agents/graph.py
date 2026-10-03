"""LangGraph workflow definition for FMEA-GPT Phase 5B Evidence-Grounded Reasoning Engine."""
from typing import Optional, Dict, Any
from langgraph.graph import StateGraph, START, END

from .state import FMEAState, FMEAReport, AnalysisStatus
from .providers.base import LLMProvider
from .providers.factory import get_llm_provider
from .nodes.classifier import classify_component_node
from .nodes.retrieval_node import retrieve_standards_node
from .nodes.evidence_extractor import extract_evidence_node
from .nodes.candidate_generator import generate_candidate_modes_node
from .nodes.targeted_retrieval import targeted_retrieval_node, retry_retrieval_node
from .nodes.claim_verifier import verify_claims_node
from .nodes.evidence_gap import evidence_gap_node
from .nodes.fmea_builder import build_fmea_node
from .nodes.validator import validate_and_package_node
from ..rag.retriever import AerospaceRetriever
from ..rag.config import RAGConfig


def check_corpus_coverage(state: FMEAState) -> str:
    """Evaluate whether local corpus contains adequate grounding data for the classified component."""
    component = state.get("component")
    if not state.get("coverage_adequate", True):
        return "inadequate"
    if component and component.analysis_status == AnalysisStatus.INSUFFICIENT_EVIDENCE:
        return "inadequate"
    passages = state.get("_flattened_passages", [])
    if not passages and not state.get("retrieved_context"):
        return "inadequate"
    return "adequate"


def check_claim_support(state: FMEAState) -> str:
    """Evaluate whether candidate claims require evidence-driven retry retrieval."""
    verification_results = state.get("verification_results", [])
    has_unverified = any(not vr.is_verified for vr in verification_results)
    retry_count = state.get("retry_count", 0)
    if has_unverified and retry_count < 1:
        return "retry"
    return "build"


class FMEAGeneratorGraph:
    """Manages the compiled LangGraph state graph for aerospace FMEA generation."""

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        retriever: Optional[AerospaceRetriever] = None,
        config: Optional[RAGConfig] = None
    ):
        self.config = config or RAGConfig.get_production_config()
        self.provider = provider or get_llm_provider()
        self.retriever = retriever or AerospaceRetriever(config=self.config)
        self.graph = self._build_graph()

    def _build_graph(self):
        """Construct and compile the LangGraph workflow with conditional routing and retry loops."""
        builder = StateGraph(FMEAState)

        # 1. Add Workflow Nodes
        builder.add_node("classify", lambda s: classify_component_node(s, self.provider))
        builder.add_node("retrieve", lambda s: retrieve_standards_node(s, self.retriever))
        builder.add_node("evidence_gap", lambda s: evidence_gap_node(s))
        builder.add_node("extract_evidence", lambda s: extract_evidence_node(s))
        builder.add_node("generate_candidates", lambda s: generate_candidate_modes_node(s))
        builder.add_node("targeted_retrieval", lambda s: targeted_retrieval_node(s, self.retriever))
        builder.add_node("verify_claims", lambda s: verify_claims_node(s))
        builder.add_node("retry_retrieval", lambda s: retry_retrieval_node(s, self.retriever))
        builder.add_node("build_fmea", lambda s: build_fmea_node(s))
        builder.add_node("validate", lambda s: validate_and_package_node(s, self.provider))

        # 2. Add Linear Edges
        builder.add_edge(START, "classify")
        builder.add_edge("classify", "retrieve")

        # 3. Conditional Edge 1: Corpus Coverage Decision
        builder.add_conditional_edges(
            "retrieve",
            check_corpus_coverage,
            {
                "inadequate": "evidence_gap",
                "adequate": "extract_evidence"
            }
        )

        # 4. Pipeline Execution along Adequate Branch
        builder.add_edge("evidence_gap", "validate")
        builder.add_edge("extract_evidence", "generate_candidates")
        builder.add_edge("generate_candidates", "targeted_retrieval")
        builder.add_edge("targeted_retrieval", "verify_claims")

        # 5. Conditional Edge 2: Claim Verification Support / Retry
        builder.add_conditional_edges(
            "verify_claims",
            check_claim_support,
            {
                "retry": "retry_retrieval",
                "build": "build_fmea"
            }
        )
        builder.add_edge("retry_retrieval", "verify_claims")

        # 6. Finalization Edges
        builder.add_edge("build_fmea", "validate")
        builder.add_edge("validate", END)

        return builder.compile()

    def run(
        self,
        component_input: str,
        target_part_number: Optional[str] = None,
        operating_notes: Optional[str] = None,
        **kwargs
    ) -> FMEAReport:
        """Execute the full agentic FMEA generation pipeline."""
        pn = target_part_number or kwargs.get("part_number")
        initial_state: FMEAState = {
            "component_input": component_input,
            "target_part_number": pn,
            "operating_notes": operating_notes,
            "retry_count": 0,
            "errors": []
        }

        final_state = self.graph.invoke(initial_state)
        report: FMEAReport = final_state.get("final_report")
        if not report:
            raise RuntimeError("FMEA Generation failed to produce final report.")
        return report
