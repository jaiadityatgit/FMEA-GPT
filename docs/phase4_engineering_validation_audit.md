# FMEA-GPT Phase 4: Engineering Validation & Forensic Evidence Audit Report

**Document ID:** FMEA-GPT-AUDIT-PHASE4  
**Date:** September 30, 2026  
**Auditor:** Antigravity Advanced Agentic AI Engineering Audit Team  
**Target Repository:** `C:\fmeagpt`  
**Scope:** Phases 1–3 Implementation Audit (RAG Pipeline, LangGraph Agent, Reasoning Synthesizer, Scoring Methodology, Validation Engine, Exporters, and Test Suite)

---

## 1. Executive Summary

This forensic audit evaluates the technical integrity, evidence grounding, scoring methodology, and architectural truthfulness of the FMEA-GPT implementation completed across Phases 1 through 3.

### Core Audit Finding

The software engineering infrastructure of FMEA-GPT—including FastAPI endpoints, local ChromaDB vector storage, ONNX-based sentence embeddings, Pydantic schemas, and multi-format exporters (Excel, PDF, Markdown, Digital Twin JSON)—is robust, well-structured, and passes 100% of its unit and integration tests (24/24 passing).

**However, from an aerospace engineering and airworthiness compliance standpoint, the current system does not perform genuine, evidence-grounded reasoning.** Instead:
1. **Failure Modes are 100% Hard-Coded:** The failure modes generated for the reference CFM56 High Pressure Turbine (HPT) Stage 1 blade are not discovered, synthesized, or extracted by RAG or an LLM. They are static, hard-coded string literals embedded directly inside `src/agents/providers/local_synthesizer.py`.
2. **Citations are Detached and Illusory:** The RAG retrieval pipeline runs general queries, retrieves 4 to 8 passages, and indiscriminately pastes the exact same 4 citations across all failure modes regardless of physical relevance. A citation on uncontained turbine blade containment (FAA AC 33.75-1A p. 11) is attached equally to Thermal Mechanical Fatigue, Creep, Cooling Passage Blockage, Dovetail Fretting, FOD, and Hot Corrosion.
3. **Scoring Methodology Violates the Claimed Standard (MIL-STD-1629A):** The implementation calculates Risk Priority Numbers as $\text{RPN} = \text{Severity} \times \text{Occurrence} \times \text{Detection}$ using ordinal 1–10 scales. This is an **automotive industry methodology** (SAE J1739 / AIAG-VDA). MIL-STD-1629A contains **no RPN, no 1–10 numerical scales, and no detection multiplication factor**. MIL-STD-1629A requires 4 qualitative Roman numeral Severity Categories (I through IV) and Quantitative Criticality Numbers ($C_m = \beta \cdot \alpha \cdot \lambda_p \cdot t$) or a $4 \times 5$ qualitative criticality matrix.
4. **LangGraph Pipeline is Sequential, Not Agentic:** The workflow in `src/agents/graph.py` is a strictly linear, procedural 4-node pipeline (`START -> classify -> retrieve -> enumerate -> validate -> END`) with zero branching, zero cyclic iteration, zero self-correction, and zero autonomous tool usage.
5. **Validator Performs No Engineering Validation:** The validation node (`validator.py` and `_validate_fmea`) performs superficial string-length checks (`len(root_cause) < 10`) and basic arithmetic recalculations. It performs zero factual verification, zero citation relevance checks, and zero physical plausibility audits.
6. **Inability to Reject Unsupported Claims:** When challenged with fictitious or out-of-domain components (e.g., "F-35 Plasma Stealth Waveguide Injector" or "Aircraft Lavatory Flush Valve"), the system cannot express uncertainty or reject the query. Instead, it hallucinates generic structural failure modes, assigns spurious airworthiness classifications, attaches random FAA AC 25.1309-1B citations, and marks the report as "PASSED / 100% Compliant."

---

## 2. Actual Architecture & Execution Path

The diagram below documents the actual execution path traced through the codebase during this audit:

```
[User Input: Component Name, Part Number, Notes]
                       │
                       ▼
          [FastAPI Endpoint / CLI Entry]
   (src/server/main.py / src/agents/cli_generate.py)
                       │
                       ▼
            [FMEAGeneratorGraph.run]
             (src/agents/graph.py)
                       │
                       ▼
 ┌─────────────────────────────────────────────────────────┐
 │ Node 1: classify_component_node                        │
 │ File: src/agents/nodes/classifier.py                    │
 │ Implementation: LocalAerospaceSynthesizer._classify_... │
 │ Logic: Substring keyword matching ('turbine', 'valve') │
 │ Output: ComponentInfo (System, Subsystem, 14 CFR Class) │
 └─────────────────────────┬───────────────────────────────┘
                           │
                           ▼
 ┌─────────────────────────────────────────────────────────┐
 │ Node 2: retrieve_standards_node                         │
 │ File: src/agents/nodes/retrieval_node.py                │
 │ Implementation: AerospaceRetriever.retrieve()           │
 │ Logic: Executes 4 static semantic queries to ChromaDB   │
 │ Output: 8 retrieved chunks (_flattened_passages)        │
 └─────────────────────────┬───────────────────────────────┘
                           │
                           ▼
 ┌─────────────────────────────────────────────────────────┐
 │ Node 3: enumerate_failure_modes_node                    │
 │ File: src/agents/nodes/enumerator.py                    │
 │ Implementation: LocalAerospaceSynthesizer._synthesize.. │
 │ Logic: Returns 6 hard-coded FailureModeEntry objects    │
 │ Citation Attachment: Blindly slices retrieved_passages[:4│
 │ Output: List[FailureModeEntry] (FM-HPT-001 to 006)      │
 └─────────────────────────┬───────────────────────────────┘
                           │
                           ▼
 ┌─────────────────────────────────────────────────────────┐
 │ Node 4: validate_and_package_node                       │
 │ File: src/agents/nodes/validator.py                     │
 │ Implementation: LocalAerospaceSynthesizer._validate_fmea│
 │ Logic: Recalculates S*O*D, checks string lengths > 10   │
 │ Output: ValidationReport (is_compliant = True)          │
 └─────────────────────────┬───────────────────────────────┘
                           │
                           ▼
               [FMEAReport Data Package]
                           │
       ┌───────────────────┼───────────────────┐
       ▼                   ▼                   ▼
[Markdown Exporter]  [Excel Exporter]    [PDF Exporter]
(fmea_table.py)      (exporters_binary)  (exporters_binary)
```

