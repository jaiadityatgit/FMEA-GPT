# Phase 5F Implementation Report — Provenance Audit, Benchmark Freeze & Knowledge Integration

**Document ID**: `DOC-P5F-IMPL-001`  
**Phase**: 5F (Validation & Integration Audit)  
**Status**: COMPLETE & VERIFIED  
**Repository**: `C:\fmeagpt`  
**Audit Date**: October 2026  

---

## 1. Executive Summary

Phase 5F executes a comprehensive provenance audit, benchmark freeze, and knowledge integration review for FMEA-GPT before acquiring additional knowledge sources.

### Key Audit Findings & Architectural Actions
1. **Source Identifiers Corrected**: The primary blade life technical publication was cataloged under the incorrect report number `NASA-TP-2013-217830`. Authoritative NASA NTRS records confirm the official report number is **`NASA/TP-2013-217030`** (Center Report Number `E-15972-2`, NTRS ID `20130013703`, authored by Erwin V. Zaretsky, Jonathan S. Litt, Robert C. Hendricks, and Sherry M. Soditus). Metadata in `data/metadata/sources.json` has been updated while maintaining `legacy_id` for backward compatibility.
2. **Dataset Population Exaggeration Resolved**: Phase 5E documentation previously claimed Zaretsky et al. analyzed "1,200+ blade sets." An exhaustive textual audit proved the dataset contains **16 engines, 16 HPT Stage 1 blade sets, 82 blades per set, and 1,312 total blades audited**, with **111 observed failed blades (8.46%)** and **1,201 unfailed (censored) blades (91.54%)**. The prior statement was an **82× exaggeration** conflating total individual blades with complete blade sets.
3. **Canonical Benchmark Frozen**: Denominator drift between Phase 5C (29 queries), Phase 5D (30/32 queries), and Phase 5E was resolved by creating **`tests/retrieval_benchmark_v1.json`**. The canonical evaluation population is permanently frozen at **32 queries** (30 evaluable queries, 2 verified open corpus gaps, 0 negative controls).
4. **All 6 Baselines Recomputed**: All retrieval configurations (Phase 5C Dense, Phase 5D Sectioned Dense, Phase 5D Hybrid, Phase 5E Sectioned Dense, Phase 5E Hybrid, Phase 5E Adaptive Router) were re-evaluated on the exact same population. On the 30 evaluable queries, Phase 5E Hybrid achieved the highest Recall@5 (**63.4%** vs. 56.6% in 5C), and Phase 5E Adaptive Router achieved the highest Precision@1 (**53.3%**) and Precision@3 (**45.6%**).
5. **Production Path Formally Integrated**: The audit discovered that `src/server/main.py` and default components previously defaulted to `data/chroma_db` (the baseline 8-document store), meaning Phase 5E sources were **not** actively retrieved during normal operation. A clean production configuration (`RAGConfig.get_production_config()`) was established and wired into the FastAPI backend, pointing explicitly to `data/chroma_db_phase5e`.
6. **Criticality Formula Provenance & Scope Protection**: In the MIL-STD-1629A equation $C_m = \beta \times \alpha \times \lambda_p \times t$, all four parameters are now represented as independent data models with units and assumption status. $\beta = 1.0$ is strictly tagged as an **`ASSUMPTION`** (worst-case bound under Table 102.1), not empirical fleet probability. Reliability scope protection (`enforce_reliability_scope`) prevents generic literature failure rates from being silently assigned to CFM56 P/N `301-789-204-0`.
7. **End-to-End HPT Trace Verified**: Fresh analysis of CFM56 HPT Stage 1 Rotor Blade (P/N `301-789-204-0`) demonstrated complete evidence provenance. TMF (FM-HPT-001) and Oxidation (FM-HPT-004) cite NASA publications. Automated scanning confirmed **0 unsupported dogmatic generalizations**.
8. **Hidden Heuristics Classified**: 160 occurrences across `src/` were audited and classified into the 6 standard engineering tiers.
9. **Zero Failing Tests**: Added `tests/test_phase5f_validation.py` containing 12 comprehensive validation tests. All 129 tests across the repository pass.

---

## 2. Recomputed Retrieval Benchmark Summary

Executed on `tests/retrieval_benchmark_v1.json` across identical queries:

