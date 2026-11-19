# Harness Telemetry Reference Matrix

Reference for **local Arize Phoenix (`http://localhost:6006`)** with **`Arize-ai/coding-harness-tracing`**.

| Harness | Global Config Modified | Project-Level Override Option | Trace & Metric Coverage | Critical Caveats |
| :--- | :--- | :--- | :--- | :--- |
| **Antigravity (IDE & CLI)** | `~/.gemini/config/hooks.json` | `.agents/hooks.json` or `PHOENIX_PROJECT_NAME` env | Turn root (`CHAIN`), `LLM: {model}`, `TOOL` spans, `session.id` | **No token counts:** Quota-metered; `llm.token_count.*` attributes are omitted locally. Use Stage 04 shadow-token backfill (`tiktoken` or Gemini `count_tokens()`). |
| **Claude Code (CLI & UI)** | `~/.claude/settings.json` | `.claude/settings.local.json` (`env` block) | Turn spans, per-response `LLM` spans with token counts, `TOOL` spans, subagent subtrees | If installed via Claude plugin marketplace instead of `install.sh`, set `PHOENIX_ENDPOINT` in `settings.json` `env` manually. |
| **OpenAI Codex CLI** | `~/.codex/config.toml` (+ `~/.codex/arize-env.sh`) | `.codex/config.toml` (trusted workspace) | Turn spans (`LLM`), `TOOL` decision/result pairs, prompt/completion tokens | **Mandatory trust step:** Open `codex`, run `/hooks`, and approve every `arize-hook-codex-*` entry or hooks are blocked. |
| **Gemini CLI** *(optional baseline)* | `~/.gemini/settings.json` | `.gemini/settings.json` (`telemetry` block) | Session & turn spans, model & tool calls, exact `gen_ai.usage.*` + cached tokens | Kept separate from Antigravity's `hooks.json`. Useful as an exact-token Gemini benchmark baseline. |

## Diagnostics
- Global Arize harness config: `~/.arize/harness/config.json`
- Hook debug logs: `~/.arize/harness/logs/<harness>.log`
- Verbose tracing launch flag: `ARIZE_VERBOSE=true`
- Status check: `./coding-harness-tracing/install.sh status`
