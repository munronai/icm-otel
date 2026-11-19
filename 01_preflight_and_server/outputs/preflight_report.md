# Stage 01 Preflight Report

- **Generated (UTC):** 2026-11-15T22:42:46.571562+00:00
- **Phoenix Endpoint:** `http://localhost:6006` — **ok**

## 1. Local Binaries
| Binary | Path |
| :--- | :--- |
| `uv` | `/Users/munron/.local/bin/uv` |
| `uvx` | `/Users/munron/.local/bin/uvx` |
| `python3` | `/Users/munron/icm-otel/.venv/bin/python3` |
| `node` | `/Users/munron/.nvm/versions/node/v22.14.0/bin/node` |
| `npx` | `/Users/munron/.nvm/versions/node/v22.14.0/bin/npx` |
| `claude` | `/Users/munron/.local/bin/claude` |
| `codex` | `NOT FOUND` |
| `agy` | `/Users/munron/.local/bin/agy` |
| `gemini` | `/Users/munron/.nvm/versions/node/v22.14.0/bin/gemini` |
| `docker` | `/usr/local/bin/docker` |

## 2. Global Harness Hooks
| Surface | Config File | Status |
| :--- | :--- | :--- |
| `arize_global` | `/Users/munron/.arize/harness/config.json` | **ok** |
| `antigravity` | `/Users/munron/.gemini/config/hooks.json` | **ok** |
| `claude_code` | `/Users/munron/.claude/settings.json` | **ok** |
| `codex` | `/Users/munron/.codex/config.toml` | **missing** |
| `gemini_cli_optional` | `/Users/munron/.gemini/settings.json` | **no_arize_hook_found** |

## 3. Recommended Next Actions
- Wire `codex` hooks: `curl -sSL https://raw.githubusercontent.com/Arize-ai/coding-harness-tracing/main/install.sh | bash -s -- codex`
