"""Final Core Engineering Completion — frozen benchmark + gap-closure evaluation.

Compares the Phase 5E production store against the core-final store (Phase 5E + 2 NASA sources):
1. Frozen tests/retrieval_benchmark_v1.json (query population NOT modified) for dense, hybrid
   and adaptive-router configurations.
2. Targeted gap-closure queries (RET-13, RET-14, RET-16 + 7 task queries). Retrieved passages are
   recorded with full provenance so relevance can be judged from the actual page text.

Outputs:
- data/output/core_final_benchmarks.json
- data/output/core_final_gap_closure.json
"""
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.rag.config import RAGConfig  # noqa: E402
from src.rag.retriever import AerospaceRetriever  # noqa: E402
from src.rag.hybrid_retriever import HybridRetriever  # noqa: E402
from src.rag.adaptive_router import AdaptiveQueryRouter  # noqa: E402
from scripts.recompute_benchmarks import evaluate_with_strict_denominator  # noqa: E402

STORES = {
    "phase5e": (Path("data/chroma_db_phase5e"), "fmea_aerospace_knowledge_phase5e"),
    "core_final": (Path("data/chroma_db_core_final"), "fmea_aerospace_knowledge_core_final"),
}

NEW_SOURCES = {
    "NASA_MSFC_2000_Arakere_Fretting_Stresses_SC_Blade_Attachments.pdf",
    "NASA_CR_189111_EBPVD_TBC_Life_Prediction.pdf",
}

GAP_QUERIES = [
    ("RET-13", "fretting", "fretting fatigue micro-motion dovetail root contact stress crack initiation"),
    ("RET-14", "fretting", "blade root fir-tree slot contact surface fretting wear galling"),
    ("RET-16", "tbc", "high temperature hot corrosion sulfidation thermal barrier coating spallation"),
    ("GAP-F1", "fretting", "turbine blade dovetail fretting fatigue"),
    ("GAP-F2", "fretting", "fir-tree root micro-slip contact stress"),
    ("GAP-F3", "fretting", "blade attachment fretting wear"),
    ("GAP-T1", "tbc", "thermal barrier coating spallation"),
    ("GAP-T2", "tbc", "TBC thermal cycling degradation"),
    ("GAP-T3", "tbc", "EB-PVD thermal barrier coating failure"),
    ("GAP-T4", "cmas", "CMAS coating degradation"),
]

FOCUS_CATEGORIES = ["thermal_fatigue", "cooling", "corrosion", "fretting", "tbc", "coating", "creep"]


def _dense(store: str):
    d, c = STORES[store]
    return AerospaceRetriever(config=RAGConfig(chroma_dir=d, collection_name=c))


def _hybrid(store: str):
    d, c = STORES[store]
    return HybridRetriever(chroma_dir=d, collection_name=c, use_query_expansion=False, use_reranker=False)


def _router(store: str):
    d, c = STORES[store]
    return AdaptiveQueryRouter(chroma_dir=d, collection_name=c)


def run_benchmarks() -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    for store in STORES:
        for mode, factory in (("dense", _dense), ("hybrid", _hybrid), ("router", _router)):
            key = f"{store}_{mode}"
            print(f"[benchmark] {key}")
            results[key] = evaluate_with_strict_denominator(factory(store))
    return results


def run_gap_queries() -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for store in STORES:
        dense = _dense(store)
        hybrid = _hybrid(store)
        store_res = {}
        for qid, theme, q in GAP_QUERIES:
            entry = {"theme": theme, "query": q}
            for mode, ret in (("dense", dense), ("hybrid", hybrid)):
                hits = ret.retrieve(q, top_k=5)
                entry[mode] = [
                    {
                        "rank": i + 1,
                        "source_document": h.source_document,
                        "page_number": h.page_number,
                        "section": h.section,
                        "similarity_score": round(float(h.similarity_score), 4),
                        "is_new_source": h.source_document in NEW_SOURCES,
                        "official_report_number": (h.metadata or {}).get("official_report_number", ""),
                        "evidence_category": (h.metadata or {}).get("evidence_category", ""),
                        "excerpt": (h.text or "")[:400].replace("\n", " "),
                    }
                    for i, h in enumerate(hits)
                ]
            store_res[qid] = entry
        out[store] = store_res
    return out


def main() -> None:
    gap = run_gap_queries()
    Path("data/output").mkdir(parents=True, exist_ok=True)
    with open("data/output/core_final_gap_closure_raw.json", "w", encoding="utf-8") as f:
        json.dump(gap, f, indent=2, ensure_ascii=False)
    print("Saved data/output/core_final_gap_closure_raw.json")

    bench = run_benchmarks()
    summary = {"frozen_benchmark": "tests/retrieval_benchmark_v1.json (unmodified)", "results": bench}
    with open("data/output/core_final_benchmarks.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 92)
    print(f"{'Configuration':<22} | {'P@1':>6} | {'P@3':>6} | {'R@3':>6} | {'R@5':>6} | {'MRR':>7} | focus categories (P@3)")
    for k, d in bench.items():
        m = d["evaluable_metrics"]
        cats = {c: v["p3"] for c, v in d["per_category"].items() if any(f in c for f in FOCUS_CATEGORIES)}
        print(f"{k:<22} | {m['p1']*100:6.1f} | {m['p3']*100:6.1f} | {m['r3']*100:6.1f} | {m['r5']*100:6.1f} | {m['mrr']:7.4f} | {cats}")


if __name__ == "__main__":
    main()
