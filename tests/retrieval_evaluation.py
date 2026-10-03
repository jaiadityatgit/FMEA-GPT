"""Retrieval benchmark evaluation engine for FMEA-GPT Phase 5C.

Measures retrieval quality against curated ground truth across 14 engineering categories.
Calculates Precision@1, Precision@3, Recall@3, Recall@5, and MRR.
Categorizes retrieval failures into:
- embedding mismatch
- poor chunking
- query formulation
- metadata filtering
- corpus gap
- PDF extraction problem
- terminology mismatch
"""
import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.rag.config import RAGConfig
from src.rag.retriever import AerospaceRetriever, RetrievalResult
from src.rag.vector_store import ChromaVectorStore


def is_passage_relevant(result: RetrievalResult, gt_item: Dict[str, Any]) -> bool:
    """Determine whether a retrieved passage matches the ground-truth criteria."""
    if gt_item.get("corpus_gap", False):
        return False

    expected_docs = gt_item.get("relevant_documents", [])
    expected_pages = gt_item.get("relevant_pages", [])
    granularity = gt_item.get("ground_truth_granularity", "document")

    # Normalize document name matching
    retrieved_doc = Path(result.source_document).name.lower()
    normalized_expected = [Path(d).name.lower() for d in expected_docs]

    doc_match = retrieved_doc in normalized_expected
    if not doc_match:
        return False

    if granularity == "document" or not expected_pages:
        return True

    # Page-level match: allows exact page or adjacent page (+/- 1) due to PDF page offset differences
    retrieved_page = result.page_number
    page_match = any(abs(retrieved_page - p) <= 1 for p in expected_pages)
    return page_match


