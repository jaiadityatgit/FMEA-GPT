# Phase 5D — Retrieval Experimentation Report

## 1. Overview & Objective

Phase 5D evaluated five architectural modifications to the retrieval pipeline against the frozen Phase 5C baseline:
1. **Section-Aware Chunking** (hierarchical regex extraction, header dilution removal, cross-page stitching).
2. **Hybrid Lexical Retrieval** (local Okapi BM25 with Reciprocal Rank Fusion, $k=60$).
3. **Controlled Terminology Expansion** (domain-specific aerospace synonym dictionary).
4. **Lightweight Local Reranker** (multi-feature candidate re-scoring).
5. **Combined Configurations** (hybrid + expansion + reranker).

Evaluation was performed on the full benchmark suite comprising 29 evaluated queries and 3 adversarial corpus gaps across 14 technical domains.

---

## 2. Experimental Results & Ablation Summary

The table below compiles the empirical metrics and CPU latency measurements across all evaluated configurations:

| Configuration | P@1 | P@3 | R@3 | R@5 | MRR | Mean Latency | Median Latency | P95 Latency | Status / Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **A. Existing dense baseline (Phase 5C)** | 51.7% | 44.8% | 46.5% | 59.4% | 0.5862 | 357.3 ms | 349.0 ms | 419.1 ms | Original baseline |
| **B. Section-aware dense** | **55.2%** | 40.2% | 48.0% | 57.0% | **0.6075** | **321.0 ms** | **313.8 ms** | **399.6 ms** | **Selected Default (Precision/MRR)** |
| **C. Hybrid retrieval (Dense + BM25)** | 48.3% | 43.7% | 51.3% | 62.2% | 0.5701 | 364.7 ms | 363.6 ms | 403.9 ms | **Selected High-Recall Mode** |
| **D. Hybrid + Terminology Expansion** | 44.8% | 43.7% | 51.7% | **65.6%** | 0.5534 | 384.5 ms | 382.2 ms | 436.3 ms | Highest multi-doc recall |
| **E. Hybrid + Reranker** | 48.3% | 40.2% | 45.5% | 57.6% | 0.5609 | 384.5 ms | 377.9 ms | 443.7 ms | **REJECTED** (Lower MRR, higher latency) |
| **F. Hybrid + Expansion + Reranker** | 48.3% | 41.4% | 49.4% | 63.3% | 0.5736 | 368.2 ms | 365.1 ms | 425.6 ms | **REJECTED** (Sub-optimal vs Section Dense) |

---

## 3. Configuration Analysis

### 3.1. Baseline (Phase 5C)
- **Database:** `data/chroma_db` (2,446 fixed 1,000-character chunks).
- **Metrics:** P@1: 51.7%, P@3: 44.8%, Recall@3: 46.5%, Recall@5: 59.4%, MRR: 0.5862.
- **Limitation:** Fixed chunking fractured paragraphs across pages, and repetitive standard headers consumed cosine space, depressing P@1 on maintenance, single point failure, and FOD.

### 3.2. Section-Aware Chunking (Configuration B)
- **Database:** `data/chroma_db_phase5d_sectioned` (1,523 structured chunks).
- **Metrics:** P@1: **55.2% (+3.5%)**, MRR: **0.6075 (+0.0213)**, Latency: **321.0 ms (-10.2%)**.
- **Impact:**
  - Removing header dilution and prepending compact section names (`[CS-E 800 (Bird Strike)]`) cleanly decoupled document identity from passage semantics.
  - The chunk count dropped by 37.7% while average chunk density increased from 611 to 916 characters.
  - 10% faster retrieval execution due to fewer vector comparisons in ChromaDB.

### 3.3. Hybrid Retrieval (Configuration C)
- **Engine:** Dense semantic + local Okapi BM25 fused via Reciprocal Rank Fusion ($k=60$).
- **Metrics:** Recall@3: **51.3% (+4.8%)**, Recall@5: **62.2% (+2.8%)**, MRR: 0.5701, Latency: 364.7 ms.
- **Impact:**
  - Excels at finding exact regulation clauses and acronyms that dense similarity alone misses.
  - Pushed FOD Recall@5 to 100.0% and Creep Recall@3 to 75.0%.
  - Introduced slight ranking jitter at rank 1 due to lexical competition from general requirements.

