"""Controlled technical terminology expansion module for FMEA-GPT Phase 5D.

Maps abbreviated or colloquial engineering terms to official regulatory and physical standard vocabulary.
Avoids uncontrolled query inflation by using a strictly curated aerospace domain synonym ontology.
"""
import re
from typing import Dict, List, Set


# Controlled aerospace engineering synonym dictionary
AEROSPACE_SYNONYM_MAP: Dict[str, List[str]] = {
    "fod": [
        "foreign object damage",
        "debris ingestion",
        "bird ingestion",
        "impact notch"
    ],
    "foreign object damage": [
        "bird ingestion",
        "runway debris impact",
        "leading edge notch"
    ],
    "tmf": [
        "thermomechanical fatigue",
        "cyclic thermal stress",
        "thermal gradient strain"
    ],
    "thermal fatigue": [
        "thermomechanical fatigue",
        "transient temperature gradient",
        "cyclic thermal stress"
    ],
    "creep": [
        "stress rupture",
        "sustained centrifugal load",
        "radial blade elongation",
        "plastic creep strain"
    ],
    "fir-tree": [
        "dovetail",
        "blade root attachment",
        "root serration"
    ],
    "dovetail": [
        "fir tree",
        "blade root attachment",
        "root slot"
    ],
    "blade release": [
        "blade separation",
        "uncontained debris",
        "rotor blade failure",
        "containment capability"
    ],
    "blade liberation": [
        "blade release",
        "blade fracture",
        "uncontained high-energy debris"
    ],
    "uncontained debris": [
        "hazardous engine effect",
        "rotor burst",
        "casing penetration"
    ],
    "sfp": [
        "single failure point",
        "single point failure",
        "critical items list"
    ],
    "single failure point": [
        "single point failure",
        "NASA-STD-8729.1A",
        "Critical Items List"
    ],
    "cil": [
        "critical items list",
        "NASA-STD-8729.1A retention criteria",
        "single failure point"
    ],
    "ndt": [
        "borescope inspection",
        "nondestructive inspection",
        "fluorescent penetrant",
        "eddy current"
    ],
    "borescope": [
        "optical borescope inspection",
        "internal hot section inspection",
        "periodic line maintenance"
    ],
    "criticality": [
        "failure mode criticality number",
        "Task 102",
        "qualitative criticality matrix"
    ],
    "tbc": [
        "thermal barrier coating",
        "spallation",
        "hot corrosion",
        "sulfidation"
    ]
}


def expand_query_terms(query: str, max_expansions_per_term: int = 2) -> str:
    """Expand recognized technical engineering terms in a query with canonical standard synonyms.
    
    Args:
        query: Original input search query.
        max_expansions_per_term: Max number of synonyms to append per matched term.
        
    Returns:
        Expanded query string containing original query plus targeted canonical terms.
    """
    if not query:
        return ""

    q_lower = query.lower()
    appended_terms: Set[str] = set()

    for term, synonyms in AEROSPACE_SYNONYM_MAP.items():
        # Match as whole word or phrase
        pattern = r'\b' + re.escape(term) + r'\b'
        if re.search(pattern, q_lower):
            for syn in synonyms[:max_expansions_per_term]:
                if syn.lower() not in q_lower and syn.lower() not in appended_terms:
                    appended_terms.add(syn)

    if appended_terms:
        # Append distinct expanded vocabulary to the end of original query
        return f"{query} {' '.join(sorted(appended_terms))}"
    
    return query
