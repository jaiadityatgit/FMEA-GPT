# Phase 5F — Criticality Formula & Parameter Provenance Audit

**Document ID**: `DOC-P5F-CRIT-001`  
**Status**: APPROVED & CANONICALLY AUDITED  
**Standard Basis**: MIL-STD-1629A Task 102 (Quantitative Criticality Analysis)  
**Governing Equation**: $C_m = \beta \times \alpha \times \lambda_p \times t$  

---

## 1. Executive Summary

This audit establishes mathematical and empirical integrity for all quantitative reliability and criticality representations across FMEA-GPT. 

In automated safety analysis systems, there is an acute danger of **silent value generation**—where algorithms fabricate plausible failure rates ($\lambda_p$), mode ratios ($\alpha$), or conditional probabilities ($\beta$) and present them as empirical data. 

Phase 5F institutes strict mathematical provenance:
1. Every formula input ($\beta, \alpha, \lambda_p, t$) is represented as an **independent, structured parameter** with its own unit, data source, scope, and assumption status.
2. $\beta = 1.0$ is strictly classified as an **`ASSUMPTION`** (specifically a conservative bounding condition per MIL-STD-1629A Table 102.1 for actual loss given mode occurrence), and is **never** presented as an empirical fleet failure probability.
3. **Reliability Scope Protection** prevents general gas turbine literature or surrogate fleet statistics from being silently assigned to a specific part number (such as CFM56 P/N `301-789-204-0`) as measured data.

---

## 2. Independent Parameter Audit for $C_m = \beta \times \alpha \times \lambda_p \times t$

MIL-STD-1629A Task 102 § 4.5.2 defines the Mode Criticality Number $C_m$ as the portion of the item criticality number associated with a specific failure mode:

$$C_m = \beta \times \alpha \times \lambda_p \times t$$

| Parameter | Symbol | Mathematical Definition | Canonical Unit | Standard Source | Classification & Assumption Status | Permitted Operational Scope |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| **Conditional Probability** | $\beta$ | Conditional probability that the failure effect results in listed severity category | Dimensionless ($0.0 \le \beta \le 1.0$) | MIL-STD-1629A Table 102.1 | `ASSUMPTION` (or `DERIVED_CALCULATION` if event tree modeled) | `WORST_CASE_BOUND` (when $\beta = 1.0$) or `UNVERIFIED_ASSUMPTION` |
| **Failure Mode Ratio** | $\alpha$ | Fraction of total part failure rate attributed to this specific mode | Dimensionless ($0.0 \le \alpha \le 1.0$) | Engineering failure mode distribution analysis | `ENGINEERING_INFERENCE` or `ASSUMPTION` | `GENERIC_TURBINE_BENCHMARK` or `FLEET_OBSERVED_SURROGATE` |
| **Part Failure Rate** | $\lambda_p$ | Expected number of failures per unit time | Failures per operating hour ($\text{hr}^{-1}$) | Operator removal logs / Engine Shop data | `PROPRIETARY_AIRLINE_DATA` (Uncataloged in open regulatory corpus) | `PART_SPECIFIC_MEASURED` (only if exact P/N verified) |
| **Operating Time** | $t$ | Operating duration (mission time or maintenance inspection interval) | Operating hours ($\text{hr}$) or cycles | Flight mission profile or maintenance schedule | `ENGINEERING_SPECIFICATION` | `WORST_CASE_BOUND` or `MISSION_PROFILE` |

---

## 3. Special Audit: Handling of $\beta = 1.0$

A critical vulnerability in automated FMECA tools is treating $\beta = 1.0$ as an empirical statement that "the part is certain to fail."

### Formal Epistemic Clarification
Under MIL-STD-1629A Table 102.1:
* $\beta = 1.0$: **Actual Loss** — Conditional probability that if the failure mode occurs, the listed severity effect (e.g., in-flight shutdown or loss of engine function) will materialize.
* $\beta = 0.10 \text{ to } 1.00$: **Probable Loss**
* $\beta = 0.00 \text{ to } 0.10$: **Possible Loss**
* $\beta = 0.00$: **No Effect**

### Phase 5F Architectural Invariant
1. In the codebase, whenever $\beta = 1.0$ is assigned, it **MUST** be labeled with:
   ```python
   assumption_status = "ASSUMPTION"
   scope = ReliabilityScope.WORST_CASE_BOUND
   is_measured = False
   rationale = "MIL-STD-1629A Table 102.1 conditional probability bound for actual loss given mode occurrence"
   ```
2. The code **strictly forbids** labeling $\beta = 1.0$ as `SOURCE-DERIVED` or representing it as an empirical fleet failure rate for the CFM56 engine.
3. In qualitative mode (default), quantitative fields remain `None` to prevent synthetic fabrication:
   ```python
   # In src/agents/nodes/fmea_builder.py
   crit_obj = CriticalityAnalysis(
       methodology=CriticalityMethodology.QUALITATIVE_MATRIX,
       qualitative_level=ProbabilityLevel.LEVEL_C,
       matrix_position=f"{sev_cat.value} - Level C",
       data_source_description="Aviation transport operating history and engineering standards analysis",
       rationale=crit_claim
   )
   ```

---

## 4. Reliability Scope Protection Architecture

