# Target ICM Telemetry & Eval Manifest

- **Target Workspace Path:** `/path/to/target-icm-repo`
- **Target Project Slug:** `icm-<project-name>`
- **Phoenix Endpoint:** `http://localhost:6006`
- **Phoenix Project Name:** `icm-<project-name>`

## Harnesses Under Comparison
- [ ] Antigravity (IDE / CLI)
- [ ] Claude Code (CLI / UI)
- [ ] OpenAI Codex CLI

## Target ICM Stages Observed
| Stage Folder | Expected Output Artifact(s) | Deterministic Check | LLM Judge Criterion |
| :--- | :--- | :--- | :--- |
| `01_.../` | `outputs/...` | File exists & non-empty | Relevance / completeness |
| `02_.../` | `outputs/...` | Schema / syntax valid | Adherence to `CONTEXT.md` |

## Configuration Mode (Target Repo Changes)
- [ ] **Non-invasive sidecar (`.otel/` + `.claude/settings.local.json` gitignored)**
- [ ] **Tracked project config (`.otel/` + `CLAUDE.md` telemetry note committed)**
