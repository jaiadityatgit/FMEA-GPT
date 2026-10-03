# FMEA-GPT Phase 5A: Standards Traceability & Verifiable Basis Document

**Document ID:** FMEA-GPT-TRACE-PHASE5A  
**Date:** October 2, 2026  
**Audited Local Sources:**
1. `data/raw/MIL-STD-1629A.pdf` (U.S. Department of Defense, Procedures for Performing a FMECA, 24 Nov 1980)
2. `data/raw/NASA-STD-8729.1A.pdf` (NASA Technical Standard, Reliability Analysis Handbook, 16 Jun 2017)
3. `data/raw/FAA_AC_33.75-1A.pdf` (Federal Aviation Administration, Guidance Material for 14 CFR 33.75 Safety Analysis, 26 Sep 2007)
4. `data/raw/FAA_AC_25.1309-1B.pdf` (Federal Aviation Administration, System Design and Analysis, Draft/Final guidelines)
5. `data/raw/EASA_CS-E_Amnd5_EasyAccessRules.pdf` (EASA Certification Specifications for Engines, Amdt 5, Feb 2020)

---

## 1. Traceability Matrix: Model Fields to Inspected Standards

Every substantive field in the revised engineering data model is mapped directly to specific clauses, page numbers, and exact text from the local PDF repository.

