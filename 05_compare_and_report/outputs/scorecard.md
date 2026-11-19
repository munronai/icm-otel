# Stage 05 Cross-Harness Scorecard

- **Generated (UTC):** 2026-11-16T12:39:31.251045+00:00
- **Phoenix Project(s):** `career-catalyst-icm`
- **Total Traces:** 1 (1 active LLM/Tool traces, 0 metadata-only/empty traces)

## 1. Comparison by Harness (Active Traces)
| Harness | Traces | Det. Pass Rate | Avg LLM / Tool (Err) | Median Latency | Avg Tokens (Mode) | Total Cost | Cost / Passed Task |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `antigravity` | 1 | 0/1 (0.0%) | 21.0 / 55.0 (0) | 356.0s | 1616 (shadow) | $0.016037 | N/A |

## 2. Comparison by Model (Active Traces)
| Model | Traces | Det. Pass Rate | Avg LLM / Tool | Avg Tokens | Total Cost |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Gemini 4 Hydrogen (Medium)` | 1 | 0/1 (0.0%) | 21.0 / 55.0 | 1616 | $0.016037 |

## 3. Flagged & Outlier Traces
### Deterministic Check Failures
- `19bc283134fd` (`antigravity`, `Gemini 4 Hydrogen (Medium)`): 21 LLM / 55 tool spans, 0 tool error(s), checks: error=PASS, loop=FAIL

### Highest Tool-Turn Traces
- `19bc283134fd` (`antigravity`, `Gemini 4 Hydrogen (Medium)`): 55 tool spans, 21 LLM spans, 356.0s, $0.016037

### Highest Estimated-Cost Traces
- `19bc283134fd` (`antigravity`, `Gemini 4 Hydrogen (Medium)`): $0.016037 (1616 shadow tokens)
