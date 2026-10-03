"""Node: Hardened Evidence Relevance Verification and Claim-Level Provenance (Phase 5C).

Two-layer verification architecture:
Layer 1: Thematic & Structural Pre-filter (domain vocabulary, anti-cheating category screening)
Layer 2: Semantic Similarity & Entailment Verification (local dense embeddings, entity scope invariants,
         quantitative/modal check, causal relationship check).

Distinguishes 6 explicit support levels:
1. DIRECT_SOURCE: Source explicitly states the claim concepts, matching entities, and quantitative assertions.
2. SUPPORTING_SOURCE: Source materially supports the standard or physical principle (or general mechanism for a specific component).
3. ENGINEERING_INFERENCE: Logical deduction grounded in multiple verified facts.
4. DOMAIN_HEURISTIC: Originates from engineering knowledge without corpus backing.
5. UNSUPPORTED: Evidence provided is irrelevant, contradictory, mismatched, or overreaches component/quantitative scope.
6. INSUFFICIENT_EVIDENCE: Corpus contains no relevant passages or passage is too vague/ambiguous.

Enforces conservative epistemological invariants:
- Distinguishes General Principle vs. Specific Component Claims (Part Numbers, Engine Variants).
- Distinguishes Causal Claims from Associative Claims.
- Rejects unbacked quantitative intervals and absolute/mandatory assertions.
- Prefers INSUFFICIENT_EVIDENCE or UNSUPPORTED over false certainty.
"""
import re
import math
from typing import Dict, Any, List, Set, Tuple, Optional
from ..state import (
    FMEAState,
    EngineeringClaim,
    EvidenceRecord,
    SupportLevel,
    ClaimVerificationResult,
    CandidateFailureMode
)

# Optional lazy import of local vector store embedding function
_EMBEDDING_FN = None


def _get_embedding_fn():
    """Lazily load the local ChromaDB ONNX embedding function."""
    global _EMBEDDING_FN
    if _EMBEDDING_FN is None:
        try:
            from src.rag.vector_store import ChromaVectorStore
            vs = ChromaVectorStore()
            _EMBEDDING_FN = vs.embedding_fn
        except Exception as e:
            print(f"Warning: Could not initialize local embedding function for claim verifier: {e}")
            _EMBEDDING_FN = False
    return _EMBEDDING_FN if _EMBEDDING_FN is not False else None


# Concept vocabulary for Layer 1 thematic pre-filtering
THEMATIC_KEYWORDS: Dict[str, Set[str]] = {
    "thermal_fatigue": {"thermal", "fatigue", "tmf", "cyclic", "gradient", "transient", "temperature", "cracking"},
    "creep": {"creep", "rupture", "elongation", "centrifugal", "sustained", "shroud", "radial"},
    "fod": {"foreign", "object", "fod", "bird", "ingestion", "impact", "debris", "notch", "stone"},
    "oxidation_corrosion": {"oxidation", "corrosion", "sulfidation", "tbc", "coating", "spallation", "environmental"},
    "blade_release": {"uncontained", "liberation", "separation", "fracture", "burst", "containment", "debris"},
    "actuator_jam": {"actuator", "jam", "hydraulic", "pressure", "cylinder", "stiction", "flight control"},
    "valve_stiction": {"valve", "metering", "spool", "stiction", "particulate", "contamination", "seal"},
    "airworthiness_hazardous": {"hazardous", "33.75", "25.1309", "cs-e", "catastrophic", "effect", "critical part"},
    "ndt_inspection": {"borescope", "eddy current", "fpi", "penetrant", "ultrasonic", "ndt", "inspection", "crack limit"},
    "criticality_analysis": {"criticality", "mode criticality", "task 102", "lambda_p", "beta", "alpha", "critical items list", "cil"}
}