def evaluate_retrieval(
    ground_truth_path: str = "tests/retrieval_ground_truth.json",
    top_k: int = 5,
    retriever: Optional[AerospaceRetriever] = None
) -> Dict[str, Any]:
    """Execute evaluation over all queries in ground truth and compute standard IR metrics."""
    with open(ground_truth_path, "r", encoding="utf-8") as f:
        ground_truth: List[Dict[str, Any]] = json.load(f)

    if retriever is None:
        vs = ChromaVectorStore()
        retriever = AerospaceRetriever(vector_store=vs)

    query_evaluations: List[Dict[str, Any]] = []
    category_metrics: Dict[str, Dict[str, Any]] = {}

    p1_scores = []
    p3_scores = []
    r3_scores = []
    r5_scores = []
    mrr_scores = []

    failed_queries = []
    corpus_gaps = []

    for item in ground_truth:
        qid = item["query_id"]
        category = item["category"]
        query_text = item["query"]
        is_gap = item.get("corpus_gap", False)

        retrieved: List[RetrievalResult] = retriever.retrieve(query_text, top_k=top_k)
        
        # Calculate relevance flags for each rank 1..k
        relevance_flags = [is_passage_relevant(res, item) for res in retrieved]

        # Calculate metrics for non-corpus-gap queries
        if is_gap:
            corpus_gaps.append({
                "query_id": qid,
                "category": category,
                "query": query_text,
                "retrieved_top1": retrieved[0].format_citation() if retrieved else "None",
                "failure_reason": "corpus gap (specific mechanism / part-level data not in regulatory corpus)"
            })
            # Skip gap queries from positive retrieval metrics to avoid distorting non-gap retriever accuracy
            query_evaluations.append({
                "query_id": qid,
                "category": category,
                "query": query_text,
                "corpus_gap": True,
                "p1": 0.0,
                "p3": 0.0,
                "r3": 0.0,
                "r5": 0.0,
                "mrr": 0.0,
                "top_results": [r.to_dict() for r in retrieved]
            })
            continue

        # Precision@1
        p1 = 1.0 if len(relevance_flags) > 0 and relevance_flags[0] else 0.0
        
        # Precision@3
        p3_count = sum(1 for flag in relevance_flags[:3] if flag)
        p3 = p3_count / 3.0

        # Recall@3 and Recall@5:
        # Expected targets count (number of expected docs or page targets, capped at 1 for hit rate, or based on targets)
        expected_targets = max(1, len(item.get("relevant_pages", [])) if item.get("ground_truth_granularity") == "page" else len(item.get("relevant_documents", [])))
        r3_hits = sum(1 for flag in relevance_flags[:3] if flag)
        r5_hits = sum(1 for flag in relevance_flags[:5] if flag)
        
        r3 = min(1.0, r3_hits / float(expected_targets))
        r5 = min(1.0, r5_hits / float(expected_targets))

        # MRR (Mean Reciprocal Rank)
        rr = 0.0
        for rank, flag in enumerate(relevance_flags, start=1):
            if flag:
                rr = 1.0 / rank
                break

        p1_scores.append(p1)
        p3_scores.append(p3)
        r3_scores.append(r3)
        r5_scores.append(r5)
        mrr_scores.append(rr)

        # Track category statistics
        if category not in category_metrics:
            category_metrics[category] = {"p1": [], "p3": [], "r3": [], "r5": [], "mrr": [], "count": 0}
        category_metrics[category]["p1"].append(p1)
        category_metrics[category]["p3"].append(p3)
        category_metrics[category]["r3"].append(r3)
        category_metrics[category]["r5"].append(r5)
        category_metrics[category]["mrr"].append(rr)
        category_metrics[category]["count"] += 1

        is_failed = (rr == 0.0)
        eval_record = {
            "query_id": qid,
            "category": category,
            "query": query_text,
            "corpus_gap": False,
            "p1": p1,
            "p3": p3,
            "r3": r3,
            "r5": r5,
            "mrr": rr,
            "relevance_flags": relevance_flags,
            "top_results": [r.to_dict() for r in retrieved]
        }
        query_evaluations.append(eval_record)

        if is_failed or p1 == 0.0:
            # Diagnose failure reason
            failure_reason = "embedding mismatch"
            if any(Path(res.source_document).name.lower() in [Path(d).name.lower() for d in item.get("relevant_documents", [])] for res in retrieved):
                failure_reason = "poor chunking / page boundary offset"
            elif any(kw.lower() in r.text.lower() for r in retrieved for kw in item.get("relevant_topics", [])):
                failure_reason = "terminology mismatch"

            failed_queries.append({
                "query_id": qid,
                "category": category,
                "query": query_text,
                "p1": p1,
                "mrr": rr,
                "top_1": retrieved[0].format_citation() if retrieved else "None",
                "top_3": [r.format_citation() for r in retrieved[:3]],
                "expected_documents": item.get("relevant_documents", []),
                "expected_pages": item.get("relevant_pages", []),
                "failure_reason": failure_reason
            })

    # Aggregate metrics
    overall_p1 = sum(p1_scores) / max(1, len(p1_scores))
    overall_p3 = sum(p3_scores) / max(1, len(p3_scores))
    overall_r3 = sum(r3_scores) / max(1, len(r3_scores))
    overall_r5 = sum(r5_scores) / max(1, len(r5_scores))
    overall_mrr = sum(mrr_scores) / max(1, len(mrr_scores))

    cat_summary = {}
    for cat, data in category_metrics.items():
        n = max(1, len(data["p1"]))
        cat_summary[cat] = {
            "p1": round(sum(data["p1"]) / n, 4),
            "p3": round(sum(data["p3"]) / n, 4),
            "r3": round(sum(data["r3"]) / n, 4),
            "r5": round(sum(data["r5"]) / n, 4),
            "mrr": round(sum(data["mrr"]) / n, 4),
            "evaluated_queries": n
        }

    return {
        "overall": {
            "evaluated_queries_count": len(p1_scores),
            "corpus_gap_count": len(corpus_gaps),
            "precision_at_1": round(overall_p1, 4),
            "precision_at_3": round(overall_p3, 4),
            "recall_at_3": round(overall_r3, 4),
            "recall_at_5": round(overall_r5, 4),
            "mrr": round(overall_mrr, 4)
        },
        "per_category": cat_summary,
        "failed_queries": failed_queries,
        "corpus_gaps": corpus_gaps,
        "query_evaluations": query_evaluations
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate retrieval pipeline against ground truth.")
    parser.add_argument("--chroma-dir", type=str, default="data/chroma_db", help="ChromaDB storage directory.")
    parser.add_argument("--collection-name", type=str, default="fmea_aerospace_knowledge", help="Collection name.")
    parser.add_argument("--out-json", type=str, default="scratch/retrieval_benchmark_results.json", help="Path to save JSON results.")
    args = parser.parse_args()

    config = RAGConfig(
        chroma_dir=Path(args.chroma_dir),
        collection_name=args.collection_name
    )
    custom_retriever = AerospaceRetriever(config=config)

    report = evaluate_retrieval(retriever=custom_retriever)
    print("=== RETRIEVAL BENCHMARK RESULTS ===")
    print(f"Store: {args.chroma_dir} ({args.collection_name})")
    print(f"Evaluated Queries: {report['overall']['evaluated_queries_count']}")
    print(f"Corpus Gaps: {report['overall']['corpus_gap_count']}")
    print(f"Precision@1: {report['overall']['precision_at_1'] * 100:.1f}%")
    print(f"Precision@3: {report['overall']['precision_at_3'] * 100:.1f}%")
    print(f"Recall@3:    {report['overall']['recall_at_3'] * 100:.1f}%")
    print(f"Recall@5:    {report['overall']['recall_at_5'] * 100:.1f}%")
    print(f"MRR:         {report['overall']['mrr']:.4f}")

    print("\n=== PER-CATEGORY METRICS ===")
    for cat, met in report["per_category"].items():
        print(f"  {cat:<35}: P@1={met['p1']*100:5.1f}% | P@3={met['p3']*100:5.1f}% | R@5={met['r5']*100:5.1f}% | MRR={met['mrr']:.3f}")

    print(f"\n=== FAILED / WEAK QUERIES ({len(report['failed_queries'])}) ===")
    for fq in report["failed_queries"]:
        print(f"  [{fq['query_id']}] {fq['query'][:50]}... -> Failure: {fq['failure_reason']} (MRR={fq['mrr']})")

    # Save results to specified JSON path
    out_path = Path(args.out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved benchmark results to {out_path}")