### Architectural Realities Discovered

* **Graph execution is synchronous and linear:** There is no conditional routing. The graph structure is equivalent to a sequential Python function call: `validate(enumerate(retrieve(classify(input))))`.
* **RAG results are disconnected from generation:** Node 2 retrieves passages, but Node 3's synthesis engine completely ignores the semantic content of the passages. It merely takes the first 4 passages from the list and copies their metadata into the `citations` list of every hard-coded failure mode entry.
* **LLM bypass:** In default execution (`FMEA_INFERENCE_PROVIDER=local`), no language model is executed. `ExternalLLMProvider` is implemented as an OpenAI-compatible wrapper, but falls back to `LocalAerospaceSynthesizer` when no API keys are configured.

---

## 3. Failure Mode Provenance Audit

Every generated failure mode in the CFM56 High Pressure Turbine Stage 1 blade baseline was traced from user invocation to output.

### Forensic Provenance Table

| Failure Mode ID | Failure Mode Title | Generation Source | Actual Code Location | RAG Evidence Used? | Citation Relevant? | Hard-Coded? | LLM-Derived? | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **FM-HPT-001** | Thermal Mechanical Fatigue (TMF) Cracking at Airfoil Leading Edge and Cooling Holes | Hard-coded python literal | `src/agents/providers/local_synthesizer.py:157-174` | **NO** (retrieval ignored) | **NO** (Cited AC 33.75-1A p.11 rotor containment) | **YES** (100%) | **NO** (0%) | **ILLUSORY GROUNDING** |
| **FM-HPT-002** | High-Temperature Creep Elongation and Airfoil Untwist | Hard-coded python literal | `src/agents/providers/local_synthesizer.py:176-193` | **NO** (retrieval ignored) | **NO** (Cited CS-E p.195 overspeed blade shedding) | **YES** (100%) | **NO** (0%) | **ILLUSORY GROUNDING** |
| **FM-HPT-003** | Internal Serpentine Cooling Passage Blockage (Silicate / Sand Dust Deposition) | Hard-coded python literal | `src/agents/providers/local_synthesizer.py:195-212` | **NO** (retrieval ignored) | **NO** (Cited CS-E p.94 turbine service experience) | **YES** (100%) | **NO** (0%) | **ILLUSORY GROUNDING** |
| **FM-HPT-004** | Blade Root Fir-Tree Dovetail Fretting Fatigue & Root Crack | Hard-coded python literal | `src/agents/providers/local_synthesizer.py:214-231` | **NO** (retrieval ignored) | **NO** (Cited CS-E p.93 rotor life stress analysis) | **YES** (100%) | **NO** (0%) | **ILLUSORY GROUNDING** |
| **FM-HPT-005** | Foreign Object Damage (FOD) / Domestic Object Damage (DOD) Impact Notch | Hard-coded python literal | `src/agents/providers/local_synthesizer.py:233-250` | **NO** (retrieval ignored) | **NO** (Same 4 generic citations copied) | **YES** (100%) | **NO** (0%) | **ILLUSORY GROUNDING** |
| **FM-HPT-006** | Hot Corrosion (Type I / Type II) & Thermal Barrier Coating (TBC) Spallation | Hard-coded python literal | `src/agents/providers/local_synthesizer.py:252-269` | **NO** (retrieval ignored) | **NO** (Same 4 generic citations copied) | **YES** (100%) | **NO** (0%) | **ILLUSORY GROUNDING** |

### Detailed Trace: `FM-HPT-001`

```
User Input: "CFM56 High Pressure Turbine Stage 1 Rotor Blade"
    │
    ▼
classifier.py: passes component to provider
    │
    ▼
local_synthesizer.py: _classify_component matches "turbine" in text
    │
    ▼
retrieval_node.py: queries ChromaDB with 4 template strings
    ├── ChromaDB returns 8 chunks (Top chunk: FAA AC 33.75-1A Page 11 on blade containment)
    │
    ▼
enumerator.py: requests failure modes from provider
    │
    ▼
local_synthesizer.py: _synthesize_failure_modes
    ├── ignores query text and chunk contents
    ├── checks subsystem contains "turbine"
    ├── instantiates static FailureModeEntry(mode_id="FM-HPT-001", ...)
    ├── slices retrieved_passages[:4]
    └── assigns citations = citations to FM-HPT-001 through FM-HPT-006
```

**Conclusion:** The engineering concepts (thermal gradients, 0.05-inch crack limits, borescope 500 FC intervals) originate solely from pre-written strings authored by the developer in `local_synthesizer.py`. The RAG pipeline contributes zero domain intelligence to the failure mode selection.

---

## 4. Evidence-to-Claim Audit & Matrix

The audit inspected how citations are attached to claims across the 9 standard FMEA engineering fields for all failure modes.

### The Detached Citation Vulnerability

In `local_synthesizer.py` lines 121–131:
```python
citations = []
for p in retrieved_passages[:4]:
    citations.append(Citation(
        source_document=p.get("source_document", "MIL-STD-1629A.pdf"),
        doc_title=p.get("doc_title", "Aerospace Standard"),
        page_number=p.get("page_number", 1),
        publisher=p.get("publisher", "FAA/DoD"),
        similarity_score=p.get("similarity_score", 0.65),
        excerpt=p.get("text", "")[:180] + "..."
    ))
```
And then in lines 173, 192, 211, 230, 249, 268:
```python
citations=citations  # Copied identically into every FailureModeEntry
```

This creates a severe epistemic vulnerability:
$$\text{Unsupported Specific Engineering Claim} + \text{Unrelated RAG Document Chunk} = \text{Apparently Grounded Airworthiness Statement}$$

### Field-by-Field Evidence Matrix

The table below breaks down the evidentiary status of each field across the baseline CFM56 HPT failure modes:

