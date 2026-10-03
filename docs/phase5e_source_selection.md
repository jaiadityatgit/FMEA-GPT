# Phase 5E — Source Selection Report

## Methodology

Sources selected exclusively to address verified knowledge gaps from Phase 5D failure analysis.
All sources are public-domain NASA/FAA publications. No paywalled or commercially restricted material.

---

## Selected Sources

### Source 1: NASA/TP-2013-217830

| Field | Value |
| :--- | :--- |
| **Title** | Determination of Turbine Blade Life From Engine Field Data |
| **Authors** | Erwin V. Zaretsky, Jonathan S. Litt, Robert C. Hendricks, Sherry M. Soditus |
| **Publisher** | NASA Glenn Research Center |
| **Date** | April 2013 |
| **Pages** | 30 |
| **Local File** | `data/raw/NASA_TP_2013_217830_Turbine_Blade_Life.pdf` |
| **Gaps Addressed** | Thermal fatigue (RET-01, RET-02), blade failure mode categorization |
| **Key Content** | Field data analysis of HPT blade sets from United Airlines CFM56 engines. Categorizes blade removal causes into TMF, oxidation/erosion, and other degradation. Provides Weibull reliability statistics for blade life. |
| **Licensing** | Public domain (U.S. Federal Government) |

### Source 2: NASA HOST Program — Creep Fatigue Life Prediction

| Field | Value |
| :--- | :--- |
| **Title** | Creep Fatigue Life Prediction for Engine Hot Section Materials (Isotropic) - Two Year Update |
| **Authors** | Vito Moreno (Pratt & Whitney) |
| **Publisher** | United Technologies Corporation / NASA |
| **Date** | 1987 |
| **Pages** | 6 |
| **Local File** | `data/raw/NASA_Fatigue_Life_Prediction_Hot_Section.pdf` |
| **Gaps Addressed** | Thermal fatigue / creep interaction (RET-01, RET-02) |
| **Key Content** | Damage accumulation model for creep-fatigue interaction at elevated temperatures. Grain cyclic capability analysis. Ductility exhaustion prediction. |
| **Licensing** | Public domain (NASA-funded research) |

### Source 3: NASA/CR-198472

| Field | Value |
| :--- | :--- |
| **Title** | Heat Transfer Experiments in the Internal Cooling Passages of a Cooled Radial Turbine Rotor |
| **Authors** | B.V. Johnson, J.H. Wagner (United Technologies Research Center) |
| **Publisher** | NASA Lewis Research Center (Contractor Report) |
| **Date** | May 1996 |
| **Pages** | 120 |
| **Local File** | `data/raw/NASA_Internal_Cooling_Passages_Heat_Transfer.pdf` |
| **Gaps Addressed** | Cooling system (RET-11, RET-12), internal cooling passages, heat transfer |
| **Key Content** | Experimental heat transfer data for rotating coolant passages. Serpentine passage flow. Coriolis and buoyancy effects. Flow distribution in internal cooling channels. |
| **Licensing** | Public domain (NASA-funded research) |

---

## Gap Coverage Matrix

| Verified Gap | Source 1 (Blade Life) | Source 2 (Creep-Fatigue) | Source 3 (Cooling) | Remaining Gap |
| :--- | :---: | :---: | :---: | :--- |
| **Thermal Fatigue / TMF** | ✅ Primary | ✅ Supporting | — | Resolved |
| **Cooling System / Passage Blockage** | — | — | ✅ Primary | Partially resolved (blockage physics still limited) |
| **Fretting Fatigue** | — | — | — | Still a corpus gap (no suitable public NASA report found covering fretting/dovetail mechanics) |
| **Criticality Formulas** | — | — | — | Addressed by formula extraction (not new corpus) |
| **TBC Degradation** | ✅ Partial (oxidation/erosion data) | — | — | Partially resolved |

---

## Sources NOT Selected (With Justification)

| Candidate | Reason for Exclusion |
| :--- | :--- |
| **Rolls-Royce "The Jet Engine"** | Commercial copyright; cannot be freely distributed |
| **NASA TM-X-71649 (Low-Cycle Thermal Fatigue, 1975)** | PDF not available via NTRS API (404 error) |
| **NASA/TM-2001-210766 (Heat Transfer in Gas Turbines)** | PDF not available via NTRS API (404 error) |
| **SAE ARP4761** | Commercial copyright ($150+ USD) |
| **FAA DOT/FAA/AR-96/126** | Server unreachable at time of acquisition |

---

## Remaining Fretting Fatigue Gap

The fretting fatigue gap (RET-13, RET-14) remains open. No suitable public-domain NASA or FAA report covering blade root dovetail contact mechanics was successfully downloadable. This gap is explicitly documented for Phase 5F consideration.
