#!/usr/bin/env python3
"""Stage 04: Export Phoenix spans, backfill shadow tokens/cost, and run evals."""

from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_RUBRIC = ROOT_DIR / "02_target_audit_and_plan" / "outputs" / "eval_rubric.yaml"
DEFAULT_PRICING = ROOT_DIR / "00_reference" / "model_pricing.json"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"


def load_yaml_or_defaults(path: Path) -> dict[str, Any]:
    """Load eval_rubric.yaml using PyYAML when available."""
    if not path.is_file():
        return {}
    try:
        import yaml  # type: ignore

        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except ImportError:
        return {}


def load_pricing(path: Path) -> dict[str, Any]:
    """Load model pricing reference table."""
    if not path.is_file():
        return {"models": {}, "fallback_default": {"input": 2.0, "output": 10.0}}
    return json.loads(path.read_text(encoding="utf-8"))


def count_tokens_text(text: Any) -> tuple[int, str]:
    """Count tokens with tiktoken (cl100k_base), falling back to char/4 heuristic."""
    if text is None:
        return 0, "empty"
    s = text if isinstance(text, str) else json.dumps(text, default=str)
    if not s:
        return 0, "empty"
    try:
        import tiktoken  # type: ignore

        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(s)), "shadow_tiktoken"
    except Exception:
        return max(1, len(s) // 4), "shadow_char4_fallback"


def lookup_model_price(model_name: str | None, pricing: dict[str, Any]) -> dict[str, float]:
    """Match a model name against model_pricing.json (exact or prefix match)."""
    models = pricing.get("models", {})
    fallback = pricing.get("fallback_default", {"input": 2.0, "output": 10.0})
    if not model_name:
        return fallback
    norm = model_name.lower().strip()
    if norm in models:
        return models[norm]
    for key, val in models.items():
        if key in norm or norm in key:
            return val
    return fallback


def _get_col(row: dict[str, Any], *candidates: str, default: Any = None) -> Any:
    """Fetch first non-None value across possible Phoenix flat/nested column names."""
    for key in candidates:
        if key in row and row[key] is not None:
            val = row[key]
            # Handle float('nan') without requiring pandas/numpy
            if val == val:  # noqa: PLR0124
                return val
    return default


def infer_harness(row: dict[str, Any]) -> str:
    """Infer agent harness from span metadata, project name, model name, or token presence."""
    explicit = _get_col(row, "attributes.harness", "attributes.agent.harness", "harness")
    if explicit:
        return str(explicit).lower()

    blob = " ".join(
        str(_get_col(row, k, default="") or "")
        for k in ("phoenix_project", "name", "attributes.llm.model_name", "attributes.metadata", "attributes.session.id")
    ).lower()
    if "antigravity" in blob or "hydrogen" in blob:
        return "antigravity"
    if any(t in blob for t in ("run_command", "edit_file", "write_file", "read_file")):
        return "antigravity"
    if "claude" in blob:
        return "claude_code"
    if "codex" in blob or "gpt-" in blob or blob.startswith("o3") or blob.startswith("o4"):
        return "codex"
    if "gemini" in blob:
        has_native_tok = _get_col(row, "attributes.llm.token_count.prompt") is not None
        return "gemini_cli" if has_native_tok else "antigravity"
    return "unknown"


def enrich_and_evaluate_records(
    records: list[dict[str, Any]],
    rubric: dict[str, Any],
    pricing: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Backfill shadow tokens/cost per span and compute deterministic trace evals."""
    max_err_rate = 0.15
    max_tool_turns = 25
    for chk in rubric.get("deterministic_checks", []):
        if chk.get("name") == "no_unhandled_tool_errors":
            max_err_rate = float(chk.get("max_error_rate", max_err_rate))
        elif chk.get("name") == "max_tool_turns_per_stage":
            max_tool_turns = int(chk.get("threshold", max_tool_turns))

    enriched_spans: list[dict[str, Any]] = []
    traces: dict[str, dict[str, Any]] = {}

    for row in records:
        trace_id = str(_get_col(row, "context.trace_id", "trace_id", default="unknown_trace"))
        span_id = str(_get_col(row, "context.span_id", "span_id", default="unknown_span"))
        span_kind = str(_get_col(row, "attributes.openinference.span.kind", "span_kind", default="UNKNOWN")).upper()
        model_name = _get_col(row, "attributes.llm.model_name", "llm.model_name", "model_name")
        harness = infer_harness(row)

        prompt_tok = _get_col(row, "attributes.llm.token_count.prompt", "llm.token_count.prompt")
        comp_tok = _get_col(row, "attributes.llm.token_count.completion", "llm.token_count.completion")
        token_source = "native"

        if span_kind == "LLM" and (prompt_tok is None or comp_tok is None):
            in_tok, in_src = count_tokens_text(_get_col(row, "attributes.input.value", "input.value"))
            out_tok, out_src = count_tokens_text(_get_col(row, "attributes.output.value", "output.value"))
            prompt_tok = int(prompt_tok) if prompt_tok is not None else in_tok
            comp_tok = int(comp_tok) if comp_tok is not None else out_tok
            token_source = in_src if in_src != "empty" else out_src
        else:
            prompt_tok = int(prompt_tok or 0)
            comp_tok = int(comp_tok or 0)

        total_tok = prompt_tok + comp_tok
        price = lookup_model_price(str(model_name) if model_name else None, pricing)
        cost_usd = (prompt_tok * price["input"] + comp_tok * price["output"]) / 1_000_000.0

        status_code = str(_get_col(row, "status_code", "status", default="OK")).upper()
        is_error = status_code in ("ERROR", "FAILED")

        start_raw = _get_col(row, "start_time")
        end_raw = _get_col(row, "end_time")
        latency_sec = _compute_latency_sec(start_raw, end_raw)

        enriched = {
            "trace_id": trace_id,
            "span_id": span_id,
            "span_kind": span_kind,
            "name": _get_col(row, "name", default=""),
            "harness": harness,
            "model_name": model_name or "unknown",
            "prompt_tokens": prompt_tok,
            "completion_tokens": comp_tok,
            "total_tokens": total_tok,
            "token_source": token_source,
            "estimated_cost_usd": round(cost_usd, 6),
            "latency_sec": round(latency_sec, 3) if latency_sec is not None else None,
            "is_error": is_error,
        }
        enriched_spans.append(enriched)

        tr = traces.setdefault(
            trace_id,
            {
                "trace_id": trace_id,
                "harness": harness if harness != "unknown" else None,
                "models": set(),
                "llm_spans": 0,
                "tool_spans": 0,
                "tool_errors": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "estimated_cost_usd": 0.0,
                "has_shadow_tokens": False,
                "max_latency_sec": 0.0,
            },
        )
        if tr["harness"] is None and harness != "unknown":
            tr["harness"] = harness
        if model_name:
            tr["models"].add(str(model_name))
        if span_kind == "LLM":
            tr["llm_spans"] += 1
        elif span_kind == "TOOL":
            tr["tool_spans"] += 1
            if is_error:
                tr["tool_errors"] += 1
        tr["prompt_tokens"] += prompt_tok
        tr["completion_tokens"] += comp_tok
        tr["total_tokens"] += total_tok
        tr["estimated_cost_usd"] += cost_usd
        if token_source.startswith("shadow"):
            tr["has_shadow_tokens"] = True
        if latency_sec is not None:
            tr["max_latency_sec"] = max(tr["max_latency_sec"], latency_sec)

    eval_rows: list[dict[str, Any]] = []
    for trace_id, tr in traces.items():
        tool_spans = tr["tool_spans"]
        err_rate = (tr["tool_errors"] / tool_spans) if tool_spans > 0 else 0.0
        err_pass = err_rate <= max_err_rate
        loop_pass = tool_spans <= max_tool_turns
        eval_rows.append(
            {
                "trace_id": trace_id,
                "harness": tr["harness"] or "unknown",
                "models": ", ".join(sorted(tr["models"])) or "unknown",
                "llm_spans": tr["llm_spans"],
                "tool_spans": tool_spans,
                "tool_errors": tr["tool_errors"],
                "tool_error_rate": round(err_rate, 4),
                "prompt_tokens": tr["prompt_tokens"],
                "completion_tokens": tr["completion_tokens"],
                "total_tokens": tr["total_tokens"],
                "token_mode": "shadow" if tr["has_shadow_tokens"] else "native",
                "estimated_cost_usd": round(tr["estimated_cost_usd"], 6),
                "duration_sec": round(tr["max_latency_sec"], 3),
                "det_error_check": "PASS" if err_pass else "FAIL",
                "det_loop_check": "PASS" if loop_pass else "FAIL",
                "overall_deterministic": "PASS" if (err_pass and loop_pass) else "FAIL",
            }
        )

    summary = {
        "total_spans": len(enriched_spans),
        "total_traces": len(eval_rows),
        "deterministic_pass_count": sum(1 for r in eval_rows if r["overall_deterministic"] == "PASS"),
        "total_estimated_cost_usd": round(sum(r["estimated_cost_usd"] for r in eval_rows), 6),
    }
    return enriched_spans, eval_rows, summary


def _compute_latency_sec(start_raw: Any, end_raw: Any) -> float | None:
    """Compute span duration in seconds from datetime or ISO string values."""
    if not start_raw or not end_raw:
        return None
    try:
        if hasattr(start_raw, "timestamp") and hasattr(end_raw, "timestamp"):
            return max(0.0, float(end_raw.timestamp() - start_raw.timestamp()))
        s = datetime.fromisoformat(str(start_raw).replace("Z", "+00:00"))
        e = datetime.fromisoformat(str(end_raw).replace("Z", "+00:00"))
        return max(0.0, (e - s).total_seconds())
    except Exception:
        return None


def list_phoenix_projects(endpoint: str) -> list[str]:
    """Return available project names from local Arize Phoenix."""
    try:
        from phoenix.client import Client  # type: ignore

        client = Client(base_url=endpoint)
        projects = list(client.projects.list())
        names: list[str] = []
        for proj in projects:
            if isinstance(proj, dict) and "name" in proj:
                names.append(str(proj["name"]))
            elif hasattr(proj, "name"):
                names.append(str(proj.name))
            else:
                names.append(str(proj))
        return names
    except Exception:
        return []


def _df_to_records(df: Any) -> tuple[Any, list[dict[str, Any]]]:
    """Safely reset DataFrame index without colliding with existing columns like context.span_id."""
    idx_names = [n for n in getattr(df.index, "names", [df.index.name]) if n is not None]
    if any(n in df.columns for n in idx_names):
        clean_df = df.reset_index(drop=True)
    else:
        clean_df = df.reset_index()
    return clean_df, clean_df.to_dict(orient="records")


def fetch_spans_from_phoenix(
    endpoint: str,
    project_names: list[str],
    limit: int,
) -> tuple[Any, list[dict[str, Any]], list[str]]:
    """Pull spans DataFrame across one or more Phoenix projects."""
    import pandas as pd  # type: ignore
    from phoenix.client import Client  # type: ignore

    client = Client(base_url=endpoint)
    frames = []
    errors: list[str] = []
    for proj in project_names:
        try:
            df = client.spans.get_spans_dataframe(project_identifier=proj, limit=limit)
            if df is not None and len(df) > 0:
                df = df.copy()
                df["phoenix_project"] = proj
                frames.append(df)
        except Exception as exc:
            errors.append(f"{proj}: {exc}")

    if not frames:
        return None, [], errors

    combined = pd.concat(frames, axis=0)
    clean_df, records = _df_to_records(combined)
    return clean_df, records, errors


def push_span_annotations(
    endpoint: str,
    enriched_spans: list[dict[str, Any]],
) -> int:
    """Log shadow token & cost annotations back onto Phoenix LLM spans."""
    import pandas as pd  # type: ignore
    from phoenix.client import Client  # type: ignore

    seen_ids: set[str] = set()
    token_rows: list[dict[str, Any]] = []
    cost_rows: list[dict[str, Any]] = []
    for sp in enriched_spans:
        sid = sp.get("span_id")
        if sp["span_kind"] != "LLM" or not sid or sid == "unknown_span" or sid in seen_ids:
            continue
        seen_ids.add(sid)
        token_rows.append(
            {
                "span_id": str(sid),
                "score": float(sp["total_tokens"]),
                "label": str(sp["token_source"] or "shadow"),
            }
        )
        cost_rows.append(
            {
                "span_id": str(sid),
                "score": float(sp["estimated_cost_usd"]),
                "label": str(sp["model_name"] or "unknown"),
            }
        )

    if not token_rows:
        return 0

    client = Client(base_url=endpoint)
    client.spans.log_span_annotations_dataframe(
        dataframe=pd.DataFrame(token_rows),
        annotation_name="estimated_tokens",
        annotator_kind="CODE",
    )
    client.spans.log_span_annotations_dataframe(
        dataframe=pd.DataFrame(cost_rows),
        annotation_name="shadow_cost_usd",
        annotator_kind="CODE",
    )
    return len(token_rows) + len(cost_rows)


def render_shadow_cost_report(
    project_names: list[str],
    endpoint: str,
    eval_rows: list[dict[str, Any]],
    summary: dict[str, Any],
    pushed_annotations: int,
    available_projects: list[str] | None = None,
    fetch_errors: list[str] | None = None,
) -> str:
    """Render Stage 04 shadow cost & deterministic eval summary."""
    proj_label = ", ".join(f"`{p}`" for p in project_names)
    lines = [
        "# Stage 04 Shadow Cost & Deterministic Eval Report",
        "",
        f"- **Generated (UTC):** {datetime.now(timezone.utc).isoformat()}",
        f"- **Phoenix Project(s):** {proj_label} (`{endpoint}`)",
        f"- **Total Spans:** {summary['total_spans']} | **Total Traces:** {summary['total_traces']}",
        f"- **Deterministic Pass:** {summary['deterministic_pass_count']}/{summary['total_traces']}",
        f"- **Total Estimated/Shadow Cost:** ${summary['total_estimated_cost_usd']:.6f}",
        f"- **Phoenix Annotations Pushed:** {pushed_annotations}",
        "",
        "## Trace Summary",
    ]
    if not eval_rows:
        lines.append("_No traces found for the requested project(s)._")
        if available_projects:
            lines.append(
                "- **Projects found on Phoenix:** " + ", ".join(f"`{p}`" for p in available_projects)
            )
            lines.append(
                "- Re-run with `--project <name ...>` or `--all-projects` to ingest spans from those projects."
            )
        if fetch_errors:
            lines.append("- **Fetch warnings:** " + "; ".join(fetch_errors))
    else:
        llm_cols = sorted({k for r in eval_rows for k in r if k.startswith("llm_") and k.endswith("_score")})
        header_extra = "".join(f" {c.removeprefix('llm_').removesuffix('_score')} |" for c in llm_cols)
        sep_extra = " :--- |" * len(llm_cols)
        lines.extend([
            f"| Trace ID | Harness | Model(s) | LLM / Tool (Err) | Tokens (Mode) | Est. Cost (USD) | Det. Check |{header_extra}",
            f"| :--- | :--- | :--- | :--- | :--- | :--- | :--- |{sep_extra}",
        ])
        for r in eval_rows:
            short_id = r["trace_id"][:12]
            counts = f"{r['llm_spans']} / {r['tool_spans']} ({r['tool_errors']})"
            toks = f"{r['total_tokens']} ({r['token_mode']})"
            extra_vals = ""
            for c in llm_cols:
                val = r.get(c)
                if isinstance(val, dict):
                    extra_vals += f" {val.get('label', val)} |"
                else:
                    extra_vals += f" {val} |"
            lines.append(
                f"| `{short_id}` | `{r['harness']}` | `{r['models']}` | {counts} | {toks} | ${r['estimated_cost_usd']:.6f} | **{r['overall_deterministic']}** |{extra_vals}"
            )

    lines.extend([
        "",
        "## Notes",
        "- Shadow tokens (`tiktoken` cl100k_base) provide an upper-bound API cost estimate for Antigravity spans (which omit server-side cache discounts).",
    ])
    return "\n".join(lines) + "\n"


def run_llm_judge_evals(
    records: list[dict[str, Any]],
    eval_rows: list[dict[str, Any]],
    rubric: dict[str, Any],
    provider: str,
    model_name: str,
) -> tuple[list[dict[str, Any]], Any]:
    """Run optional Phoenix LLM-as-a-judge evals on root CHAIN spans (falling back to LLM spans)."""
    import pandas as pd  # type: ignore
    from phoenix.evals import create_classifier, evaluate_dataframe  # type: ignore
    from phoenix.evals.llm import LLM  # type: ignore

    # Collect span_id + representative input/output per trace_id
    trace_io: dict[str, dict[str, str]] = {}
    for row in records:
        tid = str(_get_col(row, "context.trace_id", "trace_id", default="unknown_trace"))
        sid = str(_get_col(row, "context.span_id", "span_id", default=""))
        kind = str(_get_col(row, "attributes.openinference.span.kind", "span_kind", default="")).upper()
        inp = _get_col(row, "attributes.input.value", "input.value", default="")
        out = _get_col(row, "attributes.output.value", "output.value", default="")
        entry = trace_io.setdefault(tid, {"trace_id": tid, "span_id": "", "input": "", "output": ""})
        if kind == "CHAIN" and sid:
            entry["span_id"] = sid
        elif not entry["span_id"] and sid:
            entry["span_id"] = sid
        if inp and (kind == "CHAIN" or not entry["input"]):
            entry["input"] = str(inp)[:6000]
        if out and (kind == "CHAIN" or kind == "LLM" or not entry["output"]):
            entry["output"] = str(out)[:6000]

    valid_io = [v for v in trace_io.values() if v["input"] or v["output"]]
    if not valid_io:
        return eval_rows, None

    criteria = rubric.get("llm_judge_evals", {}).get("criteria", [])
    if not criteria:
        criteria = [
            {
                "name": "stage_instruction_adherence",
                "prompt_template": "Evaluate groundedness and instruction adherence.\nInput: {input}\nOutput: {output}",
            }
        ]

    llm = LLM(provider=provider, model=model_name)
    evaluators = []
    for crit in criteria:
        cname = crit.get("name", "judge_eval")
        choices = crit.get("choices")
        if not isinstance(choices, dict) or not choices:
            choices = {"PASS": 1.0, "FAIL": 0.0} if "efficiency" not in cname else {"EFFICIENT": 1.0, "WASTEFUL": 0.0}
        evaluators.append(
            create_classifier(
                name=cname,
                prompt_template=crit.get("prompt_template", "Input: {input}\nOutput: {output}"),
                llm=llm,
                choices=choices,
            )
        )

    io_df = pd.DataFrame(valid_io)
    judged = evaluate_dataframe(dataframe=io_df, evaluators=evaluators)
    by_trace = judged.set_index("trace_id").to_dict(orient="index")
    for r in eval_rows:
        j = by_trace.get(r["trace_id"], {})
        for k, v in j.items():
            if k not in ("input", "output", "span_id"):
                r[f"llm_{k}"] = v
    return eval_rows, judged


def push_llm_annotations(endpoint: str, judged_df: Any) -> int:
    """Push LLM judge scores back onto Phoenix spans."""
    if judged_df is None or len(judged_df) == 0:
        return 0
    from phoenix.client import Client  # type: ignore
    from phoenix.evals.utils import to_annotation_dataframe  # type: ignore

    ann_df = to_annotation_dataframe(dataframe=judged_df)
    if ann_df is None or len(ann_df) == 0:
        return 0
    client = Client(base_url=endpoint)
    client.spans.log_span_annotations_dataframe(dataframe=ann_df, annotator_kind="LLM")
    return len(ann_df)


def _load_offline_records(input_file: Path) -> list[dict[str, Any]]:
    """Load spans from a JSONL or Parquet file for offline testing/re-eval."""
    if input_file.suffix.lower() == ".jsonl":
        return [
            json.loads(line)
            for line in input_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    import pandas as pd  # type: ignore

    df = pd.read_parquet(input_file)
    _, records = _df_to_records(df)
    return records


def main() -> int:
    rubric = load_yaml_or_defaults(DEFAULT_RUBRIC)
    parser = argparse.ArgumentParser(description="Stage 04 ingest Phoenix traces, backfill shadow cost, run evals.")
    parser.add_argument(
        "--project",
        nargs="+",
        default=[rubric.get("project_name", "career-catalyst-icm")],
        help="One or more Phoenix project names.",
    )
    parser.add_argument("--all-projects", action="store_true", help="Query every project on the Phoenix server.")
    parser.add_argument("--list-projects", action="store_true", help="List available Phoenix projects and exit.")
    parser.add_argument("--endpoint", default=os.environ.get("PHOENIX_ENDPOINT", rubric.get("phoenix_endpoint", "http://localhost:6006")))
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--rubric", type=Path, default=DEFAULT_RUBRIC)
    parser.add_argument("--pricing", type=Path, default=DEFAULT_PRICING)
    parser.add_argument("--input-file", type=Path, default=None, help="Optional offline .jsonl/.parquet instead of querying Phoenix.")
    parser.add_argument("--run-llm-eval", action="store_true", help="Run phoenix.evals LLM-as-a-judge classifiers.")
    parser.add_argument("--judge-provider", default="google", help="Judge provider for phoenix.evals.llm.LLM.")
    parser.add_argument("--judge-model", default=None, help="Judge model name (defaults to rubric or gemini-2.5-flash).")
    parser.add_argument("--no-push", action="store_true", help="Do not push span annotations back to Phoenix.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    if args.list_projects:
        projs = list_phoenix_projects(args.endpoint)
        print("Available Phoenix projects:" if projs else "No projects found (or Phoenix unreachable).")
        for p in projs:
            print(f" - {p}")
        return 0

    rubric = load_yaml_or_defaults(args.rubric) or rubric
    pricing = load_pricing(args.pricing)

    project_names = list(args.project)
    available_projects: list[str] = []
    fetch_errors: list[str] = []
    raw_df = None
    if args.input_file:
        records = _load_offline_records(args.input_file)
    else:
        if args.all_projects:
            available_projects = list_phoenix_projects(args.endpoint)
            project_names = available_projects or project_names
        raw_df, records, fetch_errors = fetch_spans_from_phoenix(args.endpoint, project_names, args.limit)
        if not records and not available_projects:
            available_projects = list_phoenix_projects(args.endpoint)
            if available_projects:
                print("No spans in requested project(s). Available Phoenix projects:", ", ".join(available_projects))

    enriched_spans, eval_rows, summary = enrich_and_evaluate_records(records, rubric, pricing)
    judged_df = None
    if args.run_llm_eval and records:
        judge_model = args.judge_model or rubric.get("llm_judge_evals", {}).get("judge_model", "gemini-2.5-flash")
        eval_rows, judged_df = run_llm_judge_evals(records, eval_rows, rubric, args.judge_provider, judge_model)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    if raw_df is not None and len(records) > 0:
        try:
            raw_df.to_parquet(args.output_dir / "traces_raw.parquet", index=False)
        except Exception:
            (args.output_dir / "traces_raw.jsonl").write_text(
                "\n".join(json.dumps(r, default=str) for r in records) + "\n",
                encoding="utf-8",
            )
    elif records:
        (args.output_dir / "traces_raw.jsonl").write_text(
            "\n".join(json.dumps(r, default=str) for r in records) + "\n",
            encoding="utf-8",
        )

    pushed = 0
    if not args.input_file and not args.no_push and enriched_spans:
        try:
            pushed += push_span_annotations(args.endpoint, enriched_spans)
        except Exception as exc:
            print(f"Warning: failed to push annotations to Phoenix: {exc}")
        if judged_df is not None:
            try:
                pushed += push_llm_annotations(args.endpoint, judged_df)
            except Exception as exc:
                print(f"Warning: failed to push LLM judge annotations to Phoenix: {exc}")

    eval_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_names": project_names,
        "available_projects": available_projects,
        "endpoint": args.endpoint,
        "summary": summary,
        "traces": eval_rows,
        "spans": enriched_spans,
    }
    (args.output_dir / "eval_results.json").write_text(
        json.dumps(eval_payload, indent=2, default=str) + "\n",
        encoding="utf-8",
    )

    csv_path = args.output_dir / "eval_results.csv"
    base_fields = [
        "trace_id", "harness", "models", "llm_spans", "tool_spans", "tool_errors",
        "tool_error_rate", "prompt_tokens", "completion_tokens", "total_tokens",
        "token_mode", "estimated_cost_usd", "duration_sec",
        "det_error_check", "det_loop_check", "overall_deterministic",
    ]
    extra_fields = sorted({k for row in eval_rows for k in row.keys()} - set(base_fields))
    fieldnames = base_fields + extra_fields
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(eval_rows)

    report = render_shadow_cost_report(
        project_names,
        args.endpoint,
        eval_rows,
        summary,
        pushed,
        available_projects=available_projects,
        fetch_errors=fetch_errors,
    )
    (args.output_dir / "shadow_cost_report.md").write_text(report, encoding="utf-8")
    print(f"Wrote Stage 04 outputs to {args.output_dir} ({summary['total_traces']} trace(s), {summary['total_spans']} span(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
