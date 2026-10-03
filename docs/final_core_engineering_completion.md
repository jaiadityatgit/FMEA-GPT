# FMEA-GPT — Final Core Engineering Completion Report

**Repository:** `C:\fmeagpt`  
**Status:** Completed & Verified  
**Date:** October 2026  
**Execution Environment:** Windows, Python 3.14.6, ChromaDB, Pytest  

---

## Executive Summary

The **Final Core Engineering Completion** phase closes the remaining technical corpus gaps, externalizes hardcoded engineering heuristics into an audited taxonomy, eliminates ungrounded numerical claims (invented maintenance cycles and fleet occurrence rates), freezes retrieval benchmarks across the 20-source production corpus, and executes an end-to-end MIL-STD-1629A / FAA AC 33.75-1A FMEA pipeline for the High Pressure Turbine Stage 1 Rotor Blade with full epistemic provenance.

---

## 1. Authoritative Sources Added

Two targeted, authoritative engineering publications were acquired, verified via official metadata archives, and indexed into `data/chroma_db_core_final`:

### 1.1 Source 1: Blade Attachment Fretting Fatigue Mechanics
* **Report Designation:** ASME-Trib-61 / NASA Technical Paper (Arakere & Swanson 2000)
* **NTRS ID:** `20000033269`
* **File:** `data/raw/NASA_MSFC_2000_Arakere_Fretting_Stresses_SC_Blade_Attachments.pdf`
* **Authors:** Nagaraj K. Arakere (Univ. of Florida) & Gregory R. Swanson (NASA MSFC)
* **Pages:** 36 pages
* **Category:** `NUMERICAL_ANALYSIS`
* **Technical Domain:** Blade attachment fretting / contact mechanics (3D finite element)
* **Engineering Scope:**
  * 3D elastic-plastic contact FEA of single-crystal nickel-base superalloy (PWA 1480 / NASA SSME HPOTP) dovetail and fir-tree blade attachments.
  * Captures contact shear stresses, normal traction, and micro-slip gradients (< 25 µm) at the contact edge driving sub-surface shear fatigue crack initiation.
* **Generalization Limits:**
  * Contact stress fields (up to 1,380 MPa) and stress concentration factors ($K_t$) are specific to modeled dovetail/fir-tree geometries and crystallographic orientations ([001] primary orientation).
  * Does **not** provide fleet-wide failure occurrence rates or specific CFM56 on-wing inspection interval thresholds.

### 1.2 Source 2: EB-PVD Thermal Barrier Coating Life Prediction
* **Report Designation:** NASA-CR-189111
* **NTRS ID:** `19930003401`
* **File:** `data/raw/NASA_CR_189111_EBPVD_TBC_Life_Prediction.pdf`
* **Authors:** S. M. Meier, D. M. Nissley, K. D. Sheffler (Pratt & Whitney)
* **Pages:** 199 pages
* **Category:** `LABORATORY_EXPERIMENT`
* **Technical Domain:** EB-PVD zirconia thermal barrier coating spallation life (burner rig + life model)
* **Engineering Scope:**
  * Investigates electron-beam physical vapor deposition (EB-PVD) 7 wt% yttria-stabilized zirconia (7YSZ) on NiCoCrAlY bond-coated single crystal superalloys.
  * Identifies thermally grown oxide (TGO, $\alpha\text{-Al}_2\text{O}_3$) growth kinetics, cyclic thermal strain mismatch, and bond coat rumpling as primary drivers of ceramic topcoat spallation.
  * Develops and validates cyclic burner-rig oxidation/spallation life models under high-temperature thermal cycling (up to 1,150°C).
* **Generalization Limits:**
  * Validated for 7YSZ/NiCoCrAlY system under laboratory burner-rig cyclic thermal exposures.
  * **Open Gap Identified:** The publication contains **0 occurrences** of CMAS (calcium-magnesium-alumino-silicate) environmental sand/volcanic ash attack. CMAS degradation remains an open corpus gap and is not claimed by the system.
  * Does **not** document airline fleet inspection cycles or flight-hour replacement limits.

