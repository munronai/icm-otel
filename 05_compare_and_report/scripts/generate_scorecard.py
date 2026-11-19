#!/usr/bin/env python3
"""Stage 05: Aggregate Stage 04 trace evals into cross-harness scorecard & ICM notes."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_EVAL_JSON = ROOT_DIR / "04_ingest_and_eval" / "outputs" / "eval_results.json"
DEFAULT_APPLIED_MD = ROOT_DIR / "03_apply_otel_config" / "outputs" / "applied_changes.md"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"


def _aggregate_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute summary statistics for a group of traces."""
    n = len(rows)
    passed = sum(1 for r in rows if r.get("overall_deterministic") == "PASS")
    durations = [float(r.get("duration_sec", 0.0)) for r in rows]
    llm_counts = [int(r.get("llm_spans", 0)) for r in rows]
    tool_counts = [int(r.get("tool_spans", 0)) for r in rows]
    tool_errors = sum(int(r.get("tool_errors", 0)) for r in rows)
    total_tokens = sum(int(r.get("total_tokens", 0)) for r in rows)
    total_cost = sum(float(r.get("estimated_cost_usd", 0.0)) for r in rows)
    modes = sorted({str(r.get("token_mode", "unknown")) for r in rows})

    return {
        "traces": n,
        "passed": passed,
        "pass_rate_pct": round((passed / n) * 100.0, 1) if n else 0.0,
        "avg_llm": round(sum(llm_counts) / n, 1) if n else 0.0,
        "avg_tools": round(sum(tool_counts) / n, 1) if n else 0.0,
        "tool_errors": tool_errors,
        "median_dur_sec": round(statistics.median(durations), 2) if durations else 0.0,
        "avg_tokens": round(total_tokens / n, 0) if n else 0,
        "total_cost_usd": round(total_cost, 6),
        "cost_per_pass_usd": round(total_cost / passed, 6) if passed else None,
        "token_modes": "/".join(modes),
    }


