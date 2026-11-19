# Stage 04 — Ingest Traces, Shadow-Token Backfill & Run Evals

## Objective
Pull captured spans for the target Phoenix project from `http://localhost:6006`, backfill **shadow tokens & shadow USD cost** for Antigravity spans, run deterministic + LLM-as-a-judge evaluations, and push annotations back to Phoenix.

## Inputs
- Live spans in local Arize Phoenix (`http://localhost:6006`)
- `../02_target_audit_and_plan/outputs/eval_rubric.yaml`
- `../00_reference/model_pricing.json`

## Outputs
- `outputs/traces_raw.parquet` (plus summary metadata)
- `outputs/eval_results.json` & `outputs/eval_results.csv`
- `outputs/shadow_cost_report.md`

## Required Tools (OSS / Free)
- `uv run` with `arize-phoenix-client`, `arize-phoenix-evals`, `tiktoken`, `pandas`, `pyyaml` (`scripts/ingest_and_eval.py`)
- *(Alt OSS: DeepEval, Promptfoo, Ragas; Alt Paid: Arize AX Managed Evals, Braintrust)*

## Steps
1. Sync dependencies once: `uv sync`
2. Export spans, backfill Antigravity shadow tokens/cost, and run deterministic checks:
   `uv run python 04_ingest_and_eval/scripts/ingest_and_eval.py --project career-catalyst-icm`
3. *(Optional)* Run LLM-as-a-judge evals too (requires provider key or local Ollama):
   `uv run python 04_ingest_and_eval/scripts/ingest_and_eval.py --project career-catalyst-icm --run-llm-eval --judge-provider google --judge-model gemini-2.5-flash`
4. Review `outputs/shadow_cost_report.md` and `outputs/eval_results.json`.

## Human Gate (Required Before Stage 05)
- [ ] User audits low-scoring traces and judge explanations for false positives.
- [ ] User confirms shadow-cost pricing assumptions in `outputs/shadow_cost_report.md`.