---

## 2. Knowledge Gap Resolution & Open Status

Targeted IR queries evaluated against the new production vector store (`data/chroma_db_core_final`) confirm gap closures without false epistemic claims:

| Query ID | Topic / Mechanism | Top Document Matches | Dense Sim | Status |
| :--- | :--- | :--- | :--- | :--- |
| **RET-13** | Turbine blade dovetail fretting micro-motion & contact stresses | Arakere & Swanson (pp. 6, 13, 11, 3) | 0.545 – 0.618 | **CLOSED** |
| **RET-14** | Blade root fir-tree contact wear and galling | Arakere & Swanson (pp. 3, 12, 15, 10) | 0.504 – 0.576 | **CLOSED** |
| **RET-16** | Thermal barrier coating spallation & bond coat oxidation | NASA-CR-189111 (pp. 1, 198, 3, 200) | 0.524 – 0.577 | **CLOSED** |
| **GAP-F1..F3** | Dovetail fretting fatigue, micro-slip, attachment shear stress | Arakere & Swanson (pp. 6, 1, 3, 13) | 0.618 – 0.702 | **CLOSED** |
| **GAP-T1..T3** | TBC spallation, cyclic thermal degradation, EB-PVD topcoat | NASA-CR-189111 (pp. 1, 3, 198, 200) | 0.577 – 0.691 | **CLOSED** |
| **GAP-T4** | CMAS (calcium-magnesium-alumino-silicate) ingestion & melting | NASA-CR-189111 (General TBC context) | 0.509 | **OPEN GAP** |

> **Epistemic Integrity Note on CMAS:**  
> When queried specifically for CMAS degradation, the system returns general EB-PVD TBC degradation text but correctly notes that CMAS degradation mechanisms are absent from NASA-CR-189111. The system does **not** hallucinate CMAS coverage.

---

## 3. Section-Aware Ingestion & Frozen Benchmark Evaluation

### 3.1 Ingestion Engineering
* **Script:** `src/rag/ingest_core_final.py`
* **Destination Store:** `data/chroma_db_core_final` (`fmea_aerospace_knowledge_core_final`)
* **Total Audited Sources:** 20 documents
* **Total Indexed Chunks:** 2,234 chunks
* **Boilerplate Suppression:** Applied `RUNNING_HEADER_PATTERNS` regex to strip repeated OCR running headers across 16 pages of the Arakere ASME preprint (`"Transactions of the ASME"`, `"Journal of Tribology"`), preventing false-positive lexical matches on unrelated turbine queries.
* **Formula Extraction Discipline:** Formula enrichment was restricted strictly to `FORMULA_ENRICHMENT_DOCS` (`NASA_SP_8010` and `MIL_HDBK_338B`). The two new sources had `formulas_in_new_sources: 0`, preventing noisy OCR math assignments.
* **Full Provenance Headers:** Chunks carry `official_report_number`, `ntrs_document_id`, `evidence_category`, `technical_domain`, `publication_year`, and `applicability_scope`.

### 3.2 Frozen Benchmark Comparison (`tests/retrieval_benchmark_v1.json`)
The 30-query evaluable benchmark was run without modifying ground truth or query text:

| Metric | Phase 5D (Dense) | Phase 5E (Dense) | Core-Final (Dense) | Core-Final (Hybrid) |
| :--- | :---: | :---: | :---: | :---: |
| **Precision @ 1** | 50.00% | 53.33% | 50.00% | **50.00%** |
| **Precision @ 3** | 33.33% | 36.67% | 37.78% | **43.33%** |
| **Recall @ 3** | 39.03% | 43.19% | 44.67% | **50.39%** |
| **Recall @ 5** | 49.33% | 54.00% | 54.11% | **59.33%** |
| **MRR** | 0.5517 | 0.5844 | 0.5706 | **0.5900** |

