## Telemetry (OTel + Local Arize Phoenix)
- This ICM workspace is instrumented for local Arize Phoenix (`http://localhost:6006`) under project `__PROJECT_NAME__`.
- Config & eval rubric live in `.otel/` (do not modify unless running `icm-otel` Stage 03+).
- When launching from a CLI terminal, ensure `.otel/phoenix.env` is sourced (`source .otel/phoenix.env`) if project-level hook overrides are not active.
