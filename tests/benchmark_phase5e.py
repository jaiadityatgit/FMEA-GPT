"""Phase 5E comprehensive benchmark and comparison runner.

Compares:
1. Phase 5D Baseline (data/chroma_db)
2. Phase 5D Selected Configuration (Section-aware Dense on data/chroma_db_phase5d_sectioned)
3. Phase 5E Expanded Corpus (Section-aware Dense on data/chroma_db_phase5e)
4. Phase 5E Expanded Corpus (Hybrid Dense+BM25)
5. Phase 5E Expanded Corpus (Adaptive Query Router)

Saves results to data/output/phase5e_benchmark_results.json.
"""
import sys
import json
import time
import statistics
from pathlib import Path
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.rag.config import RAGConfig
from src.rag.retriever import AerospaceRetriever
from src.rag.hybrid_retriever import HybridRetriever
from src.rag.adaptive_router import AdaptiveQueryRouter, RetrievalStrategy
from tests.retrieval_evaluation import evaluate_retrieval


def run_benchmark():
    print("=" * 80)
    print("           FMEA-GPT PHASE 5E KNOWLEDGE EXPANSION BENCHMARK")
    print("=" * 80)

    gt_path = "tests/retrieval_ground_truth.json"
    with open(gt_path, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    results = {}

    # 1. Config A: Baseline Dense (Phase 5D baseline data/chroma_db)
    print("\n[1/5] Evaluating Baseline Dense (data/chroma_db)...")
    cfg_base = RAGConfig(
        chroma_dir=Path("data/chroma_db"),
        collection_name="fmea_aerospace_knowledge"
    )
    ret_base = AerospaceRetriever(config=cfg_base)
    lat_base = []
    for item in ground_truth:
        t0 = time.perf_counter()
        _ = ret_base.retrieve(item["query"], top_k=5)
        lat_base.append((time.perf_counter() - t0) * 1000)
    rep_base = evaluate_retrieval(gt_path, top_k=5, retriever=ret_base)
    results["baseline_dense"] = {
        "metrics": rep_base["overall"],
        "latency": {
            "mean_ms": round(statistics.mean(lat_base), 2),
            "median_ms": round(statistics.median(lat_base), 2),
            "p95_ms": round(sorted(lat_base)[int(0.95 * len(lat_base))], 2)
        },
        "per_category": rep_base["per_category"]
    }

    # 2. Config B: Phase 5D Section-Aware Dense (data/chroma_db_phase5d_sectioned)
    print("\n[2/5] Evaluating Phase 5D Section-Aware Dense (data/chroma_db_phase5d_sectioned)...")
    cfg_5d = RAGConfig(
        chroma_dir=Path("data/chroma_db_phase5d_sectioned"),
        collection_name="fmea_aerospace_knowledge_sectioned"
    )
    ret_5d = AerospaceRetriever(config=cfg_5d)
    lat_5d = []
    for item in ground_truth:
        t0 = time.perf_counter()
        _ = ret_5d.retrieve(item["query"], top_k=5)
        lat_5d.append((time.perf_counter() - t0) * 1000)
    rep_5d = evaluate_retrieval(gt_path, top_k=5, retriever=ret_5d)
    results["phase5d_sectioned_dense"] = {
        "metrics": rep_5d["overall"],
        "latency": {
            "mean_ms": round(statistics.mean(lat_5d), 2),
            "median_ms": round(statistics.median(lat_5d), 2),
            "p95_ms": round(sorted(lat_5d)[int(0.95 * len(lat_5d))], 2)
        },
        "per_category": rep_5d["per_category"]
    }

    # 3. Config C: Phase 5E Section-Aware Dense (data/chroma_db_phase5e)
    print("\n[3/5] Evaluating Phase 5E Section-Aware Dense (data/chroma_db_phase5e)...")
    cfg_5e = RAGConfig(
        chroma_dir=Path("data/chroma_db_phase5e"),
        collection_name="fmea_aerospace_knowledge_phase5e"
    )
    ret_5e_dense = AerospaceRetriever(config=cfg_5e)
    lat_5e_dense = []
    for item in ground_truth:
        t0 = time.perf_counter()
        _ = ret_5e_dense.retrieve(item["query"], top_k=5)
        lat_5e_dense.append((time.perf_counter() - t0) * 1000)
    rep_5e_dense = evaluate_retrieval(gt_path, top_k=5, retriever=ret_5e_dense)
    results["phase5e_sectioned_dense"] = {
        "metrics": rep_5e_dense["overall"],
        "latency": {
            "mean_ms": round(statistics.mean(lat_5e_dense), 2),
            "median_ms": round(statistics.median(lat_5e_dense), 2),
            "p95_ms": round(sorted(lat_5e_dense)[int(0.95 * len(lat_5e_dense))], 2)
        },
        "per_category": rep_5e_dense["per_category"]
    }

    # 4. Config D: Phase 5E Hybrid Dense + BM25
    print("\n[4/5] Evaluating Phase 5E Hybrid (Dense + BM25)...")
    ret_5e_hybrid = HybridRetriever(
        chroma_dir=Path("data/chroma_db_phase5e"),
        collection_name="fmea_aerospace_knowledge_phase5e",
        use_query_expansion=False,
        use_reranker=False
    )
    lat_5e_hybrid = []
    for item in ground_truth:
        t0 = time.perf_counter()
        _ = ret_5e_hybrid.retrieve(item["query"], top_k=5)
        lat_5e_hybrid.append((time.perf_counter() - t0) * 1000)
    rep_5e_hybrid = evaluate_retrieval(gt_path, top_k=5, retriever=ret_5e_hybrid)
    results["phase5e_hybrid"] = {
        "metrics": rep_5e_hybrid["overall"],
        "latency": {
            "mean_ms": round(statistics.mean(lat_5e_hybrid), 2),
            "median_ms": round(statistics.median(lat_5e_hybrid), 2),
            "p95_ms": round(sorted(lat_5e_hybrid)[int(0.95 * len(lat_5e_hybrid))], 2)
        },
        "per_category": rep_5e_hybrid["per_category"]
    }

    # 5. Config E: Phase 5E Adaptive Query Router
    print("\n[5/5] Evaluating Phase 5E Adaptive Query Router...")
    router = AdaptiveQueryRouter(
        chroma_dir=Path("data/chroma_db_phase5e"),
        collection_name="fmea_aerospace_knowledge_phase5e"
    )
    lat_router = []
    routes = {}
    for item in ground_truth:
        t0 = time.perf_counter()
        res = router.retrieve_detailed(item["query"], top_k=5)
        lat_router.append((time.perf_counter() - t0) * 1000)
        strat = res.classification.strategy.value
        routes[strat] = routes.get(strat, 0) + 1
    rep_router = evaluate_retrieval(gt_path, top_k=5, retriever=router)
    results["phase5e_adaptive_router"] = {
        "metrics": rep_router["overall"],
        "latency": {
            "mean_ms": round(statistics.mean(lat_router), 2),
            "median_ms": round(statistics.median(lat_router), 2),
            "p95_ms": round(sorted(lat_router)[int(0.95 * len(lat_router))], 2)
        },
        "per_category": rep_router["per_category"],
        "routing_distribution": routes
    }

    # Summary table
    print("\n" + "=" * 90)
    print("                      PHASE 5E BENCHMARK COMPARISON TABLE")
    print("=" * 90)
    header = f"{'Configuration':<32} | {'P@1':<7} | {'P@3':<7} | {'R@3':<7} | {'R@5':<7} | {'MRR':<7} | {'Mean Latency':<12}"
    print(header)
    print("-" * 90)
    for name, data in results.items():
        m = data["metrics"]
        lat = data["latency"]["mean_ms"]
        row = f"{name:<32} | {m['precision_at_1']*100:>5.1f}% | {m['precision_at_3']*100:>5.1f}% | {m['recall_at_3']*100:>5.1f}% | {m['recall_at_5']*100:>5.1f}% | {m['mrr']:>7.4f} | {lat:>8.1f} ms"
        print(row)
    print("=" * 90)

    # Save to file
    out_path = Path("data/output/phase5e_benchmark_results.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved full benchmark results to {out_path}")

    return results


if __name__ == "__main__":
    run_benchmark()
