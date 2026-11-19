# Stage 02 Target ICM Audit

- **Generated (UTC):** 2026-11-16T12:00:03.841096+00:00
- **Target Path:** `/Users/munron/dev/career-catalyst-icm`
- **Git Repo:** Yes

## 1. Root ICM & Orientation Files
| File | Present | Symlink | Line Count |
| :--- | :--- | :--- | :--- |
| `AGENTS.md` | No | No | 0 |
| `CLAUDE.md` | No | No | 0 |
| `GEMINI.md` | Yes | No | 23 |
| `CONTEXT.md` | Yes | No | 24 |
| `README.md` | Yes | No | 120 |
| `.gitignore` | Yes | No | 7 |

## 2. Existing Harness / Telemetry Directories
| Directory | Contents |
| :--- | :--- |
| `.claude/` | `settings.local.json` |
| `.codex/` | _absent / empty_ |
| `.gemini/` | _absent / empty_ |
| `.agents/` | _absent / empty_ |
| `.otel/` | `eval_rubric.yaml`, `phoenix.env` |

## 3. Discovered Stages
| Stage | Type | Context / Spec File | Declared Outputs | Existing `outputs/` |
| :--- | :--- | :--- | :--- | :--- |
| `stages/01-job-search/` | dir | `CONTEXT.md` | Job Search Report — `output/job-search-YYYY-MM-DD.md`; Updated History — `output/seen_jobs.json`; Status Card — `../../_tv/screens/01-job-search/002-search-status.md`; Latest Report Card — `../../_tv/screens/01-job-search/004-latest-report.md` | `output/job-search-2026-06-20.md`, `output/job-search-2026-06-22.md`, `output/job-search-2026-06-23.md`, `output/job-search-2026-06-24.md`, `output/job-search-2026-06-25.md`, `output/job-search-2026-06-26.md`, `output/job-search-2026-06-29.md`, `output/job-search-2026-06-30.md`, `output/job-search-2026-07-01.md`, `output/job-search-2026-07-02.md`, `output/job-search-2026-07-03.md`, `output/job-search-2026-07-06.md`, `output/job-search-2026-07-07.md`, `output/job-search-2026-07-08.md`, `output/job-search-2026-07-09.md`, `output/job-search-2026-07-13.md`, `output/job-search-2026-07-14.md`, `output/job-search-2026-07-15.md`, `output/job-search-2026-07-16.md`, `output/job-search-2026-07-26.md`, `output/job-search-2026-07-27.md`, `output/job-search-2026-07-29.md`, `output/job-search-2026-07-30.md`, `output/job-search-2026-08-04.md`, `output/job-search-2026-08-06.md`, `output/job-search-2026-08-07.md`, `output/job-search-2026-08-10.md`, `output/job-search-2026-08-11-contract.md`, `output/job-search-2026-08-11.md`, `output/job-search-2026-08-13.md`, `output/job-search-2026-08-15.md`, `output/job-search-2026-08-17.md`, `output/job-search-2026-08-25.md`, `output/job-search-2026-09-14.md`, `output/job-search-2026-09-15.md`, `output/job-search-2026-09-22.md`, `output/job-search-2026-09-23.md`, `output/job-search-2026-10-02.md`, `output/job-search-2026-10-03.md`, `output/job-search-2026-10-09.md`, `output/job-search-2026-10-14.md`, `output/job-search-2026-10-28.md`, `output/job-search-2026-10-29.md`, `output/job-search-2026-11-04.md`, `output/job-search-2026-11-05.md`, `output/job-search-2026-11-15.md`, `output/seen_jobs.json` |
| `stages/02-role-prep/` | dir | `CONTEXT.md` | Role Prep Report — `output/YYYY-MM-DD-[company-slug]-[role-slug].md`; Active Role Card — `../../_tv/screens/02-role-prep/001-active-role.md`; Reality Check Card — `../../_tv/screens/02-role-prep/002-reality-check.md`; Bridge Card — `../../_tv/screens/02-role-prep/003-strategic-bridge.md` | `output/2026-06-20-cint-senior-pm-supply-api.md`, `output/2026-06-23-cohere-product-manager-integrations.md`, `output/2026-06-23-experian-senior-platform-pm-crosscore.md`, `output/2026-06-24-exactera-principal-pm-agentic-platform.md`, `output/2026-07-01-cohere-product-manager-integrations.md`, `output/2026-07-03-genomics-england-senior-product-manager-data-platform.md`, `output/2026-07-13-numan-lead-technical-pm.md`, `output/2026-07-13-veed-technical-pm-api-office.md`, `output/2026-07-27-collinson-senior-product-manager-api.md`, `output/2026-07-27-genomics-england-star-examples.md`, `output/2026-07-27-genomics-england-technical-concepts-deep-dive.md`, `output/2026-07-30-hopper-senior-product-manager-flight-connectivity.md`, `output/2026-07-30-lloyds-banking-group-solution-architect-api-lab.md`, `output/2026-07-30-roompricegenie-group-product-manager-integrations.md`, `output/2026-08-06-gwi-technical-product-manager-data-platform.md`, `output/2026-08-06-mercor-platform-product-manager-model-gateway.md`, `output/2026-08-10-apexx-global-senior-product-manager-self-service-onboarding.md`, `output/2026-08-11-bondsmith-product-manager.md`, `output/2026-08-13-flagstone-senior-product-manager.md`, `output/2026-08-15-swap-senior-product-manager.md`, `output/2026-08-17-1st-formations-senior-product-manager.md`, `output/2026-08-28-wise-senior-product-manager-api-tooling.md`, `output/2026-09-15-xapien-technical-product-manager.md`, `output/2026-10-04-artificial-labs-senior-product-manager.md`, `output/2026-10-05-harmonic-security-senior-product-manager.md`, `output/2026-10-13-plentific-senior-product-manager.md` |
| `stages/03-proposal-builder/` | dir | `CONTEXT.md` | Research Summary — `output/proposals/[proposal-name]/research/discovery_report.md`; One-Pager & PRD — `output/proposals/[proposal-name]/one-pagers/` & `prds/`; Strategy & Tech Spec — `output/proposals/[proposal-name]/strategy/` & `technical-architecture/`; Presentation — `output/proposals/[proposal-name]/presentations/deck.md` | _none_ |

## 4. Target Directory Preview (Depth <= 2)
```text
_config/
  profile.md
  search-config.md
_tv/
  responses/
  screens/
archive/
  job-search/
  proposal-builder/
  role-prep/
public/
  app.js
  index.html
  styles.css
  tailwind-styles.css
scripts/
  build_proposals.py
  generate_card.py
  setup_screens.py
skill/
  SKILL.md
src/
  app.js
  index.html
  styles.css
stages/
  01-job-search/
  02-role-prep/
  03-proposal-builder/
  .DS_Store
.DS_Store
.gitignore
CONTEXT.md
GEMINI.md
LICENSE
package-lock.json
package.json
README.md
research.md
server.js
test.html
```

## 5. Walk Test & Readiness Notes
- **Note:** Uses `GEMINI.md` at root (add `CLAUDE.md` / `AGENTS.md` symlink or note if running Claude Code / Codex here).
- All discovered stages have a context/spec file.