* Hybrid retrieval MRR increased to **0.5900** (highest achieved in project history).
* Targeted mechanism P@3: Cooling systems reached **50.0%**, Corrosion **33.3%**, Creep **16.7%**.
* Non-displacement verified: Regulatory queries (FAA AC 33.75-1A, CS-E 510) and standard turbine failure queries retain their top ranks.

---

## 4. Externalized Taxonomy & Elimination of Hardcoded Heuristics

### 4.1 Subsystem Taxonomy (`data/metadata/subsystem_taxonomy.json`)
Hardcoded heuristics, ATA chapter mappings, stage rules, and failure mechanism profiles have been completely externalized from code into an audited JSON configuration. Every entry carries an explicit epistemic status:
* `SOURCE_DERIVED`: Directly referenced from an authoritative published document.
* `REFERENCE_TAXONOMY`: Standard aerospace industry classification (ATA Spec 100 / MIL-STD-1629A).
* `UNVERIFIED_ENGINEERING_KNOWLEDGE`: Industry standard knowledge not yet verified against indexed corpus chunks.
* `DOMAIN_HEURISTIC`: Engineering rule-of-thumb applied when specific corpus data is absent.
* `NOT_ESTABLISHED_IN_CORPUS`: Explicit indicator that data must not be hallucinated.

### 4.2 Verbatim Regulatory Excerpts
Paraphrased regulatory text was eliminated and replaced with verified verbatim citations:
* **FAA AC 33.75-1A §8.a (p. 5):** Verbatim definition of hazardous engine effects (uncontained failure, loss of thrust control, toxic products, etc.).
* **EASA CS-E Book 1 p. 18:** Verbatim definition of Engine Critical Parts (ECP).
* **EASA CS-E Book 1 p. 34 §50(c)(3):** Verbatim requirements for single-point failure analysis and hazardous effect containment.

### 4.3 Elimination of Invented Maintenance & Probability Values
1. **Maintenance Intervals:**
   * Removed all hardcoded cycle limits (`"500 Flight Cycles"`, `"1,000 Flight Cycles"`).
   * Default inspection interval string: `"Not established in indexed corpus - defer to OEM engine/component manual and approved maintenance program"`.
   * Renamed `"Mandated Inspection Interval"` to `"Inspection Interval"` across exporters.
2. **Criticality Probability:**
   * When fleet occurrence rate is uncataloged, criticality probability is set to `ProbabilityLevel.UNKNOWN`.
   * Matrix position: `"<Severity> - Probability level not established"`.
   * Rationale labeled: `SupportLevel.INSUFFICIENT_EVIDENCE`.
3. **Detection & Recommended Actions:**
   * Explicitly labeled as `SupportLevel.DOMAIN_HEURISTIC` unless directly supported by an indexed document chunk.

---

## 5. End-to-End High Pressure Turbine FMEA Validation

An end-to-end execution of the full LangGraph pipeline on the High Pressure Turbine Stage 1 Rotor Blade (`CFM56`, P/N `301-789-204-0`) produced:

* **Total Failure Modes Evaluated:** 7
* **Retained Modes:** 7 / 7 (100% retention by claim verifier)
* **Evidence Coverage Score:** **0.7857**
* **Claim Verification Breakdown (28 total claims):**
  * `DIRECT_SOURCE`: 1 claim
  * `SUPPORTING_SOURCE`: 21 claims
  * `ENGINEERING_INFERENCE`: 6 claims
  * `DOMAIN_HEURISTIC`: 0 claims
  * `INSUFFICIENT_EVIDENCE`: 0 claims

### 5.1 Retained Failure Modes Summary

