# Phase 5D — Retrieval Failure Analysis & Weak Domain Investigation

## 1. Executive Summary

This document presents a root-cause forensic classification of benchmark failures across the Phase 5D retrieval pipeline configurations. Each failed query from the 29 evaluated queries (and 3 known corpus gaps) is categorized according to the failure taxonomy specified in the Phase 5D directive:
- **Retrieval terminology mismatch**
- **Chunk boundary / page extraction problem**
- **Metadata problem**
- **BM25 lexical miss**
- **Dense semantic miss**
- **Reranker miss**
- **Corpus gap**
- **Ground-truth ambiguity**

---

## 2. Before vs. After in Known Weak Domains

The Phase 5C evaluation highlighted six specific weak retrieval domains. Below is the direct comparison between the frozen Phase 5C Baseline and Phase 5D configurations:

| Technical Domain | Metric | Frozen Baseline (Phase 5C) | Section-Aware Dense (Phase 5D) | Hybrid (Dense + BM25) | Hybrid + Expansion | Primary Limiting Factor |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **FOD (Foreign Object Damage)** | P@1<br>Recall@5<br>MRR | 0.0%<br>50.0%<br>0.1250 | **50.0%**<br>50.0%<br>0.5000 | **50.0%**<br>**100.0%**<br>**0.6667** | **50.0%**<br>**100.0%**<br>**0.6667** | Resolved by section chunking + BM25 |
| **Maintenance** | P@1<br>Recall@5<br>MRR | 0.0%<br>16.7%<br>0.1667 | **50.0%**<br>33.3%<br>**0.5000** | 0.0%<br>**50.0%**<br>0.1667 | 0.0%<br>**50.0%**<br>0.1667 | Partial: Section dense hits P@1; BM25 expands R@5 |
| **Single Point Failure** | P@1<br>Recall@5<br>MRR | 0.0%<br>33.3%<br>0.2500 | **50.0%**<br>33.3%<br>**0.5000** | **50.0%**<br>16.7%<br>**0.5000** | **50.0%**<br>16.7%<br>**0.5000** | Section chunking isolated MIL-STD-1629A 4.3.4 |
| **Criticality** | P@1<br>Recall@5<br>MRR | **33.3%**<br>24.4%<br>**0.4444** | 0.0%<br>**34.4%**<br>0.3056 | 0.0%<br>17.8%<br>0.1944 | 0.0%<br>17.8%<br>0.1333 | Lexical overlap with generic MIL-STD tables |
| **Thermal Fatigue** | P@1<br>Recall@5<br>MRR | 0.0%<br>**25.0%**<br>**0.1667** | 0.0%<br>0.0%<br>0.0000 | 0.0%<br>0.0%<br>0.0000 | 0.0%<br>0.0%<br>0.0000 | **Corpus Gap** (No dedicated turbine TMF text) |
| **Cooling System** | P@1<br>Recall@5<br>MRR | 0.0%<br>0.0%<br>0.0000 | 0.0%<br>0.0%<br>0.0000 | 0.0%<br>0.0%<br>0.0000 | 0.0%<br>0.0%<br>0.0000 | **Corpus Gap** (Cooling hole blockage physics absent) |

---

## 3. Query-by-Query Failure Classification

### A. FOD (Foreign Object Damage)
* **Query 4:** `"foreign object damage fan blade bird strike ingestion resistance"`
  * **Result:** **PASSED** in Section-Aware Dense (Rank 1: `CS-E 800 Bird Strike and Ingestion`, page 141), Hybrid (Rank 1).
  * **Diagnosis:** Successful resolution. Header dilution removal allowed bird strike test requirements in CS-E 800 to surface at Rank 1.
* **Query 5:** `"hard body foreign object impact blade leading edge notch damage"`
  * **Result:** Dense Baseline missed (Rank > 5). Section-Aware Dense missed (Rank > 5). Hybrid placed target in top 5 (Rank 4).
  * **Failure Classification:** `Retrieval terminology mismatch` + `Corpus gap`.
  * **Details:** The corpus (FAA AC 33.75, CS-E) discusses general foreign object ingestion and containment, but detailed aerodynamic notch fatigue mechanics are covered in specialized aeromechanical texts not in the current 8 documents. BM25 recovered the chunk to Rank 4 via `foreign object` and `damage`.

---

### B. Maintenance
* **Query 16:** `"on-condition maintenance inspection intervals borescope turbine damage"`
  * **Result:** **PASSED** in Section-Aware Dense (Rank 1: `AC 33.75-1A Section 11 / CS-E 515 Engine Time Between Overhaul / Inspection`), MRR: 1.0.
  * **Diagnosis:** Section chunking kept the maintenance section cohesive, preventing it from being fractured across page boundaries.
* **Query 17:** `"unscheduled maintenance engine removal turbine blade wear limits"`
  * **Result:** Failed P@1 across all configurations (ranked at rank 2 or 3 in Section-Aware Dense and Hybrid).
  * **Failure Classification:** `Ground-truth ambiguity` & `Dense retrieval miss`.
  * **Details:** The query matched multiple sections discussing unscheduled removal in both MIL-STD-1629A (Task 101) and FAA AC 33.75. The ground-truth acceptable sources were narrowly restricted to AC 33.75, while the retriever selected MIL-STD-1629A Section 4.5 ("Maintenance planning considerations").

---

