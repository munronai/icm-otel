# icm-otel — Agent Orientation (Layer 0)

You are in **`icm-otel`**, an Interpretable Context Methodology (ICM) workspace that configures **OpenTelemetry (OTel) + local Arize Phoenix (`http://localhost:6006`)** on target ICM pipelines and evaluates traces across **Antigravity (IDE/CLI)**, **Claude Code**, and **Codex**.

## Rules
1. **Read `CONTEXT.md` next** to find the active stage and workspace state.
2. **Load only the active stage's `CONTEXT.md`** (`01_`–`05_`) and its listed inputs; never pre-load unrelated stage outputs.
3. **Never cross a Human Gate** without explicit user confirmation.
4. **Target repos are external:** When configuring another ICM workspace (Stages `02`–`03`), propose exact diffs in `outputs/` and wait for approval before writing outside this repo.
5. **Prefer local OSS/free defaults:** Local Phoenix (`http://localhost:6006`), `uv`, `arize-phoenix-client`, `arize-phoenix-evals`, `tiktoken`.

## Directory Map
- `icm-otel` (`icm_otel_cli.py`) — Interactive deterministic CLI & live Phoenix monitor
- `README.md` & `docs/USER_GUIDE.md` — Quickstart, diagrams, flags, troubleshooting, rubric extension
- `CONTEXT.md` — Layer 1 router, stage status, and Walk Test checklist
- `00_reference/` — Harness caveats, OpenInference attributes, model pricing table
- `_templates/` — Reusable target-repo OTel configs and eval rubrics
- `01_preflight_and_server/` — Local Phoenix + global harness hook verification
- `02_target_audit_and_plan/` — Target ICM audit, project tagging, eval rubric design
- `03_apply_otel_config/` — Apply approved OTel/eval config to target ICM workspace
- `04_ingest_and_eval/` — Export Phoenix spans, backfill shadow tokens, run evals
- `05_compare_and_report/` — Cross-harness scorecard & ICM optimization notes
- `06_extend_eval_rubric/` — Optional/iterative project-specific rubric & preset extender
