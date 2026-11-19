# icm-otel

A reusable **Interpretable Context Methodology (ICM)** toolkit and deterministic CLI app (`./icm-otel`) for wiring **OpenTelemetry (OTel) + local Arize Phoenix (`http://localhost:6006`)** onto **any target ICM workspace**, monitoring traces live, backfilling shadow tokens/cost for quota-metered harnesses, and evaluating runs across **Antigravity (IDE/CLI)**, **Claude Code**, and **OpenAI Codex**.

## Status & How It Works
- **Deterministic CLI App (`./icm-otel`):** Runs directly in your terminal with **zero LLM required**—guides setup, audits any target ICM layout, applies non-invasive `.otel/` config, monitors Phoenix live with failure-recovery menus, runs evals, and generates cross-harness scorecards.
- **Dual-Mode ICM Workspace:** Also retains full ICM Markdown navigation (`AGENTS.md`, `CLAUDE.md`, `CONTEXT.md`, `01_`–`06_`) if you want an AI agent to help analyze scorecards or draft custom rubrics.

## Quickstart (Fresh Setup)

1. **Clone and install Python dependencies** (requires [`uv`](https://docs.astral.sh/uv/); pins Python `3.11–3.13` automatically):
   ```bash
   git clone <your-fork-or-repo-url>
   cd icm-otel
   uv sync
   ```
2. **Start local Arize Phoenix** in a dedicated terminal tab:
   ```bash
   uvx arize-phoenix serve
   ```
3. **Wire global agent hooks** (first time on your machine; see [docs/USER_GUIDE.md](docs/USER_GUIDE.md#1-first-time-setup--installation) for Codex `/hooks` trust and troubleshooting):
   ```bash
   curl -sSL https://raw.githubusercontent.com/Arize-ai/coding-harness-tracing/main/install.sh | bash -s -- antigravity
   curl -sSL https://raw.githubusercontent.com/Arize-ai/coding-harness-tracing/main/install.sh | bash -s -- claude
   curl -sSL https://raw.githubusercontent.com/Arize-ai/coding-harness-tracing/main/install.sh | bash -s -- codex
   ```
4. **Launch `./icm-otel` pointed at any target ICM workspace:**
   ```bash
   ./icm-otel --target /path/to/your-icm-workspace
   ```

## Supported Target ICM Layouts
`icm-otel` works with both **classic root-numbered ICM** workspaces (`01_research/`, `02_draft/`, `outputs/`) and **container-based / non-classic layouts** (`stages/01-intake/`, `pipeline/`, `workflows/`, `phases/`, `output/`, `GEMINI.md` / `AGENTS.md` / `CLAUDE.md`, or Markdown stage files like `stages/01_step.md`). See [Target ICM Directory Layouts & Customization](docs/USER_GUIDE.md#4-supported-icm-directory-structures--customization) to adapt it to custom repo conventions.

## Pipeline Overview

| Stage | Folder | Purpose |
| :--- | :--- | :--- |
| **01** | `01_preflight_and_server/` | Verify local Phoenix (`localhost:6006`) and global harness hooks |
| **02** | `02_target_audit_and_plan/` | Audit a target ICM workspace and draft instrumentation plan + `eval_rubric.yaml` |
| **03** | `03_apply_otel_config/` | Apply non-invasive `.otel/` & `.claude/settings.local.json` config to target |
| **04** | `04_ingest_and_eval/` | Export Phoenix spans, backfill shadow tokens/cost, run deterministic & LLM evals |
| **05** | `05_compare_and_report/` | Generate cross-harness scorecard & ICM optimization notes |
| **06** | `06_extend_eval_rubric/` | *(Optional / Iterative)* Customize project-specific evals & presets (e.g. EU AI Act) |

## Documentation
- **[Comprehensive User Guide](docs/USER_GUIDE.md)** — Fresh machine setup, Mermaid diagrams, target directory layouts & customization, script flags, resuming without Stage 1, extending rubrics, and troubleshooting.
- **[AGENTS.md](AGENTS.md)** & **[CONTEXT.md](CONTEXT.md)** — ICM Layer 0/1 entry points for AI agents (`CLAUDE.md` is symlinked to `AGENTS.md`).
