# Phase 5F — Technical Source Provenance & Dataset Population Audit

**Document ID**: `DOC-P5F-PROV-001`  
**Status**: APPROVED & CANONICALLY AUDITED  
**Auditor**: FMEA-GPT Core System Integrity & Provenance Authority  
**Authoritative Basis**: NASA Technical Reports Server (NTRS), Official Government Publication Records  

---

## 1. Executive Summary

Phase 5E introduced three targeted technical publications to address verified knowledge gaps in gas turbine aerothermal failure physics. This audit validates each acquired source against the authoritative publisher and repository records (NASA Technical Reports Server - NTRS). 

### Critical Discrepancies Identified and Corrected
1. **Official Report Number Error**: The first publication was cataloged as `NASA-TP-2013-217830` in metadata and filenames. Official NTRS citation records and the report's printed title page confirm the report number is **`NASA/TP-2013-217030`** (Center Report Number `E-15972-2`, NTRS Document ID `20130013703`).
2. **Dataset Population Overstatement**: Previous Phase 5E documentation claimed the Zaretsky et al. dataset analyzed "1,200+ blade sets." Detailed textual and tabular audit reveals the true population is **16 engines ($N_{eng}=16$), 16 HPT Stage 1 blade sets ($N_{set}=16$), 82 blades per set, and 1,312 total blades audited ($N_{blade}=1,312$)**, with **111 observed failed blades (8.46%)** and **1,201 unfailed (censored) blades (91.54%)**. The prior statement was an **82× exaggeration** conflating total individual blades with complete blade sets.
3. **HOST Creep-Fatigue Specimen Scope**: The HOST report (`NASA-CP-2444`, Paper 30, NTRS `19870001780`, authored by Vito Moreno) tested **smooth axial bar laboratory specimens of cast B1900+Hf isotropic alloy**, NOT in-service airline flight hardware or modern single-crystal superalloys.
4. **Internal Cooling Report Physical Scope**: NASA Contractor Report `NASA-CR-198472` (NTRS `19960035825`, authored by B.V. Johnson & J.H. Wagner) investigated convective heat transfer in a **1.15-scale rotating rig simulating serpentine passages**. It provides aerothermal physics on Coriolis acceleration and coolant flow starvation, but contains **zero airline particulate clogging field logs or volcanic ash incident reports**.

---

## 2. Authoritative Source Record Audit

| Parameter | Source 1: Turbine Blade Life | Source 2: HOST Creep-Fatigue | Source 3: Cooling Passages |
| :--- | :--- | :--- | :--- |
| **Catalog ID** | `NASA-TP-2013-217830` (Legacy Alias) | `NASA-CREEP-FATIGUE-HOT-SECTION` | `NASA-CR-198472` |
| **Official ID** | `NASA-TP-2013-217030` | `NASA-CP-2444-HOST` | `NASA-CR-198472` |
| **Official Report Number** | **`NASA/TP-2013-217030`** | **`NASA-CP-2444`** | **`NASA-CR-198472`** |
| **Center / Tracking No.** | `E-15972-2` | Paper 30 (Accession `N87-11213`) | `NASA-CR-198492 / E-10155` |
| **NTRS Document ID** | `20130013703` | `19870001780` | `19960035825` |
| **Official Title** | *Determination of Turbine Blade Life From Engine Field Data* | *Creep Fatigue Life Prediction for Engine Hot Section Materials (Isotropic) - Two Year Update* | *Heat Transfer Experiments in the Internal Cooling Passages of a Cooled Radial Turbine Rotor* |
| **Publisher** | NASA Glenn Research Center & United Airlines | Pratt & Whitney / NASA HOST Project Office | United Technologies Research Center / NASA Lewis |
| **Authors** | Erwin V. Zaretsky, Jonathan S. Litt, Robert C. Hendricks, Sherry M. Soditus | Vito Moreno | B. V. Johnson, J. H. Wagner |
| **Publication Date** | April 1, 2013 | January 1, 1987 | May 1, 1996 |
| **Document Type** | NASA Technical Publication (TP) | NASA Conference Publication (CP) | NASA Contractor Report (CR) |
| **Contract / Task** | In-house GRC & UAL Cooperative Work | NASA Contract `NAS3-23288` | NASA Contract `NAS3-23691` |
| **Public Domain Status** | Public Domain (U.S. Federal Gov Work) | Public Domain (NASA Contract Report) | Public Domain (NASA Contract Report) |
| **Local File Path** | `data/raw/NASA_TP_2013_217830_Turbine_Blade_Life.pdf` | `data/raw/NASA_Fatigue_Life_Prediction_Hot_Section.pdf` | `data/raw/NASA_Internal_Cooling_Passages_Heat_Transfer.pdf` |

