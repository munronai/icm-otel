# Stage 02 — Target ICM Audit & Telemetry/Eval Plan

## Objective
Point `icm-otel` at an existing target ICM workspace, audit its structure and stages, and design the non-invasive OTel project configuration + evaluation rubric **without modifying the target repo yet**.

## Inputs
- Target ICM workspace path (provided by user)
- `../01_preflight_and_server/outputs/preflight_report.md`
- `../_templates/run_manifest.md`
- `../_templates/eval_rubric.yaml`

## Outputs
- `outputs/target_audit.md` — Inventory of target ICM `CLAUDE.md`/`AGENTS.md`, `CONTEXT.md`, and numbered stages
- `outputs/instrumentation_plan.md` — Exact files/diffs proposed for the target repo, Phoenix `project_name`, and harness override strategy
- `outputs/eval_rubric.yaml` — Customized deterministic checks + LLM-as-a-judge prompts mapped to the target's stages

## Required Tools (OSS / Free)
- `scripts/audit_target.py` (Python stdlib) + Agent Markdown/YAML refinement
- *(Alt OSS: `icm-architect` Restructure/Audit skill, Promptfoo YAML; Alt Paid: Arize AX / LangSmith UI)*

## Steps
1. Run `python3 02_target_audit_and_plan/scripts/audit_target.py --target /path/to/target-icm-repo` (optionally pass `--project-name icm-<slug>` and `--mode sidecar|tracked`).
2. Review the generated `outputs/target_audit.md` and refine `outputs/instrumentation_plan.md` / `outputs/eval_rubric.yaml` for any stage-specific artifact checks.
3. Confirm the target repo's Phoenix `project_name` and whether `.otel/` + `.claude/settings.local.json` should stay gitignored (`sidecar`) or tracked (`tracked`).

## Human Gate ("Voice & Storyboard" — Required Before Stage 03)
- [ ] User approves `outputs/instrumentation_plan.md` (Phoenix project name, exact files to create/edit in target repo).
- [ ] User approves `outputs/eval_rubric.yaml` (deterministic bounds, judge model, and scoring prompts).
