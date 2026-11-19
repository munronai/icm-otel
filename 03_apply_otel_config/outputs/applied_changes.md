# Stage 03 Applied OTel & Eval Configuration

- **Generated (UTC):** 2026-11-16T12:00:39.435405+00:00
- **Dry Run:** No
- **Target Workspace:** `/Users/munron/dev/career-catalyst-icm`
- **Phoenix Project Name:** `career-catalyst-icm`
- **Phoenix Endpoint:** `http://localhost:6006`
- **Mode:** `sidecar`

## 1. File Changes
| Target File | Status |
| :--- | :--- |
| `.otel/phoenix.env` | written |
| `.otel/eval_rubric.yaml` | copied |
| `.claude/settings.local.json` | updated |
| `.gitignore` | unchanged (already ignored) |

## 2. Target Walk Test Check
- **Result:** **PASS**
- **Layer 0 Docs:** {'GEMINI.md': 23}
- **Root `CONTEXT.md`:** Present
- **Discovered Stages:** 3 (missing `CONTEXT.md`: none)

## 3. Target `git status --short`
```text
M .gitignore
 M _tv/responses/01-job-search/004-latest-report.md
 M _tv/screens/00-guide/_layout.json
 M _tv/screens/01-job-search/001-welcome.md
 M _tv/screens/01-job-search/002-search-status.md
 M _tv/screens/01-job-search/004-latest-report.md
 M _tv/screens/01-job-search/_layout.json
 M _tv/screens/02-role-prep/001-active-role.md
 M _tv/screens/02-role-prep/002-reality-check.md
 M _tv/screens/02-role-prep/003-strategic-bridge.md
 M _tv/screens/02-role-prep/004-proposals-selection.md
 M _tv/screens/02-role-prep/005-interview-prep.md
 M _tv/screens/02-role-prep/_layout.json
 M _tv/screens/03-proposal-builder/001-active-proposal.md
 M _tv/screens/03-proposal-builder/002-deliverables.md
 M stages/01-job-search/output/seen_jobs.json
?? _tv/screens/02-role-prep/harmonic_001-active-role.md
?? _tv/screens/02-role-prep/harmonic_002-reality-check.md
?? _tv/screens/02-role-prep/harmonic_003-strategic-bridge.md
?? _tv/screens/02-role-prep/harmonic_004-proposals-selection.md
?? _tv/screens/02-role-prep/harmonic_005-interview-prep.md
?? stages/01-job-search/output/job-search-2026-06-25.md
?? stages/01-job-search/output/job-search-2026-06-26.md
?? stages/01-job-search/output/job-search-2026-06-29.md
?? stages/01-job-search/output/job-search-2026-06-30.md
?? stages/01-job-search/output/job-search-2026-07-01.md
?? stages/01-job-search/output/job-search-2026-07-02.md
?? stages/01-job-search/output/job-search-2026-07-03.md
?? stages/01-job-search/output/job-search-2026-07-06.md
?? stages/01-job-search/output/job-search-2026-07-07.md
?? stages/01-job-search/output/job-search-2026-07-08.md
?? stages/01-job-search/output/job-search-2026-07-09.md
?? stages/01-job-search/output/job-search-2026-07-13.md
?? stages/01-job-search/output/job-search-2026-07-14.md
?? stages/01-job-search/output/job-search-2026-07-15.md
?? stages/01-job-search/output/job-search-2026-07-16.md
?? stages/01-job-search/output/job-search-2026-07-26.md
?? stages/01-job-search/output/job-search-2026-07-27.md
?? stages/01-job-search/output/job-search-2026-07-29.md
?? stages/01-job-search/output/job-search-2026-07-30.md
?? stages/01-job-search/output/job-search-2026-08-04.md
?? stages/01-job-search/output/job-search-2026-08-06.md
?? stages/01-job-search/output/job-search-2026-08-07.md
?? stages/01-job-search/output/job-search-2026-08-10.md
?? stages/01-job-search/output/job-search-2026-08-11-contract.md
?? stages/01-job-search/output/job-search-2026-08-11.md
?? stages/01-job-search/output/job-search-2026-08-13.md
?? stages/01-job-search/output/job-search-2026-08-15.md
?? stages/01-job-search/output/job-search-2026-08-17.md
?? stages/01-job-search/output/job-search-2026-08-25.md
?? stages/01-job-search/output/job-search-2026-09-14.md
?? stages/01-job-search/output/job-search-2026-09-15.md
?? stages/01-job-search/output/job-search-2026-09-22.md
?? stages/01-job-search/output/job-search-2026-09-23.md
?? stages/01-job-search/output/job-search-2026-10-02.md
?? stages/01-job-search/output/job-search-2026-10-03.md
?? stages/01-job-search/output/job-search-2026-10-09.md
?? stages/01-job-search/output/job-search-2026-10-14.md
?? stages/01-job-search/output/job-search-2026-10-28.md
?? stages/01-job-search/output/job-search-2026-10-29.md
?? stages/01-job-search/output/job-search-2026-11-04.md
?? stages/01-job-search/output/job-search-2026-11-05.md
?? stages/01-job-search/output/job-search-2026-11-15.md
?? stages/02-role-prep/output/2026-07-01-cohere-product-manager-integrations.md
?? stages/02-role-prep/output/2026-07-03-genomics-england-senior-product-manager-data-platform.md
?? stages/02-role-prep/output/2026-07-13-numan-lead-technical-pm.md
?? stages/02-role-prep/output/2026-07-13-veed-technical-pm-api-office.md
?? stages/02-role-prep/output/2026-07-27-collinson-senior-product-manager-api.md
?? stages/02-role-prep/output/2026-07-27-genomics-england-star-examples.md
?? stages/02-role-prep/output/2026-07-27-genomics-england-technical-concepts-deep-dive.md
?? stages/02-role-prep/output/2026-07-30-hopper-senior-product-manager-flight-connectivity.md
?? stages/02-role-prep/output/2026-07-30-lloyds-banking-group-solution-architect-api-lab.md
?? stages/02-role-prep/output/2026-07-30-roompricegenie-group-product-manager-integrations.md
?? stages/02-role-prep/output/2026-08-06-gwi-technical-product-manager-data-platform.md
?? stages/02-role-prep/output/2026-08-06-mercor-platform-product-manager-model-gateway.md
?? stages/02-role-prep/output/2026-08-10-apexx-global-senior-product-manager-self-service-onboarding.md
?? stages/02-role-prep/output/2026-08-11-bondsmith-product-manager.md
?? stages/02-role-prep/output/2026-08-13-flagstone-senior-product-manager.md
?? stages/02-role-prep/output/2026-08-15-swap-senior-product-manager.md
?? stages/02-role-prep/output/2026-08-17-1st-formations-senior-product-manager.md
?? stages/02-role-prep/output/2026-08-28-wise-senior-product-manager-api-tooling.md
?? stages/02-role-prep/output/2026-09-15-xapien-technical-product-manager.md
?? stages/02-role-prep/output/2026-10-04-artificial-labs-senior-product-manager.md
?? stages/02-role-prep/output/2026-10-05-harmonic-security-senior-product-manager.md
?? stages/02-role-prep/output/2026-10-13-plentific-senior-product-manager.md
?? stages/02-role-prep/references/
?? stages/03-proposal-builder/output/proposals/partner-api-prebooking-engine/
```

## 4. 1-Turn Verification Instructions
- **Claude Code:** Run `claude` inside `/Users/munron/dev/career-catalyst-icm` (reads `.claude/settings.local.json` automatically -> project `career-catalyst-icm`).
- **Antigravity CLI / Terminal:** Run `source .otel/phoenix.env` inside `/Users/munron/dev/career-catalyst-icm` before launching CLI tools.
- **Antigravity IDE:** Global `~/.gemini/config/hooks.json` captures spans automatically under your default Arize project unless `.otel/phoenix.env` is inherited.
- Confirm the 1-turn verification trace appears at `http://localhost:6006`.
