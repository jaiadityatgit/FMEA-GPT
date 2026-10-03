"""Node: Targeted RAG Retrieval for Candidate Failure Modes.

Executes candidate-specific targeted retrieval queries against the ChromaDB vector store.
Ensures every candidate failure mode retrieves and retains evidence specifically addressing
its physical mechanism, causes, effects, detection methods, and airworthiness implications.

Prohibits attaching generic global citations across unrelated failure modes.
"""
from typing import Dict, Any, List
from ..state import (
    FMEAState,
    CandidateFailureMode,
    EvidenceRecord,
    SupportLevel
)
from ...rag.retriever import AerospaceRetriever, RetrievalResult


def targeted_retrieval_node(
    state: FMEAState,
    retriever: AerospaceRetriever
) -> Dict[str, Any]:
    """Execute targeted semantic queries for each candidate failure mode."""
    candidate_modes: List[CandidateFailureMode] = state.get("candidate_modes", [])
    targeted_evidence: Dict[str, List[EvidenceRecord]] = {}
    all_retrieval_queries: List[str] = list(state.get("retrieved_context", {}).keys())

    for cand in candidate_modes:
        cand_records: List[EvidenceRecord] = []
        queries = cand.targeted_queries or [cand.proposed_mode]

        for q in queries:
            all_retrieval_queries.append(q)
            results = retriever.retrieve(query=q, top_k=2)

            for r in results:
                # Deduplicate records by source_document and page_number within this candidate
                already_present = any(
                    cr.source_document == r.source_document and cr.page_number == r.page_number
                    for cr in cand_records
                )
                if not already_present:
                    # Evaluate initial support level based on similarity_score
                    if r.similarity_score >= 0.65:
                        s_level = SupportLevel.DIRECT_SOURCE
                    elif r.similarity_score >= 0.50:
                        s_level = SupportLevel.SUPPORTING_SOURCE
                    else:
                        s_level = SupportLevel.INSUFFICIENT_EVIDENCE

                    meta = r.metadata or {}
                    record = EvidenceRecord(
                        evidence_id=f"EVID-{cand.candidate_id}-{len(cand_records)+1:02d}",
                        source_document=r.source_document,
                        document_title=r.doc_title,
                        publisher=r.publisher,
                        page_number=r.page_number,
                        section=r.section,
                        excerpt=r.text,
                        retrieval_query=q,
                        retrieval_score=round(r.similarity_score, 4),
                        support_level=s_level,
                        evidence_type=meta.get("evidence_category") or "regulatory_standard",
                        official_report_number=meta.get("official_report_number"),
                        publication_year=meta.get("publication_year"),
                        evidence_category=meta.get("evidence_category"),
                        technical_domain=meta.get("technical_domain"),
                        applicability_scope=meta.get("applicability_scope"),
                    )
                    cand_records.append(record)

        targeted_evidence[cand.candidate_id] = cand_records

    # Update reasoning trace
    trace = state.get("reasoning_trace")
    if trace:
        trace.retrieval_queries = list(set(all_retrieval_queries))
        trace.execution_route.append("targeted_retrieval")

    return {
        "targeted_evidence": targeted_evidence,
        "reasoning_trace": trace
    }


def retry_retrieval_node(
    state: FMEAState,
    retriever: AerospaceRetriever
) -> Dict[str, Any]:
    """Execute broadened fallback queries for unverified or insufficient-evidence candidate modes."""
    candidate_modes: List[CandidateFailureMode] = state.get("candidate_modes", [])
    targeted_evidence: Dict[str, List[EvidenceRecord]] = state.get("targeted_evidence", {})
    verification_results = state.get("verification_results", [])
    unverified_ids = {vr.claim_id for vr in verification_results if not vr.is_verified}

    retry_count = state.get("retry_count", 0) + 1

    for cand in candidate_modes:
        if any(cand.candidate_id in cid for cid in unverified_ids):
            # Broad fallback queries
            fallback_queries = [
                f"{cand.proposed_mechanism} civil aviation safety analysis",
                f"{cand.proposed_mode} MIL-STD-1629A failure effect"
            ]
            current_records = targeted_evidence.get(cand.candidate_id, [])
            for fq in fallback_queries:
                results = retriever.retrieve(query=fq, top_k=2)
                for r in results:
                    already_present = any(
                        cr.source_document == r.source_document and cr.page_number == r.page_number
                        for cr in current_records
                    )
                    if not already_present and r.similarity_score >= 0.50:
                        rmeta = r.metadata or {}
                        rec = EvidenceRecord(
                            evidence_id=f"EVID-RETRY-{cand.candidate_id}-{len(current_records)+1:02d}",
                            source_document=r.source_document,
                            document_title=r.doc_title,
                            publisher=r.publisher,
                            page_number=r.page_number,
                            section=r.section,
                            excerpt=r.text,
                            retrieval_query=fq,
                            retrieval_score=round(r.similarity_score, 4),
                            support_level=SupportLevel.SUPPORTING_SOURCE,
                            evidence_type=rmeta.get("evidence_category") or "regulatory_standard",
                            official_report_number=rmeta.get("official_report_number"),
                            publication_year=rmeta.get("publication_year"),
                            evidence_category=rmeta.get("evidence_category"),
                            technical_domain=rmeta.get("technical_domain"),
                            applicability_scope=rmeta.get("applicability_scope"),
                        )
                        current_records.append(rec)
            targeted_evidence[cand.candidate_id] = current_records

    trace = state.get("reasoning_trace")
    if trace:
        trace.retries_performed = retry_count
        trace.execution_route.append("retry_retrieval")

    return {
        "targeted_evidence": targeted_evidence,
        "retry_count": retry_count,
        "reasoning_trace": trace
    }
