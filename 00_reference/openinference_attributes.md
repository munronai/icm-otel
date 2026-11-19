# OpenInference Attributes Cheat Sheet

Spans exported by `coding-harness-tracing` to local Arize Phoenix follow OpenInference conventions:

- **Span kinds (`openinference.span.kind`):**
  - `CHAIN` — Turn / agent invocation root
  - `LLM` — Model request/response (contains `llm.model_name`, `input.value`, `output.value`)
  - `TOOL` — Tool invocation & output
- **Core span fields used in Stage 04 & 05:**
  - `context.trace_id`, `context.span_id`, `parent_id`
  - `start_time`, `end_time` (wall-clock latency)
  - `attributes.session.id` (groups multi-turn runs)
  - `attributes.llm.model_name`
  - `attributes.llm.token_count.prompt` / `completion` / `total` *(present on Claude Code & Codex; omitted on Antigravity)*
  - `attributes.input.value` / `attributes.output.value` *(used for shadow-token counting and LLM-as-a-judge evals)*
