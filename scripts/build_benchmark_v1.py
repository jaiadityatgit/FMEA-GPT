"""Script to freeze canonical retrieval benchmark v1."""
import json
from pathlib import Path

# Load existing ground truth
with open("tests/retrieval_ground_truth.json", "r", encoding="utf-8") as f:
    gt = json.load(f)

# Canonical ground truth basis descriptions
basis_map = {
    "RET-01": "NASA-STD-8729.1A § 4.3 (thermal stress design margins) and NASA/TP-2013-217030 / NASA HOST Creep-Fatigue isotropic cyclic strain accumulation.",
    "RET-02": "NASA C-MAPSS damage propagation modeling and NASA/TP-2013-217030 (CFM56 airline overhaul field data on TMF cracking).",
    "RET-03": "EASA CS-E 510 / CS-E 840 (rotor integrity) and CS-E 740 (temperature and stress rupture limits).",
    "RET-04": "EASA CS-E 510 (blade-casing clearance limits) and NASA C-MAPSS blade clearance degradation modeling.",
    "RET-05": "EASA CS-E 800 / CS-E 810 (bird strike ingestion) and FAA AC 33.75-1A § 33.75(a)(3) (environmental ingestion).",
    "RET-06": "FAA AC 33.75-1A § 33.75(b) (foreign object containment and notch fatigue crack initiation).",
    "RET-07": "EASA CS-E 510 AMC E 510 § 3 and FAA AC 33.75-1A (HCF aerodynamic resonant excitation).",
    "RET-08": "EASA CS-E 650 (Vibration Surveys & Campbell diagram resonant crossing clearance) and FAA AC 33.75-1A.",
    "RET-09": "FAA AC 33.75-1A § 33.75(g)(2) and EASA CS-E 510 (Hazardous Engine Effect definition: uncontained high-energy debris).",
    "RET-10": "FAA AC 33.75-1A § 33.75(e) and EASA CS-E 810 / CS-E 520 (containment ring energy absorption capability).",
    "RET-11": "FAA AC 33.75-1A, EASA CS-E 510, and NASA-CR-198472 (heat transfer in rotating coolant passages).",
    "RET-12": "NASA-CR-198472 (heat transfer coefficients in serpentine rotating coolant channels; flow starvation physics).",
    "RET-13": "Corpus gap query. No document in regulatory or current technical corpus covers contact mechanics at blade root dovetail contacts.",
    "RET-14": "Corpus gap query. No document in regulatory or current technical corpus covers dovetail fir-tree fretting wear.",
    "RET-15": "EASA CS-E 510 AMC E 510 and NASA-STD-8729.1A § 4.3 (environmental durability and hot corrosion attack).",
    "RET-16": "EASA CS-E 510 § 4 and NASA-STD-8729.1A § 5 (salt fog / marine environment corrosion testing).",
    "RET-17": "EASA CS-E 510 AMC E 510 § 4 (Fluorescent Penetrant Inspection criteria for surface-breaking fatigue cracks).",
    "RET-18": "EASA CS-E 510 AMC E 510 and NASA ASRS maintenance incident reports (borescope access and optical flaw limits).",
    "RET-19": "EASA CS-E 510 AMC E 510 and FAA AC 33.75-1A § 4 (On-condition maintenance and scheduled overhaul intervals).",
    "RET-20": "NASA ASRS Maintenance Incident Reports (maintenance human factors and cross-threading/torque error) and EASA CS-E 510.",
    "RET-21": "FAA AC 33.75-1A § 33.75(g)(2) (statutory definition of Hazardous Engine Effects including uncontained debris and uncontrolled fire).",
    "RET-22": "FAA AC 33.75-1A § 33.75(g)(2)(i) and EASA CS-E 510 § 3 (casing penetration by non-contained high-energy fragments).",
    "RET-23": "FAA AC 25.1309-1A § 8.d(1) and AC 25.1309-1B § 7 (Catastrophic Failure Condition definition: multiple fatalities / hull loss).",
    "RET-24": "MIL-STD-1629A § 4.4.3.a (Severity Category I - Catastrophic definition) and FAA AC 25.1309-1B.",
    "RET-25": "MIL-STD-1629A Task 102 § 4.5.2 (Mode Criticality Number equation: Cm = beta * alpha * lambda_p * t).",
    "RET-26": "MIL-STD-1629A Task 102 § 4.5.3 (Item Criticality Number equation: Cr = sum(Cm)).",
    "RET-27": "NASA-STD-8729.1A § 4.4 (Single Failure Point definition, elimination, and retention rationale requirements).",
    "RET-28": "NASA-STD-8729.1A § 4.4.2 (Critical Items List Category 1/1R identification) and NASA SP-2016-6105.",
    "RET-29": "MIL-STD-1629A Task 102 Table 102.1 (Conditional probability beta values: actual loss = 1.0, probable = 0.1-1.0, possible = 0-0.1, none = 0).",
    "RET-30": "FAA AC 33.75-1A § 33.75(g)(1) and EASA CS-E 510 (definition of Major Engine Effects: controlled in-flight shutdown, partial power loss).",
    "RET-31": "MIL-STD-1629A § 4.4.3.c (Severity Category III - Marginal definition: minor system damage without injury).",
    "RET-32": "FAA AC 33.75-1A § 33.75(e) and EASA CS-E 810 (rotor burst fragment deflection and containment ring impact dynamics)."
}

benchmark_v1 = []
evaluable_count = 0
corpus_gap_count = 0
negative_control_count = 0

for item in gt:
    qid = item["query_id"]
    is_gap = item.get("corpus_gap", False)
    
    if is_gap:
        q_type = "corpus_gap"
        corpus_gap_count += 1
    else:
        q_type = "evaluable"
        evaluable_count += 1

    entry = {
        "query_id": qid,
        "query": item["query"],
        "category": item["category"],
        "query_type": q_type,
        "corpus_gap": is_gap,
        "relevant_documents": item.get("relevant_documents", []),
        "relevant_pages": item.get("relevant_pages", []),
        "relevant_topics": item.get("relevant_topics", []),
        "ground_truth_granularity": item.get("ground_truth_granularity", "document"),
        "ground_truth_basis": basis_map.get(qid, "Engineering standard reference.")
    }
    benchmark_v1.append(entry)

out_file = Path("tests/retrieval_benchmark_v1.json")
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(benchmark_v1, f, indent=2)

print(f"Frozen benchmark v1 saved to {out_file}")
print(f"Total queries: {len(benchmark_v1)}")
print(f"Evaluable queries: {evaluable_count}")
print(f"Corpus gap queries: {corpus_gap_count}")
print(f"Negative control queries: {negative_control_count}")