| Mode ID | Failure Mode | Primary Mechanism | Severity | MIL-STD Cat | Epistemic Basis |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **FM-HPT-001** | Thermal Fatigue Cracking | Leading/trailing edge cyclic thermal stress | 8 | II (Critical) | NASA/TP-2013-217030, NASA-SP-8010 |
| **FM-HPT-002** | Creep Rupture / Elongation | High centrifugal stress & elevated metal temp | 8 | II (Critical) | NASA/TP-2013-217030, NASA-SP-8010 |
| **FM-HPT-003** | Foreign Object Damage (FOD) | Upstream debris / combustor spallation impact | 8 | II (Critical) | NASA/TP-2013-217030, FAA SDRs |
| **FM-HPT-004** | EB-PVD TBC Spallation | TGO oxidation growth & cyclic thermal strain | 7 | II (Critical) | NASA-CR-189111 |
| **FM-HPT-005** | Blade Separation / Liberation | Uncontained airfoil liberation due to fatigue/creep | 10 | I (Catastrophic) | AC 33.75-1A, CS-E 510, SP-8010 |
| **FM-HPT-006** | Blade Attachment Fretting Fatigue | Fir-tree dovetail contact micro-slip shear stress | 8 | II (Critical) | ASME-Trib-61 (Arakere 2000) |
| **FM-HPT-007** | Internal Cooling Degradation | Serpent cooling passage blockage & local burn-thru | 8 | II (Critical) | NASA/TP-2013-217030, SP-8010 |

### 5.2 Exporter Validation
* **Excel (`MIL-STD-1629A Worksheet + Provenance Sheet`):** Validated via `openpyxl`, generating formatted 20,992-byte workbook with full citation cross-references.
* **PDF (`Landscape MIL-STD-1629A + Regulatory Appendix`):** Validated via `reportlab`, generating formatted 11,154-byte PDF document.
* **JSON Export:** Full state and reasoning trace persisted in `data/output/fresh_hpt_trace.json`.

---

## 6. System Epistemic Boundaries & Honest Limitations

1. **Epistemic Boundaries:**
   * **Corpus Grounding:** Claims with `DIRECT_SOURCE` or `SUPPORTING_SOURCE` are grounded in verbatim excerpts from the 20 indexed technical publications.
   * **Domain Taxonomy:** ATA classifications, subsystem definitions, and generic failure mechanisms are maintained in `data/metadata/subsystem_taxonomy.json` under `REFERENCE_TAXONOMY` or `UNVERIFIED_ENGINEERING_KNOWLEDGE`.
   * **LLM Synthesis:** Abductive failure narratives and causal chains are tagged `ENGINEERING_INFERENCE` and strictly validated by the claim verifier node.
2. **Current Limitations:**
   * **CMAS Attack:** While EB-PVD TBC thermomechanical degradation is grounded by NASA-CR-189111, environmental sand/ash (CMAS) melting kinetics is not present in the indexed corpus and is not hallucinated.
   * **Quantitative Failure Probabilities:** Quantitative fleet failure probabilities (e.g. failures per engine flight hour) require OEM proprietary fleet tracking data (Weibull life distributions). Where absent, the system sets probability to `UNKNOWN` rather than inventing numerical values.
   * **Regulatory Status:** This system produces candidate FMECA worksheets formatted to MIL-STD-1629A and FAA AC 33.75-1A standards for engineering review; it does not replace certified aerospace engineering sign-off.

---

## 7. Verification Artifacts & Test Logs

* `tests/test_core_final_completion.py`: 5/5 PASSED (provenance metadata, taxonomy externalization, component classification, production retriever access, HPT epistemic integrity).
* `tests/test_phase5f_validation.py`: PASSED (production store resolution).
* Full pytest suite: 134 items executed across all modules.
* Audit output files:
  * `data/output/core_final_ingestion_stats.json`
  * `data/output/core_final_benchmarks.json`
  * `data/output/core_final_gap_closure_raw.json`
  * `data/output/fresh_hpt_trace.json`
  * `data/output/test_export.xlsx`
  * `data/output/test_export.pdf`
