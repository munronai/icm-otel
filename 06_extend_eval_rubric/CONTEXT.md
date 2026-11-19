# Stage 06 — Extend Project Eval Rubric & Annotations (Optional / Iterative)

## Objective
Iteratively customize deterministic checks, LLM-as-a-judge criteria, and Phoenix span annotations for a **specific target ICM project** (without changing other projects' rubrics).

## Inputs
- `../02_target_audit_and_plan/outputs/eval_rubric.yaml` (or `<target>/.otel/eval_rubric.yaml`)
- Optional domain presets in `presets/` (e.g., `presets/eu_ai_act_rubric.yaml`)
- Optional findings from `../05_compare_and_report/outputs/icm_optimization_notes.md`

## Outputs
- Updated project rubric (saved to `outputs/eval_rubric.<project>.yaml`, synced to `02_.../outputs/eval_rubric.yaml` and `<target>/.otel/eval_rubric.yaml` on approval)

## Required Tools (OSS / Free)
- `scripts/extend_rubric.py` (Python stdlib interactive menu + CLI flags, uses `pyyaml` if available)
- *(Alt OSS: Promptfoo / DeepEval YAML; Alt Paid: Arize AX Rubric / Prompt Playground)*

## Steps
1. Run interactively: `python3 06_extend_eval_rubric/scripts/extend_rubric.py`
   *(Or non-interactively with `--preset eu_ai_act`, `--add-criterion ...`, `--max-tool-turns ...`)*
2. Choose to apply a preset (e.g., EU AI Act risk assessment), tune deterministic thresholds, or add custom LLM judge criteria with explicit `choices`.
3. Sync the updated rubric to the target repo's `.otel/eval_rubric.yaml`, then re-run **Stage 04 -> Stage 05**.

## Human Gate (Iterative)
- [ ] Confirm the added deterministic bounds and judge criteria match the target project's domain requirements.