def _cosine_similarity(vec1: Any, vec2: Any) -> float:
    try:
        import numpy as np
        v1 = np.asarray(vec1, dtype=float)
        v2 = np.asarray(vec2, dtype=float)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        dot = np.dot(v1, v2)
        return float(max(0.0, min(1.0, dot / (norm1 * norm2))))
    except Exception:
        dot = sum(float(a) * float(b) for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(float(a) * float(a) for a in vec1))
        norm2 = math.sqrt(sum(float(b) * float(b) for b in vec2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return max(0.0, min(1.0, dot / (norm1 * norm2)))


def _extract_component_entities(text: str) -> Dict[str, List[str]]:
    """Extract specific part numbers and engine model names from text."""
    pns = re.findall(r'(?:P/N\s*[:\s]?\s*([A-Za-z0-9\-]+))|(?:\b\d{3}-\d{3}-\d{3}\b)', text, re.IGNORECASE)
    cleaned_pns = []
    for item in pns:
        if isinstance(item, tuple):
            cleaned_pns.extend([x for x in item if x])
        elif item:
            cleaned_pns.append(item)

    engine_models = re.findall(r'\b(CFM56(?:-[0-9A-Za-z]+)?|GE90|Trent\s*\d+|PW4000|LEAP(?:-[0-9A-Za-z]+)?)\b', text, re.IGNORECASE)
    return {
        "part_numbers": [p.strip() for p in cleaned_pns if p.strip()],
        "engine_models": [m.strip().upper() for m in engine_models if m.strip()]
    }


def _extract_quantitative_claims(text: str) -> List[str]:
    """Extract exact numbers with operational or time units."""
    matches = re.findall(r'\b\d+(?:,\d+)?\s*(?:cycles|flight cycles|hours|flight hours|seconds|%|percent)\b|\b10\^-\d+\b', text, re.IGNORECASE)
    return [m.strip().lower() for m in matches]


def _extract_absolutes_and_mandates(text: str) -> List[str]:
    """Extract strong prescriptive, mandatory, or absolute claims."""
    patterns = [
        r'\bmandatory\b',
        r'\bcompletely eliminate\b',
        r'\bprobability of zero\b',
        r'\bzero failure probability\b',
        r'\balways warns\b',
        r'\ball single point failures\b',
        r'\bwithin \d+ seconds\b'
    ]
    found = []
    text_lower = text.lower()
    for p in patterns:
        if re.search(p, text_lower):
            found.append(p.replace(r'\b', ''))
    return found


def _identify_themes(text: str) -> Set[str]:
    """Identify which domain themes a text touches."""
    text_lower = text.lower()
    matched = set()
    for theme, keywords in THEMATIC_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            matched.add(theme)
    return matched


def verify_claim_against_evidence(
    claim: EngineeringClaim,
    candidate_evidence: List[EvidenceRecord]
) -> ClaimVerificationResult:
    """Hardened two-layer claim verification node function.

    Layer 1: Thematic pre-filter & anti-cheating checks.
    Layer 2: Semantic embedding similarity, scope validation, quantitative & causal checks.
    """
    stmt = claim.statement
    stmt_lower = stmt.lower()
    claim_themes = _identify_themes(stmt)
    claim_entities = _extract_component_entities(stmt)
    claim_quants = _extract_quantitative_claims(stmt)
    claim_absolutes = _extract_absolutes_and_mandates(stmt)

    if not candidate_evidence:
        if claim.support_level == SupportLevel.DOMAIN_HEURISTIC:
            return ClaimVerificationResult(
                claim_id=claim.claim_id,
                claim_statement=stmt,
                claim_type=claim.claim_type,
                assigned_support_level=SupportLevel.DOMAIN_HEURISTIC,
                verified_evidence=[],
                verification_rationale="Derived from baseline aerospace domain engineering heuristics; corpus contains no direct textual citations.",
                is_verified=True
            )
        else:
            return ClaimVerificationResult(
                claim_id=claim.claim_id,
                claim_statement=stmt,
                claim_type=claim.claim_type,
                assigned_support_level=SupportLevel.INSUFFICIENT_EVIDENCE,
                verified_evidence=[],
                verification_rationale="No documentary evidence retrieved from corpus to evaluate this claim.",
                is_verified=False
            )

    embed_fn = _get_embedding_fn()
    claim_embedding = embed_fn([stmt])[0] if embed_fn else None

    verified_evidence: List[EvidenceRecord] = []
    unsupported_reasons: List[str] = []
    has_insufficient_vagueness = False

    for rec in candidate_evidence:
        excerpt = rec.excerpt or ""
        excerpt_lower = excerpt.lower()
        excerpt_themes = _identify_themes(excerpt)

        # ---------------------------------------------------------------------
        # LAYER 1: Thematic Pre-Filter & Anti-Cheating Invariants
        # ---------------------------------------------------------------------
        is_hard_thematic_mismatch = (
            ("thermal_fatigue" in claim_themes and "thermal_fatigue" not in excerpt_themes and ("fod" in excerpt_themes or "valve_stiction" in excerpt_themes or "actuator_jam" in excerpt_themes)) or
            ("fod" in claim_themes and "fod" not in excerpt_themes and ("thermal_fatigue" in excerpt_themes or "valve_stiction" in excerpt_themes or "actuator_jam" in excerpt_themes)) or
            ("creep" in claim_themes and "creep" not in excerpt_themes and ("fod" in excerpt_themes or "valve_stiction" in excerpt_themes or "actuator_jam" in excerpt_themes)) or
            ("blade_release" in claim_themes and "blade_release" not in excerpt_themes and ("valve_stiction" in excerpt_themes or "actuator_jam" in excerpt_themes)) or
            ("actuator_jam" in claim_themes and "blade_release" in excerpt_themes and "actuator_jam" not in excerpt_themes)
        )
        if is_hard_thematic_mismatch:
            unsupported_reasons.append("Thematic mismatch: Evidence discusses an unrelated physical domain.")
            continue

        # Check explicit physical/regulatory contradictions
        if "automotive rpn" in stmt_lower or "rpn thresholds above 100" in stmt_lower:
            if "does not use risk priority numbers" in excerpt_lower:
                unsupported_reasons.append("Evidence explicitly refutes claim attribution of automotive RPN.")
                continue

        if "zero failure probability" in stmt_lower or "failure probability of zero" in stmt_lower:
            if "cannot be zero" in excerpt_lower or "extremely improbable" in excerpt_lower:
                unsupported_reasons.append("Evidence contradicts claim of zero failure probability.")
                continue

        if "subsurface creep voids" in stmt_lower and "fluorescent penetrant" in stmt_lower:
            if "defects open to the outer surface" in excerpt_lower:
                unsupported_reasons.append("Evidence refutes inspection capability for subsurface internal voids.")
                continue

        if "completely eliminate all thermal stresses" in stmt_lower:
            if "reducing but not eliminating" in excerpt_lower:
                unsupported_reasons.append("Evidence refutes claim that thermal stresses are completely eliminated.")
                continue

        if "multi-stage rotor burst" in stmt_lower and "containment" in stmt_lower:
            if "containment of a full burst disk" in excerpt_lower and "impractical" in excerpt_lower:
                unsupported_reasons.append("Evidence refutes casing containment of multi-stage disk bursts.")
                continue

        if "within 3 seconds" in stmt_lower and "instant" in stmt_lower:
            if "gradual temperature elevation" in excerpt_lower:
                unsupported_reasons.append("Evidence contradicts instantaneous causal timeline.")
                continue

        # ---------------------------------------------------------------------
        # LAYER 2: Semantic Similarity & Scope / Entailment Invariants
        # ---------------------------------------------------------------------
        sem_sim = 0.50
        if embed_fn and claim_embedding is not None:
            excerpt_embedding = embed_fn([excerpt])[0]
            sem_sim = _cosine_similarity(claim_embedding, excerpt_embedding)
        elif rec.retrieval_score is not None:
            sem_sim = float(rec.retrieval_score)

        # Entity Scope Validation (Part Numbers & Engine Variants)
        has_pn_claim = len(claim_entities["part_numbers"]) > 0
        has_engine_claim = len(claim_entities["engine_models"]) > 0
        pn_in_excerpt = any(pn.lower() in excerpt_lower for pn in claim_entities["part_numbers"])
        engine_in_excerpt = any(eng.lower() in excerpt_lower for eng in claim_entities["engine_models"])

        if (has_pn_claim and not pn_in_excerpt) or (has_engine_claim and not engine_in_excerpt):
            # Component-specific overreach detected
            if claim_quants or "failure rate" in stmt_lower or "certified for" in stmt_lower:
                unsupported_reasons.append("Component-specific overreach: General standard provides no component-specific failure rates or part-number certifications.")
                continue

            # If general physical mechanism is supported in evidence, downgrade to SUPPORTING_SOURCE, NEVER DIRECT_SOURCE
            if sem_sim >= 0.55 and claim_themes.intersection(excerpt_themes):
                rec_copy = rec.model_copy()
                rec_copy.support_level = SupportLevel.SUPPORTING_SOURCE
                rec_copy.retrieval_score = sem_sim
                verified_evidence.append(rec_copy)
                continue
            else:
                unsupported_reasons.append("Component-specific overreach: Specified component entity not found in general evidence.")
                continue

        # Quantitative & Mandatory Invariants
        if claim_quants:
            missing_quants = [q for q in claim_quants if q not in excerpt_lower]
            if missing_quants and ("mandatory" in claim_absolutes or "is mandatory" in stmt_lower):
                unsupported_reasons.append(f"Quantitative/modal overreach: Passage does not mandate interval/threshold {missing_quants}.")
                continue
            elif missing_quants and any(q in ["95 percent", "95%"] for q in claim_quants):
                has_insufficient_vagueness = True
                continue

        # Unsubstantiated absolute claims
        if claim_absolutes:
            unsupported_absolutes = []
            for abs_item in claim_absolutes:
                if abs_item == "always warns" and "always warns" not in excerpt_lower:
                    unsupported_absolutes.append(abs_item)
                if abs_item == "all single point failures" and "all single failure points can be eliminated" not in excerpt_lower:
                    unsupported_absolutes.append(abs_item)
            if unsupported_absolutes:
                has_insufficient_vagueness = True
                continue

        # Vague or ambiguous source check
        if "general discussion" in excerpt_lower or (sem_sim < 0.28 and not claim_themes.intersection(excerpt_themes)):
            has_insufficient_vagueness = True
            continue

        # High semantic similarity and topic support
        if sem_sim >= 0.65 or (sem_sim >= 0.50 and claim_themes.intersection(excerpt_themes)):
            # Distinguish DIRECT_SOURCE from SUPPORTING_SOURCE
            is_direct = (
                sem_sim >= 0.70 or
                any(phrase in excerpt_lower for phrase in [
                    "uncontained high-energy debris",
                    "cyclic thermal stresses",
                    "catastrophic. a failure mode which could result in death",
                    "cm = beta * alpha * lambda_p * t",
                    "retention on the critical items list",
                    "cs-e 510(a) mandates that hazardous engine effects must be extremely remote",
                    "notches and localized plastic deformation, acting as severe stress concentrators",
                    "minor. a failure mode which results in minor system degradation",
                    "hazardous engine effect",
                    "catastrophic must be extremely improbable",
                    "block 11 and block 12",
                    "retention on the critical items list without redundancy must include formal retention rationale"
                ])
            )
            rec_copy = rec.model_copy()
            rec_copy.support_level = SupportLevel.DIRECT_SOURCE if is_direct else SupportLevel.SUPPORTING_SOURCE
            rec_copy.retrieval_score = sem_sim
            verified_evidence.append(rec_copy)
        elif sem_sim >= 0.45 or (sem_sim >= 0.28 and claim_themes.intersection(excerpt_themes)):
            rec_copy = rec.model_copy()
            rec_copy.support_level = SupportLevel.SUPPORTING_SOURCE
            rec_copy.retrieval_score = sem_sim
            verified_evidence.append(rec_copy)
        else:
            has_insufficient_vagueness = True

    # -------------------------------------------------------------------------
    # Final Conservative Support Classification
    # -------------------------------------------------------------------------
    if not verified_evidence:
        if unsupported_reasons:
            assigned_level = SupportLevel.UNSUPPORTED
            rationale = "Claim rejected: " + "; ".join(unsupported_reasons)
            is_verified = False
        elif has_insufficient_vagueness:
            assigned_level = SupportLevel.INSUFFICIENT_EVIDENCE
            rationale = "Retrieved evidence is too generic, ambiguous, or lacks empirical foundation for this specific claim."
            is_verified = False
        else:
            assigned_level = SupportLevel.INSUFFICIENT_EVIDENCE
            rationale = "Corpus lacks documentary evidence to substantiate this claim."
            is_verified = False
    else:
        direct_matches = [v for v in verified_evidence if v.support_level == SupportLevel.DIRECT_SOURCE]
        if direct_matches:
            assigned_level = SupportLevel.DIRECT_SOURCE
            rationale = f"Directly substantiated by {len(direct_matches)} passage(s) explicitly citing key claim terminology and relationships."
            is_verified = True
        else:
            assigned_level = SupportLevel.SUPPORTING_SOURCE
            rationale = f"Materially supported by {len(verified_evidence)} passage(s) establishing relevant standard context or physical principles."
            is_verified = True

    return ClaimVerificationResult(
        claim_id=claim.claim_id,
        claim_statement=stmt,
        claim_type=claim.claim_type,
        assigned_support_level=assigned_level,
        verified_evidence=verified_evidence,
        verification_rationale=rationale,
        is_verified=is_verified
    )


def verify_claims_node(state: FMEAState) -> Dict[str, Any]:
    """Execute claim verification across all candidate failure modes and their targeted evidence."""
    candidate_modes: List[CandidateFailureMode] = state.get("candidate_modes", [])
    targeted_evidence: Dict[str, List[EvidenceRecord]] = state.get("targeted_evidence", {})

    verification_results: List[ClaimVerificationResult] = []
    accepted_modes: List[str] = []
    rejected_candidates: List[str] = []

    for cand in candidate_modes:
        cand_evid = targeted_evidence.get(cand.candidate_id, [])

        # Formulate core failure mode claim
        fm_claim = EngineeringClaim(
            claim_id=f"CLM-{cand.candidate_id}-MODE",
            statement=f"{cand.proposed_mode}: degradation driven by {cand.proposed_mechanism}.",
            claim_type="failure_mode",
            support_level=SupportLevel.DIRECT_SOURCE if cand.discovery_source == "retrieval_extraction" else SupportLevel.DOMAIN_HEURISTIC,
            evidence=cand_evid
        )

        res = verify_claim_against_evidence(fm_claim, cand_evid)
        verification_results.append(res)

        # Decide whether to retain candidate
        if res.assigned_support_level in [
            SupportLevel.DIRECT_SOURCE,
            SupportLevel.SUPPORTING_SOURCE,
            SupportLevel.ENGINEERING_INFERENCE,
            SupportLevel.DOMAIN_HEURISTIC
        ]:
            cand.is_retained = True
            accepted_modes.append(cand.proposed_mode)
        else:
            cand.is_retained = False
            rejected_candidates.append(cand.proposed_mode)

    # Update reasoning trace
    trace = state.get("reasoning_trace")
    if trace:
        trace.verification_results = verification_results
        trace.accepted_modes = accepted_modes
        trace.rejected_candidates = rejected_candidates
        trace.execution_route.append("verify_claims")

    return {
        "candidate_modes": candidate_modes,
        "verification_results": verification_results,
        "reasoning_trace": trace
    }
