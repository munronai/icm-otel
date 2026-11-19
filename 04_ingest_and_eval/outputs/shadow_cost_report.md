# Stage 04 Shadow Cost & Deterministic Eval Report

- **Generated (UTC):** 2026-11-16T12:33:11.708257+00:00
- **Phoenix Project(s):** `career-catalyst-icm` (`http://localhost:6006`)
- **Total Spans:** 77 | **Total Traces:** 1
- **Deterministic Pass:** 0/1
- **Total Estimated/Shadow Cost:** $0.016037
- **Phoenix Annotations Pushed:** 42

## Trace Summary
| Trace ID | Harness | Model(s) | LLM / Tool (Err) | Tokens (Mode) | Est. Cost (USD) | Det. Check |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `19bc283134fd` | `antigravity` | `Gemini 4 Hydrogen (Medium)` | 21 / 55 (0) | 1616 (shadow) | $0.016037 | **FAIL** |

## Notes
- Shadow tokens (`tiktoken` cl100k_base) provide an upper-bound API cost estimate for Antigravity spans (which omit server-side cache discounts).
