"""Canonical benchmark runner for Phase 5F.

Evaluates all 6 configurations across the frozen tests/retrieval_benchmark_v1.json:
1. Phase 5C Baseline Dense (data/chroma_db)
2. Phase 5D Section-Aware Dense (data/chroma_db_phase5d_sectioned)
3. Phase 5D Hybrid (Dense + BM25 on data/chroma_db_phase5d_sectioned)
4. Phase 5E Section-Aware Dense (data/chroma_db_phase5e)
5. Phase 5E Hybrid (Dense + BM25 on data/chroma_db_phase5e)
6. Phase 5E Adaptive Query Router (data/chroma_db_phase5e)

Computes metrics with consistent denominators:
- Evaluable Queries Denominator: 30
- Total Queries Denominator: 32 (strict IR)
"""
import sys
import json
import time
import statistics
from pathlib import Path
from typing import Dict, Any, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.rag.config import RAGConfig
from src.rag.retriever import AerospaceRetriever, RetrievalResult
from src.rag.hybrid_retriever import HybridRetriever
from src.rag.adaptive_router import AdaptiveQueryRouter
from tests.retrieval_evaluation import evaluate_retrieval, is_passage_relevant


def evaluate_with_strict_denominator(
    retriever_instance: Any,
    benchmark_path: str = "tests/retrieval_benchmark_v1.json",
    top_k: int = 5
) -> Dict[str, Any]:
    with open(benchmark_path, "r", encoding="utf-8") as f:
        benchmark: List[Dict[str, Any]] = json.load(f)

    # 1. Warm-up
    _ = retriever_instance.retrieve("turbine blade failure", top_k=5)

    # 2. Measure per-query latency and evaluate relevance
    latencies = []
    
    # Evaluable population (30 queries)
    eval_p1 = []
    eval_p3 = []
    eval_r3 = []
    eval_r5 = []
    eval_mrr = []

    # All queries population (32 queries, gap queries contribute 0)
    all_p1 = []
    all_p3 = []
    all_r3 = []
    all_r5 = []
    all_mrr = []

    per_category = {}

    for item in benchmark:
        qid = item["query_id"]
        cat = item["category"]
        q_text = item["query"]
        is_gap = item.get("corpus_gap", False)

        t0 = time.perf_counter()
        retrieved: List[RetrievalResult] = retriever_instance.retrieve(q_text, top_k=top_k)
        latencies.append((time.perf_counter() - t0) * 1000.0)

        relevance_flags = [is_passage_relevant(res, item) for res in retrieved]

        # Calculate metrics
        p1 = 1.0 if len(relevance_flags) > 0 and relevance_flags[0] else 0.0
        p3 = sum(1 for flag in relevance_flags[:3] if flag) / 3.0
        expected_targets = max(1, len(item.get("relevant_pages", [])) if item.get("ground_truth_granularity") == "page" else len(item.get("relevant_documents", [])))
        r3 = min(1.0, sum(1 for flag in relevance_flags[:3] if flag) / float(expected_targets)) if not is_gap else 0.0
        r5 = min(1.0, sum(1 for flag in relevance_flags[:5] if flag) / float(expected_targets)) if not is_gap else 0.0

        rr = 0.0
        if not is_gap:
            for rank_idx, flag in enumerate(relevance_flags, start=1):
                if flag:
                    rr = 1.0 / rank_idx
                    break

        # Record for all queries
        all_p1.append(p1 if not is_gap else 0.0)
        all_p3.append(p3 if not is_gap else 0.0)
        all_r3.append(r3)
        all_r5.append(r5)
        all_mrr.append(rr)

        # Record for evaluable queries
        if not is_gap:
            eval_p1.append(p1)
            eval_p3.append(p3)
            eval_r3.append(r3)
            eval_r5.append(r5)
            eval_mrr.append(rr)

            if cat not in per_category:
                per_category[cat] = {"p1": [], "p3": [], "r3": [], "r5": [], "mrr": []}
            per_category[cat]["p1"].append(p1)
            per_category[cat]["p3"].append(p3)
            per_category[cat]["r3"].append(r3)
            per_category[cat]["r5"].append(r5)
            per_category[cat]["mrr"].append(rr)

    category_summary = {}
    for c, scores in per_category.items():
        category_summary[c] = {
            "p1": round(statistics.mean(scores["p1"]), 4),
            "p3": round(statistics.mean(scores["p3"]), 4),
            "r3": round(statistics.mean(scores["r3"]), 4),
            "r5": round(statistics.mean(scores["r5"]), 4),
            "mrr": round(statistics.mean(scores["mrr"]), 4),
            "count": len(scores["p1"])
        }

    return {
        "evaluable_metrics": {
            "query_count": len(eval_p1),
            "p1": round(statistics.mean(eval_p1), 4),
            "p3": round(statistics.mean(eval_p3), 4),
            "r3": round(statistics.mean(eval_r3), 4),
            "r5": round(statistics.mean(eval_r5), 4),
            "mrr": round(statistics.mean(eval_mrr), 4)
        },
        "all_queries_metrics": {
            "query_count": len(all_p1),
            "p1": round(statistics.mean(all_p1), 4),
            "p3": round(statistics.mean(all_p3), 4),
            "r3": round(statistics.mean(all_r3), 4),
            "r5": round(statistics.mean(all_r5), 4),
            "mrr": round(statistics.mean(all_mrr), 4)
        },
        "latency": {
            "mean_ms": round(statistics.mean(latencies), 2),
            "median_ms": round(statistics.median(latencies), 2),
            "p95_ms": round(sorted(latencies)[int(0.95 * len(latencies))], 2)
        },
        "per_category": category_summary
    }