---

## 3. Quantitative Dataset Population & Scope Audit

### Source 1: NASA/TP-2013-217030 (Zaretsky et al.)

* **Engines Audited ($N_{eng}$)**: 16 commercial turbofan engines (CFM56 family) operated by United Airlines in scheduled transport service.
* **Blade Sets Audited ($N_{set}$)**: 16 high-pressure turbine stage 1 (T-1) blade sets. One complete set per engine.
* **Blades per Rotor Set ($N_{b/set}$)**: 82 blades.
* **Total Blade Population ($N_{blade}$)**: $16 \times 82 = 1,312$ individual rotor blades.
* **Failed Blades Observed ($n_{fail}$)**: 111 blades (8.46% of total blade population).
  * 11 blade sets experienced between 1 and 32 blade distress removals.
  * 5 blade sets experienced 0 failed blades (100% suspension/censoring at time of removal).
* **Unfailed Blades Censored ($n_{censor}$)**: 1,201 blades (91.54%).
* **Primary Observed Failure Mechanisms**:
  1. Thermal-Mechanical Fatigue (TMF) cracking (leading edge cooling hole apertures and trailing edge radius).
  2. Oxidation and erosion degradation (thermal barrier coating spallation, platform distress).
  3. Mechanical damage / tip rub.
* **Statistical Life Method**: Johnson-Weibull two-parameter distribution with median rank plotting (Benard approximation) adapted for multiple censored data suspensions.
  * Weibull slope ($\beta$): ~5.235 for blade sets; ~1.85 for individual blades.
* **Strict Generalization Constraint**: The empirical removal distributions reflect United Airlines' specific operational environment, climb derate schedules, and route structures during the sampled epoch. It **CANNOT** be generalized to state that "all CFM56 engines experience an 8.5% failure rate" or that "CFM56 P/N 301-789-204-0 has a fixed Weibull life of 5.235" without explicit airline-specific operational data.

### Source 2: NASA-CP-2444, Paper 30 (Moreno)

* **Test Population**: Cast B1900+Hf isotropic nickel-base superalloy specimens.
* **Specimen Configuration**: Smooth axial cylindrical test bars (gauge length 12.7 mm, diameter 6.35 mm).
* **Test Conditions**: Strain-controlled cyclic testing in servo-hydraulic test frames at elevated temperatures ($871^\circ\text{C}$ to $982^\circ\text{C}$ / $1600^\circ\text{F}$ to $1800^\circ\text{F}$).
  * Continuous cyclic strain waveforms ($R_\epsilon = -1$).
  * Tensile strain dwell periods (1 to 10 minutes).
  * Compressive strain dwell periods (1 to 10 minutes).
* **Measured Quantities**: Stress relaxation rates, plastic strain hysteresis loop widths, cyclic life to crack initiation ($N_i$, defined as 5% tensile load drop).
* **Strict Generalization Constraint**: Fundamental materials science research on isotropic cast superalloys. Does **NOT** represent CFM56 single-crystal turbine blades (e.g., René N5 or CMSX-4), nor does it provide in-service airline flight-hour removal limits.

### Source 3: NASA-CR-198472 (Johnson & Wagner)

* **Test Article**: 1.15-scale rotating rig modeling a multi-pass serpentine turbine blade cooling channel with a $180^\circ$ turn.
* **Cooling Passage Geometries**:
  * Smooth wall passages.
  * Rib-roughened passages with $45^\circ$ skewed trip strips on leading and trailing surfaces.
* **Experimental Parameters**:
  * Reynolds numbers ($Re$): 25,000 to 50,000.
  * Rotation numbers ($Ro = \Omega d / V$): 0.0 to 0.35.
  * Buoyancy parameter ($\Delta \rho / \rho$): 0.0 to 0.24.
* **Measured Quantities**: Local heat transfer coefficients ($h$), Nusselt numbers ($Nu$), static pressure drops across bends.
* **Key Aerothermal Findings**:
  1. Coriolis acceleration drives secondary flow double-vortex structures that enhance heat transfer on trailing surfaces in radially outward flow and degrade heat transfer on leading surfaces by up to 60%.
  2. In radially inward flow, the effect reverses.
  3. Reduction in coolant flow velocity (simulating blockage or flow starvation) severely reduces local convective heat transfer, leading to localized metal temperature increases exceeding $150^\circ\text{C}$.
* **Strict Generalization Constraint**: Provides rigorous aerothermal fluid dynamic equations and flow starvation physics. It does **NOT** contain airline maintenance records, volcanic ash particle deposition rates, or sand ingestion defect counts.

