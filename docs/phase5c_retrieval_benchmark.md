# FMEA-GPT Phase 5C — Retrieval Benchmark Report

**Document ID:** DOC-PHASE5C-RETRIEVAL-001  
**Repository:** `C:\fmeagpt`  
**Evaluation Date:** October 2026  
**Status:** Measured Benchmark & Gap Analysis  

---

## 1. Executive Summary

Phase 5C establishes an empirical, quantitative retrieval benchmark for the FMEA-GPT aerospace RAG pipeline, replacing the previous arbitrary heuristic threshold (`similarity > 0.50`). 

A curated ground-truth dataset of 32 queries across 14 required aerospace failure analysis categories was evaluated against the existing ChromaDB vector index (2,446 chunks extracted from official FAA, EASA, DoD, and NASA standards). 

### Key Benchmark Metrics
* **Total Benchmark Queries:** 32 (29 evaluable against corpus, 3 identified as true `CORPUS_GAP`)
* **Precision@1:** 51.7%
* **Precision@3:** 44.8%
* **Recall@3:** 46.5%
* **Recall@5:** 59.4%
* **Mean Reciprocal Rank (MRR):** 0.5862

The evaluation confirms that while core airworthiness definitions, catastrophic hazards, blade fracture mechanics, and hot corrosion achieve high recall (MRR 0.83–1.00), retrieval struggles with high-temperature thermal cycling, foreign object damage (FOD) notch mechanics, and internal serpentine cooling channels due to chunk boundary fragmentation and terminology mismatches between regulatory and metallurgical texts.

---

## 2. Retriever Pipeline Audit & Mathematical Formulation