| Field | Source Type | Evidentiary Basis | Supported by Cited Document? | Audit Assessment |
| :--- | :--- | :--- | :--- | :--- |
| **Failure Mode** | Hard-coded | Standard turbomachinery failure modes | **NO** | Plausible aerospace engineering knowledge, but hard-coded |
| **Root Cause** | Hard-coded | Engineering physics (thermal strain, CMAS, fretting) | **NO** | Accurate physics, but unsupported by attached citations |
| **Local Effect** | Hard-coded | Airfoil cracking, untwist, burnout | **NO** | Plausible, but unverified by RAG evidence |
| **Next Higher Effect** | Hard-coded | EGT increase (+15°C), vibration, casing rub | **NO** | Plausible CFM56 operational dynamics, purely heuristic |
| **End Effect** | Hard-coded | IFSD, uncontained blade release | **PARTIALLY** (FAA AC 33.75-1A mentions uncontained release) | Citations define general hazards, not specific component links |
| **Severity (1–10)** | Hard-coded | Heuristic scale (8, 7, 9, 10, 7, 6) | **NO** | Scale is automotive AIAG/VDA, not MIL-STD-1629A |
| **Occurrence (1–10)**| Hard-coded | Heuristic numbers (4, 3, 3, 2, 3, 4) | **NO** | Arbitrary integer assignments; no fleet rate or flight-hour data |
| **Detection (1–10)** | Hard-coded | Heuristic numbers (4, 3, 6, 7, 3, 4) | **NO** | Detection rating does not exist in MIL-STD-1629A |
| **RPN (S×O×D)** | Calculated | Automotive formula ($S \times O \times D$) | **NO** | Mathematically invalid for MIL-STD-1629A |
| **Recommended Action**| Hard-coded | Maintenance limits (e.g. 0.05-inch crack limit) | **NO** | Specific limits are from CFM56 EMM, not cited in RAG |
| **Inspection Interval**| Hard-coded | 500 FC, 1200 FH, 250 FC, 6000 FC | **NO** | Specific maintenance program intervals unverified by RAG |

---

## 5. Scoring Methodology Audit: MIL-STD-1629A vs. Implementation

The prompt and repository documentation repeatedly claim compliance with **MIL-STD-1629A**. This audit performed a direct textual comparison between the standard in `data/raw/MIL-STD-1629A.pdf` and the codebase.

### Forensic Finding: The System Uses Automotive AIAG RPN, Not MIL-STD-1629A

#### 1. RPN Does Not Exist in MIL-STD-1629A
A search across all 54 pages of `data/raw/MIL-STD-1629A.pdf` confirms:
* Matches for `Risk Priority Number` or `RPN`: **0 matches**.
* The term "RPN" never appears anywhere in the military standard.

#### 2. Severity Classification in MIL-STD-1629A
* **Standard Specification (MIL-STD-1629A, Task 101 § 4.4, Page 16):**
  Severity must be classified into one of four qualitative Roman numeral categories:
  * **Category I – Catastrophic:** A failure which may cause death or weapon system loss.
  * **Category II – Critical:** A failure which may cause severe injury, major property damage, or major system damage resulting in mission loss.
  * **Category III – Marginal:** A failure which may cause minor injury, minor property damage, or delay/loss of availability.
  * **Category IV – Minor:** A failure not serious enough to cause injury or system damage, but resulting in unscheduled maintenance.
* **Code Implementation:**
  In `src/agents/state.py` line 46, severity is defined as `severity: int = Field(ge=1, le=10)`. The codebase tracks a parallel string `mil_std_severity_category`, but the quantitative calculations rely entirely on the 1–10 integer scale.

#### 3. Criticality Analysis in MIL-STD-1629A
MIL-STD-1629A Task 102 (Pages 29–35) specifies two distinct approaches for criticality:
1. **Quantitative Criticality Analysis (§ 3.2, Pages 30–33):**
   Calculates the **Failure Mode Criticality Number ($C_m$)**:
   $$C_m = \beta \cdot \alpha \cdot \lambda_p \cdot t$$
   Where:
   * $\beta$ = Conditional probability of the failure effect (Table 102.1).
   * $\alpha$ = Failure mode ratio (fraction of part failure rate attributed to this mode).
   * $\lambda_p$ = Part failure rate (from MIL-HDBK-217 or empirical fleet reliability data).
   * $t$ = Operating time (mission duration in hours or operating cycles).
   The **Item Criticality Number ($C_r$)** is the sum of mode criticalities: $C_r = \sum_{j=1}^n (C_m)_j$.
2. **Qualitative Criticality Analysis (§ 3.1, Pages 29–30 & Page 35):**
   Evaluates failure probability against 5 discrete levels:
   * Level A – Frequent ($p > 0.20$)
   * Level B – Reasonably Probable ($0.10 \le p \le 0.20$)
   * Level C – Occasional ($0.01 \le p \le 0.10$)
   * Level D – Remote ($0.001 \le p \le 0.01$)
   * Level E – Extremely Unlikely ($p < 0.001$)
   Modes are mapped onto a **Criticality Matrix** (Figure 102.2, Page 35) with Severity Categories (I–IV) on the horizontal axis and Probability Levels (A–E) on the vertical axis.

#### 4. Detection Treatment
* **MIL-STD-1629A (Task 101 § 5.7, Page 23):**
  Requires recording a qualitative description of operator and maintenance detection means ("visual or audible warning devices, automatic sensing devices, sensing instrumentation, other unique indications, or none"). There is **no numerical detection rating** and **no mathematical multiplication of detection into criticality**.
* **Code Implementation:**
  In `src/agents/state.py` line 48, detection is an integer 1–10 multiplied into RPN.

#### 5. Summary Comparison Table

| Attribute | MIL-STD-1629A Standard | Current Codebase (`c:\fmeagpt`) | Source Origin of Current Code |
| :--- | :--- | :--- | :--- |
| **Severity Metric** | Categories I, II, III, IV | Integer 1 to 10 | AIAG / SAE J1739 (Automotive) |
| **Occurrence Metric**| Rate $\lambda_p$, Mode Ratio $\alpha$, or Levels A–E | Integer 1 to 10 | AIAG / SAE J1739 (Automotive) |
| **Detection Metric** | Descriptive text (§ 5.7) | Integer 1 to 10 | AIAG / SAE J1739 (Automotive) |
| **Prioritization Formula** | $C_m = \beta \alpha \lambda_p t$ or $4 \times 5$ Matrix | $\text{RPN} = S \times O \times D$ (1 to 1000) | AIAG / SAE J1739 (Automotive) |
| **CIL Threshold** | All Cat I / Cat II modes (§ 4.5.2.1) | $\text{SPF} \lor S \ge 9 \lor \text{RPN} \ge 100$ | Arbitrary heuristic |