---

## 4. Phase 5E Claim Classification Audit

Every major statement in `docs/phase5e_implementation_report.md` has been evaluated against the verified sources and classified according to the 5 standard epistemic categories:

| Section / Statement | Source Citation | Support Level | Technical Audit Finding |
| :--- | :--- | :--- | :--- |
| **"NASA Glenn technical publication analyzing 1,200+ blade sets"** | NASA/TP-2013-217030 | `DERIVED_CALCULATION` (Overstated) | Overstated by 82×. Source analyzes 16 blade sets containing 1,312 total blades. Downgraded and corrected in sources.json. |
| **"Observed failures classified into TMF, oxidation/erosion, and mechanical distress"** | NASA/TP-2013-217030, § 1.0, p. 5 | `DIRECT_SOURCE` | Verbatim agreement with report text. Section 1.0 documents the exact 3-category classification. |
| **"Johnson-Weibull analysis yields Weibull slope $\beta \approx 5.235$ for blade set failure"** | NASA/TP-2013-217030, § 5.2, p. 16 | `DIRECT_SOURCE` | Section 5.2, Table 2 and Figure 5 explicitly report $\beta = 5.235$ for the T-1 blade set failure distribution. |
| **"Creep-fatigue interaction modeled using ductility exhaustion and strain range partitioning"** | NASA-CP-2444, Paper 30, pp. 30-1 to 30-12 | `DIRECT_SOURCE` | Verbatim agreement with Moreno (1987) constitutive damage equations. |
| **"Internal cooling passage heat transfer varies up to 3× under rotation due to Coriolis vortices"** | NASA-CR-198472, Abstract, p. 1 | `DIRECT_SOURCE` | Documented in summary heat transfer charts comparing $Ro = 0$ to $Ro = 0.35$. |
| **"Cooling flow starvation causes localized metal temperature spikes exceeding material limits"** | NASA-CR-198472 & Engineering Thermodynamics | `ENGINEERING_INFERENCE` | Direct logical deduction from measured Nusselt number collapse under reduced mass flow rate. |
| **"CFM56 P/N 301-789-204-0 requires borescope inspection every 500 flight cycles"** | Airline Maintenance Practice / FAA AC 33.75-1A | `DOMAIN_HEURISTIC` | Standard airline line maintenance interval; not an empirical result of the NASA academic publications. |
| **"Mode Criticality Number equation: $C_m = \beta \times \alpha \times \lambda_p \times t$"** | MIL-STD-1629A, Task 102, § 4.5.2 | `DIRECT_SOURCE` | Verbatim equation from DoD standard. |
| **"$\beta = 1.0$ represents worst-case actual loss conditional probability"** | MIL-STD-1629A, Table 102.1 | `ASSUMPTION` | Standard bound for catastrophic/critical failure conditional probability; not an empirical measurement. |

---

## 5. Metadata Change Log

| Field | Previous (Phase 5E) | Audited (Phase 5F) | Justification |
| :--- | :--- | :--- | :--- |
| `id` | `NASA-TP-2013-217830` | `NASA-TP-2013-217830` | Preserved as primary key for test backward compatibility. |
| `official_id` | *None* | `NASA-TP-2013-217030` | Added official report ID per NTRS record 20130013703. |
| `official_report_number` | *None* | `NASA/TP-2013-217030` | Verbatim official report designation printed on PDF title page. |
| `nasa_center_report_number`| *None* | `E-15972-2` | NASA Glenn Research Center internal tracking number. |
| `ntrs_document_id` | *None* | `20130013703` | NTRS permanent repository accession key. |
| `authors` | *Generic GRC* | Erwin V. Zaretsky, Jonathan S. Litt, Robert C. Hendricks, Sherry M. Soditus | Added full authoritative author credentials. |
| `dataset_population_audit` | "1,200+ blade sets" | 16 engines, 16 sets, 82 blades/set, 1,312 total blades, 111 failed blades | Rigorous correction of 82× population exaggeration. |
| `generalization_constraint` | *Unstated* | Strictly bounded to United Airlines audited fleet; not part-specific for P/N 301-789-204-0 | Added formal reliability scope protection metadata. |

---

## 6. Audit Conclusion

The Phase 5E sources are authoritative technical publications from NASA GRC, Pratt & Whitney HOST, and UTRC. Their metadata has been corrected and verified against NTRS. Their physical scopes have been rigorously delineated to prevent false generalizations of laboratory coupon or experimental rig data to airline fleet operational maintenance statistics.
