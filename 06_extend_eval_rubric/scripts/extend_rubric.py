#!/usr/bin/env python3
"""Stage 06: Interactive & CLI tool to extend a project's eval_rubric.yaml."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent.parent.parent
STAGE_02_RUBRIC = ROOT_DIR / "02_target_audit_and_plan" / "outputs" / "eval_rubric.yaml"
PRESETS_DIR = Path(__file__).resolve().parent.parent / "presets"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load YAML using PyYAML, with a minimal fallback parser for simple rubrics."""
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text) or {}
    except ImportError as exc:
        raise SystemExit(
            "PyYAML is required for structured rubric editing. Run with `uv run python ...` or `uv sync`."
        ) from exc


def _dump_yaml(data: dict[str, Any]) -> str:
    """Serialize rubric dictionary cleanly to YAML."""
    import yaml  # type: ignore

    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False)


def apply_preset(rubric: dict[str, Any], preset_path: Path) -> dict[str, Any]:
    """Merge deterministic checks and LLM judge criteria from a preset YAML."""
    preset = _load_yaml(preset_path)

    existing_det = {c.get("name"): c for c in rubric.get("deterministic_checks", []) if isinstance(c, dict)}
    for chk in preset.get("deterministic_checks", []):
        if isinstance(chk, dict) and chk.get("name"):
            existing_det[chk["name"]] = chk
    rubric["deterministic_checks"] = list(existing_det.values())

    judge = rubric.setdefault("llm_judge_evals", {"enabled": True, "judge_model": "gemini-2.5-flash", "criteria": []})
    existing_crit = {c.get("name"): c for c in judge.get("criteria", []) if isinstance(c, dict)}
    for crit in preset.get("llm_judge_evals", {}).get("criteria", []):
        if isinstance(crit, dict) and crit.get("name"):
            existing_crit[crit["name"]] = crit
    judge["criteria"] = list(existing_crit.values())
    return rubric


def add_custom_criterion(
    rubric: dict[str, Any],
    name: str,
    prompt_body: str,
    pass_label: str = "PASS",
    fail_label: str = "FAIL",
) -> dict[str, Any]:
    """Add or update a single LLM-as-a-judge criterion."""
    judge = rubric.setdefault("llm_judge_evals", {"enabled": True, "judge_model": "gemini-2.5-flash", "criteria": []})
    criteria = [c for c in judge.get("criteria", []) if c.get("name") != name]
    full_prompt = prompt_body.strip()
    if "{input}" not in full_prompt:
        full_prompt += "\nInput: {input}\nOutput: {output}"
    criteria.append(
        {
            "name": name,
            "choices": {pass_label: 1.0, fail_label: 0.0},
            "prompt_template": full_prompt + "\n",
        }
    )
    judge["criteria"] = criteria
    return rubric


def update_deterministic_bound(
    rubric: dict[str, Any],
    max_tool_turns: int | None = None,
    max_error_rate: float | None = None,
) -> dict[str, Any]:
    """Update deterministic thresholds in-place."""
    checks = rubric.setdefault("deterministic_checks", [])
    by_name = {c.get("name"): c for c in checks if isinstance(c, dict)}
    if max_tool_turns is not None:
        by_name.setdefault(
            "max_tool_turns_per_stage",
            {"name": "max_tool_turns_per_stage", "description": "Flag runaway tool loops"},
        )["threshold"] = int(max_tool_turns)
    if max_error_rate is not None:
        by_name.setdefault(
            "no_unhandled_tool_errors",
            {"name": "no_unhandled_tool_errors", "description": "Check TOOL spans for errors"},
        )["max_error_rate"] = float(max_error_rate)
    rubric["deterministic_checks"] = list(by_name.values())
    return rubric