**Verdict:** The scoring methodology claimed by the system is **factually incorrect**. The system implements an automotive FMEA methodology while labeling all outputs and reports with MIL-STD-1629A certification headers.

---

## 6. Hard-Coded Engineering Knowledge Audit

The repository was searched for hard-coded domain knowledge, physics thresholds, and specific aerospace parameters.

### Forensic Inventory of Hard-Coded Knowledge

| Engineering Knowledge Item | File Location | Line Numbers | Hard-Coded? | Evidence-Backed? | Recommendation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **CFM56 HPT Part Number (`301-789-204-0`)** | `local_synthesizer.py` | 79 | **YES** | **NO** | Allow user input / database lookup |
| **Operating Temp (1400°C) & RPM (14,500)** | `local_synthesizer.py`, `digital_twin.py` | 84, 19–20 | **YES** | **NO** | Extract from engine type certificate / spec sheets |
| **TMF Crack Limit (0.05 inches)** | `local_synthesizer.py`, `test_rag.py` | 170, 90 | **YES** | **NO** | Ground in Engine Maintenance Manual (EMM) |
| **Borescope Inspection Intervals (500 FC)** | `local_synthesizer.py` | 171, 209 | **YES** | **NO** | Ground in Maintenance Planning Document (MPD) |
| **Creep Tip Clearance & C-Check (1200 FH)** | `local_synthesizer.py` | 190 | **YES** | **NO** | Ground in MPD / C-MAPSS literature |
| **CMAS Sand Blockage (250 FC wash interval)**| `local_synthesizer.py` | 209 | **YES** | **NO** | Ground in airline desert operations ADs / SBs |
| **Fir-Tree Fretting & MoS2 / Shot Peening** | `local_synthesizer.py` | 227–228 | **YES** | **NO** | Ground in FAA 14 CFR § 33.70 life-limited part data |
| **FOD Nick Limits per EMM § 72-51** | `local_synthesizer.py` | 246 | **YES** | **NO** | Ground in CFM56 EMM Chapter 72 |
| **Hot Corrosion Na2SO4 & MCrAlY coatings** | `local_synthesizer.py` | 254, 265 | **YES** | **NO** | Ground in materials engineering literature |
| **Digital Twin Sensor Signatures** | `digital_twin.py` | 33–42 | **YES** | **NO** | Telemetry mapping must be configurable / dynamic |
| **Generic Component Fallbacks (FM-GEN-001/002)**| `local_synthesizer.py` | 275–312 | **YES** | **NO** | Must reject unsupported components instead |

### Analysis of the 8 Primary Turbomachinery Degradation Mechanisms

1. **Thermal Mechanical Fatigue (TMF):** Predefined static record; not extracted from RAG.
2. **Creep:** Predefined static record; tip rub and vibration indicators are hard-coded strings.
3. **Foreign Object Damage (FOD):** Predefined static record; notch factor $K_t > 3.0$ is hard-coded.
4. **Fretting Fatigue:** Predefined static record; bearing #4 load and MoS2 coating are hard-coded.
5. **Hot Corrosion:** Predefined static record; Na2SO4 chemistry is hard-coded.
6. **Thermal Barrier Coating (TBC) Spallation:** Bundled into FM-HPT-006 as a static string.
7. **Cooling Passage Blockage:** Predefined static record; desert CMAS mechanism is hard-coded.
8. **Fir-Tree Root Failure:** Predefined static record; single-point failure designation is hard-coded.

**Conclusion:** None of these degradation mechanisms are being discovered or synthesized dynamically. They are hard-coded templates triggered when the string `"turbine"` or `"hpt"` appears in the component name.

---

## 7. `LocalAerospaceSynthesizer` Audit

The file `src/agents/providers/local_synthesizer.py` (373 lines) was subjected to line-by-line inspection.

### Characteristics

* **Is it truly deterministic?** **YES.** Given the same string input, it executes exact deterministic conditional branches and returns identical data structures every time.
* **What rules does it contain?**
  * Substring match on `["turbine", "blade", "compressor", "hpc", "hpt", "rotor", "cfm56"]` $\rightarrow$ triggers CFM56 turbine rotor blade classification and the 6 CFM56 failure modes.
  * Substring match on `["hydraulic", "actuator", "pump", "valve"]` $\rightarrow$ triggers flight control hydraulic actuator classification.
  * Fallback $\rightarrow$ triggers generic mechanical/avionics line-replaceable unit classification and 2 generic failure modes (`FM-GEN-001` and `FM-GEN-002`).
* **How many failure modes are predefined?** Exactly **8 failure modes** exist in the entire codebase: 6 for turbine blades, and 2 generic modes.
* **Does RAG influence selection?** **NO.** RAG retrieval output has zero influence on which failure modes are selected, what root causes are assigned, or what scores are given.
* **Does RAG merely provide citations after generation?** **YES.** It takes `retrieved_passages[:4]` and attaches them indiscriminately to all entries.
* **What happens when retrieval returns irrelevant evidence?** The irrelevant evidence is accepted without validation and formatted into citations with similarity percentages displayed to the user.

### Call Graph

```
LocalAerospaceSynthesizer.generate_structured(prompt, response_model, context)
 │
 ├── Case 1: response_model == ComponentInfo
 │    └── _classify_component(prompt, context)
 │         ├── Checks substrings: "turbine", "blade", "cfm56"...
 │         ├── Checks substrings: "hydraulic", "valve", "pump"...
 │         └── Fallback: Generic LRU
 │
 ├── Case 2: response_model == List[FailureModeEntry]
 │    └── _synthesize_failure_modes(prompt, context)
 │         ├── Slices citations = retrieved_passages[:4]
 │         ├── If "turbine" in component:
 │         │    └── Returns [FM-HPT-001, FM-HPT-002, FM-HPT-003, FM-HPT-004, FM-HPT-005, FM-HPT-006]
 │         └── Else:
 │              └── Returns [FM-GEN-001, FM-GEN-002]
 │
 └── Case 3: response_model == ValidationReport
      └── _validate_fmea(prompt, context)
           ├── Recalculates expected_rpn = S * O * D
           ├── Checks len(root_cause) >= 10
           ├── Checks len(recommended_action) >= 15
           └── Returns ValidationReport(is_compliant=True)
```