| Model Field | Governing Standard | Document & Section/Page | Direct Standard Text / Interpretation | Verification Confidence |
| :--- | :--- | :--- | :--- | :---: |
| **Component Name & Item Identification** | MIL-STD-1629A | Task 101 § 4.3.1 (Page 18) | *"Identification number. An identification number shall be assigned to each item..."* Tracks hardware tree. | **VERIFIED** (Direct Text) |
| **Indenture Level / Analysis Scope** | MIL-STD-1629A | General Requirements § 3.1.17, Task 101 § 4.3 (Pages 11, 18) | *"3.1.17.1 Initial indenture level... 3.1.17.2 Other indenture levels... progressing down through decreasing indenture levels."* | **VERIFIED** (Direct Text) |
| **Primary Function** | MIL-STD-1629A | Task 101 § 4.3.2 (Page 19) | *"Function. A concise statement of the function to be performed by the hardware item shall be listed."* | **VERIFIED** (Direct Text) |
| **Airworthiness Tier / Critical Part** | FAA / EASA | 14 CFR § 33.75 / FAA AC 33.75-1A § 4 (Page 4); EASA CS-E 510 (Page 82) | *"An engine part the failure of which could reasonably result in a hazardous engine effect must be designated an Engine Critical Part..."* | **VERIFIED** (Direct Text) |
| **Failure Mode** | MIL-STD-1629A | Task 101 § 4.3.3 (Page 19) | *"All predictable potential failure modes for each indenture level analyzed shall be identified and described."* | **VERIFIED** (Direct Text) |
| **Physical Failure Mechanism** | NASA-STD-8729.1A / EASA CS-E | NASA-STD-8729.1A § 12; EASA AMC E 510 (Page 83-94) | *Physical process (e.g. thermal fatigue, creep, erosion, chemical reaction) causing degradation.* Distinct from observable mode. | **VERIFIED** (Established Engineering Best Practice) |
| **Root Cause** | MIL-STD-1629A | Task 101 § 4.3.3 (Page 19) | *"The most probable causes for each potential failure mode shall be identified and described."* | **VERIFIED** (Direct Text) |
| **Local Effect** | MIL-STD-1629A | Task 101 § 5.6.1 (Page 23) | *"Local effects concentrate on the impact an assumed failure has on the operation and function of the item in the indenture level under consideration."* | **VERIFIED** (Direct Text) |
| **Next Higher Level Effect** | MIL-STD-1629A | Task 101 § 5.6.2 (Page 23) | *"Next higher level effects concentrate on the impact an assumed failure has on the operation and function of the items in the next higher indenture level..."* | **VERIFIED** (Direct Text) |
| **End Effect** | MIL-STD-1629A | Task 101 § 5.6.3 (Page 23) | *"End effects evaluate and define the total effect an assumed failure has on the operation, function, or status of the uppermost system."* | **VERIFIED** (Direct Text) |
| **Hazardous Engine Effects Definition** | FAA AC 33.75-1A | § 6 (Pages 10–13) | Defines uncontained high-energy debris, uncontrollable fire, toxic cabin air, loss of shutdown capability as Hazardous Engine Effects ($p < 10^{-7}$). | **VERIFIED** (Direct Text) |
| **Severity Category I (Catastrophic)** | MIL-STD-1629A | General Requirements § 4.4.3.a (Page 16) | *"Category I - Catastrophic - A failure which may cause death or weapon system loss (i.e., aircraft, tank, missile, ship, etc.)"* | **VERIFIED** (Direct Text) |
| **Severity Category II (Critical)** | MIL-STD-1629A | General Requirements § 4.4.3.b (Page 16) | *"Category II - Critical - A failure which may cause severe injury, major property damage, or major system damage which will result in mission loss."* | **VERIFIED** (Direct Text) |
| **Severity Category III (Marginal)** | MIL-STD-1629A | General Requirements § 4.4.3.c (Page 16) | *"Category III - Marginal - A failure which may cause minor injury, minor property damage, or minor system damage resulting in delay or mission degradation."* | **VERIFIED** (Direct Text) |
| **Severity Category IV (Minor)** | MIL-STD-1629A | General Requirements § 4.4.3.d (Page 16) | *"Category IV - Minor - A failure not serious enough to cause injury, property damage or system damage, but which will result in unscheduled maintenance or repair."* | **VERIFIED** (Direct Text) |
| **Severity Integer 1–10 Scale** | **NONE** | **Not established by inspected source.** | MIL-STD-1629A, AC 33.75-1A, and CS-E 510 contain **zero** 1–10 ordinal severity scales. Originates from automotive SAE J1739 / AIAG. | **UNSUPPORTED IN AEROSPACE CORE** |
| **Criticality Analysis Approach** | MIL-STD-1629A | Task 102 § 3 (Page 29) | Requires selection of either Qualitative approach (§ 3.1) or Quantitative approach (§ 3.2). | **VERIFIED** (Direct Text) |
| **Qualitative Failure Probability Levels A–E** | MIL-STD-1629A | Task 102 § 3.1.a–e (Pages 29–30) | Level A (Frequent $>0.2$), Level B (Probable $0.1-0.2$), Level C (Occasional $0.01-0.1$), Level D (Remote $0.001-0.01$), Level E (Extremely Unlikely $<0.001$). | **VERIFIED** (Direct Text) |
| **Criticality Matrix Display** | MIL-STD-1629A | Task 102 § 4 & Figure 102.2 (Pages 33, 35) | $4 \times 5$ matrix comparing Severity Categories (I–IV) on horizontal axis against Probability Levels (A–E) or $C_r$ on vertical axis. | **VERIFIED** (Direct Text) |
| **Failure Mode Criticality Number ($C_m$)** | MIL-STD-1629A | Task 102 § 3.2.1.6 (Pages 32–33) | Formula: $C_m = \beta \cdot \alpha \cdot \lambda_p \cdot t$. All 4 parameters explicitly defined in §§ 3.2.1.2–3.2.1.5. | **VERIFIED** (Direct Text) |
| **Conditional Probability ($\beta$)** | MIL-STD-1629A | Task 102 § 3.2.1.2 & Table 102.1 (Page 31) | Conditional probability that failure causes listed effect: Actual loss (1.00), Probable loss (0.10 to 1.00), Possible loss (0 to 0.10), No effect (0). | **VERIFIED** (Direct Text) |
| **Failure Mode Ratio ($\alpha$)** | MIL-STD-1629A | Task 102 § 3.2.1.3 (Page 31) | Fraction of part failure rate attributed to the specific failure mode ($\sum \alpha = 1.0$). | **VERIFIED** (Direct Text) |
| **Part Failure Rate ($\lambda_p$)** | MIL-STD-1629A | Task 102 § 3.2.1.4 (Page 32) | Part failure rate from reliability prediction (MIL-HDBK-217) or operating experience with stress factors applied. | **VERIFIED** (Direct Text) |
| **Operating Time ($t$)** | MIL-STD-1629A | Task 102 § 3.2.1.5 (Page 32) | Operating time in hours or operating cycles per mission. | **VERIFIED** (Direct Text) |
| **Detection Method** | MIL-STD-1629A | Task 101 § 5.7 (Pages 23–24) | Description of visual, audible, automatic sensing, instrumentation, or routine inspection means by which failure is detected. | **VERIFIED** (Direct Text) |
| **Detection Integer 1–10 Scale** | **NONE** | **Not established by inspected source.** | MIL-STD-1629A does not quantify detection into an integer or multiply it into criticality. Originates from automotive AIAG FMEA. | **UNSUPPORTED IN AEROSPACE CORE** |
| **Undetectable Failure** | MIL-STD-1629A | General Requirements § 3.1.21 (Page 11) | *"A postulated failure mode in the FMEA for which there is no failure detection method by which the operator is made aware of the failure."* | **VERIFIED** (Direct Text) |
| **Single Failure Point (SFP)** | MIL-STD-1629A / NASA-STD-8729.1A | MIL-STD-1629A § 3.1.19 (Page 11); NASA-STD-8729.1A § 13 (Page 13) | *"The failure of an item which would result in failure of the system and is not compensated for by redundancy or alternative operational procedure."* | **VERIFIED** (Direct Text) |
| **Critical Items List (CIL) Criteria** | MIL-STD-1629A / NASA-STD-8729.1A | MIL-STD-1629A § 4.5.2.1 (Pages 16–17); NASA-STD-8729.1A § 13 | Requires explicit list of all Category I (Catastrophic) and Category II (Critical) failure modes and Single Point Failures. | **VERIFIED** (Direct Text) |
| **CIL Inclusion Threshold: RPN $\ge$ 100** | **NONE** | **Not established by inspected source.** | Arbitrary threshold found in previous code; completely absent from MIL-STD-1629A and NASA-STD-8729.1A. | **REMOVED AS INVALID** |
| **Risk Priority Number ($S \times O \times D$)** | **NONE** | **Not established by inspected source.** | The term "RPN" appears 0 times in MIL-STD-1629A. It is quarantined as a legacy automotive metric. | **QUARANTINED AS LEGACY COMPATIBILITY** |