def main():
    print("=" * 80)
    print("      FMEA-GPT PHASE 5F RECOMPUTED BENCHMARKS (FROZEN V1)")
    print("=" * 80)

    results = {}

    # Config 1: Phase 5C Original Dense Baseline
    print("\n[1/6] Evaluating Config 1: Phase 5C Original Dense (data/chroma_db)...")
    cfg_5c = RAGConfig(
        chroma_dir=Path("data/chroma_db"),
        collection_name="fmea_aerospace_knowledge"
    )
    ret_5c = AerospaceRetriever(config=cfg_5c)
    results["phase5c_dense_baseline"] = evaluate_with_strict_denominator(ret_5c)

    # Config 2: Phase 5D Section-Aware Dense
    print("\n[2/6] Evaluating Config 2: Phase 5D Section-Aware Dense (data/chroma_db_phase5d_sectioned)...")
    cfg_5d = RAGConfig(
        chroma_dir=Path("data/chroma_db_phase5d_sectioned"),
        collection_name="fmea_aerospace_knowledge_sectioned"
    )
    ret_5d = AerospaceRetriever(config=cfg_5d)
    results["phase5d_sectioned_dense"] = evaluate_with_strict_denominator(ret_5d)

    # Config 3: Phase 5D Hybrid (Dense + BM25)
    print("\n[3/6] Evaluating Config 3: Phase 5D Hybrid (data/chroma_db_phase5d_sectioned)...")
    ret_5d_hyb = HybridRetriever(
        chroma_dir=Path("data/chroma_db_phase5d_sectioned"),
        collection_name="fmea_aerospace_knowledge_sectioned",
        use_query_expansion=False,
        use_reranker=False
    )
    results["phase5d_hybrid"] = evaluate_with_strict_denominator(ret_5d_hyb)

    # Config 4: Phase 5E Section-Aware Dense
    print("\n[4/6] Evaluating Config 4: Phase 5E Section-Aware Dense (data/chroma_db_phase5e)...")
    cfg_5e = RAGConfig(
        chroma_dir=Path("data/chroma_db_phase5e"),
        collection_name="fmea_aerospace_knowledge_phase5e"
    )
    ret_5e = AerospaceRetriever(config=cfg_5e)
    results["phase5e_sectioned_dense"] = evaluate_with_strict_denominator(ret_5e)

    # Config 5: Phase 5E Hybrid (Dense + BM25)
    print("\n[5/6] Evaluating Config 5: Phase 5E Hybrid (data/chroma_db_phase5e)...")
    ret_5e_hyb = HybridRetriever(
        chroma_dir=Path("data/chroma_db_phase5e"),
        collection_name="fmea_aerospace_knowledge_phase5e",
        use_query_expansion=False,
        use_reranker=False
    )
    results["phase5e_hybrid"] = evaluate_with_strict_denominator(ret_5e_hyb)

    # Config 6: Phase 5E Adaptive Router
    print("\n[6/6] Evaluating Config 6: Phase 5E Adaptive Router (data/chroma_db_phase5e)...")
    router_5e = AdaptiveQueryRouter(
        chroma_dir=Path("data/chroma_db_phase5e"),
        collection_name="fmea_aerospace_knowledge_phase5e"
    )
    results["phase5e_adaptive_router"] = evaluate_with_strict_denominator(router_5e)

    # Save to JSON
    out_json = Path("data/output/phase5f_recomputed_benchmarks.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved raw recomputed benchmark data to {out_json}")

    # Print Comparison Table
    print("\n" + "=" * 95)
    print(f"{'Configuration':<30} | {'P@1 (N=30)':<10} | {'P@3':<8} | {'R@3':<8} | {'R@5':<8} | {'MRR':<8} | {'Latency':<10}")
    print("-" * 95)
    for name, d in results.items():
        m = d["evaluable_metrics"]
        lat = d["latency"]["mean_ms"]
        print(f"{name:<30} | {m['p1']*100:>8.1f}% | {m['p3']*100:>6.1f}% | {m['r3']*100:>6.1f}% | {m['r5']*100:>6.1f}% | {m['mrr']:>7.4f} | {lat:>7.1f} ms")
    print("=" * 95)

    print("\n" + "=" * 95)
    print(f"{'Configuration (Strict N=32)':<30} | {'P@1 (N=32)':<10} | {'P@3':<8} | {'R@3':<8} | {'R@5':<8} | {'MRR':<8} | {'Latency':<10}")
    print("-" * 95)
    for name, d in results.items():
        m = d["all_queries_metrics"]
        lat = d["latency"]["mean_ms"]
        print(f"{name:<30} | {m['p1']*100:>8.1f}% | {m['p3']*100:>6.1f}% | {m['r3']*100:>6.1f}% | {m['r5']*100:>6.1f}% | {m['mrr']:>7.4f} | {lat:>7.1f} ms")
    print("=" * 95)

    return results

if __name__ == "__main__":
    main()
