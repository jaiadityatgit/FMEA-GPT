"""Claim verification benchmark evaluation runner for FMEA-GPT Phase 5C.

Measures verifier performance against curated benchmark dataset (tests/claim_verification_benchmark.json).
Calculates:
- Multi-class confusion matrix
- Per-class Precision, Recall, F1
- Binary classification metrics (Supported vs Rejected/Insufficient)
Outputs clean JSON report for docs/phase5c_claim_verification.md.
"""
import sys
import json
from pathlib import Path
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agents.state import (
    EngineeringClaim,
    EvidenceRecord,
    SupportLevel
)
from src.agents.nodes.claim_verifier import verify_claim_against_evidence


def evaluate_claim_verifier(
    benchmark_path: str = "tests/claim_verification_benchmark.json"
) -> Dict[str, Any]:
    """Execute claim verification benchmark and return comprehensive performance metrics."""
    with open(benchmark_path, "r", encoding="utf-8") as f:
        cases: List[Dict[str, Any]] = json.load(f)

    labels = ["DIRECT_SOURCE", "SUPPORTING_SOURCE", "INSUFFICIENT_EVIDENCE", "UNSUPPORTED"]
    confusion: Dict[str, Dict[str, int]] = {
        true_lbl: {pred_lbl: 0 for pred_lbl in labels}
        for true_lbl in labels
    }

    results_details = []
    correct_count = 0
    total_count = len(cases)

    binary_tp = 0  # Expected supported, predicted supported
    binary_fp = 0  # Expected unsupported/insufficient, predicted supported
    binary_fn = 0  # Expected supported, predicted unsupported/insufficient
    binary_tn = 0  # Expected unsupported/insufficient, predicted unsupported/insufficient

    for c in cases:
        cid = c["case_id"]
        expected_lbl = c["expected_label"].upper()

        claim = EngineeringClaim(
            claim_id=f"CLM-{cid}",
            statement=c["claim"],
            claim_type=c.get("claim_type", "failure_mode"),
            support_level=SupportLevel.DIRECT_SOURCE
        )

        evidence = [
            EvidenceRecord(
                evidence_id=f"EVID-{cid}",
                source_document=c.get("source_doc", "unknown.pdf"),
                document_title="Evaluated Standard",
                publisher="Aerospace Authority",
                page_number=1,
                excerpt=c["evidence_excerpt"],
                retrieval_query=c["claim"],
                retrieval_score=0.75,
                support_level=SupportLevel.SUPPORTING_SOURCE
            )
        ]

        res = verify_claim_against_evidence(claim, evidence)
        predicted_lbl = res.assigned_support_level.value.upper()

        if predicted_lbl in labels and expected_lbl in labels:
            confusion[expected_lbl][predicted_lbl] += 1

        is_correct = (predicted_lbl == expected_lbl)
        if is_correct:
            correct_count += 1

        # Binary evaluation: Supported vs Non-Supported
        exp_is_supported = expected_lbl in ["DIRECT_SOURCE", "SUPPORTING_SOURCE"]
        pred_is_supported = predicted_lbl in ["DIRECT_SOURCE", "SUPPORTING_SOURCE"]

        if exp_is_supported and pred_is_supported:
            binary_tp += 1
        elif not exp_is_supported and pred_is_supported:
            binary_fp += 1
        elif exp_is_supported and not pred_is_supported:
            binary_fn += 1
        else:
            binary_tn += 1

        results_details.append({
            "case_id": cid,
            "category": c.get("category"),
            "claim_type": c.get("claim_type"),
            "claim": c["claim"],
            "expected_label": expected_lbl,
            "predicted_label": predicted_lbl,
            "is_correct": is_correct,
            "rationale": res.verification_rationale
        })

    # Calculate per-class metrics
    per_class_metrics = {}
    for lbl in labels:
        tp = confusion[lbl][lbl]
        fp = sum(confusion[other][lbl] for other in labels if other != lbl)
        fn = sum(confusion[lbl][other] for other in labels if other != lbl)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        per_class_metrics[lbl] = {
            "true_positive": tp,
            "false_positive": fp,
            "false_negative": fn,
            "support": sum(confusion[lbl].values()),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4)
        }

    # Binary metrics
    b_prec = binary_tp / (binary_tp + binary_fp) if (binary_tp + binary_fp) > 0 else 0.0
    b_rec = binary_tp / (binary_tp + binary_fn) if (binary_tp + binary_fn) > 0 else 0.0
    b_f1 = (2 * b_prec * b_rec) / (b_prec + b_rec) if (b_prec + b_rec) > 0 else 0.0
    b_acc = (binary_tp + binary_tn) / total_count if total_count > 0 else 0.0

    overall_accuracy = correct_count / total_count if total_count > 0 else 0.0

    return {
        "benchmark_summary": {
            "total_evaluated_pairs": total_count,
            "overall_exact_label_accuracy": round(overall_accuracy, 4),
            "binary_classification": {
                "accuracy": round(b_acc, 4),
                "precision": round(b_prec, 4),
                "recall": round(b_rec, 4),
                "f1_score": round(b_f1, 4),
                "true_positives": binary_tp,
                "false_positives": binary_fp,
                "true_negatives": binary_tn,
                "false_negatives": binary_fn
            }
        },
        "per_class_metrics": per_class_metrics,
        "confusion_matrix": confusion,
        "results_details": results_details
    }


if __name__ == "__main__":
    report = evaluate_claim_verifier()
    print("=== CLAIM VERIFICATION BENCHMARK PERFORMANCE ===")
    summary = report["benchmark_summary"]
    print(f"Total Evaluated Pairs: {summary['total_evaluated_pairs']}")
    print(f"Exact Multi-Class Accuracy: {summary['overall_exact_label_accuracy'] * 100:.1f}%")
    print(f"Binary Decision Accuracy:   {summary['binary_classification']['accuracy'] * 100:.1f}%")
    print(f"Binary Precision:           {summary['binary_classification']['precision'] * 100:.1f}%")
    print(f"Binary Recall:              {summary['binary_classification']['recall'] * 100:.1f}%")
    print(f"Binary F1 Score:            {summary['binary_classification']['f1_score'] * 100:.1f}%")

    print("\n=== PER-CLASS METRICS ===")
    for lbl, m in report["per_class_metrics"].items():
        print(f"  {lbl:<22} (N={m['support']:2d}): P={m['precision']*100:5.1f}% | R={m['recall']*100:5.1f}% | F1={m['f1_score']*100:5.1f}%")

    print("\n=== CONFUSION MATRIX (Row=Expected, Col=Predicted) ===")
    headers = [lbl[:6] for lbl in report["per_class_metrics"].keys()]
    print(f"{'Expected':<22} | " + " | ".join(f"{h:>6}" for h in headers))
    print("-" * 55)
    for exp_lbl in report["per_class_metrics"].keys():
        row = [f"{report['confusion_matrix'][exp_lbl][pred_lbl]:>6}" for pred_lbl in report["per_class_metrics"].keys()]
        print(f"{exp_lbl:<22} | " + " | ".join(row))

    # Save to scratch
    out_file = Path("scratch/claim_verification_benchmark_results.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved report to {out_file}")