---

## 8. LangGraph Pipeline Audit

The files `src/agents/graph.py`, `src/agents/state.py`, and `src/agents/nodes/*.py` were inspected.

### Graph Structure

```
START ──► [classify] ──► [retrieve] ──► [enumerate] ──► [validate] ──► END
```

### Detailed Node Specifications

| Node | Input State Keys | Output State Keys | LLM Usage | RAG Usage | Deterministic Logic | Validation Performed |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **classify** | `component_input`, `target_part_number`, `operating_notes` | `component` | None (Local Synthesizer) | None | Substring matching | None |
| **retrieve** | `component`, `component_input` | `retrieved_context`, `_flattened_passages` | None | ChromaDB query (4 template queries) | Static query construction | None |
| **enumerate** | `component`, `_flattened_passages`, `retrieved_context` | `failure_modes` | None (Local Synthesizer) | Attaches top 4 chunks as citations | Hard-coded list return | None |
| **validate** | `component`, `failure_modes` | `validation`, `final_report` | None (Local Synthesizer) | None | $S \times O \times D$ recompute, string lengths | String length $> 10/15$ |

### "Agentic" Reality Assessment

The implementation uses the `langgraph.graph.StateGraph` class, but:
* It contains **no conditional edges** (`builder.add_conditional_edges` is never called).
* It contains **no loops or retry cycles** (if validation fails, execution does not loop back to re-generate).
* It contains **no tool calling** (the synthesizer cannot choose to search for additional documents).
* It is a **strictly sequential procedural pipeline** wrapped in LangGraph syntactic abstractions. Calling this system an "agentic AI reasoning engine" is a marketing mischaracterization.

---

## 9. RAG Quality Audit

The local ChromaDB vector database (2,446 chunks, embedded with ONNX `all-MiniLM-L6-v2`) was audited by executing the 9 required representative queries.

### Similarity vs. Calibrated Probability

The system calculates:
$$\text{similarity} = \max(0.0, \min(1.0, 1.0 - \text{cosine\_distance}))$$
In the UI and exported files, this number is labeled as `Similarity: 58.7%` or implied to represent retrieval confidence.

**Critical Clarification:** In dense vector space using cosine distance, a similarity of $0.50$ (distance $0.50$) does **not** mean a $50\%$ probability of truth, nor does it imply that the passage is $50\%$ relevant. In 384-dimensional space, unrelated texts often have cosine distances between $0.40$ and $0.60$. Treating $1 - \text{distance}$ as a calibrated confidence probability is mathematically and semantically misleading.

### Forensic Query Results

| # | Query | Top Result Document & Page | Distance | "Similarity" | Actual Engineering Content | Actual Relevance |
| :- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `CFM56 HPT blade failure` | `EASA_CS-E_Amnd5_EasyAccessRules.pdf` p. 102 | 0.5219 | 47.8% | AMC E 520(c)(1) Strength – Shedding of Blades certification rules | **WEAK** (Generic blade shedding rule, not CFM56 specific) |
| 2 | `turbine blade thermal fatigue` | `EASA_CS-E_Amnd5_EasyAccessRules.pdf` p. 207 | 0.4588 | 54.1% | Consideration of high-frequency vibrations during engine endurance tests | **WEAK** (Discusses vibration testing, not thermal fatigue physics) |
| 3 | `turbine blade creep` | `EASA_CS-E_Amnd5_EasyAccessRules.pdf` p. 102 | 0.4826 | 51.7% | AMC E 520(c)(1) Shedding of Blades | **POOR** (Discusses blade shedding, no mention of creep elongation) |
| 4 | `turbine blade FOD` | `EASA_CS-E_Amnd5_EasyAccessRules.pdf` p. 125 | 0.4973 | 50.3% | Subpart E: Turbine Engines Type Substantiation Table of Contents | **IRRELEVANT** (Table of Contents / section header text) |
| 5 | `fir-tree/dovetail fretting` | `EASA_CS-E_Amnd5_EasyAccessRules.pdf` p. 192 | 0.7338 | 26.6% | Turbofan first-stage fan blade bird ingestion mass and blade twist | **COMPLETELY IRRELEVANT** (Fan blade bird strike, not HPT fretting) |
| 6 | `cooling passage blockage` | `EASA_CS-E_Amnd5_EasyAccessRules.pdf` p. 148 | 0.5433 | 45.7% | Protection devices required for CS-E 510 engine compliance | **COMPLETELY IRRELEVANT** (Engine protection devices; no cooling info) |
| 7 | `turbine blade containment` | `FAA_AC_33.75-1A.pdf` p. 11 | 0.4132 | 58.7% | Release of blades (corn-cobbed rotors) and containment ring capabilities | **HIGH** (Directly discusses blade containment and hazards) |
| 8 | `engine hazardous effects` | `FAA_AC_33.75-1A.pdf` p. 13 | 0.2958 | 70.4% | Definition of Major and Hazardous Engine Effects under 14 CFR § 33.75 | **EXCELLENT** (Defines airworthiness hazardous effect boundaries) |
| 9 | `maintenance/NDT evidence` | `FAA_AC_33.75-1A.pdf` p. 8 | 0.4799 | 52.0% | General safety analysis summary requirements for FAA submittal | **POOR** (Administrative report requirements; no NDT procedures) |

### RAG Retrieval Analysis

* **Regulatory definitions succeed:** The RAG system excels when querying broad regulatory certification terms (`engine hazardous effects`, `turbine blade containment`), returning relevant passages from FAA AC 33.75-1A with distances below $0.42$.
* **Component-specific physics fail:** When querying specific physical degradation mechanisms (`fir-tree/dovetail fretting`, `cooling passage blockage`, `turbine blade creep`), the retriever produces severe false positives, returning table of contents pages or bird-strike rules because the ingested corpus consists predominantly of high-level regulatory frameworks (CS-E, AC 33.75, AC 25.1309) rather than technical engine shop manuals or metallographic failure analyses.

---

## 10. Citation Integrity Test

Five deliberately difficult queries were executed to test whether semantic similarity generates misleading or false citations.

### Test Results