def _prompt_menu(title: str, options: list[str]) -> int:
    """Display a numbered menu and return the 1-based selection."""
    print(f"\n=== {title} ===")
    for idx, label in enumerate(options, start=1):
        print(f"  [{idx}] {label}")
    while True:
        raw = input(f"Select option [1-{len(options)}]: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw)
        print("Invalid choice. Enter a number from the menu.")


def run_interactive(rubric: dict[str, Any], rubric_path: Path, target_sync: bool) -> tuple[dict[str, Any], bool]:
    """Interactive menu loop for extending a project's eval rubric."""
    while True:
        proj = rubric.get("project_name", "unknown")
        crit_names = [c.get("name") for c in rubric.get("llm_judge_evals", {}).get("criteria", [])]
        print(f"\nActive Rubric: {proj} ({rubric_path})")
        print(f"Current LLM criteria: {', '.join(crit_names) or 'none'}")
        choice = _prompt_menu(
            "Stage 06 — Extend Project Eval Rubric",
            [
                "Apply domain preset (e.g., EU AI Act Risk Assessment)",
                "Add custom LLM-as-a-judge criterion",
                "Adjust deterministic thresholds (tool turn cap / error rate)",
                "Change judge model",
                "Save & finish (and sync to target .otel/eval_rubric.yaml if present)",
                "Cancel without saving",
            ],
        )
        if choice == 1:
            presets = sorted(PRESETS_DIR.glob("*.yaml"))
            if not presets:
                print("No presets found in 06_extend_eval_rubric/presets/.")
                continue
            p_idx = _prompt_menu("Available Presets", [p.name for p in presets] + ["Back"])
            if p_idx <= len(presets):
                rubric = apply_preset(rubric, presets[p_idx - 1])
                print(f"Merged preset: {presets[p_idx - 1].name}")
        elif choice == 2:
            raw_name = input("Criterion slug (e.g., regulatory_citation_check): ").strip()
            cname = re.sub(r"[^a-zA-Z0-9_]+", "_", raw_name).strip("_") or "custom_eval"
            prompt_body = input("Describe what the judge should evaluate: ").strip()
            pass_lbl = input("Pass label [PASS]: ").strip() or "PASS"
            fail_lbl = input("Fail label [FAIL]: ").strip() or "FAIL"
            rubric = add_custom_criterion(rubric, cname, prompt_body, pass_lbl, fail_lbl)
            print(f"Added criterion '{cname}'.")
        elif choice == 3:
            turns_in = input("New max_tool_turns_per_stage (blank to keep): ").strip()
            err_in = input("New max_error_rate 0.0-1.0 (blank to keep): ").strip()
            rubric = update_deterministic_bound(
                rubric,
                max_tool_turns=int(turns_in) if turns_in else None,
                max_error_rate=float(err_in) if err_in else None,
            )
            print("Updated deterministic checks.")
        elif choice == 4:
            cur_m = rubric.get("llm_judge_evals", {}).get("judge_model", "gemini-2.5-flash")
            new_m = input(f"Judge model [{cur_m}]: ").strip() or cur_m
            rubric.setdefault("llm_judge_evals", {})["judge_model"] = new_m
        elif choice == 5:
            return rubric, True
        else:
            return rubric, False


def save_and_sync(
    rubric: dict[str, Any],
    rubric_path: Path,
    output_dir: Path,
    sync_target: bool,
) -> list[Path]:
    """Write extended rubric to Stage 06 outputs, source rubric, and target .otel/."""
    yaml_text = _dump_yaml(rubric)
    written: list[Path] = []

    output_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", str(rubric.get("project_name", "project")))
    stage06_copy = output_dir / f"eval_rubric.{slug}.yaml"
    stage06_copy.write_text(yaml_text, encoding="utf-8")
    written.append(stage06_copy)

    rubric_path.parent.mkdir(parents=True, exist_ok=True)
    rubric_path.write_text(yaml_text, encoding="utf-8")
    written.append(rubric_path)

    target_ws = rubric.get("target_workspace")
    if sync_target and target_ws:
        target_rubric = Path(str(target_ws)).expanduser() / ".otel" / "eval_rubric.yaml"
        if target_rubric.parent.is_dir():
            target_rubric.write_text(yaml_text, encoding="utf-8")
            written.append(target_rubric)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage 06: Extend project eval rubric interactively or via flags.")
    parser.add_argument("--rubric", type=Path, default=STAGE_02_RUBRIC, help="Path to base eval_rubric.yaml.")
    parser.add_argument("--preset", default=None, help="Preset name in presets/ (e.g., eu_ai_act_rubric).")
    parser.add_argument("--add-criterion", nargs=2, metavar=("NAME", "PROMPT"), default=None)
    parser.add_argument("--max-tool-turns", type=int, default=None)
    parser.add_argument("--max-error-rate", type=float, default=None)
    parser.add_argument("--no-sync-target", action="store_true", help="Do not overwrite <target>/.otel/eval_rubric.yaml.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    if not args.rubric.is_file():
        raise SystemExit(f"Error: rubric not found at {args.rubric}. Run Stage 02 first.")

    rubric = _load_yaml(args.rubric)
    non_interactive = any([args.preset, args.add_criterion, args.max_tool_turns is not None, args.max_error_rate is not None])

    if non_interactive:
        if args.preset:
            fname = args.preset if args.preset.endswith(".yaml") else f"{args.preset}.yaml"
            preset_path = PRESETS_DIR / fname
            if not preset_path.is_file():
                preset_path = PRESETS_DIR / f"{args.preset}_rubric.yaml"
            if not preset_path.is_file():
                raise SystemExit(f"Preset not found in {PRESETS_DIR}: {args.preset}")
            rubric = apply_preset(rubric, preset_path)
        if args.add_criterion:
            rubric = add_custom_criterion(rubric, args.add_criterion[0], args.add_criterion[1])
        if args.max_tool_turns is not None or args.max_error_rate is not None:
            rubric = update_deterministic_bound(rubric, args.max_tool_turns, args.max_error_rate)
        should_save = True
    else:
        rubric, should_save = run_interactive(rubric, args.rubric, not args.no_sync_target)

    if not should_save:
        print("Cancelled without saving.")
        return 0

    written = save_and_sync(rubric, args.rubric, args.output_dir, not args.no_sync_target)
    for p in written:
        print(f"Updated: {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
