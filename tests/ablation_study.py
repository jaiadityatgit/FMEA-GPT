"""Ablation study runner for FMEA-GPT Phase 5D.

Evaluates and benchmarks the 6 mandatory configurations:
A. Existing dense retrieval (Baseline: data/chroma_db)
B. Section-aware dense retrieval (data/chroma_db_phase5d_sectioned)
C. Hybrid retrieval (Dense + BM25 Okapi with RRF)
D. Hybrid + Controlled Terminology Expansion
E. Hybrid + Local Reranker
F. Hybrid + Controlled Terminology Expansion + Local Reranker

Calculates Precision@1, Precision@3, Recall@3, Recall@5, MRR,
and benchmarks latency (mean, median, p95) across all queries.
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
from tests.retrieval_evaluation import evaluate_retrieval


def benchmark_configuration(
    name: str,
    retriever_instance: Any,
    ground_truth_path: str = "tests/retrieval_ground_truth.json"
) -> Tuple[Dict[str, Any], Dict[str, float]]:
    """Run retrieval evaluation and measure latency across queries."""
    with open(ground_truth_path, "r", encoding="utf-8") as f:
        ground_truth: List[Dict[str, Any]] = json.load(f)

    # 1. Warm-up
    _ = retriever_instance.retrieve("turbine rotor blade failure", top_k=5)

    # 2. Measure per-query latency across all queries
    latencies: List[float] = []
    for item in ground_truth:
        q = item["query"]
        t0 = time.perf_counter()
        _ = retriever_instance.retrieve(q, top_k=5)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)  # milliseconds

    latency_stats = {
        "mean_ms": round(statistics.mean(latencies), 2),
        "median_ms": round(statistics.median(latencies), 2),
        "p95_ms": round(sorted(latencies)[int(0.95 * len(latencies))], 2)
    }

    # 3. Evaluate IR accuracy metrics
    report = evaluate_retrieval(
        ground_truth_path=ground_truth_path,
        top_k=5,
        retriever=retriever_instance
    )

    return report, latency_stats


def run_full_ablation_study() -> Dict[str, Any]:
    """Execute all 6 ablation configurations and assemble comparison table."""
    print("=" * 80)
    print("           FMEA-GPT PHASE 5D RETRIEVAL ABLATION STUDY")
    print("=" * 80)

    results: Dict[str, Any] = {}

    # Config A: Baseline Dense Retrieval
    print("\n[1/6] Running Config A: Existing Dense Baseline...")
    base_config = RAGConfig(
        chroma_dir=Path("data/chroma_db"),
        collection_name="fmea_aerospace_knowledge"
    )
    retriever_a = AerospaceRetriever(config=base_config)
    report_a, lat_a = benchmark_configuration("Config A: Existing Dense", retriever_a)
    results["A_existing_dense"] = {"metrics": report_a["overall"], "latency": lat_a, "per_category": report_a["per_category"]}

    # Config B: Section-Aware Dense Retrieval
    print("\n[2/6] Running Config B: Section-Aware Dense...")
    sec_config = RAGConfig(
        chroma_dir=Path("data/chroma_db_phase5d_sectioned"),
        collection_name="fmea_aerospace_knowledge_sectioned"
    )
    retriever_b = AerospaceRetriever(config=sec_config)
    report_b, lat_b = benchmark_configuration("Config B: Section-Aware Dense", retriever_b)
    results["B_section_aware_dense"] = {"metrics": report_b["overall"], "latency": lat_b, "per_category": report_b["per_category"]}

    # Config C: Hybrid Retrieval (Dense + BM25)
    print("\n[3/6] Running Config C: Hybrid (Dense + BM25)...")
    retriever_c = HybridRetriever(
        chroma_dir=Path("data/chroma_db_phase5d_sectioned"),
        collection_name="fmea_aerospace_knowledge_sectioned",
        use_query_expansion=False,
        use_reranker=False
    )
    report_c, lat_c = benchmark_configuration("Config C: Hybrid", retriever_c)
    results["C_hybrid"] = {"metrics": report_c["overall"], "latency": lat_c, "per_category": report_c["per_category"]}

    # Config D: Hybrid + Terminology Expansion
    print("\n[4/6] Running Config D: Hybrid + Terminology Expansion...")
    retriever_d = HybridRetriever(
        chroma_dir=Path("data/chroma_db_phase5d_sectioned"),
        collection_name="fmea_aerospace_knowledge_sectioned",
        use_query_expansion=True,
        use_reranker=False
    )
    report_d, lat_d = benchmark_configuration("Config D: Hybrid + Query Expansion", retriever_d)
    results["D_hybrid_expansion"] = {"metrics": report_d["overall"], "latency": lat_d, "per_category": report_d["per_category"]}

    # Config E: Hybrid + Local Reranker
    print("\n[5/6] Running Config E: Hybrid + Local Reranker...")
    retriever_e = HybridRetriever(
        chroma_dir=Path("data/chroma_db_phase5d_sectioned"),
        collection_name="fmea_aerospace_knowledge_sectioned",
        use_query_expansion=False,
        use_reranker=True
    )
    report_e, lat_e = benchmark_configuration("Config E: Hybrid + Reranker", retriever_e)
    results["E_hybrid_reranker"] = {"metrics": report_e["overall"], "latency": lat_e, "per_category": report_e["per_category"]}

    # Config F: Hybrid + Terminology Expansion + Local Reranker
    print("\n[6/6] Running Config F: Hybrid + Terminology Expansion + Local Reranker...")
    retriever_f = HybridRetriever(
        chroma_dir=Path("data/chroma_db_phase5d_sectioned"),
        collection_name="fmea_aerospace_knowledge_sectioned",
        use_query_expansion=True,
        use_reranker=True
    )
    report_f, lat_f = benchmark_configuration("Config F: Hybrid + Expansion + Reranker", retriever_f)
    results["F_hybrid_expansion_reranker"] = {"metrics": report_f["overall"], "latency": lat_f, "per_category": report_f["per_category"]}

    # Print Ablation Comparison Table
    print("\n" + "=" * 95)
    print("                     PHASE 5D RETRIEVAL ABLATION RESULTS TABLE")
    print("=" * 95)
    header = f"{'Configuration':<40} | {'P@1':>6} | {'P@3':>6} | {'R@3':>6} | {'R@5':>6} | {'MRR':>6} | {'Mean Latency':>12}"
    print(header)
    print("-" * 95)

    config_labels = [
        ("A. Existing dense retrieval", "A_existing_dense"),
        ("B. Section-aware dense retrieval", "B_section_aware_dense"),
        ("C. Hybrid retrieval", "C_hybrid"),
        ("D. Hybrid + terminology expansion", "D_hybrid_expansion"),
        ("E. Hybrid + reranker", "E_hybrid_reranker"),
        ("F. Hybrid + expansion + reranker", "F_hybrid_expansion_reranker"),
    ]

    for label, key in config_labels:
        m = results[key]["metrics"]
        lat = results[key]["latency"]
        row = (
            f"{label:<40} | "
            f"{m['precision_at_1']*100:5.1f}% | "
            f"{m['precision_at_3']*100:5.1f}% | "
            f"{m['recall_at_3']*100:5.1f}% | "
            f"{m['recall_at_5']*100:5.1f}% | "
            f"{m['mrr']:6.4f} | "
            f"{lat['mean_ms']:8.1f} ms"
        )
        print(row)
    print("=" * 95)

    # Save to scratch/ablation_study_results.json
    out_file = Path("scratch/ablation_study_results.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved comprehensive ablation results to {out_file}")

    return results


if __name__ == "__main__":
    run_full_ablation_study()
