"""Scanner for hidden hard-coded engineering knowledge across src/."""
import os
import re

search_terms = {
    "CFM56": r"\bCFM56\b",
    "HPT": r"\bHPT\b",
    "turbine blade": r"\bturbine blade\b",
    "TMF": r"\bTMF\b",
    "creep": r"\bcreep\b",
    "FOD": r"\bFOD\b",
    "cooling": r"\bcooling\b",
    "beta_1": r"(?:beta|β)\s*=\s*1(?:\.0)?",
    "maintenance_interval": r"\b(?:\d+[\d,]*\s*(?:hours|cycles|flight hours|fc|fh)|interval)\b",
    "sensor_signatures": r"\b(?:EGT|vibration|N1|N2|oil pressure|fuel flow|margin)\b",
    "ATA_mappings": r"\bATA\s*\d+\b"
}

results = {term: [] for term in search_terms}

for root, dirs, files in os.walk("src"):
    for f in files:
        if f.endswith(".py"):
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8", errors="ignore") as fp:
                lines = fp.readlines()
            for line_idx, line in enumerate(lines, 1):
                for term_name, pat in search_terms.items():
                    if re.search(pat, line, re.I):
                        results[term_name].append({
                            "file": path,
                            "line": line_idx,
                            "text": line.strip()
                        })

print("=" * 80)
print("HIDDEN HARD-CODING OCCURRENCE SUMMARY IN src/:")
print("=" * 80)
for term_name, hits in results.items():
    print(f"Term '{term_name}': {len(hits)} occurrences across {len(set(h['file'] for h in hits))} files")

out_file = "data/output/phase5f_heuristic_scan.json"
import json
with open(out_file, "w", encoding="utf-8") as fp:
    json.dump(results, fp, indent=2)
print(f"\nDetailed hits saved to {out_file}")