The retriever pipeline in [retriever.py](file:///c:/fmeagpt/src/rag/retriever.py), [vector_store.py](file:///c:/fmeagpt/src/rag/vector_store.py), and [chunker.py](file:///c:/fmeagpt/src/rag/chunker.py) operates deterministically as follows:

```text
Query String
   ↓
Local ONNX Embedding Model (sentence-transformers/all-MiniLM-L6-v2, 384 dimensions)
   ↓
L2 Normalized Embedding Vector: v_q = E(q) / ||E(q)||_2
   ↓
ChromaDB HNSW Approximate Nearest Neighbor Search (Cosine Space)
   ↓
Raw Cosine Distance: d = 1 - (v_q · v_d) ∈ [0, 2]
   ↓
Similarity Score Mapping: s = max(0.0, min(1.0, 1.0 - d))
   ↓
Passage Ranking & Top-K Cutoff: [Passage_1, Passage_2, ..., Passage_k]
```

### Mathematical Scoring & Calibration Analysis
1. **Raw Vector Distance:** ChromaDB uses HNSW with the cosine space metric:
   $$d(u, v) = 1 - \frac{u \cdot v}{\|u\|_2 \|v\|_2}$$
2. **Similarity Score Calculation:** [vector_store.py](file:///c:/fmeagpt/src/rag/vector_store.py) maps distance to similarity:
   $$\text{similarity\_score} = \max\left(0.0, \min\left(1.0, 1.0 - d\right)\right)$$
3. **Calibration Finding:** Raw cosine similarity is an uncalibrated geometric dot product in 384-dimensional Euclidean space. **It is NOT a probability, Bayesian confidence, or true accuracy.**
   - In cross-length sentence-to-paragraph retrieval, a relevant regulatory passage frequently scores between $0.45$ and $0.62$ because boilerplate regulatory header text dilutes dense token embeddings.
   - Calling raw cosine similarity "confidence" or "accuracy" is technically invalid. In Phase 5C, all user-facing interfaces and models treat this value strictly as `retrieval_score` or `uncalibrated_similarity`.

---

## 3. Retrieval Ground Truth Benchmark Dataset

The ground-truth dataset was authored in [tests/retrieval_ground_truth.json](file:///c:/fmeagpt/tests/retrieval_ground_truth.json) with 32 queries organized across 14 engineering categories (at least 2 queries per category):

| Query ID | Category | Query String | Relevant Documents | Target Pages | Granularity | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `RET-01` | thermal fatigue | thermal stress cyclic gradients transient temperature blade | `NASA-STD-8729.1A.pdf` | [48] | page | Evaluable |
| `RET-02` | thermal fatigue | high pressure turbine blade thermomechanical fatigue cracking | `FAA_AC_33.75-1A.pdf` | [11, 14] | document | Evaluable |
| `RET-03` | creep | turbine rotor stress rupture creep sustained centrifugal load high temperature | `FAA_AC_33.75-1A.pdf`, `NASA-STD-8729.1A.pdf` | [14, 48] | page | Evaluable |
| `RET-04` | creep | radial blade elongation plastic creep tip rub shroud clearance | `FAA_AC_33.75-1A.pdf` | [11, 12] | document | Evaluable |
| `RET-05` | FOD | foreign object damage bird ingestion runway debris impact compressor blade notch | `EASA_CS-E_Amnd5_EasyAccessRules.pdf` | [105, 106] | page | Evaluable |
| `RET-06` | FOD | hard body debris ingestion engine inlet leading edge impact damage | `FAA_AC_33.75-1A.pdf`, `EASA_CS-E_Amnd5_EasyAccessRules.pdf` | [14, 105] | document | Evaluable |
| `RET-07` | blade fracture | turbine blade fracture separation root crack propagation | `FAA_AC_33.75-1A.pdf` | [11, 12] | page | Evaluable |
| `RET-08` | blade fracture | catastrophic airfoil structural separation high cycle fatigue | `FAA_AC_33.75-1A.pdf`, `EASA_CS-E_Amnd5_EasyAccessRules.pdf` | [11, 105] | document | Evaluable |
| `RET-09` | blade release / uncontained debris | uncontained high-energy debris fragment hazard engine casing penetration | `FAA_AC_33.75-1A.pdf` | [10, 11] | page | Evaluable |
| `RET-10` | blade release / uncontained debris | rotor burst fragment containment kinetic energy casing containment capability | `FAA_AC_33.75-1A.pdf`, `EASA_CS-E_Amnd5_EasyAccessRules.pdf` | [10, 106] | page | Evaluable |
| `RET-11` | cooling system | compressor bleed air cooling airflow turbine casing heat dissipation | `FAA_AC_33.75-1A.pdf` | [14] | document | Evaluable |
| `RET-12` | cooling system | internal serpentine cooling passage blockage particle clogging | None | None | document | **CORPUS_GAP** |
| `RET-13` | fretting | blade root fir tree dovetail fretting wear cyclic micro-motion | None | None | document | **CORPUS_GAP** |
| `RET-14` | fretting | contact surface fretting fatigue clamping contact shear stress | None | None | document | **CORPUS_GAP** |
| `RET-15` | corrosion | hot corrosion sulfidation sodium sulfate molten salt attack superalloy | `NASA-STD-8729.1A.pdf` | [48] | page | Evaluable |
| `RET-16` | corrosion | thermal barrier coating spallation substrate oxidation hot gas path | `FAA_AC_33.75-1A.pdf`, `NASA-STD-8729.1A.pdf` | [14, 48] | document | Evaluable |
| `RET-17` | NDT / inspection | borescope optical inspection internal hot section blade trailing edge | `FAA_AC_33.75-1A.pdf` | [8, 14] | document | Evaluable |
| `RET-18` | NDT / inspection | eddy current fluorescent penetrant inspection surface crack detection depot | `MIL-STD-1629A.pdf` | [21, 22] | page | Evaluable |
| `RET-19` | maintenance | engine maintenance manual inspection intervals scheduled line maintenance | `FAA_AC_33.75-1A.pdf` | [8, 14] | page | Evaluable |
| `RET-20` | maintenance | preventive maintenance scheduled inspection flight cycles engine teardown | `MIL-STD-1629A.pdf`, `FAA_AC_33.75-1A.pdf` | [8, 20] | document | Evaluable |
| `RET-21` | hazardous engine effects | 14 CFR 33.75 hazardous engine effects uncontained failure fire toxic fumes | `FAA_AC_33.75-1A.pdf` | [10, 11] | page | Evaluable |
| `RET-22` | hazardous engine effects | EASA CS-E 510 engine safety analysis hazardous engine effect definition | `EASA_CS-E_Amnd5_EasyAccessRules.pdf` | [105, 106] | page | Evaluable |
| `RET-23` | severity | MIL-STD-1629A severity categories Category I Catastrophic Category II Critical | `MIL-STD-1629A.pdf` | [9, 10] | page | Evaluable |
| `RET-24` | severity | FAA AC 25.1309 failure condition severity catastrophic hazardous major minor | `FAA_AC_25.1309-1B.pdf` | [8, 9] | page | Evaluable |
| `RET-25` | criticality | MIL-STD-1629A Task 102 criticality analysis failure mode criticality number | `MIL-STD-1629A.pdf` | [15, 16] | page | Evaluable |
| `RET-26` | criticality | item criticality number Cr summation failure mode ratios operating time | `MIL-STD-1629A.pdf` | [16] | page | Evaluable |
| `RET-27` | single point failure | NASA-STD-8729.1A single failure point SFP Critical Items List retention | `NASA-STD-8729.1A.pdf` | [13, 14] | page | Evaluable |
| `RET-28` | single point failure | FAA AC 25.1309 single failure condition catastrophic loss of aircraft | `FAA_AC_25.1309-1B.pdf` | [11, 12] | page | Evaluable |
| `RET-29` | criticality | NASA qualitative criticality analysis Category 1 critical items list | `NASA-STD-8729.1A.pdf` | [13, 14] | page | Evaluable |
| `RET-30` | severity | MIL-STD-1629A paragraph 4.4.3 severity classification criteria | `MIL-STD-1629A.pdf` | [9, 10] | page | Evaluable |
| `RET-31` | blade fracture | 14 CFR 33.19 containment compressor and turbine rotor blade release | `FAA_AC_33.75-1A.pdf` | [10, 11] | page | Evaluable |
| `RET-32` | hazardous engine effects | uncontained high-energy debris hazardous engine effect FAA AC 33.75 | `FAA_AC_33.75-1A.pdf` | [10, 11] | page | Evaluable |

---

## 4. Benchmark Performance Metrics

Execution of [retrieval_evaluation.py](file:///c:/fmeagpt/tests/retrieval_evaluation.py) yielded the following empirical performance metrics across the 29 evaluable benchmark queries:

### Overall Metrics
* **Precision@1:** 51.7% (15 / 29)
* **Precision@3:** 44.8% (39 / 87)
* **Recall@3:** 46.5%
* **Recall@5:** 59.4%
* **Mean Reciprocal Rank (MRR):** 0.5862

### Per-Category Performance Breakdown

| Category | Query Count | Precision@1 | Precision@3 | Recall@5 | Mean Reciprocal Rank (MRR) | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **blade release / uncontained debris** | 2 | **100.0%** | **83.3%** | **83.3%** | **1.000** | Strong |
| **hazardous engine effects** | 3 | **100.0%** | **77.8%** | **88.9%** | **1.000** | Strong |
| **blade fracture** | 3 | **100.0%** | **66.7%** | **100.0%** | **1.000** | Strong |
| **corrosion** | 2 | **100.0%** | **66.7%** | **83.3%** | **1.000** | Strong |
| **severity** | 3 | 66.7% | 55.6% | 66.7% | 0.667 | Moderate |
| **creep** | 2 | 50.0% | 50.0% | 100.0% | 0.625 | Moderate |
| **NDT / inspection** | 2 | 50.0% | 50.0% | 50.0% | 0.500 | Moderate |
| **criticality** | 3 | 33.3% | 33.3% | 24.4% | 0.444 | Weak |
| **single point failure** | 2 | 0.0% | 16.7% | 33.3% | 0.250 | Weak |
| **thermal fatigue** | 2 | 0.0% | 16.7% | 25.0% | 0.167 | Weak |
| **maintenance** | 2 | 0.0% | 16.7% | 16.7% | 0.167 | Weak |
| **FOD** | 2 | 0.0% | 0.0% | 50.0% | 0.125 | Weak |
| **cooling system** | 1 | 0.0% | 0.0% | 0.0% | 0.000 | Weak |
| **fretting** | 2 | N/A | N/A | N/A | N/A | **CORPUS_GAP** |

---

## 5. Detailed Failure Analysis of Failed & Weak Queries

Each failed or weak query was inspected manually to diagnose the root cause of the retrieval deficiency:

```text
Query Breakdown Table
```

### 1. `RET-01`: Thermal Fatigue Cyclic Gradients
* **Query:** `thermal stress cyclic gradients transient temperature blade`
* **Top-1 Retrieved:** `NASA-STD-8729.1A.pdf`, Page 11 (General FMEA planning and life cycle phases)
* **Top-3 Retrieved:** `FAA_AC_33.75-1A.pdf` P12, `NASA-STD-8729.1A.pdf` P10
* **Expected Evidence:** `NASA-STD-8729.1A.pdf`, Page 48 (Degradation failure mechanisms Appendix)
* **Actual Evidence:** Administrative task planning sections from the front matter of NASA-STD-8729.1A.
* **Failure Classification:** `poor chunking / page boundary offset` & `embedding mismatch`. The technical text on thermal gradients in the NASA appendix is short and embedded in a large multi-paragraph chunk that loses dense vector similarity to generic headers.

### 2. `RET-05`: Foreign Object Damage (FOD) Bird Ingestion
* **Query:** `foreign object damage bird ingestion runway debris impact compressor blade notch`
* **Top-1 Retrieved:** `EASA_CS-E_Amnd5_EasyAccessRules.pdf`, Page 14 (Certification Specifications general index)
* **Top-3 Retrieved:** `FAA_AC_33.75-1A.pdf` P14, `EASA_CS-E_Amnd5_EasyAccessRules.pdf` P22
* **Expected Evidence:** `EASA_CS-E_Amnd5_EasyAccessRules.pdf`, Pages 105–106 (CS-E 800 Bird Strike and Ingestion Test Requirements)
* **Actual Evidence:** CS-E Table of Contents and administrative paragraphs.
* **Failure Classification:** `terminology mismatch` & `poor chunking`. CS-E 800 uses the legal phraseology "Ingestion of Birds - Large, Medium, Small" rather than "foreign object damage" or "compressor blade notch". The regulatory language does not use the colloquial word "notch".

### 3. `RET-11`: Cooling System Airflow Dissipation
* **Query:** `compressor bleed air cooling airflow turbine casing heat dissipation`
* **Top-1 Retrieved:** `FAA_AC_33.75-1A.pdf`, Page 11 (Hazardous effects list)
* **Top-3 Retrieved:** `FAA_AC_25.1309-1B.pdf` P14, `MIL-STD-1629A.pdf` P16
* **Expected Evidence:** `FAA_AC_33.75-1A.pdf`, Page 14 (Cooling system failure considerations)
* **Actual Evidence:** Rotor burst and uncontained failure paragraphs.
* **Failure Classification:** `embedding mismatch`. The vector space strongly pulls any turbine query toward high-energy uncontained debris paragraphs because those sections are dense with words like "turbine", "rotor", "casing", and "compressor".

### 4. `RET-27`: Single Point Failure (NASA-STD-8729.1A)
* **Query:** `NASA-STD-8729.1A single failure point SFP Critical Items List retention`
* **Top-1 Retrieved:** `NASA-STD-8729.1A.pdf`, Page 5 (Scope and applicability)
* **Top-3 Retrieved:** `NASA-STD-8729.1A.pdf` P6, `NASA-STD-8729.1A.pdf` P13
* **Expected Evidence:** `NASA-STD-8729.1A.pdf`, Page 13 (§ 13 Critical Items List)
* **Actual Evidence:** P13 was retrieved at rank 3, missing the top-1 cutoff.
* **Failure Classification:** `query formulation`. Dense embedding of acronym "SFP" alongside standard name diluted the specific section relevance.

---

## 6. Failure Distribution & Diagnosis

Categorization of all 14 failed/weak queries reveals the dominant mechanisms driving retrieval degradation:

| Failure Mode Category | Count | Percentage | Primary Technical Driver |
| :--- | :---: | :---: | :--- |
| **Poor Chunking / Page Boundary Offset** | 10 | 71.4% | 500-token fixed chunks cut across technical sections; table of contents headers dilute body text. |
| **Embedding Mismatch** | 2 | 14.3% | Cross-length sentence-to-paragraph vector dilution in `all-MiniLM-L6-v2`. |
| **Terminology Mismatch** | 2 | 14.3% | Discrepancy between engineering physics terms ("notch", "cyclic thermal stress") and regulatory legal standards ("CS-E 800 Ingestion", "compliance demonstration"). |
| **Corpus Gap** | 3 | — | Physical phenomena absent from public standard PDFs. |

---

## 7. Corpus Gaps Documented

The benchmark explicitly verified three true corpus gaps where no relevant passages exist in the indexed database:

1. **`RET-12`: Internal Serpentine Cooling Passage Blockage (CMAS Vitrification)**
   - *Status:* `CORPUS_GAP`
   - *Reason:* Public regulatory standards (FAA AC 33.75-1A, EASA CS-E, MIL-STD-1629A) mandate general cooling airworthiness safety criteria but do not describe the specific chemical physics of calcium-magnesium-alumino-silicate (CMAS) environmental dust melting and blocking film cooling holes.
2. **`RET-13`: Dovetail Slot / Blade Root Fretting Wear**
   - *Status:* `CORPUS_GAP`
   - *Reason:* Fretting wear and fretting fatigue in turbine fir-tree root attachments are detailed in proprietary OEM engine overhaul manuals (EMM § 72-51) and metallurgical research papers, not in high-level system safety standards.
3. **`RET-14`: Contact Surface Fretting Fatigue Clamping Stress**
   - *Status:* `CORPUS_GAP`
   - *Reason:* Contact shear stress and micro-slip fatigue mechanics are absent from the indexed regulatory documents.

> **Integrity Rule:** In accordance with Phase 5C Rule 3, no external PDFs were downloaded to inflate benchmark scores. These gaps are recorded as permanent corpus boundaries.

---

## 8. Summary of Retrieval Limitations

1. **Regulatory Bias:** The corpus is heavily weighted toward high-level system safety regulations (`14 CFR § 33.75`, `EASA CS-E 510`, `MIL-STD-1629A`). While excellent for severity classification and regulatory hazard tiers, it lacks low-level mechanical physics equations.
2. **Dense Header Dilution:** Standard PDF chunking (500 tokens, 100 overlap) frequently captures repetitive document title headers (`DEPARTMENT OF DEFENSE`, `MIL-STD-1629A`), depressing cosine similarity for specific engineering queries.
3. **Lack of Calibration:** Raw similarity scores cannot be compared across different documents; a score of $0.55$ in FAA AC 33.75-1A represents a direct verbatim match, whereas a score of $0.55$ in MIL-STD-1629A represents a broad conceptual alignment.
