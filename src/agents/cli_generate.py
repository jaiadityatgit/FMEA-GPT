"""CLI generation tool for FMEA-GPT aerospace analysis."""
import argparse
import os
import sys
from pathlib import Path

from .graph import FMEAGeneratorGraph
from .exporters.fmea_table import format_mil_std_1629a_markdown
from .exporters.digital_twin import export_digital_twin_json
from .exporters.cil_exporter import format_critical_items_list_markdown


def main():
    parser = argparse.ArgumentParser(description="Generate complete MIL-STD-1629A FMEA analysis for aerospace components.")
    parser.add_argument("component", nargs="*", help="Component description (e.g., 'CFM56 High Pressure Turbine Blade').")
    parser.add_argument("--part-number", "-p", type=str, default=None, help="Component Part Number (e.g., '301-789-204-0').")
    parser.add_argument("--output-dir", "-o", type=str, default="data/output", help="Directory to save generated FMEA artifacts.")
    parser.add_argument("--digital-twin", action="store_true", help="Print Digital Twin telemetry JSON output.")
    parser.add_argument("--cil", action="store_true", help="Print Critical Items List (CIL) report.")
    parser.add_argument("--json", action="store_true", help="Output raw FMEAReport in JSON format.")
    args = parser.parse_args()

    comp_name = " ".join(args.component).strip() if args.component else ""
    if not comp_name:
        comp_name = "CFM56 High Pressure Turbine Stage 1 Rotor Blade"

    print("=" * 80)
    print("                FMEA-GPT AEROSPACE AGENTIC REASONING ENGINE")
    print("               MIL-STD-1629A & FAA AC 33.75-1A GENERATOR")
    print("=" * 80)
    print(f"Target Component : {comp_name}")
    print(f"Part Number      : {args.part_number or 'Standard Catalog'}")
    print("Initializing LangGraph reasoning workflow...")

    generator = FMEAGeneratorGraph()
    report = generator.run(
        component_input=comp_name,
        target_part_number=args.part_number
    )

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Export MIL-STD-1629A Markdown Worksheet
    md_content = format_mil_std_1629a_markdown(report)
    md_file = out_dir / f"fmea_{report.component.subsystem.lower().replace(' ', '_')}.md"
    md_file.write_text(md_content, encoding="utf-8")

    # 2. Export Digital Twin JSON
    dt_json = export_digital_twin_json(report)
    dt_file = out_dir / "digital_twin_telemetry.json"
    dt_file.write_text(dt_json, encoding="utf-8")

    # 3. Export Critical Items List (CIL)
    cil_content = format_critical_items_list_markdown(report)
    cil_file = out_dir / "critical_items_list.md"
    cil_file.write_text(cil_content, encoding="utf-8")

    print("\n[SUCCESS] FMEA Analysis generated and verified!")
    print(f"  - Total Failure Modes Evaluated : {len(report.failure_modes)}")
    print(f"  - Single Point Failures (SPF)   : {report.validation.single_point_failures_count}")
    print(f"  - Peak Risk Priority Number     : {report.validation.max_rpn}")
    print(f"  - MIL-STD-1629A Compliance      : {'PASSED' if report.validation.is_compliant else 'FLAGGED'}")
    print(f"\nArtifacts saved to {out_dir}/:")
    print(f"  - Worksheet   : {md_file.name}")
    print(f"  - DigitalTwin : {dt_file.name}")
    print(f"  - CIL Report  : {cil_file.name}")
    print("-" * 80)

    if args.digital_twin:
        print("\n" + dt_json)
    elif args.cil:
        print("\n" + cil_content)
    elif args.json:
        print("\n" + report.model_dump_json(indent=2))
    else:
        print("\n" + md_content)


if __name__ == "__main__":
    main()