#### 1. Query: `"turbine blade creep inspection interval"`
* **Retrieved:** `EASA_CS-E_Amnd5_EasyAccessRules.pdf` p. 95 (Distance: 0.4853, Similarity: 51.5%)
* **Retrieved Content:** Subpart D: Turbine Engines – Design and Construction table of contents.
* **Integrity Evaluation:** **FAILURE.** The passage contains zero information on creep inspection intervals. Attaching this as a citation for a 1,200 Flight Hour C-Check interval is misleading.

#### 2. Query: `"CFM56 HPT blade cooling passage blockage detection"`
* **Retrieved:** `EASA_CS-E_Amnd5_EasyAccessRules.pdf` p. 159 (Distance: 0.4904, Similarity: 51.0%)
* **Retrieved Content:** Discusses finite element models of fan blades for bird ingestion certification.
* **Integrity Evaluation:** **FAILURE.** Fan blade bird strike finite element modeling has no connection to borescopic inspection or cooling passage sand blockage.

#### 3. Query: `"fir-tree dovetail fretting failure severity"`
* **Retrieved:** `MIL-STD-1629A.pdf` p. 45 (Distance: 0.5978, Similarity: 40.2%)
* **Retrieved Content:** Appendix A: General ground rules and analysis assumptions for military FMECA contracts.
* **Integrity Evaluation:** **FAILURE.** The document discusses contractor ground rules, not mechanical fretting fatigue or severity ranking.

#### 4. Query: `"thermal fatigue crack detection method"`
* **Retrieved:** `EASA_CS-E_Amnd5_EasyAccessRules.pdf` p. 93 (Distance: 0.4591, Similarity: 54.1%)
* **Retrieved Content:** Describes combined stress/temperature fatigue life calculations for engine rotor bores and rims.
* **Integrity Evaluation:** **PARTIAL / MISLEADING.** Mentions fatigue life of rotor attachments, but does not mention optical borescope inspection, Eddy Current Testing (ECT), or Fluorescent Penetrant Inspection (FPI).

#### 5. Query: `"uncontained turbine blade release catastrophic classification"`
* **Retrieved:** `EASA_CS-E_Amnd5_EasyAccessRules.pdf` p. 102 & `FAA_AC_33.75-1A.pdf` p. 11 (Distances: 0.4313, 0.4535)
* **Retrieved Content:** AMC E 520(c)(1) Shedding of blades and AC 33.75-1A blade containment requirements.
* **Integrity Evaluation:** **GENUINE SUPPORT.** Both documents directly discuss rotor blade containment and define non-containment as a Hazardous Engine Effect.

---

## 11. Unsupported-Claim Stress Test

To evaluate the system's ability to reject claims unsupported by its knowledge base, three out-of-domain / fictitious components were passed to the generator:
1. `F-35 Plasma Stealth Waveguide Injector` (Fictitious military subsystem)
2. `SpaceX Raptor Liquid Methane Turbopump Impeller` (Rocket engine turbomachinery, not civil aircraft)
3. `Commercial Aircraft Lavatory Flush Valve` (Non-propulsion cabin utility valve)

### Experimental Observations

In all three cases, the system **failed to reject the unsupported component**:

```
=== Input: Commercial Aircraft Lavatory Flush Valve ===
Classified Subsystem : Primary Flight Control Actuation
Classified System    : Flight Control / Hydraulic Power
Airworthiness Tier   : Critical Flight Control Component (14 CFR § 25.1309)
Failure Modes Generated:
  1. FM-GEN-001: Structural Fatigue Cracking (S=8, O=3, D=4, RPN=96)
  2. FM-GEN-002: Seal Degradation and Internal Fluid Leakage (S=5, O=4, D=2, RPN=40)
Attached Citations   :
  - FAA_AC_25.1309-1B.pdf p. 74
  - EASA_CS-E_Amnd5_EasyAccessRules.pdf p. 52
Validation Result    : PASSED / 100% Compliant (MIL-STD-1629A & FAA AC 33.75-1A)
```

### Forensic Root Cause
1. **Aggressive Fallback Templates:** In `_classify_component`, the keyword `"valve"` caused a lavatory flush valve to be classified as a `Critical Flight Control Component` governing flight control surfaces!
2. **Absence of Rejection Logic:** The system lacks any mechanism to evaluate whether its knowledge base contains relevant data for the component. It is architected to always generate output.
3. **Spurious Citations:** The system blindly retrieved FAA AC 25.1309-1B (transport category aircraft systems) and EASA CS-E (aircraft engine type certification) and attached them as authoritative citations for a lavatory valve.

---

## 12. Validation Node Audit

The file `src/agents/nodes/validator.py` and the method `LocalAerospaceSynthesizer._validate_fmea` were audited.

### Software Validation vs. Engineering Validation

| Validation Check | Category | Implemented in Code? | Code Location | Engineering Efficacy |
| :--- | :--- | :--- | :--- | :--- |
| **RPN Arithmetic Check ($S \times O \times D$)** | Software | **YES** | `local_synthesizer.py:327-330` | Validates arithmetic; does not validate if formula is appropriate |
| **Root Cause Minimum Length ($> 10$ chars)** | Software | **YES** | `local_synthesizer.py:341-347` | Flags 1-word inputs; accepts any sentence regardless of engineering truth |
| **Mitigation Minimum Length ($> 15$ chars)** | Software | **YES** | `local_synthesizer.py:349-355` | Flags empty inputs; accepts any plausible-sounding text |
| **Single Point Failure Counting** | Software | **YES** | `local_synthesizer.py:334-338` | Tally counters; no physics check |
| **Citation Fact Verification** | Engineering | **NO** | None | System never verifies if citation text mentions failure mode |
| **Severity Grounding in AC 33.75-1A** | Engineering | **NO** | None | System never verifies if Severity 9/10 meets Hazardous effect definition |
| **Physical Degradation Mechanism Match** | Engineering | **NO** | None | System never verifies if material or operating conditions support mode |
| **Inspection Interval Justification** | Engineering | **NO** | None | System never checks whether 500 FC is supported by fleet data |

**Verdict:** The current validator is **100% software validation** (syntactic schema validation, string lengths, arithmetic recomputation). It performs **0% engineering validation**. Despite this, the exported validation report states:
> `"FMEA validated against MIL-STD-1629A and FAA AC 33.75-1A requirements. Compliance status: PASSED."`
This statement is factually unsupported by the code.

---

## 13. Export Audit