| Metric | Phase 5C Dense | Phase 5D Sectioned Dense | Phase 5D Hybrid | Phase 5E Sectioned Dense | Phase 5E Hybrid | Phase 5E Adaptive Router |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Precision @ 1 (Evaluable $N=30$)** | 50.0% | 53.3% | 46.7% | 50.0% | 50.0% | **53.3%** |
| **Precision @ 3 (Evaluable $N=30$)** | 43.3% | 38.9% | 42.2% | 40.0% | 44.4% | **45.6%** |
| **Recall @ 3 (Evaluable $N=30$)** | 44.1% | 46.4% | 49.6% | 47.2% | **52.1%** | 50.9% |
| **Recall @ 5 (Evaluable $N=30$)** | 56.6% | 55.1% | 61.8% | 57.4% | **63.4%** | 57.3% |
| **MRR (Evaluable $N=30$)** | 0.5667 | 0.5872 | 0.5578 | **0.6011** | 0.5911 | 0.5956 |
| **Precision @ 1 (Strict $N=32$)** | 46.9% | 50.0% | 43.8% | 46.9% | 46.9% | **50.0%** |
| **Recall @ 5 (Strict $N=32$)** | 53.1% | 51.6% | 57.9% | 53.8% | **59.4%** | 53.7% |
| **MRR (Strict $N=32$)** | 0.5312 | 0.5505 | 0.5229 | **0.5635** | 0.5542 | 0.5583 |
| **Mean Latency (ms)** | 424.1 ms | 421.6 ms | 454.1 ms | **392.3 ms** | 446.3 ms | 456.8 ms |

---

## 3. Production Retrieval Path Integration Verification

Prior to Phase 5F, `src/server/main.py` instantiated `RAGConfig()`, which defaulted to `data/chroma_db`. 

### Resolution
1. Created `RAGConfig.get_production_config()` which deterministically selects `data/chroma_db_phase5e` when available, falling back to `phase5d` and base.
2. Updated `src/server/main.py` to use `RAGConfig.get_production_config()`.
3. Executed verification on the 5 required technical queries:

| Required Verification Query | Top Retrieved Document | Page | Similarity | Section / Topic |
| :--- | :--- | :---: | :---: | :--- |
| **`high pressure turbine blade thermomechanical fatigue`** | `NASA_TP_2013_217830_Turbine_Blade_Life.pdf` | 28 | 69.7% | Abstract / Commercial CFM56 T-1 Fleet Removal |
| **`CFM56 turbine blade life thermal mechanical fatigue`** | `NASA_TP_2013_217830_Turbine_Blade_Life.pdf` | 28 | 63.9% | Abstract / Weibull Life Estimation |
| **`turbine blade internal cooling passage heat transfer`** | `NASA_Internal_Cooling_Passages_Heat_Transfer.pdf` | 12 | 78.1% | Objectives / Serpentine Rotating Rig Convection |
| **`cooling passage flow starvation`** | `NASA_Internal_Cooling_Passages_Heat_Transfer.pdf` | 5 | 51.2% | Nomenclature / Flow Conditions for Scaled Rotor |
| **`turbine blade oxidation erosion`** | `NASA_TP_2013_217830_Turbine_Blade_Life.pdf` | 13 | 57.2% | § 5.2 / T-1 Blade Failure Removal Causes |

---

## 4. Criticality Formula & Parameter Integrity

### Independent Input Representation
In `src/agents/state.py`:
```python
class CriticalityInputParameter(BaseModel):
    parameter_name: str
    symbol: str
    value: Optional[float] = None
    unit: str = "dimensionless"
    source: str = ""
    scope: ReliabilityScope = ReliabilityScope.WORST_CASE_BOUND
    is_measured: bool = False
    assumption_status: str = "ASSUMPTION"
    rationale: str = ""
```

### Invariants Established
1. $\beta = 1.0$ is strictly an `ASSUMPTION` representing Table 102.1 conditional probability bound for actual loss of mission given failure occurrence. It is never empirical fleet failure probability.
2. `enforce_reliability_scope(target_pn, source_pn, scope)` downgrades generic literature failure rates to `ReliabilityScope.GENERIC_TURBINE_BENCHMARK`, preventing silent attribution as `PART_SPECIFIC_MEASURED` for CFM56 P/N `301-789-204-0`.
3. Expanded `tests/formula_ground_truth.json` from 3 to 10 audited aerospace formulas with full unit and page references.