---

## 2. Epistemic Integrity Gap Analysis

The table below documents where current system implementations make assumptions beyond what is established in the source documents:

| Concept | Inspected Document State | Code Architecture Resolution in Phase 5A |
| :--- | :--- | :--- |
| **Specific Component Failure Rates ($\lambda_p$)** | Not present in general regulatory standards (AC 33.75 / CS-E do not provide CFM56 blade failure rates per hour). | When fleet failure rate data is not in corpus, system must use **Qualitative Criticality Analysis (Task 102 § 3.1)** and explicitly record `methodology = QUALITATIVE_MATRIX` rather than hallucinating $\lambda_p$. |
| **Inspection Intervals (e.g. 500 FC borescope)** | Contained in Engine Maintenance Manuals (EMM Chapter 72) and Airworthiness Directives (ADs), not in high-level standards. | Must be assigned `support_level = DOMAIN_HEURISTIC` or `SUPPORTING_SOURCE`, with an explicit `EngineeringAssumption` stating that intervals are subject to airline MPD / EMM approval. |
| **Severity When Hazard is Ambiguous** | MIL-STD-1629A § 4.4.3 requires loss statements approved in ground rules. | When end aircraft effect cannot be deduced with certainty, the system must set `severity_category = UNKNOWN` or `INSUFFICIENT_EVIDENCE`. |
| **Detection Method Quantification** | Standards require qualitative descriptions only. | Quantified 1–10 detection scores are completely removed from the core airworthiness model and preserved only in an isolated `LegacyRPN` object. |