The export modules (`src/agents/exporters/fmea_table.py`, `src/agents/exporters/digital_twin.py`, `src/agents/exporters/cil_exporter.py`, and `src/server/exporters_binary.py`) were evaluated.

### Findings Across Export Formats

1. **Excel Export (`.xlsx` via openpyxl):**
   * **Citations Completely Dropped:** The generated spreadsheet contains columns for Item ID, Failure Mode, Root Cause, Effects, S, O, D, RPN, Category, Detection, Action, and Interval. **It contains no citations column, no source document column, and no page number column.** All provenance tracking is stripped from the Excel delivery.
2. **PDF Export (`.pdf` via ReportLab):**
   * **Citations Completely Dropped:** The PDF export renders a landscape table of failure modes, severity scores, and actions. **It completely omits the citations section.** An engineer reviewing the PDF has no way of knowing what documents allegedly support the claims.
3. **Markdown Export (`.md`):**
   * Preserves citations, but formats them as authoritative compliance references without indicating whether the citation directly mentions the failure mode or was merely retrieved via semantic similarity.
4. **Digital Twin JSON Export (`.json`):**
   * Includes telemetry sensor signatures (`EGT_trend_divergence`, `accelerometer_bearing_4_peak_radial`), but these are produced by hard-coded `if/elif` string matching in Python (`digital_twin.py:33-42`), not derived from physical sensor models or failure physics.
5. **Presentation of AI Conclusions as Certified Facts:**
   * All exported formats use authoritative language: `"MIL-STD-1629A FMECA Worksheet"`, `"Compliance status: PASSED"`, `"Fully compliant with MIL-STD-1629A and FAA AC 33.75-1A guidelines."`
   * There are no disclaimers, no confidence intervals, no uncertainty flags, and no distinction between direct evidence and synthetic inference.

---

## 14. Test Suite Audit

The project currently has **24 unit and integration tests passing** across three test files.

### Test Audit Matrix

| Test Name | File | What It Actually Proves | What It Does NOT Prove |
| :--- | :--- | :--- | :--- |
| `test_config_paths` | `test_rag.py` | Directory paths are named properly | Vector store integrity or embedding quality |
| `test_clean_page_text_hyphens` | `test_rag.py` | Regex removes newline hyphens | PDF parser accuracy across tables or OCR scans |
| `test_clean_page_text_whitespace` | `test_rag.py` | Regex collapses multiple spaces | Text layout preservation |
| `test_sources_metadata_loaded` | `test_rag.py` | `sources.json` contains valid JSON | Ingested PDF text matches metadata |
| `test_single_small_page` | `test_rag.py` | Chunker prefixes header text | Chunker handles complex aerospace tables |
| `test_multi_paragraph_chunking`| `test_rag.py` | Chunker splits long text with overlap | Semantic coherence of split text |
| `test_citation_formatting` | `test_rag.py` | Formats a citation string | Citation is actually relevant to claim |
| `test_semantic_retrieval_...` | `test_rag.py` | ChromaDB returns a non-empty result | Retrieved passage answers the question |
| `test_component_classification`| `test_fmea_agent.py`| Hard-coded substring returns hard-coded dict | System can classify uncataloged components |
| `test_failure_modes_generation`| `test_fmea_agent.py`| String lengths $> 5$, $S \times O \times D = \text{RPN}$ | Failure modes are physically accurate or grounded |
| `test_validation_report_comp..`| `test_fmea_agent.py`| Validator returns boolean `True` | Any airworthiness standard is actually met |
| `test_end_to_end_graph_exec..` | `test_fmea_agent.py`| `len(citations) > 0` on output | Citations have any relation to failure modes |
| `test_mil_std_1629a_markdown` | `test_fmea_agent.py`| Markdown string contains header substring | Output complies with MIL-STD-1629A format |
| `test_digital_twin_json_format`| `test_fmea_agent.py`| JSON string parses with expected keys | Telemetry models correspond to actual sensors |
| `test_cil_markdown_format` | `test_fmea_agent.py`| CIL markdown contains header string | Critical items list complies with NASA/DoD CIL |
| `test_health_endpoint` | `test_server.py` | HTTP GET `/api/health` returns status 200 | Server health implies engineering correctness |
| `test_sample_fmea_endpoint` | `test_server.py` | HTTP GET `/api/fmea/sample` returns JSON | Sample data is evidence-grounded |
| `test_generate_fmea_endpoint` | `test_server.py` | HTTP POST `/api/fmea/generate` returns 200 | Generated FMEA is accurate or safe |
| `test_export_excel_endpoint` | `test_server.py` | Returns binary Excel buffer $> 2000$ bytes | Excel export contains provenance citations |
| `test_export_pdf_endpoint` | `test_server.py` | Returns binary PDF buffer $> 2000$ bytes | PDF export contains citations or methodology |
| `test_export_digital_twin_...` | `test_server.py` | Returns valid JSON payload | Digital Twin schema is operationally valid |
| `test_rag_search_endpoint` | `test_server.py` | RAG endpoint returns ranked results | Results are accurate or unpolluted |
| `test_rag_sources_endpoint` | `test_server.py` | Sources endpoint returns metadata list | Sources cover required engine subsystems |

**Critical Insight:** If the AI generator were modified to generate completely hallucinated failure modes (e.g. "Turbine blade dissolves due to cosmic radiation" with $S=10, O=10, D=10, \text{RPN}=1000$), **all 24 tests would still pass without a single failure**. Passing tests in this codebase prove software contract stability, not engineering airworthiness.

---

## 15. Subsystem Classification (GREEN / YELLOW / RED)

