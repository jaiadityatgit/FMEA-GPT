# Phase 5E — Engineering Knowledge Architecture

## 1. Overview and Core Principles

Phase 5E establishes an evidence-first, mathematically-grounded knowledge architecture for FMEA-GPT. Rather than indiscriminately ingesting technical documents or expanding the corpus arbitrarily, Phase 5E directly targets the verified empirical gaps identified in the Phase 5D benchmark:

1. **Thermal Fatigue / Thermomechanical Fatigue (TMF)** in hot gas path turbine airfoils
2. **Turbine Blade Internal Cooling Physics** and passage blockage mechanics
3. **Structured Mathematical Equations and Criticality Formulations** with full parameter provenance
4. **Empirical Field Reliability Distributions** without synthetic failure-rate fabrication

---

## 2. Multi-Store Vector Architecture

To ensure strict regression control and experimental isolation (Rule 15), Phase 5E maintains isolated vector database stores:

```text
data/
├── chroma_db/                         # Phase 5C Baseline (Fixed-size sliding window, 8 documents, 1,481 chunks)
├── chroma_db_phase5d_sectioned/       # Phase 5D Selected Architecture (Section-aware, 8 documents, 1,523 chunks)
└── chroma_db_phase5e/                 # Phase 5E Expanded Knowledge Base (11 documents, 1,825 chunks, formula-enriched)
```

The baseline collections remain unmodified, ensuring exact reproducibility of previous benchmark results.

---

## 3. Technical Source Hierarchy & Metadata Schema

Every indexed chunk in `data/chroma_db_phase5e` preserves the hierarchical structure of technical engineering literature:

| Metadata Field | Type | Description | Values / Examples |
| :--- | :--- | :--- | :--- |
| `source_document` | `str` | Normalized filename of authoritative source | `NASA_TP_2013_217830_Turbine_Blade_Life.pdf` |
| `source_id` | `str` | Unique catalog identifier from `sources.json` | `NASA-TP-2013-217830` |
| `source_authority` | `str` | Regulatory or scientific authority basis | `NASA Glenn Research Center`, `DoD`, `FAA`, `EASA` |
| `page_number` | `int` | Physical PDF page number (1-indexed) | `1` to `224` |
| `section_id` | `str` | Hierarchical section numbering | `Task 102`, `Section 3.2.1`, `Chapter 4` |
| `section_title` | `str` | Human-readable section heading | `Mode Criticality Number`, `Heat Transfer in Cooling Passages` |
| `engineering_domain` | `str` | Technical domain classification | `turbine_blade`, `cooling`, `fatigue`, `safety_analysis` |
| `contains_equations` | `bool` | True if chunk contains mathematical equations | `True` / `False` |
| `contains_tables` | `bool` | True if chunk preserves structured tabular data | `True` / `False` |
| `phase` | `str` | Ingestion pipeline phase | `5E` |

---

## 4. Technical Document Preprocessing Pipeline

```text
[Raw PDF: NASA / FAA / MIL-STD]
              │
              ▼
    [Document Loader (pypdf)]
              │
              ▼
   [Section & Heading Detection]
              │
              ├────────────────────────────────────────┐
              ▼                                        ▼
   [Text Section Chunker]                  [Formula Extractor]
   (Section-boundary aware,                (Greek normalization,
    900-char target, 180 overlap)           known pattern matching,
              │                             variable extraction)
              │                                        │
              ▼                                        ▼
   [Chunk Formulation] ◄─────────────────── [Formula Enrichment]
              │                             (Appends structured
              ▼                              machine representation)
   [ChromaDB Ingestion (Phase 5E Store)]
              │
              ├── Collection: fmea_aerospace_knowledge_phase5e
              ├── Embedding: all-MiniLM-L6-v2 (ONNX CPU)
              └── Distance Metric: Cosine
```

---

## 5. Mathematical & Formula Provenance

Formula extraction operates as a deterministic enrichment layer during technical ingestion:
1. **Symbolic Normalization:** Greek characters ($\alpha, \beta, \lambda, \sigma, \mu$) are converted to canonical ASCII equivalents (`alpha`, `beta`, `lambda_p`, `sigma`) while preserving original display forms.
2. **Structured Provenance:** Every extracted formula is assigned a unique `formula_id` (e.g., `FORM-934c7b80a6b9`) retaining document, page number, variable definitions, and confidence level (`extracted`).
3. **Enriched Indexing:** Formula chunks include searchable blocks pairing display representations (`Cm = β × α × λp × t`) with explicit variable definitions (`beta = conditional probability of mission loss`, `lambda_p = part failure rate`).

---

## 6. Deterministic Adaptive Query Routing Architecture

The adaptive retrieval engine dynamically routes queries based on structural features rather than opaque LLM routing:

```text
                              Incoming Engineering Query
                                           │
                                           ▼
                            [Rule-Based Query Classifier]
                                           │
              ┌────────────────────────────┼────────────────────────────┐
              ▼                            ▼                            ▼
      [Formula Query]             [Terminology Heavy]           [General Fact]
       • equation keywords         • acronyms, standards         • failure modes
       • criticality math          • multi-word mechanisms       • general physics
       • Greek variables           • ATA codes, CIL/SFP          • inspection
              │                            │                            │
              ▼                            ▼                            ▼
     [Hybrid BM25 + Dense]        [Hybrid + Terminology]        [Section-Aware Dense]
      Exact token & symbol         Query expansion with          HNSW cosine semantic
      matching + semantic          synonyms & regulatory links   similarity over chunks
              │                            │                            │
              └────────────────────────────┼────────────────────────────┘
                                           ▼
                            [Reciprocal Rank Fusion (RRF)]
                                           │
                                           ▼
                           [Inspectable Retrieval Result]
                            (includes routing rationale)
```

---

## 7. Corpus Inventory Summary (Phase 5E)

| Document | Authority | Category | Pages | Chunks | Formulas |
| :--- | :--- | :--- | :---: | :---: | :---: |
| `MIL-STD-1629A.pdf` | DoD | Methodology & Criticality | 54 | 148 | 21 |
| `NASA-STD-8729.1A.pdf` | NASA | R&M, CIL, SFP | 52 | 144 | 4 |
| `FAA_AC_25.1309-1A.pdf` | FAA | System Safety | 19 | 49 | 2 |
| `FAA_AC_25.1309-1B.pdf` | FAA | System Safety (2024) | 75 | 185 | 3 |
| `FAA_AC_33.75-1A.pdf` | FAA | Engine Safety Analysis | 15 | 38 | 0 |
| `EASA_CS-E_Amnd5_EasyAccessRules.pdf` | EASA | Engine Certification | 224 | 557 | 7 |
| `NASA_ASRS_Maintenance_Incident_Reports.pdf` | NASA | Service Difficulty | 22 | 58 | 0 |
| `NASA_C-MAPSS_Damage_Propagation_Modeling.pdf` | NASA | Degradation Modeling | 9 | 26 | 2 |
| `NASA_TP_2013_217830_Turbine_Blade_Life.pdf` *(New)* | NASA GRC | Turbine Blade TMF & Life | 24 | 64 | 2 |
| `NASA_Fatigue_Life_Prediction_Hot_Section.pdf` *(New)* | NASA/UTC | Hot Section Creep-Fatigue | 6 | 16 | 0 |
| `NASA_Internal_Cooling_Passages_Heat_Transfer.pdf` *(New)* | NASA/UTRC | Internal Cooling Physics | 118 | 340 | 0 |
| **Total** | | | **618** | **1,825** | **41** |