---

## 5. Hidden Heuristic Scan Classification

All 160 occurrences of target aerospace terms across `src/` were scanned and categorized:
* **`SOURCE DATA`** (18 items): Passages extracted directly from FAA ACs, EASA CS-E, MIL-STD-1629A, and NASA technical publications.
* **`INDEXING METADATA`** (24 items): Document titles, publisher tags, section headers, and NTRS identifiers.
* **`DISCOVERY HEURISTIC`** (38 items): Candidate mode generators in `candidate_generator.py` and `local_synthesizer.py`.
* **`VALIDATION RULE`** (32 items): Verification invariants in `claim_verifier.py` (thematic mismatch rules, entity checking).
* **`ASSUMPTION`** (28 items): Operating profile assumptions, worst-case $\beta = 1.0$ conditional bounds, and qualitative criticality matrix positions.
* **`UNVERIFIED ENGINEERING KNOWLEDGE`** (20 items): Fallback maintenance task descriptions (e.g., EMM § 72-51-01 blend repair) used when external LLM is offline, explicitly tagged as `DOMAIN_HEURISTIC` and `mode_status = AnalysisStatus.INFERRED`.

---

## 6. Regression Testing Summary

| Test File | Total Tests | Passed | Failed | Test Coverage Domain |
| :--- | :---: | :---: | :---: | :--- |
| `tests/test_fmea_agent.py` | 7 | 7 | 0 | Graph orchestration and end-to-end flow |
| `tests/test_formula_extraction.py` | 26 | 26 | 0 | Greek normalization, formula detection, ground truth |
| `tests/test_phase5a_schema.py` | 10 | 10 | 0 | Schema models, CIL, legacy RPN, validation |
| `tests/test_phase5b_reasoning.py` | 17 | 17 | 0 | Claim support, anti-cheating, adversarial components |
| `tests/test_phase5c_hardening.py` | 10 | 10 | 0 | Adversarial attacks, deterministic claim checking |
| `tests/test_phase5d_retrieval.py` | 12 | 12 | 0 | Sectioned chunking, BM25, hybrid fusion, reranking |
| `tests/test_phase5e_knowledge.py` | 18 | 18 | 0 | NASA sources, adaptive query routing, formula extraction |
| `tests/test_phase5f_validation.py` | 12 | 12 | 0 | Source identifiers, population audit, benchmark freeze |
| `tests/test_rag.py` | 9 | 9 | 0 | Loader, chunker, vector store, config |
| `tests/test_server.py` | 8 | 8 | 0 | FastAPI endpoints, health, generation, exports |
| **Total Test Suite** | **129** | **129** | **0** | **100% Pass Rate** |

---

## 7. Open Corpus Gaps & Future Phase 5G Recommendation

### Verified Open Corpus Gaps
* **`RET-13`**: *CFM56 HPT blade dovetail contact mechanics, contact pressure distribution, and shear stress at fir-tree serration flanks under centrifugal blade pull.*
* **`RET-14`**: *Turbine blade fir-tree dovetail root fretting fatigue, micro-slip amplitude, and coefficient of friction degradation under engine cyclic thermal and vibrational loading.*

### Is New Document Acquisition Justified?
**No new document acquisition should be conducted immediately.**
While dovetail fretting is an open corpus gap, Phase 5E sources (Zaretsky et al. TMF, Moreno HOST creep-fatigue, Johnson & Wagner cooling passages) have only just been canonically audited and integrated into the production path. The existing corpus now reliably grounds:
* Thermal-mechanical fatigue cracking
* Gas turbine hot-section creep
* Blade internal cooling flow starvation
* Oxidation, erosion, and TBC spallation
* Uncontained rotor burst and casing containment
* Qualitative and quantitative MIL-STD-1629A criticality

### Recommended Phase 5G Scope
1. **Interactive Evaluation Dashboard**: Benchmark visualization tool to allow human engineers to inspect retrieved evidence passages alongside generated failure modes.
2. **Targeted Fretting Acquisition Only If User-Approved**: If and only if the user approves addressing the contact mechanics gap, acquire a single targeted publication: *NASA/CR-2005-213651 (Fretting Fatigue of Gas Turbine Blade Attachments)*.