| Subsystem | Classification | Technical Rationale |
| :--- | :---: | :--- |
| **PDF Ingestion & Metadata Tracking** | **GREEN** | Robust PDF loading, clean hyphenation/whitespace handling, accurate page-number tracking in metadata (`sources.json`). |
| **ChromaDB Vector Persistence & ONNX Embedding** | **GREEN** | Fully local, zero-API dependency, onnxruntime execution of `all-MiniLM-L6-v2`, sub-millisecond retrieval. |
| **FastAPI REST API & Endpoints** | **GREEN** | Clean asynchronous endpoints, solid error handling, Pydantic request/response validation, working CORS. |
| **Vite / React Interactive Web Cockpit** | **GREEN** | Polished, responsive dark-mode UI with FMEA worksheet table, CIL view, RAG search inspector, and export buttons. |
| **Regulatory Corpus Coverage** | **YELLOW** | Good high-level regulatory coverage (MIL-STD-1629A, AC 33.75-1A, CS-E, AC 25.1309), but completely lacks component-level manuals (EMM, MPD, SB, AD, metallurgy failure case studies). |
| **Retrieval Quality for Technical Failure Modes** | **YELLOW** | Excellent on regulatory clauses; poor on specific degradation physics (fretting, blockage, cooling). High cosine distances ($0.50$ to $0.75$). |
| **Digital Twin Exporter** | **YELLOW** | Structured JSON schema is good, but sensor telemetry signatures are hard-coded heuristics rather than physical models. |
| **LangGraph Agent Workflow** | **RED** | Not an agentic reasoning engine. Strictly linear 4-node procedural sequence with no branching, no loops, and no tool selection. |
| **Failure Mode Provenance & Generation** | **RED** | 100% hard-coded failure modes. RAG is completely bypassed during generation. Zero dynamic discovery or LLM extraction. |
| **Evidence Grounding & Citation Attachment** | **RED** | Illusory citation chain. The same 4 retrieved passages are attached blindly across all 6 failure modes regardless of relevance. |
| **Scoring Methodology (RPN vs. MIL-STD-1629A)** | **RED** | Uses automotive $S \times O \times D$ (1–10 scale). Falsely claims compliance with MIL-STD-1629A, which uses Categories I–IV and $C_m = \beta \alpha \lambda_p t$. |
| **Validation Node (`validator.py`)** | **RED** | Performs zero engineering validation; accepts any failure mode as "COMPLIANT" as long as string lengths $> 10/15$. |
| **Rejection of Unsupported Claims** | **RED** | Generates authoritative-sounding failure modes for fictitious parts and lavatory valves with zero epistemic humility. |
| **Excel & PDF Provenance Preservation** | **RED** | Drops all citations, document references, and page numbers from exported Excel and PDF deliverables. |

---

## 16. Recommended Fixes for Phase 5

1. **Scoring Methodology Redesign (Mandatory Pre-requisite):**
   * Align scoring with true MIL-STD-1629A Task 101/102 standards:
     * Replace 1–10 Severity with MIL-STD-1629A **Categories I, II, III, IV**.
     * Implement the **Qualitative Criticality Matrix** ($4 \times 5$ grid: Levels A through E vs Categories I through IV).
     * Implement the **Quantitative Criticality Number** ($C_m = \beta \cdot \alpha \cdot \lambda_p \cdot t$).
     * Clearly delineate when an automotive $RPN = S \times O \times D$ is being used vs when aerospace MIL-STD-1629A / FAA AC 33.75-1A is being used.
2. **Decouple Mode Generation from Hard-Coded Literals:**
   * Implement genuine LLM-driven or RAG-driven failure mode extraction.
   * Require that each failure mode cite the specific chunk from which its physical degradation mechanism was inferred.
   * If a failure mode cannot be grounded in retrieved evidence, explicitly flag it in the UI and report as: `[UNVERIFIED HEURISTIC INFERENCE]`.
3. **Per-Mode Citation Relevance Filtering:**
   * Stop copying `retrieved_passages[:4]` across all modes.
   * Run targeted per-failure-mode RAG retrieval (e.g. specifically retrieve for "fir-tree fretting fatigue" for FM-004).
   * Apply a cross-encoder re-ranking or verification step to ensure the citation text actually mentions the failure mode or its physical root cause before attaching it.
4. **Implement True Agentic LangGraph Routing with Self-Correction:**
   * Add conditional branching: `classify -> evaluate_corpus_coverage -> if covered -> retrieve -> synthesize -> verify -> if unverified -> retry_with_broader_query -> validate`.
   * Add an explicit **"Reject / Insufficient Evidence"** terminal state when confidence or corpus coverage is below threshold.
5. **Engineering Validation Node:**
   * Upgrade `validator.py` to check:
     * Does the component exist in the knowledge base?
     * Are all Category I / Catastrophic modes substantiated by high-energy uncontained failure criteria per FAA AC 33.75-1A § 7?
     * Are citations semantically relevant to the specific mode?
6. **Provenance Preservation in Binary Exporters:**
   * Update `exporters_binary.py` to add a dedicated "Citations & Evidence" worksheet in Excel and an Appendix table in PDF.

---

## 17. Priority Order for Phase 5 Implementation

1. **Priority 1: Scoring Methodology Redesign** (Replace automotive RPN with true MIL-STD-1629A Severity Categories I–IV and Qualitative Criticality Matrix).
2. **Priority 2: Rejection & Epistemic Humility Node** (Enable the agent to say "Insufficient evidence to generate airworthiness FMEA for component X").
3. **Priority 3: Per-Mode RAG Retrieval & Citation Verification** (Eliminate blind 4-chunk copying; verify citation relevance before attaching).
4. **Priority 4: Real LLM Structured Extraction Integration** (Replace static python lists with dynamic generation grounded in retrieved chunks).
5. **Priority 5: Provenance Preservation in Excel and PDF Exporters** (Ensure citations and source pages are never stripped from exported deliverables).
6. **Priority 6: Engineering Validation Rules in `validator.py`** (Replace string-length checks with physics-based and regulatory checks).

---

## PHASE 4 STATUS

```text
PHASE 4 STATUS

Engineering validity:     FAIL (Hard-coded heuristics, pseudo-grounding, automotive RPN mislabeled as MIL-STD-1629A)
Evidence grounding:       POOR (Citations attached indiscriminately; zero relevance to specific rows)
RAG quality:              MIXED (High precision on high-level FAA/EASA clauses; poor on component failure physics)
Scoring methodology:      INVALID (Automotive S*O*D RPN framework retrofitted onto claimed MIL-STD-1629A baseline)
Software reliability:     PASS (FastAPI, React UI, ChromaDB, ONNX embeddings, exporters, and 24 unit tests operate flawlessly)
Main unresolved risks:    Presentation of synthetic, hard-coded engineering guesses as certified airworthiness compliance; complete absence of claim rejection logic for unknown parts.
Recommended next action:  Halt promotional claims of MIL-STD-1629A compliance; redesign state schemas and scoring engine to adhere to MIL-STD-1629A Categories I–IV and Criticality Analysis before proceeding to Phase 5.
```
