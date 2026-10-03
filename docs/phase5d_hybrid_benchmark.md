# Phase 5D — Hybrid Retrieval Benchmark Report

## 1. Executive Summary

Phase 5D evaluated lexical BM25 retrieval combined with dense semantic retrieval via Reciprocal Rank Fusion ($k=60$) over 1,523 section-aware chunks in `data/chroma_db_phase5d_sectioned`.

Evaluation was performed across the complete Phase 5C evaluation benchmark (29 evaluated queries, 3 identified corpus-gap negative controls across 14 technical domains).

## 2. Overall Performance Comparison

| Metric | Dense Baseline (Phase 5C) | Section-Aware Dense | Hybrid (Dense + BM25 RRF) | Delta (Hybrid vs Dense Baseline) | Delta (Hybrid vs Section Dense) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Precision@1** | 51.7% | **55.2%** | 48.3% | -3.4% | -6.9% |
| **Precision@3** | 44.8% | 40.2% | 43.7% | -1.1% | +3.5% |
| **Recall@3** | 46.5% | 48.0% | **51.3%** | **+4.8%** | **+3.3%** |
| **Recall@5** | 59.4% | 57.0% | **62.2%** | **+2.8%** | **+5.2%** |
| **MRR** | 0.5862 | **0.6075** | 0.5701 | -0.0161 | -0.0374 |
| **Mean Latency** | 357.3 ms | **321.0 ms** | 364.7 ms | +7.4 ms | +43.7 ms |

## 3. Key Findings

1. **Recall Dominance of Hybrid Retrieval:**
   - Hybrid retrieval attained **Recall@3 of 51.3%** and **Recall@5 of 62.2%**, noticeably outperforming both Dense Baseline (59.4%) and Section-Aware Dense (57.0%).
   - Lexical BM25 successfully recovers specific keyword-dense passages (e.g., specific regulation codes, part numbers, exact failure mechanisms like `bird ingestion`, `creep rupture`, `uncontained debris`) that dense cosine similarity can sometimes rank outside the top 5.

2. **Precision vs. Recall Tradeoff:**
   - Section-Aware Dense retains the highest top-rank focus (**P@1: 55.2%**, **MRR: 0.6075**), as cosine similarity over high-density section chunks excels at matching conceptual intent.
   - Hybrid fusion pulls lexical matches into rank 2 and 3, which slightly dilutes P@1 (48.3%) but significantly widens multi-document recall.

3. **Per-Category Performance Breakdown:**

| Category | Queries | Dense Baseline P@1 | Section Dense P@1 | Hybrid P@1 | Hybrid Recall@5 | Hybrid MRR |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **FOD** | 2 | 0.0% | 50.0% | 50.0% | **100.0%** | **0.6667** |
| **Creep** | 2 | 50.0% | 50.0% | 50.0% | 75.0% | **0.6667** |
| **Blade Fracture** | 3 | 100.0% | 100.0% | 100.0% | 100.0% | 1.0000 |
| **Blade Release / Uncontained** | 2 | 100.0% | 50.0% | **100.0%** | 83.3% | 1.0000 |
| **Hazardous Engine Effects** | 3 | 100.0% | 100.0% | 100.0% | 100.0% | 1.0000 |
| **Severity** | 3 | 66.7% | 66.7% | 66.7% | 83.3% | 0.7333 |
| **NDT / Inspection** | 2 | 50.0% | 50.0% | 50.0% | 50.0% | 0.5000 |
| **Single Point Failure** | 2 | 0.0% | 50.0% | 50.0% | 16.7% | 0.5000 |
| **Corrosion** | 2 | 100.0% | 100.0% | 0.0% | 75.0% | 0.3750 |
| **Maintenance** | 2 | 0.0% | 50.0% | 0.0% | 50.0% | 0.1667 |
| **Criticality** | 3 | 33.3% | 0.0% | 0.0% | 17.8% | 0.1944 |
| **Thermal Fatigue** | 2 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0000 |
| **Cooling System** | 1 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0000 |

## 4. Analysis of Weak Categories

- **FOD (Foreign Object Damage):** Dramatic improvement. Hybrid retrieval pushed Recall@5 to **100.0%** and MRR to **0.6667** (up from Baseline MRR of 0.125 and Recall@5 of 50.0%). Lexical BM25 effectively matched bird ingestion and foreign object terminology in CS-E 800 and AC 33.75.
- **Corrosion:** Baseline had 100% P@1. Hybrid placed the exact target document at rank 2 or 3 due to lexical competition from generic corrosion prevention passages, resulting in P@1 of 0.0% but solid Recall@5 of 75.0%.
- **Thermal Fatigue & Cooling System:** Both Dense and Hybrid failed to locate satisfactory ground truth chunks. As confirmed in Phase 5C, the current 8-document corpus lacks dedicated chapters on high-pressure turbine blade internal convective cooling geometry and transient thermal stress equations.

## 5. Provenance Integrity in Hybrid Pipeline

Each candidate returned by the hybrid engine preserves:
- `source_document`: Originating file name.
- `page_number`: Exact physical document page.
- `section`: Structured hierarchical heading (e.g., `CS-E 800 (Bird Strike and Ingestion)`).
- `distance`: ChromaDB cosine distance (float).
- `dense_score`: Normalized dense similarity ($1.0 / (1.0 + \text{distance})$).
- `bm25_score`: Raw Okapi BM25 score.
- `fusion_score`: Reciprocal Rank Fusion score ($\sum \frac{1}{60 + \text{rank}}$).

No provenance is lost, and no candidate scores are flattened into opaque values.