To prevent general turbomachinery reliability data (e.g., generic gas turbine failure rates from IEEE-500, NPRD-2016, or academic surveys) from being silently attributed to a specific hardware part number, Phase 5F implements formal **Reliability Scope Enforcement**:

```python
class ReliabilityScope(str, Enum):
    PART_SPECIFIC_MEASURED = "part_specific_measured"       # Empirically measured on exact Part Number
    FLEET_OBSERVED_SURROGATE = "fleet_observed_surrogate"   # Observed in fleet on same family/stage
    GENERIC_TURBINE_BENCHMARK = "generic_turbine_benchmark" # Literature / handbook reference value
    WORST_CASE_BOUND = "worst_case_bound"                   # Conservative standard bound (e.g. beta=1.0)
    UNVERIFIED_ASSUMPTION = "unverified_assumption"         # Unverified analyst assumption
```

### Enforcement Logic (`enforce_reliability_scope`)
```python
def enforce_reliability_scope(
    target_part_number: str,
    source_part_number: Optional[str],
    data_scope: ReliabilityScope
) -> ReliabilityScope:
    """Enforces reliability scope protection.
    
    Prevents general turbine reliability data from silently being assigned
    to specific part numbers (e.g. CFM56 P/N 301-789-204-0) as PART_SPECIFIC_MEASURED.
    """
    if not source_part_number or source_part_number.strip() != target_part_number.strip():
        if data_scope == ReliabilityScope.PART_SPECIFIC_MEASURED:
            return ReliabilityScope.GENERIC_TURBINE_BENCHMARK
    return data_scope
```

When evaluating `CFM56 High Pressure Turbine Stage 1 Rotor Blade (P/N 301-789-204-0)`:
* Zaretsky et al. (NASA/TP-2013-217030) provides fleet removal data on 16 United Airlines blade sets, but does **not** catalog P/N `301-789-204-0` specifically.
* The system enforces `scope = ReliabilityScope.FLEET_OBSERVED_SURROGATE`.
* It is prohibited from claiming that P/N `301-789-204-0` has an empirically certified failure rate.

---

## 5. Audited Formula Ground Truth Vector ($N = 10$)

All 10 aerospace equations in `tests/formula_ground_truth.json` and `src/rag/formula_extractor.py` were audited for exact mathematical agreement, variable nomenclature, units, and source page ranges:

| ID | Formula Name | Display Representation | Normalized Expression | Source Document | Page | Verified Standard Reference |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **FGT-01** | `mode_criticality_number` | $C_m = \beta \times \alpha \times \lambda_p \times t$ | `Cm = beta * alpha * lambda_p * t` | `MIL-STD-1629A.pdf` | 28 | Task 102 § 4.5.2 |
| **FGT-02** | `item_criticality_number` | $C_r = \sum (C_m)_n$ | `Cr = sum(Cm_n for n in failure_modes)` | `MIL-STD-1629A.pdf` | 28 | Task 102 § 4.5.3 |
| **FGT-03** | `exponential_reliability` | $R(t) = e^{-\lambda t}$ | `R_t = exp(-lambda * t)` | `MIL-STD-1629A.pdf` | 28 | Task 102 § 4.5 |
| **FGT-04** | `exponential_failure_probability` | $P(t) = 1 - e^{-\lambda t}$ | `P_t = 1 - exp(-lambda * t)` | `MIL-STD-1629A.pdf` | 27 | Task 102 § 4.5 |
| **FGT-05** | `weibull_cumulative_failure` | $F(t) = 1 - e^{-(t/\eta)^\beta}$ | `F_t = 1 - exp(-(t / eta)^beta)` | `NASA_TP_2013_217830` | 11 | NASA/TP-2013-217030 Eq. 1 |
| **FGT-06** | `weibull_reliability_function` | $R(t) = e^{-(t/\eta)^\beta}$ | `R_t = exp(-(t / eta)^beta)` | `NASA_TP_2013_217830` | 11 | NASA/TP-2013-217030 § 5.1 |
| **FGT-07** | `johnson_weibull_median_rank` | $MR = \frac{i - 0.3}{N + 0.4}$ | `MR = (i - 0.3) / (N + 0.4)` | `NASA_TP_2013_217830` | 12 | NASA/TP-2013-217030 § 5.1 (Benard) |
| **FGT-08** | `nusselt_number` | $Nu = \frac{h \times d}{k}$ | `Nu = (h * d) / k` | `NASA_Internal_Cooling...` | 14 | NASA CR-198472 § 4.1 |
| **FGT-09** | `reynolds_number` | $Re = \frac{\rho \times V \times d}{\mu}$ | `Re = (rho * V * d) / mu` | `NASA_Internal_Cooling...` | 14 | NASA CR-198472 § 4.1 |
| **FGT-10** | `rotation_number` | $Ro = \frac{\Omega \times d}{V}$ | `Ro = (Omega * d) / V` | `NASA_Internal_Cooling...` | 14 | NASA CR-198472 § 4.1 |

---

## 6. Audit Conclusion

All criticality equations and parameter fields comply with MIL-STD-1629A Task 102. Silent fabrication of numerical reliability inputs is architecturally prevented. Bounding assumptions are explicitly distinguished from empirical field observations.
