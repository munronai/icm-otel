# Stage 03 — Apply OTel & Eval Config to Target ICM Workspace

## Objective
Install the approved per-project OTel and eval configuration onto the target ICM workspace so normal execution in **Antigravity**, **Claude Code**, and **Codex** streams traces to local Phoenix automatically.

## Inputs
- `../02_target_audit_and_plan/outputs/instrumentation_plan.md`
- `../02_target_audit_and_plan/outputs/eval_rubric.yaml`
- `../_templates/target_*`
- Target ICM workspace

## Outputs
- `outputs/applied_changes.md` — Log of every file created or modified in the target workspace + git status/diff summary
- Config files inside target ICM workspace (e.g., `.otel/phoenix.env`, `.otel/eval_rubric.yaml`, `.claude/settings.local.json`, optional `CLAUDE.md` note)

## Required Tools (OSS / Free)
- `scripts/apply_config.py` (Python stdlib, supports `--dry-run`)
- `arize-phoenix-client` or `npx @arizeai/phoenix-cli` for 1-turn verification *(Alt OSS: `otelcol`; Alt Paid: Helicone / Arize AX)*

## Steps
1. Dry-run first: `python3 03_apply_otel_config/scripts/apply_config.py --dry-run`
2. Apply to the approved target ICM workspace: `python3 03_apply_otel_config/scripts/apply_config.py`
3. Inspect `git status` / `git diff` in the target workspace and verify the Walk Test check passes in `outputs/applied_changes.md`.
4. Run a 1-turn verification prompt in the target workspace (for CLI: `source .otel/phoenix.env`, or run `claude` which reads `.claude/settings.local.json`) and confirm the trace appears in `http://localhost:6006`.

## Human Gate (Required Before Stage 04)
- [ ] User inspects `git diff` / new files in the target ICM workspace.
- [ ] Target workspace passes Walk Test and 1-turn verification trace appears under target Phoenix project.
- *After this gate, run your target ICM pipeline naturally in Antigravity, Claude Code, or Codex; return to Stage 04 whenever ready to evaluate.*
