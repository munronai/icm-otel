# Workspace Router (Layer 1)

## Goal
Configure OpenTelemetry + local Arize Phoenix (`http://localhost:6006`) onto any target ICM workspace so running that pipeline in **Antigravity**, **Claude Code**, or **Codex** captures traces automatically, then evaluate and compare runs on demand.

## Pipeline Stages & Gates

| Stage | Status | Input | Primary Outputs | Human Gate |
| :--- | :--- | :--- | :--- | :--- |
| `01_preflight_and_server/` | **DONE** *(Codex deferred)* | Local env, `00_reference/` | `outputs/preflight_report.md`, `outputs/env_manifest.json` | Phoenix UI loads + Antigravity & Claude Code 1-turn smoke traces verified |
| `02_target_audit_and_plan/` | **DONE** | Target ICM path, `01` report, `_templates/` | `outputs/target_audit.md`, `outputs/instrumentation_plan.md`, `outputs/eval_rubric.yaml` | Target diff plan & eval rubric approved (`career-catalyst-icm`) |
| `03_apply_otel_config/` | **DONE** | `02` plan & rubric, target ICM repo | `outputs/applied_changes.md` + target repo config files | Applied to `/Users/munron/dev/career-catalyst-icm`; Walk Test PASS |
| `04_ingest_and_eval/` | **DONE** | Live Phoenix spans, `02` rubric, `00_reference/model_pricing.json` | `outputs/traces_raw.parquet`, `outputs/eval_results.json`, `outputs/shadow_cost_report.md` | 69 traces / 744 spans ingested; 546 Phoenix annotations pushed |
| `05_compare_and_report/` | **ACTIVE** | `04` evals & shadow cost, `03` changes | `outputs/scorecard.md`, `outputs/icm_optimization_notes.md` | Choose harness/model config and approve `CONTEXT.md` edits for target repo |
| `06_extend_eval_rubric/` | Optional | `02`/`05` rubric, `presets/` | `outputs/eval_rubric.<project>.yaml` | Confirm project-specific bounds & LLM judge criteria |

## How to Run Any Stage (Walk Test Protocol)
1. Open the next incomplete stage folder (`01_` -> `05_`) and read its `CONTEXT.md`.
2. Verify all listed **Inputs** exist from prior stages.
3. Execute the stage instructions / scripts, write outputs to that stage's `outputs/` folder, and update the status table above when its **Human Gate** passes.