### 3.4. Terminology Expansion (Configuration D)
- **Impact:**
  - Maximized Recall@5 to **65.6%** (highest in the study).
  - Slightly depressed P@1 (44.8%) because appending synonym terms (e.g. `foreign object impact bird strike ingestion` to `FOD`) increased the lexical footprint, occasionally pulling tangentially related sections into rank 1.

### 3.5. Candidates Reranker Evaluation (Configurations E & F)
- **Evaluation Criteria:**
  - *Primary:* MRR improvement over Section-Aware Dense (>0.6075).
  - *Secondary:* Latency overhead (<100 ms) and Precision@3.
- **Empirical Results:**
  - Configuration E (Hybrid + Reranker) achieved MRR of 0.5609 and mean latency of 384.5 ms.
  - Configuration F (Hybrid + Expansion + Reranker) achieved MRR of 0.5736 and mean latency of 368.2 ms.
- **Formal Decision:** **The reranker was REJECTED as the primary retrieval pipeline.**
  - Neither configuration exceeded the MRR of Section-Aware Dense (0.6075).
  - Multi-feature re-scoring altered top-ranked exact hits from Section-Aware Dense, adding ~50–60 ms latency without improving ground truth alignment.
  - In an offline evidence-grounded system, simpler high-density indexing proved more effective than post-hoc scoring heuristics.

---

## 4. Final Selected Configuration

The system provides two modes configured via `configs/retrieval_phase5d.yaml`:
1. **Default Mode (Precision & MRR Optimized):**
   - **Engine:** Section-Aware Dense (`use_hybrid: false`, `use_reranker: false`).
   - **Metrics:** **P@1: 55.2%**, **MRR: 0.6075**, **Latency: 321.0 ms**.
   - **Use Case:** Interactive engineering synthesis where top-1 precision and low latency are prioritized.
2. **Deep Evidence Mode (Recall Optimized):**
   - **Engine:** Hybrid Dense + BM25 RRF (`use_hybrid: true`, `use_expansion: true`, `use_reranker: false`).
   - **Metrics:** **Recall@5: 65.6%**, **Recall@3: 51.7%**, **Latency: 384.5 ms**.
   - **Use Case:** Multi-document verification audits where exhaustive discovery of all regulatory cross-references is required.

---

## 5. Domain Breakdown Across Weak Categories

| Category | Queries | Baseline P@1 | Section Dense P@1 | Hybrid P@1 | Hybrid R@5 | Hybrid MRR | Before vs After Summary |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **FOD** | 2 | 0.0% | **50.0%** | **50.0%** | **100.0%** | **0.6667** | **Substantial gain:** P@1 0% $\to$ 50%, MRR 0.125 $\to$ 0.667 |
| **Maintenance** | 2 | 0.0% | **50.0%** | 0.0% | **50.0%** | **0.5000** | **Substantial gain:** P@1 0% $\to$ 50%, MRR 0.167 $\to$ 0.500 |
| **Single Point Failure**| 2 | 0.0% | **50.0%** | **50.0%** | 33.3% | **0.5000** | **Substantial gain:** P@1 0% $\to$ 50%, MRR 0.250 $\to$ 0.500 |
| **Severity** | 3 | 66.7% | 66.7% | 66.7% | **83.3%** | **0.8333** | **Solid gain:** MRR 0.667 $\to$ 0.833, R@5 66.7% $\to$ 83.3% |
| **Criticality** | 3 | **33.3%** | 0.0% | 0.0% | **34.4%** | 0.3056 | Mixed: Formula text extraction limits P@1; R@5 improved |
| **Thermal Fatigue** | 2 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0000 | **Corpus gap:** No turbine blade TMF text in standards |
| **Cooling System** | 1 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0000 | **Corpus gap:** Internal convective hole physics absent |

---

## 6. What Remains Broken

1. **Turbine Blade Physics & Thermodynamics Corpus Gaps:**
   - The current corpus comprises high-level systems safety standards (MIL-STD-1629A, MIL-HDBK-338B, CS-E, FAA AC 33.75).
   - Detailed heat transfer, thermal barrier coating sintering mechanisms, and internal serpentine cooling passage aerothermodynamics are simply not present in these administrative texts.
2. **Formula OCR & Single-Letter Variable Collisions:**
   - Criticality calculations ($C_m = \alpha \beta \lambda_p t$ and $C_r = \sum C_m$) are rendered into plain text as `Cm = a * b * lambda * t`. Cosine embeddings and BM25 tokenizers struggle with single-letter variable names.
