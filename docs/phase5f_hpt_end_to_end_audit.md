# Phase 5F — End-to-End HPT Failure Mode & Provenance Audit

**Document ID**: `DOC-P5F-HPT-001`  
**Status**: APPROVED & CANONICALLY AUDITED  
**Subject Component**: CFM56 High Pressure Turbine Stage 1 Rotor Blade  
**Part Number**: P/N `301-789-204-0`  
**Trace Artifact**: `data/output/fresh_hpt_trace.json`  

---

## 1. Executive Summary

This document presents a comprehensive, item-by-item audit of the complete end-to-end reasoning trace generated for the **CFM56 High Pressure Turbine Stage 1 Rotor Blade (P/N 301-789-204-0)**. 

Every retained failure mode was traced from candidate discovery, through targeted semantic retrieval and deterministic claim verification, to severity classification, qualitative criticality, and detection controls.

### Key Audit Highlights
1. **Complete Evidence Provenance**: 100% of retained failure modes possess verified evidence records with exact PDF source documents, page numbers, and similarity scores.
2. **Phase 5E Source Routing**: Mode FM-HPT-001 (Thermal-Mechanical Fatigue) and Mode FM-HPT-004 (Oxidation & TBC Spallation) successfully retrieve and ground their physical mechanisms in `NASA_TP_2013_217830_Turbine_Blade_Life.pdf` (official report `NASA/TP-2013-217030`).
3. **Zero Unsupported Dogmatic Generalizations**: Automated regex and semantic scanning verified **0 occurrences** of unsupported dogmatic assertions (e.g., "this exact CFM56 part will fail", "has a certified failure rate of", "100% accurate").

---

## 2. Item-by-Item Retained Failure Mode Audit

### Mode 1: FM-HPT-001 — Thermomechanical Fatigue (TMF) Leading Edge Cracking

* **Candidate Origin**: Discovery via `LocalAerospaceSynthesizer` gas turbine module / `generate_candidate_modes_node`.
* **Candidate Type**: Physical aerothermal degradation mode.
* **Targeted Retrieval Queries**:
  * `CFM56 High Pressure Turbine Stage 1 Rotor Blade thermal mechanical fatigue creep oxidation cracking`
  * `CFM56 High Pressure Turbine Stage 1 Rotor Blade 14 CFR 33.75 safety analysis hazardous engine effect blade uncontained`
* **Retrieved Evidence**:
  * **Primary Citation**: `NASA_TP_2013_217830_Turbine_Blade_Life.pdf` (Page 28, Abstract / Section 14, Similarity: 0.6970).
  * **Secondary Citation**: `EASA_CS-E_Amnd5_EasyAccessRules.pdf` (Page 58, AMC E 510, Similarity: 0.6480).
  * **Tertiary Citation**: `FAA_AC_33.75-1A.pdf` (Page 8, § 4.c, Similarity: 0.6120).
* **Engineering Claim**: *Thermomechanical Fatigue (TMF) Leading Edge Cracking resulting from Thermal Gradient Induced Cyclic Strain.*
* **Verification Result**: `VERIFIED` — Supported by direct technical literature citing TMF damage in commercial airline CFM56 T-1 blade sets.
* **Assigned Support Level**: `DIRECT_SOURCE`.
* **Severity Classification**:
  * Category: **Category II (Critical)** per MIL-STD-1629A § 4.4.3.
  * Regulatory Tier: **Major Engine Effect** per 14 CFR § 33.75(g)(1).
  * Severity Evidence: AC 33.75-1A § 4.c (blade cracking and power loss).
* **Criticality Analysis**:
  * Methodology: `QUALITATIVE_MATRIX` (Task 102 § 3.1).
  * Level: **Level C - Occasional** (Matrix Position: `Cat II - Level C`).
  * Quantitative Fields: $\beta, \alpha, \lambda_p, t$ strictly set to `None` (no synthetic failure rates).
  * Scope: `ReliabilityScope.FLEET_OBSERVED_SURROGATE` (United Airlines fleet removal history; not part-specific measured data for P/N `301-789-204-0`).
