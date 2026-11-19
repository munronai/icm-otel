#!/usr/bin/env python3
"""Stage 03 config applier: writes approved OTel & eval config into a target ICM repo."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent.parent.parent
STAGE_02_OUT = ROOT_DIR / "02_target_audit_and_plan" / "outputs"
TEMPLATES_DIR = ROOT_DIR / "_templates"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"


def _parse_simple_yaml_scalars(yaml_path: Path) -> dict[str, str]:
    """Read top-level scalar keys from eval_rubric.yaml without external deps."""
    result: dict[str, str] = {}
    if not yaml_path.is_file():
        return result
    for raw in yaml_path.read_text(encoding="utf-8").splitlines():
        if not raw or raw.startswith("#") or raw[0].isspace():
            continue
        m = re.match(r'^([a-zA-Z0-9_]+):\s*"?([^"#]+?)"?\s*$', raw)
        if m:
            result[m.group(1)] = m.group(2).strip()
    return result


def _parse_plan_mode(plan_path: Path) -> str:
    """Extract Instrumentation Mode from instrumentation_plan.md."""
    if not plan_path.is_file():
        return "sidecar"
    text = plan_path.read_text(encoding="utf-8")
    m = re.search(r"Instrumentation Mode:\*\*\s*`([^`]+)`", text)
    return m.group(1).strip() if m else "sidecar"


def _merge_claude_settings(path: Path, project_name: str, endpoint: str, dry_run: bool) -> str:
    """Create or merge .claude/settings.local.json with Phoenix env vars."""
    existing: dict[str, Any] = {}
    action = "would create" if dry_run else "created"
    if path.is_file():
        action = "would update" if dry_run else "updated"
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Refusing to overwrite invalid JSON in {path}: {exc}")

    env_block = existing.get("env")
    if not isinstance(env_block, dict):
        env_block = {}
    env_block["PHOENIX_ENDPOINT"] = endpoint
    env_block["PHOENIX_PROJECT"] = project_name
    env_block["PHOENIX_PROJECT_NAME"] = project_name
    existing["env"] = env_block

    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    return action


def _ensure_gitignore_entries(gitignore_path: Path, entries: list[str], dry_run: bool) -> str:
    """Idempotently append sidecar paths to target .gitignore."""
    current = gitignore_path.read_text(encoding="utf-8") if gitignore_path.is_file() else ""
    existing_lines = {line.strip() for line in current.splitlines()}
    missing = [e for e in entries if e not in existing_lines]
    if not missing:
        return "unchanged (already ignored)"

    if not dry_run:
        prefix = "" if (not current or current.endswith("\n")) else "\n"
        block = "\n# icm-otel local sidecar\n" + "\n".join(missing) + "\n"
        gitignore_path.write_text(current + prefix + block, encoding="utf-8")
        return f"appended ({', '.join(missing)})"
    return f"would append ({', '.join(missing)})"


def _run_walk_test(target: Path) -> dict[str, Any]:
    """Verify target ICM workspace orientation files remain intact and concise."""
    layer0_candidates = [target / f for f in ("AGENTS.md", "CLAUDE.md", "GEMINI.md")]
    present_l0 = [p for p in layer0_candidates if p.exists()]
    l0_lines = {
        p.name: len(p.read_text(encoding="utf-8", errors="replace").splitlines())
        for p in present_l0
        if p.is_file()
    }
    has_context = (target / "CONTEXT.md").is_file()
    stages_dir = target / "stages"
    search_root = stages_dir if stages_dir.is_dir() else target
    stage_dirs = [
        d for d in sorted(search_root.iterdir())
        if d.is_dir() and re.match(r"^(?:0?[1-9]|stage|step)", d.name, re.IGNORECASE)
    ]
    missing_stage_ctx = [d.name for d in stage_dirs if not (d / "CONTEXT.md").is_file()]

    passed = bool(present_l0) and has_context and not missing_stage_ctx
    return {
        "passed": passed,
        "layer0_files": l0_lines,
        "has_root_context": has_context,
        "stage_count": len(stage_dirs),
        "missing_stage_context": missing_stage_ctx,
    }


def _git_status(target: Path) -> str:
    """Return short git status if target is a git repository."""
    if not (target / ".git").exists():
        return "(not a git repository)"
    proc = subprocess.run(
        ["git", "-C", str(target), "status", "--short"],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout.strip() or "(clean working tree)"


def main() -> int:
    rubric_defaults = _parse_simple_yaml_scalars(STAGE_02_OUT / "eval_rubric.yaml")
    default_mode = _parse_plan_mode(STAGE_02_OUT / "instrumentation_plan.md")

    parser = argparse.ArgumentParser(description="Stage 03 apply approved OTel & eval config to target ICM repo.")
    parser.add_argument("--target", type=Path, default=rubric_defaults.get("target_workspace"))
    parser.add_argument("--project-name", default=rubric_defaults.get("project_name"))
    parser.add_argument("--endpoint", default=rubric_defaults.get("phoenix_endpoint", "http://localhost:6006"))
    parser.add_argument("--mode", choices=("sidecar", "tracked"), default=default_mode)
    parser.add_argument("--rubric", type=Path, default=STAGE_02_OUT / "eval_rubric.yaml")
    parser.add_argument("--claude-symlink", action="store_true", help="Create CLAUDE.md -> GEMINI.md if missing.")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without modifying target workspace.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    if not args.target:
        raise SystemExit("Error: --target is required (not found in Stage 02 outputs).")
    target = args.target.expanduser().resolve()
    if not target.is_dir():
        raise SystemExit(f"Error: target workspace not found: {target}")
    if not args.project_name:
        raise SystemExit("Error: --project-name is required.")
    if not args.rubric.is_file():
        raise SystemExit(f"Error: eval rubric not found: {args.rubric}")

    env_template = (TEMPLATES_DIR / "target_otel_env.sh").read_text(encoding="utf-8")
    env_content = (
        env_template
        .replace("__PROJECT_NAME__", args.project_name)
        .replace("http://localhost:6006", args.endpoint)
    )
    rubric_content = args.rubric.read_text(encoding="utf-8")

    changes: list[tuple[str, str]] = []

    otel_dir = target / ".otel"
    env_path = otel_dir / "phoenix.env"
    rubric_dest = otel_dir / "eval_rubric.yaml"
    if not args.dry_run:
        otel_dir.mkdir(parents=True, exist_ok=True)
        env_path.write_text(env_content, encoding="utf-8")
        rubric_dest.write_text(rubric_content, encoding="utf-8")
    changes.append((".otel/phoenix.env", "would write" if args.dry_run else "written"))
    changes.append((".otel/eval_rubric.yaml", "would copy" if args.dry_run else "copied"))

    claude_path = target / ".claude" / "settings.local.json"
    claude_action = _merge_claude_settings(claude_path, args.project_name, args.endpoint, args.dry_run)
    changes.append((".claude/settings.local.json", claude_action))

    if args.mode == "sidecar":
        gi_action = _ensure_gitignore_entries(
            target / ".gitignore", [".otel/", ".claude/settings.local.json"], args.dry_run
        )
        changes.append((".gitignore", gi_action))
    else:
        note_template = (TEMPLATES_DIR / "target_agents_otel_note.md").read_text(encoding="utf-8")
        note = note_template.replace("__PROJECT_NAME__", args.project_name).replace("http://localhost:6006", args.endpoint)
        entry = next((target / f for f in ("AGENTS.md", "CLAUDE.md", "GEMINI.md") if (target / f).is_file()), None)
        if entry:
            cur = entry.read_text(encoding="utf-8")
            if "## Telemetry (OTel + Local Arize Phoenix)" in cur:
                changes.append((entry.name, "unchanged (note already present)"))
            else:
                if not args.dry_run:
                    sep = "\n" if cur.endswith("\n") else "\n\n"
                    entry.write_text(cur + sep + note, encoding="utf-8")
                changes.append((entry.name, "would append telemetry note" if args.dry_run else "appended telemetry note"))

    if args.claude_symlink and (target / "GEMINI.md").is_file() and not (target / "CLAUDE.md").exists():
        if not args.dry_run:
            (target / "CLAUDE.md").symlink_to("GEMINI.md")
        changes.append(("CLAUDE.md", "would symlink -> GEMINI.md" if args.dry_run else "symlinked -> GEMINI.md"))

    walk = _run_walk_test(target)
    git_stat = _git_status(target) if not args.dry_run else "(skipped during --dry-run)"

    lines = [
        "# Stage 03 Applied OTel & Eval Configuration",
        "",
        f"- **Generated (UTC):** {datetime.now(timezone.utc).isoformat()}",
        f"- **Dry Run:** {'Yes' if args.dry_run else 'No'}",
        f"- **Target Workspace:** `{target}`",
        f"- **Phoenix Project Name:** `{args.project_name}`",
        f"- **Phoenix Endpoint:** `{args.endpoint}`",
        f"- **Mode:** `{args.mode}`",
        "",
        "## 1. File Changes",
        "| Target File | Status |",
        "| :--- | :--- |",
    ]
    for fname, status in changes:
        lines.append(f"| `{fname}` | {status} |")

    lines.extend([
        "",
        "## 2. Target Walk Test Check",
        f"- **Result:** **{'PASS' if walk['passed'] else 'WARN'}**",
        f"- **Layer 0 Docs:** {walk['layer0_files']}",
        f"- **Root `CONTEXT.md`:** {'Present' if walk['has_root_context'] else 'MISSING'}",
        f"- **Discovered Stages:** {walk['stage_count']} (missing `CONTEXT.md`: {walk['missing_stage_context'] or 'none'})",
        "",
        "## 3. Target `git status --short`",
        "```text",
        git_stat,
        "```",
        "",
        "## 4. 1-Turn Verification Instructions",
        f"- **Claude Code:** Run `claude` inside `{target}` (reads `.claude/settings.local.json` automatically -> project `{args.project_name}`).",
        f"- **Antigravity CLI / Terminal:** Run `source .otel/phoenix.env` inside `{target}` before launching CLI tools.",
        "- **Antigravity IDE:** Global `~/.gemini/config/hooks.json` captures spans automatically under your default Arize project unless `.otel/phoenix.env` is inherited.",
        f"- Confirm the 1-turn verification trace appears at `{args.endpoint}`.",
    ])

    report = "\n".join(lines) + "\n"
    if args.dry_run:
        print(report)
    else:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        out_path = args.output_dir / "applied_changes.md"
        out_path.write_text(report, encoding="utf-8")
        print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
