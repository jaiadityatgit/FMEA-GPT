"""Run end-to-end HPT analysis through production pipeline.

Audits:
- Component classification
- Discovered candidate modes
- Targeted evidence retrieval
- Claim verification
- Severity classification
- Criticality analysis
- CIL assessment
- Detection and controls
- Final report generation

Saves:
- data/output/hpt_core_final_trace.json
- data/output/fresh_hpt_trace.json
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.rag.config import RAGConfig
from src.agents.graph import FMEAGeneratorGraph


def main():
    print("=" * 80)
    print("      FMEA-GPT HPT END-TO-END AUDIT (CORE-FINAL)")
    print("=" * 80)

    cfg = RAGConfig.get_production_config()
    print(f"Production Store: {cfg.chroma_dir}")
    print(f"Collection Name:  {cfg.collection_name}")

    graph = FMEAGeneratorGraph(config=cfg)

    comp_name = "CFM56 High Pressure Turbine Stage 1 Rotor Blade"
    part_number = "301-789-204-0"

    print(f"\nRunning analysis for: {comp_name} (P/N: {part_number})...")
    report = graph.run(comp_name, target_part_number=part_number)

    print(f"\nClassification:")
    print(f"  System:           {report.component.system}")
    print(f"  Subsystem:        {report.component.subsystem}")
    print(f"  Regulatory Class: {report.component.regulatory_class}")
    print(f"  Analysis Status:  {report.component.analysis_status.value}")

    print(f"\nRetained Failure Modes ({len(report.failure_modes)} total):")
    for i, fm in enumerate(report.failure_modes, 1):
        print(f"\n[{i}] {fm.mode_id}: {fm.failure_mode}")
        print(f"    Mechanism:   {fm.physical_mechanism}")
        print(f"    Severity:    {fm.mil_std_severity_category} (Category: {fm.severity_classification.category.value})")
        print(f"    Criticality: Matrix={fm.criticality_analysis.matrix_position}, Prob={fm.criticality_analysis.qualitative_level.value}")
        print(f"    CIL SPF:     {fm.cil_assessment.single_failure_point}, CriticalItem={fm.cil_assessment.is_critical_item}")
        print(f"    Interval:    {fm.inspection_interval}")
        print(f"    Evidence Records ({len(fm.evidence_records)}):")
        for ev in fm.evidence_records[:3]:
            print(f"      - {ev.source_document} (p.{ev.page_number}): {ev.document_title[:40]} [{ev.support_level.value}]")
            if ev.official_report_number:
                print(f"        Report No: {ev.official_report_number} | Domain: {ev.technical_domain}")

    report_dict = report.model_dump()

    # Save to data/output/hpt_core_final_trace.json
    out_path = Path("data/output/hpt_core_final_trace.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, default=str)
    print(f"\nSaved core-final trace to {out_path}")

    # Also save to fresh_hpt_trace.json for test compatibility
    fresh_path = Path("data/output/fresh_hpt_trace.json")
    with open(fresh_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, default=str)
    print(f"Saved fresh trace to {fresh_path}")

    cov = report.evidence_coverage
    print(f"\nEvidence Coverage Summary:")
    print(f"  Total Claims:        {cov.total_claims}")
    print(f"  Directly Supported:  {cov.directly_supported}")
    print(f"  Supporting Evidence: {cov.supporting_evidence}")
    print(f"  Inferences:          {cov.engineering_inference}")
    print(f"  Domain Heuristics:   {cov.domain_heuristic}")
    print(f"  Coverage Score:      {cov.coverage_score}")
    print(f"  Adequate:            {cov.is_coverage_adequate}")


if __name__ == "__main__":
    main()