def build_scorecard(payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Build cross-harness & per-model scorecard Markdown and computed stats."""
    traces = payload.get("traces", [])
    active_traces = [t for t in traces if t.get("llm_spans", 0) > 0 or t.get("tool_spans", 0) > 0]
    empty_traces = [t for t in traces if t.get("llm_spans", 0) == 0 and t.get("tool_spans", 0) == 0]

    by_harness: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for t in active_traces:
        by_harness[str(t.get("harness", "unknown"))].append(t)
        by_model[str(t.get("models", "unknown"))].append(t)

    harness_stats = {k: _aggregate_group(v) for k, v in sorted(by_harness.items())}
    model_stats = {k: _aggregate_group(v) for k, v in sorted(by_model.items())}

    failed = [t for t in active_traces if t.get("overall_deterministic") != "PASS"]
    top_tools = sorted(active_traces, key=lambda r: int(r.get("tool_spans", 0)), reverse=True)[:5]
    top_cost = sorted(active_traces, key=lambda r: float(r.get("estimated_cost_usd", 0.0)), reverse=True)[:5]

    projects = ", ".join(f"`{p}`" for p in payload.get("project_names", [])) or "`unknown`"
    lines = [
        "# Stage 05 Cross-Harness Scorecard",
        "",
        f"- **Generated (UTC):** {datetime.now(timezone.utc).isoformat()}",
        f"- **Phoenix Project(s):** {projects}",
        f"- **Total Traces:** {len(traces)} ({len(active_traces)} active LLM/Tool traces, {len(empty_traces)} metadata-only/empty traces)",
        "",
        "## 1. Comparison by Harness (Active Traces)",
    ]
    if not harness_stats:
        lines.append("_No active traces to compare._")
    else:
        lines.extend([
            "| Harness | Traces | Det. Pass Rate | Avg LLM / Tool (Err) | Median Latency | Avg Tokens (Mode) | Total Cost | Cost / Passed Task |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ])
        for h, st in harness_stats.items():
            cpp = f"${st['cost_per_pass_usd']:.6f}" if st["cost_per_pass_usd"] is not None else "N/A"
            lines.append(
                f"| `{h}` | {st['traces']} | {st['passed']}/{st['traces']} ({st['pass_rate_pct']}%) | "
                f"{st['avg_llm']} / {st['avg_tools']} ({st['tool_errors']}) | {st['median_dur_sec']}s | "
                f"{int(st['avg_tokens'])} ({st['token_modes']}) | ${st['total_cost_usd']:.6f} | {cpp} |"
            )

    lines.extend(["", "## 2. Comparison by Model (Active Traces)"])
    if not model_stats:
        lines.append("_No model records available._")
    else:
        lines.extend([
            "| Model | Traces | Det. Pass Rate | Avg LLM / Tool | Avg Tokens | Total Cost |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ])
        for m, st in model_stats.items():
            lines.append(
                f"| `{m}` | {st['traces']} | {st['passed']}/{st['traces']} ({st['pass_rate_pct']}%) | "
                f"{st['avg_llm']} / {st['avg_tools']} | {int(st['avg_tokens'])} | ${st['total_cost_usd']:.6f} |"
            )

    lines.extend(["", "## 3. Flagged & Outlier Traces"])
    if failed:
        lines.append("### Deterministic Check Failures")
        for r in failed:
            lines.append(
                f"- `{r['trace_id'][:12]}` (`{r['harness']}`, `{r['models']}`): "
                f"{r['llm_spans']} LLM / {r['tool_spans']} tool spans, {r['tool_errors']} tool error(s), "
                f"checks: error={r['det_error_check']}, loop={r['det_loop_check']}"
            )
    else:
        lines.append("- No deterministic failures among active traces.")

    if top_tools:
        lines.extend(["", "### Highest Tool-Turn Traces"])
        for r in top_tools:
            lines.append(
                f"- `{r['trace_id'][:12]}` (`{r['harness']}`, `{r['models']}`): "
                f"{r['tool_spans']} tool spans, {r['llm_spans']} LLM spans, {r['duration_sec']}s, ${r['estimated_cost_usd']:.6f}"
            )

    if top_cost:
        lines.extend(["", "### Highest Estimated-Cost Traces"])
        for r in top_cost:
            lines.append(
                f"- `{r['trace_id'][:12]}` (`{r['harness']}`, `{r['models']}`): "
                f"${r['estimated_cost_usd']:.6f} ({r['total_tokens']} {r['token_mode']} tokens)"
            )

    computed = {
        "active_count": len(active_traces),
        "empty_count": len(empty_traces),
        "harness_stats": harness_stats,
        "failed": failed,
        "top_tools": top_tools,
    }
    return "\n".join(lines) + "\n", computed


def build_optimization_notes(payload: dict[str, Any], computed: dict[str, Any], applied_path: Path) -> str:
    """Generate actionable ICM optimization notes from observed telemetry."""
    projects = payload.get("project_names", [])
    has_career_catalyst = "career-catalyst-icm" in projects
    failed = computed["failed"]
    harness_stats = computed["harness_stats"]

    lines = [
        "# Stage 05 ICM Optimization & Telemetry Notes",
        "",
        f"- **Generated (UTC):** {datetime.now(timezone.utc).isoformat()}",
        f"- **Active Traces Analyzed:** {computed['active_count']} (plus {computed['empty_count']} empty/metadata-only traces)",
        f"- **Stage 03 Target Config Present:** {'Yes' if applied_path.is_file() else 'No'}",
        "",
        "## Key Findings",
    ]

    if not has_career_catalyst:
        lines.append(
            "- **Target Project Coverage Gap:** `career-catalyst-icm` has no traces on Phoenix yet. "
            "Re-run `python3 03_apply_otel_config/scripts/apply_config.py` (now includes `PHOENIX_PROJECT`) "
            "and execute a real stage in `/Users/munron/dev/career-catalyst-icm` via `claude` or `source .otel/phoenix.env && agy`."
        )
    if "claude_code" not in harness_stats or "codex" not in harness_stats:
        missing = [h for h in ("claude_code", "codex") if h not in harness_stats]
        lines.append(
            f"- **Harness Coverage:** No active traces captured yet for: {', '.join(f'`{m}`' for m in missing)}. "
            "Run equivalent ICM stages across them to unlock true cross-harness comparisons."
        )
    if failed:
        for r in failed:
            lines.append(
                f"- **Runaway / High-Turn Loop (`{r['trace_id'][:12]}`):** `{r['harness']}` took {r['tool_spans']} tool calls "
                f"({r['duration_sec']}s). Tighten the stage `CONTEXT.md` (explicit file targets / search bounds) to curb tool loops."
            )
    if computed["empty_count"] > 0:
        lines.append(
            f"- **Empty Traces ({computed['empty_count']}):** Traces with 0 LLM and 0 TOOL spans likely reflect partial/aborted hooks or non-turn telemetry events."
        )
    if any(t.get("models") == "unknown" for t in payload.get("traces", []) if t.get("llm_spans", 0) > 0):
        lines.append(
            "- **Unlabeled Model Names:** Several `antigravity` spans had `model_name = unknown` and fell back to `fallback_default` pricing. "
            "Check hook version or `00_reference/model_pricing.json` if tighter shadow-cost accuracy is needed."
        )

    lines.extend([
        "",
        "## Recommended Next Actions (Human Gate)",
        "- [ ] Decide whether to keep current `max_tool_turns_per_stage` threshold (25) or tighten/relax per ICM stage.",
        "- [ ] Run a complete stage in `/Users/munron/dev/career-catalyst-icm` under `Antigravity` and `Claude Code`, then re-run Stages 04 -> 05 for a target-specific comparison.",
        "- [ ] Optional: Enable `--run-llm-eval` in Stage 04 once you want LLM-as-a-judge quality scores alongside deterministic + cost metrics.",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage 05 cross-harness scorecard generator.")
    parser.add_argument("--input", type=Path, default=DEFAULT_EVAL_JSON, help="Path to Stage 04 eval_results.json.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    if not args.input.is_file():
        raise SystemExit(f"Error: Stage 04 eval_results.json not found at {args.input}")

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    scorecard_md, computed = build_scorecard(payload)
    notes_md = build_optimization_notes(payload, computed, DEFAULT_APPLIED_MD)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    scorecard_path = args.output_dir / "scorecard.md"
    notes_path = args.output_dir / "icm_optimization_notes.md"
    scorecard_path.write_text(scorecard_md, encoding="utf-8")
    notes_path.write_text(notes_md, encoding="utf-8")

    print(f"Wrote {scorecard_path}")
    print(f"Wrote {notes_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
