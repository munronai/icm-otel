# Stage 05 — Cross-Harness Scorecard & ICM Optimization Notes

## Objective
Synthesize Stage 04 evaluation and cost/latency data into an apples-to-apples scorecard across **Antigravity**, **Claude Code**, and **Codex**, and propose concrete `CONTEXT.md` / stage improvements for the target ICM workspace.

## Inputs
- `../04_ingest_and_eval/outputs/eval_results.json`
- `../04_ingest_and_eval/outputs/shadow_cost_report.md`
- `../03_apply_otel_config/outputs/applied_changes.md`

## Outputs
- `outputs/scorecard.md` — Pass Rate, Tool-Turn Efficiency, Wall-Clock Latency, and Exact/Shadow Cost per Solved Task
- `outputs/icm_optimization_notes.md` — Stage-level bottleneck diagnosis and proposed `CONTEXT.md` edits for the target ICM repo

## Required Tools (OSS / Free)
- `scripts/generate_scorecard.py` (Python stdlib aggregator) + agent Markdown synthesis
- *(Alt OSS: Marimo/Jupyter notebooks; Alt Paid: Arize AX, W&B Weave dashboards)*

## Steps
1. Run `python3 05_compare_and_report/scripts/generate_scorecard.py` to aggregate `04_ingest_and_eval/outputs/eval_results.json`.
2. Inspect `outputs/scorecard.md` (cross-harness pass rate, tool-turn efficiency, latency, and cost per passed trace).
3. Review `outputs/icm_optimization_notes.md` for bottleneck diagnoses and apply approved `CONTEXT.md` refinements to the target ICM workspace.

## Human Gate (Final Sign-Off)
- [ ] User selects preferred harness/model configuration for the target ICM pipeline.
- [ ] User approves which `CONTEXT.md` optimizations (if any) to apply back to the target ICM workspace.
