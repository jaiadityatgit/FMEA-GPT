"""Script to audit the fresh HPT reasoning trace."""
import json
import re

with open("data/output/fresh_hpt_trace.json", "r", encoding="utf-8") as f:
    trace = json.load(f)

print("=" * 80)
print(f"HPT TRACE AUDIT: {trace['component']['component_name']} (P/N: {trace['component']['part_number']})")
print("=" * 80)

forbidden_phrases = [
    r"this exact cfm56 part",
    r"will fail",
    r"has a failure rate of",
    r"requires inspection every",
    r"is known to fail",
    r"is certified",
    r"is mandatory"
]

all_flagged = []

for i, fm in enumerate(trace["failure_modes"], 1):
    print(f"\n--- FAILURE MODE {i}: {fm['mode_id']} - {fm['failure_mode']} ---")
    print(f"Physical Mechanism: {fm['physical_mechanism']}")
    print(f"Root Cause: {fm['root_cause']}")
    print(f"Severity Category: {fm['severity_classification']['category']}")
    print(f"Regulatory Hazard Tier: {fm['severity_classification']['regulatory_hazard_tier']}")
    print(f"Criticality Methodology: {fm['criticality_analysis']['methodology']}")
    print(f"Criticality Qualitative Level: {fm['criticality_analysis'].get('qualitative_level')}")
    print(f"CIL Critical Item: {fm['cil_assessment']['is_critical_item']} (SPF: {fm['cil_assessment']['single_failure_point']})")
    print(f"CIL Inclusion Basis: {fm['cil_assessment'].get('inclusion_basis')}")
    
    print("\nCitations:")
    for c in fm.get("citations", []):
        print(f"  * {c['source_document']} Page {c['page_number']} [{c.get('doc_title', '')}] (Sim: {c.get('similarity_score', 0)})")
    
    print("\nEvidence Records:")
    for er in fm.get("evidence_records", []):
        print(f"  * [{er['evidence_id']}] {er['source_document']} p.{er['page_number']} (Score: {er['retrieval_score']}, Support: {er['support_level']}) - Q: '{er['retrieval_query']}'")

    print("\nAssumptions in Criticality:")
    for a in fm.get("criticality_analysis", {}).get("assumptions", []):
        print(f"  * [{a['assumption_id']}] {a['statement']} (Risk: {a.get('risk_impact')})")

    # Audit text statements for forbidden overgeneralizations
    texts_to_check = [
        fm['failure_mode'],
        fm['physical_mechanism'],
        fm['root_cause'],
        fm['local_effect'],
        fm['next_higher_effect'],
        fm['end_effect'],
        fm['detection_method'],
        fm['recommended_action'],
        fm['severity_classification']['justification']['statement'],
        fm['criticality_analysis']['rationale']['statement']
    ]
    for text in texts_to_check:
        for pat in forbidden_phrases:
            if re.search(pat, text, re.I):
                all_flagged.append((fm['mode_id'], pat, text))

print("\n" + "=" * 80)
print("UNSUPPORTED GENERALIZATION AUDIT:")
if all_flagged:
    print(f"WARNING: Flagged {len(all_flagged)} statements with potentially overgeneralized language:")
    for mid, pat, stmt in all_flagged:
        print(f"  [{mid}] Matched '{pat}': {stmt}")
else:
    print("PASSED: Zero unsupported generalization phrases found across all failure modes.")
print("=" * 80)
