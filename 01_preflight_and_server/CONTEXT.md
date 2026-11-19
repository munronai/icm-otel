# Stage 01 — Preflight, Local Phoenix Server & Global Harness Hooks

## Objective
Ensure local **Arize Phoenix (`http://localhost:6006`)** is running and **`Arize-ai/coding-harness-tracing`** hooks are wired and trusted for **Antigravity (IDE & CLI)**, **Claude Code**, and **Codex CLI**.

## Inputs
- Local machine environment (`~/.gemini/`, `~/.claude/`, `~/.codex/`, `~/.arize/`)
- `../00_reference/harness_matrix.md`

## Outputs
- `outputs/preflight_report.md`
- `outputs/env_manifest.json`

## Required Tools (OSS / Free)
- `uv` / `uvx arize-phoenix serve` *(Alt OSS: Docker `arizephoenix/phoenix`, Jaeger; Alt Paid: Phoenix Cloud)*
- `Arize-ai/coding-harness-tracing` installer (`antigravity`, `claude`, `codex`)
- `scripts/preflight_check.py` (Python stdlib)

## Steps
1. Ensure `uv` is installed (`brew install uv`) and start Phoenix in a dedicated terminal:
   `uvx arize-phoenix serve`
2. Wire global hooks (user runs locally outside workspace sandbox):
   - Antigravity: `curl -sSL https://raw.githubusercontent.com/Arize-ai/coding-harness-tracing/main/install.sh | bash -s -- antigravity`
   - Claude Code: `curl -sSL https://raw.githubusercontent.com/Arize-ai/coding-harness-tracing/main/install.sh | bash -s -- claude`
   - Codex CLI: `curl -sSL https://raw.githubusercontent.com/Arize-ai/coding-harness-tracing/main/install.sh | bash -s -- codex`
3. **Codex trust step:** Run `codex`, execute `/hooks`, and approve every `arize-hook-codex-*` entry.
4. Run `python3 01_preflight_and_server/scripts/preflight_check.py` locally to generate `outputs/preflight_report.md` and `outputs/env_manifest.json`.
5. Run a 1-turn smoke prompt in each harness and verify spans appear in `http://localhost:6006`.

## Human Gate (Required Before Stage 02)
- [ ] `http://localhost:6006` UI loads.
- [ ] `outputs/preflight_report.md` shows all 3 harnesses configured.
- [ ] Codex `/hooks` trust approved.
- [ ] 1-turn smoke-test spans confirmed in Phoenix for Antigravity, Claude Code, and Codex.
