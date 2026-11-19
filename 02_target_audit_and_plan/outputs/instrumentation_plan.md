# Stage 02 Target Instrumentation Plan (Draft — Awaiting Approval)

- **Target Workspace Path:** `/Users/munron/dev/career-catalyst-icm`
- **Phoenix Endpoint:** `http://localhost:6006`
- **Phoenix Project Name:** `career-catalyst-icm`
- **Instrumentation Mode:** `sidecar`
- **Harnesses Observed:** `antigravity`, `claude_code`

## Proposed Target Files & Edits (Executed in Stage 03 After Approval)
| Target File | Action | Purpose |
| :--- | :--- | :--- |
| `.otel/phoenix.env` | Create | Sets `PHOENIX_ENDPOINT=http://localhost:6006` and `PHOENIX_PROJECT_NAME=career-catalyst-icm` for CLI shells |
| `.otel/eval_rubric.yaml` | Create | Copy of approved Stage 02 eval rubric for this target pipeline |
| `.claude/settings.local.json` | Create / Merge | Project-scoped Claude Code `env` override (`PHOENIX_PROJECT_NAME=career-catalyst-icm`) |
| `.gitignore` | Append (if needed) | Ignore `.otel/` and `.claude/settings.local.json` so instrumentation stays local |

## Target ICM Stages Mapped to Eval
| Stage | Expected Output(s) | Deterministic Check | LLM Judge Focus |
| :--- | :--- | :--- | :--- |
| `stages/01-job-search/` | Job Search Report — `output/job-search-YYYY-MM-DD.md`; Updated History — `output/seen_jobs.json`; Status Card — `../../_tv/screens/01-job-search/002-search-status.md`; Latest Report Card — `../../_tv/screens/01-job-search/004-latest-report.md` | Expected output files exist & non-empty | Stage instruction adherence & groundedness |
| `stages/02-role-prep/` | Role Prep Report — `output/YYYY-MM-DD-[company-slug]-[role-slug].md`; Active Role Card — `../../_tv/screens/02-role-prep/001-active-role.md`; Reality Check Card — `../../_tv/screens/02-role-prep/002-reality-check.md`; Bridge Card — `../../_tv/screens/02-role-prep/003-strategic-bridge.md` | Expected output files exist & non-empty | Stage instruction adherence & groundedness |
| `stages/03-proposal-builder/` | Research Summary — `output/proposals/[proposal-name]/research/discovery_report.md`; One-Pager & PRD — `output/proposals/[proposal-name]/one-pagers/` & `prds/`; Strategy & Tech Spec — `output/proposals/[proposal-name]/strategy/` & `technical-architecture/`; Presentation — `output/proposals/[proposal-name]/presentations/deck.md` | Expected output files exist & non-empty | Stage instruction adherence & groundedness |

## Human Gate Checklist (Stage 02)
- [ ] Confirm `Phoenix Project Name` (`career-catalyst-icm`).
- [ ] Confirm `Instrumentation Mode` (`sidecar`).
- [ ] Confirm proposed target files above and customized `outputs/eval_rubric.yaml`.