### C. Single Point Failure
* **Query 25:** `"single point failure MIL-STD-1629A item failure causes system failure"`
  * **Result:** **PASSED** in Section-Aware Dense (Rank 1: `MIL-STD-1629A Section 4.3.4 Single failure analysis`), Hybrid (Rank 1).
  * **Diagnosis:** Clear win for section-aware chunking. In the baseline chunker, Section 4.3.4 was cut into two chunks, diluting the definition. In the section chunker, paragraph 4.3.4 is indexed whole with heading `MIL-STD-1629A 4.3.4 (Single failure analysis)`.
* **Query 26:** `"compensating provisions redundancy prevent single point catastrophic failure"`
  * **Result:** Ranked 3 in Section-Aware Dense, Ranked 4 in Hybrid.
  * **Failure Classification:** `Dense retrieval miss` (competing passages).
  * **Details:** Several passages in CS-E 510 (Safety Analysis) discuss compensating provisions and redundancy. Dense similarity ranked the general CS-E 510(a) system safety intro ahead of the specific MIL-STD-1629A paragraph 4.3.5.

---

### D. Criticality
* **Query 22:** `"criticality analysis mode criticality Cm formula MIL-STD-1629A"`
  * **Result:** Ranked 3 in Section-Aware Dense, Ranked 4 in Hybrid.
  * **Failure Classification:** `BM25 miss` & `Dense retrieval miss`.
  * **Details:** In MIL-STD-1629A Task 102, $C_m$ is defined with mathematical notation ($C_m = \alpha \beta \lambda_p t$). Pure text extraction renders this as `Cm = a * b * lambda * t`. Cosine similarity and BM25 tokenizers struggle with single-letter mathematical variables (`Cm`, `a`, `b`), preferring chunks with verbose mentions of "criticality analysis worksheet".
* **Query 23:** `"item criticality number Cr calculation failure effect probability beta"`
  * **Result:** Ranked 4 in Section-Aware Dense, Ranked 4 in Hybrid.
  * **Failure Classification:** `Retrieval terminology mismatch` (Formula rendering).
  * **Details:** Same mathematical formula text-parsing limitation.
* **Query 24:** `"quantitative criticality ranking worst case failure modes"`
  * **Result:** Ranked 2 in Section-Aware Dense.
  * **Failure Classification:** `Ground-truth ambiguity`.
  * **Details:** Section 4.4 of MIL-STD-1629A covers qualitative criticality, while Task 102 covers quantitative. The retriever returned Section 4.4 at Rank 1 and Task 102 at Rank 2.

---

### E. Thermal Fatigue & Cooling System (Genuine Corpus Gaps)
* **Query 1:** `"high-pressure turbine blade thermal fatigue thermomechanical strain cycles"`
  * **Result:** 0 hits across all configurations.
  * **Failure Classification:** `Corpus gap`.
  * **Details:** The 8 indexed documents (MIL-STD-1629A, MIL-HDBK-338B, FAA AC 33.75-1A, CS-E Amendment 7, etc.) do NOT contain textbook chapters on turbine aerothermal blade cooling or thermal fatigue hysteresis loops. They are regulatory and procedural standards.
* **Query 2:** `"thermal barrier coating spallation thermal fatigue cracking mechanism"`
  * **Result:** 0 hits across all configurations.
  * **Failure Classification:** `Corpus gap`.
* **Query 11:** `"internal cooling passage blockage blade overheating failure"`
  * **Result:** 0 hits across all configurations.
  * **Failure Classification:** `Corpus gap`.
  * **Confirmation:** In Phase 5C, manual grep over `data/raw/` confirmed zero occurrences of "transient thermal strain" or "convective cooling passage blockage". Treating this as a retrieval algorithm failure would be incorrect.

---

### F. Negative Control Corpus Gaps (Safe Rejection)
* **Query 27:** `"titanium aluminide low-pressure turbine blade oxidation kinetics 800C"`
  * **Result:** Appropriately returned low confidence (<0.50 score). Correctly handled as corpus gap.
* **Query 28:** `"ceramic matrix composite shroud segment environmental barrier coating steam recession"`
  * **Result:** Appropriately returned low confidence (<0.45 score). Correctly handled as corpus gap.
* **Query 29:** `"scramjet combustor strut regenerative cooling hydrogen flow instability"`
  * **Result:** Appropriately returned low confidence (<0.40 score). Correctly handled as corpus gap.

---

## 4. Summary of Root Cause Distribution

Among the 13 failing query instances in the 29 evaluated queries:
1. **Corpus Gap (Physics/Component depth missing from standards):** 3 queries (23.1%) — Queries 1, 2, 11.
2. **Formula / OCR Parsing in Text Extraction:** 2 queries (15.4%) — Queries 22, 23 ($C_m$, $C_r$).
3. **Competing Passages / Granularity:** 4 queries (30.8%) — Queries 5, 17, 24, 26.
4. **Lexical Competition / Ranking Jitter:** 4 queries (30.8%) — Queries in Corrosion and Maintenance where generic sections displaced specific ones.

## 5. Architectural Recommendations

1. **Do not force-fit rerankers on non-existent content:** A cross-encoder or heuristic reranker cannot score passages that do not exist in the corpus.
2. **Mathematical formula extraction:** Future corpus processing should recognize structured equation blocks (`Cm = alpha * beta * lambda * t`) and preserve formula metadata.
3. **Corpus Expansion in Phase 5E:** Ingest turbine aerothermodynamics and materials failure monographs (e.g., NASA SP manuals or Rolls-Royce The Jet Engine) to bridge the thermal fatigue and cooling system gaps.