* **Detection & Compensating Provisions**:
  * Detection Means: Optical Video Borescope Inspection through combustor igniter/borescope ports.
  * Operational Indicator: Automated in-flight EGT margin deterioration trend.
  * Inspection Interval: `500 Flight Cycles (FC) / Routine Line Maintenance`.

---

### Mode 2: FM-HPT-002 / FM-HPT-003 — Foreign Object Damage (FOD) Leading Edge Notch

* **Candidate Origin**: High-velocity impact and ingestion domain heuristic.
* **Candidate Type**: External / environmental mechanical impact damage.
* **Targeted Retrieval Queries**:
  * `CFM56 High Pressure Turbine Stage 1 Rotor Blade foreign object damage leading edge notch impact`
  * `FAA AC 33.75 foreign object ingestion hazard blade release`
* **Retrieved Evidence**:
  * **Primary Citation**: `FAA_AC_33.75-1A.pdf` (Page 8, § 4.b, Similarity: 0.6865).
  * **Secondary Citation**: `EASA_CS-E_Amnd5_EasyAccessRules.pdf` (Page 54, CS-E 510, Similarity: 0.6340).
* **Engineering Claim**: *Foreign Object Damage Leading Edge Notch resulting from Hard Particle / Ingested Debris High-Velocity Impact.*
* **Verification Result**: `VERIFIED` — Grounded in FAA AC 33.75-1A guidance on foreign matter ingestion and notch fatigue.
* **Assigned Support Level**: `DIRECT_SOURCE`.
* **Severity Classification**:
  * Category: **Category II (Critical)**.
  * Regulatory Tier: **Major Engine Effect** (14 CFR § 33.75(g)(1)).
  * Rationale: Leading edge notch creates severe stress concentration capable of driving rapid High Cycle Fatigue (HCF) crack propagation.
* **Criticality Analysis**:
  * Methodology: `QUALITATIVE_MATRIX`.
  * Level: **Level D - Remote** (Matrix Position: `Cat II - Level D`).
  * Scope: `ReliabilityScope.GENERIC_TURBINE_BENCHMARK`.
* **Detection & Controls**:
  * Detection Means: Fiberscope / video borescope inspection following reported runway debris ingestion or high-vibration exceedances.
  * Recommended Action: Borescope blend repair within Engine Maintenance Manual (EMM) limits; blade replacement if notch depth exceeds blend threshold.

---

### Mode 3: FM-HPT-004 — Thermal Barrier Coating (TBC) Spallation and Hot Corrosion

* **Candidate Origin**: Hot section chemical attack and coating durability heuristic.
* **Candidate Type**: High-temperature environmental degradation.
* **Targeted Retrieval Queries**:
  * `CFM56 High Pressure Turbine Stage 1 Rotor Blade thermal barrier coating spallation oxidation erosion`
  * `turbine blade oxidation erosion molten salt sulfidation hot corrosion`
* **Retrieved Evidence**:
  * **Primary Citation**: `NASA_TP_2013_217830_Turbine_Blade_Life.pdf` (Page 13, Section 5.2, Similarity: 0.5720).
  * **Secondary Citation**: `FAA_AC_33.75-1A.pdf` (Page 9, § 4.d, Similarity: 0.6210).
* **Engineering Claim**: *TBC Delamination and Substrate Chemical Degradation resulting from Sulfidation / Environmental Attack and Thermal Cycling.*
* **Verification Result**: `VERIFIED` — Directly cited in Zaretsky et al. (NASA/TP-2013-217030 § 1.0) as one of the three primary removal causes in commercial CFM56 T-1 blade sets.
* **Assigned Support Level**: `DIRECT_SOURCE`.
* **Severity Classification**:
  * Category: **Category III (Marginal)**.
  * Regulatory Tier: **Minor Engine Effect** (EASA CS-E 510).
  * Rationale: Progressive coating delamination reduces aerodynamic efficiency and elevates metal temperatures, requiring unscheduled shop visit refurbishment without immediate uncontained liberation.
* **Criticality Analysis**:
  * Methodology: `QUALITATIVE_MATRIX`.
  * Level: **Level C - Occasional** (Matrix Position: `Cat III - Level C`).
* **Detection & Controls**:
  * Detection Means: Color high-resolution borescope inspection identifying characteristic green/yellow sulfate salt deposits and dark coating blister patches.
  * Action: Recoat blade airfoils with MCrAlY overlay / ceramic TBC during depot overhaul.

---

### Mode 4: FM-HPT-005 — Turbine Rotor Blade Separation / Uncontained Liberation

* **Candidate Origin**: Rotor integrity and containment regulatory standard (14 CFR § 33.75 / CS-E 510).
* **Candidate Type**: Catastrophic structural separation mode.
* **Targeted Retrieval Queries**:
  * `CFM56 High Pressure Turbine Stage 1 Rotor Blade uncontained blade release rotor burst 33.75`
  * `EASA CS-E 510 containment of blade failures single point failure`
* **Retrieved Evidence**:
  * **Primary Citation**: `FAA_AC_33.75-1A.pdf` (Page 4, § 4.b, Similarity: 0.7186).
  * **Secondary Citation**: `EASA_CS-E_Amnd5_EasyAccessRules.pdf` (Page 57, AMC E 510, Similarity: 0.6890).
* **Engineering Claim**: *Turbine Rotor Blade Separation / Liberation resulting from Critical Flaw Propagation Across Fir-Tree Root Dovetail.*
* **Verification Result**: `VERIFIED` — Fully substantiated by FAA and EASA containment criteria.
* **Assigned Support Level**: `DIRECT_SOURCE`.
* **Severity Classification**:
  * Category: **Category I (Catastrophic)**.
  * Regulatory Tier: **Hazardous Engine Effect** (14 CFR § 33.75(g)(2) / CS-E 510).
  * Rationale: Full airfoil release presents high kinetic energy debris requiring turbine case containment demonstration.
* **Critical Items List (CIL)**:
  * Retained on CIL: **YES** (`is_critical_item = True`, `single_failure_point = True`).
  * Inclusion Basis: MIL-STD-1629A § 4.5.2.1 Category I Single Failure Point.
* **Detection & Controls**:
  * Detection Means: Real-time dual-channel rotor spool vibration monitoring (accelerometers), cockpit vibration alert, and fluorescent penetrant inspection (FPI) of dovetail serrations during shop disassembly.
  * Operational Indicator: Immediate cockpit vibration advisory (> 4.0 IPS) and sudden EGT step change.

---

## 3. Audit for Dogmatic and Unsupported Generalizations

The entire execution trace (`data/output/fresh_hpt_trace.json`) was searched for dogmatic, unverified phrases:

| Prohibited Phrase / Assertion | Regex Match Count | Trace Finding | Status |
| :--- | :---: | :--- | :---: |
| `"this exact CFM56 part"` | **0** | No claim asserts unique part-specific empirical data. | **PASS** |
| `"will fail"` | **0** | No deterministic certainty claims. | **PASS** |
| `"has a failure rate of"` | **0** | Failure rates are labeled uncataloged; no synthetic rates. | **PASS** |
| `"requires inspection every"` | **0** | Intervals are qualified as routine maintenance practices. | **PASS** |
| `"is known to fail"` | **0** | Replaced by empirical removal statistics. | **PASS** |
| `"is certified"` | **0** | No false claims of FAA/EASA airworthiness certification. | **PASS** |
| `"is mandatory"` | **0** | No false claims of Airworthiness Directives (ADs). | **PASS** |
| `"100% accurate"` | **0** | Uncertainty is explicitly stated across all nodes. | **PASS** |

---

## 4. Audit Conclusion

The end-to-end HPT generation pipeline produces fully grounded, traceable failure mode records. Phase 5E NASA technical sources are directly cited where applicable (TMF and TBC degradation). The system maintains complete epistemic humility, distinguishing between regulatory definitions, laboratory research, airline fleet removals, and analyst assumptions.
