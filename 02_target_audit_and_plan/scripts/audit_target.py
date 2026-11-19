#!/usr/bin/env python3
"""Stage 02 target ICM workspace auditor and OTel/eval plan generator."""

from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STAGE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = STAGE_DIR / "outputs"

# Matches classic `01_foo`, hyphenated `01-foo`, `1_foo`, `stage_01`, `step-1`, etc.
STAGE_NAME_RE = re.compile(
    r"^(?:(?:0?[1-9]\d?)[_-].+|(?:stage|step)[_-]?\d+.*)$", re.IGNORECASE
)
IGNORE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".otel",
    ".claude",
    ".codex",
    ".gemini",
    ".agents",
    "_templates",
    "outputs",
    "output",
}
STAGE_CONTAINER_DIRS = ("stages", "pipeline", "workflows", "phases")
CONTEXT_FILENAMES = ("CONTEXT.md", "README.md", "SKILL.md", "PROMPT.md", "context.md")


def slugify(name: str) -> str:
    """Create a safe Phoenix project slug from a directory name."""
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", name.strip().lower()).strip("-")
    return f"icm-{cleaned}" if not cleaned.startswith("icm-") else cleaned


def _extract_section_lines(md_text: str, heading_keywords: tuple[str, ...], limit: int = 4) -> list[str]:
    """Extract bullet, table data, or plain lines under a matching markdown heading."""
    lines = md_text.splitlines()
    captured: list[str] = []
    in_section = False
    skipped_table_header = False
    for raw in lines:
        stripped = raw.strip()
        if stripped.startswith("#"):
            title = stripped.lstrip("#").strip().lower()
            in_section = any(k in title for k in heading_keywords)
            skipped_table_header = False
            continue
        if in_section:
            if not stripped:
                if captured:
                    break
                continue
            if stripped.startswith("|"):
                cells = [c.strip() for c in stripped.strip("|").split("|")]
                # Skip markdown separator rows like |---|---|
                if all(re.fullmatch(r":?-{2,}:?", c or "") for c in cells):
                    skipped_table_header = True
                    continue
                # Skip header row (the row immediately preceding separator)
                if not skipped_table_header and not captured:
                    # Peek ahead by holding nothing yet; wait for separator
                    continue
                row_summary = " — ".join(c for c in cells[:2] if c)
                if row_summary:
                    captured.append(row_summary)
            else:
                captured.append(stripped.lstrip("-* ").strip())
            if len(captured) >= limit:
                break
    return captured


def _inspect_stage_dir(stage_path: Path, rel_label: str) -> dict[str, Any]:
    """Inspect a stage directory."""
    context_file = None
    for candidate in CONTEXT_FILENAMES:
        p = stage_path / candidate
        if p.is_file():
            context_file = p
            break

    objective: list[str] = []
    outputs: list[str] = []
    if context_file:
        text = context_file.read_text(encoding="utf-8", errors="replace")
        objective = _extract_section_lines(text, ("objective", "purpose", "goal"), limit=2)
        outputs = _extract_section_lines(text, ("output", "deliverable", "artifact"), limit=4)

    existing_outputs = []
    for out_name in ("outputs", "output"):
        outputs_dir = stage_path / out_name
        if outputs_dir.is_dir():
            existing_outputs.extend(
                f"{out_name}/{p.name}"
                for p in sorted(outputs_dir.iterdir())
                if p.is_file() and p.name != ".gitkeep"
            )

    return {
        "name": rel_label,
        "kind": "dir",
        "has_context_md": context_file is not None,
        "context_file": context_file.name if context_file else None,
        "objective": objective,
        "outputs": outputs,
        "existing_outputs": existing_outputs,
    }


def _inspect_stage_file(file_path: Path, rel_label: str) -> dict[str, Any]:
    """Inspect a stage defined as a standalone Markdown file (e.g., stages/01_intake.md)."""
    text = file_path.read_text(encoding="utf-8", errors="replace")
    objective = _extract_section_lines(text, ("objective", "purpose", "goal"), limit=2)
    outputs = _extract_section_lines(text, ("output", "deliverable", "artifact"), limit=4)
    return {
        "name": rel_label,
        "kind": "file",
        "has_context_md": True,
        "context_file": file_path.name,
        "objective": objective,
        "outputs": outputs,
        "existing_outputs": [],
    }


def _discover_stages(target: Path) -> list[dict[str, Any]]:
    """Discover stages across classic root `NN_*` dirs and `stages/`-style containers."""
    stages: list[dict[str, Any]] = []
    seen_paths: set[Path] = set()

    # 1. Root-level stage directories (classic ICM or hyphenated/stage_* variants)
    for p in sorted(target.iterdir(), key=lambda x: x.name):
        if not p.is_dir() or p.name in IGNORE_DIRS or p.name.startswith("00_"):
            continue
        if STAGE_NAME_RE.match(p.name):
            seen_paths.add(p)
            stages.append(_inspect_stage_dir(p, f"{p.name}/"))

    # 2. Container directories like `stages/`, `pipeline/`, `workflows/`
    for container_name in STAGE_CONTAINER_DIRS:
        container = target / container_name
        if not container.is_dir():
            continue
        for child in sorted(container.iterdir(), key=lambda x: x.name):
            if child in seen_paths or child.name in IGNORE_DIRS or child.name.startswith("."):
                continue
            if child.is_dir():
                has_ctx = any((child / c).is_file() for c in CONTEXT_FILENAMES)
                if STAGE_NAME_RE.match(child.name) or has_ctx:
                    seen_paths.add(child)
                    stages.append(_inspect_stage_dir(child, f"{container_name}/{child.name}/"))
            elif child.is_file() and child.suffix.lower() == ".md":
                if child.name.upper() not in ("README.MD", "CONTEXT.MD"):
                    seen_paths.add(child)
                    stages.append(_inspect_stage_file(child, f"{container_name}/{child.name}"))

    return stages


def _collect_tree_preview(target: Path, max_entries: int = 60) -> list[str]:
    """Build a shallow (depth <= 2) directory preview for audit visibility."""
    entries: list[str] = []
    for p in sorted(target.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
        if p.name in IGNORE_DIRS:
            continue
        suffix = "/" if p.is_dir() else ""
        entries.append(f"{p.name}{suffix}")
        if p.is_dir() and not p.name.startswith("."):
            for sub in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                if sub.name in IGNORE_DIRS:
                    continue
                sub_suffix = "/" if sub.is_dir() else ""
                entries.append(f"  {sub.name}{sub_suffix}")
                if len(entries) >= max_entries:
                    entries.append("  ... (truncated)")
                    return entries
        if len(entries) >= max_entries:
            entries.append("... (truncated)")
            return entries
    return entries


def audit_target_workspace(target: Path) -> dict[str, Any]:
    """Inspect root ICM files, harness configs, directory tree, and stages."""
    root_files = {}
    for fname in ("AGENTS.md", "CLAUDE.md", "GEMINI.md", "CONTEXT.md", "README.md", ".gitignore"):
        p = target / fname
        root_files[fname] = {
            "exists": p.exists(),
            "is_symlink": p.is_symlink(),
            "lines": len(p.read_text(encoding="utf-8", errors="replace").splitlines())
            if p.is_file()
            else 0,
        }

    harness_dirs = {}
    for dname in (".claude", ".codex", ".gemini", ".agents", ".otel"):
        d = target / dname
        harness_dirs[dname] = sorted(p.name for p in d.iterdir()) if d.is_dir() else []

    stages = _discover_stages(target)

    gitignore_text = ""
    gi = target / ".gitignore"
    if gi.is_file():
        gitignore_text = gi.read_text(encoding="utf-8", errors="replace")

    return {
        "target_path": str(target),
        "is_git_repo": (target / ".git").exists(),
        "root_files": root_files,
        "harness_dirs": harness_dirs,
        "stages": stages,
        "tree_preview": _collect_tree_preview(target),
        "ignores_otel": ".otel" in gitignore_text,
        "ignores_claude_local": ".claude/settings.local.json" in gitignore_text,
    }


def render_target_audit(audit: dict[str, Any], generated_at: str) -> str:
    """Render target_audit.md."""
    lines = [
        "# Stage 02 Target ICM Audit",
        "",
        f"- **Generated (UTC):** {generated_at}",
        f"- **Target Path:** `{audit['target_path']}`",
        f"- **Git Repo:** {'Yes' if audit['is_git_repo'] else 'No'}",
        "",
        "## 1. Root ICM & Orientation Files",
        "| File | Present | Symlink | Line Count |",
        "| :--- | :--- | :--- | :--- |",
    ]
    for fname, info in audit["root_files"].items():
        present = "Yes" if info["exists"] else "No"
        sym = "Yes" if info["is_symlink"] else "No"
        lines.append(f"| `{fname}` | {present} | {sym} | {info['lines']} |")

    lines.extend([
        "",
        "## 2. Existing Harness / Telemetry Directories",
        "| Directory | Contents |",
        "| :--- | :--- |",
    ])
    for dname, contents in audit["harness_dirs"].items():
        val = ", ".join(f"`{c}`" for c in contents) if contents else "_absent / empty_"
        lines.append(f"| `{dname}/` | {val} |")

    lines.extend([
        "",
        "## 3. Discovered Stages",
    ])
    if not audit["stages"]:
        lines.append("_No stage directories or `stages/*.md` definitions matched automatically. Review the directory tree below._")
    else:
        lines.extend([
            "| Stage | Type | Context / Spec File | Declared Outputs | Existing `outputs/` |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ])
        for st in audit["stages"]:
            ctx = f"`{st['context_file']}`" if st["context_file"] else "**MISSING**"
            decl_out = "; ".join(st["outputs"]) if st["outputs"] else "_unspecified_"
            cur_out = ", ".join(f"`{x}`" for x in st["existing_outputs"]) if st["existing_outputs"] else "_none_"
            lines.append(f"| `{st['name']}` | {st['kind']} | {ctx} | {decl_out} | {cur_out} |")

    lines.extend([
        "",
        "## 4. Target Directory Preview (Depth <= 2)",
        "```text",
        *(audit["tree_preview"] or ["(empty)"]),
        "```",
        "",
        "## 5. Walk Test & Readiness Notes",
    ])
    if not (
        audit["root_files"]["AGENTS.md"]["exists"]
        or audit["root_files"]["CLAUDE.md"]["exists"]
        or audit["root_files"]["GEMINI.md"]["exists"]
    ):
        lines.append("- **Warning:** No Layer 0 entry file (`AGENTS.md`, `CLAUDE.md`, or `GEMINI.md`) exists at target root.")
    elif not (audit["root_files"]["AGENTS.md"]["exists"] or audit["root_files"]["CLAUDE.md"]["exists"]):
        lines.append("- **Note:** Uses `GEMINI.md` at root (add `CLAUDE.md` / `AGENTS.md` symlink or note if running Claude Code / Codex here).")
    if not audit["root_files"]["CONTEXT.md"]["exists"]:
        lines.append("- **Warning:** Root `CONTEXT.md` is missing.")
    missing_ctx = [st["name"] for st in audit["stages"] if not st["has_context_md"]]
    if missing_ctx:
        lines.append(f"- **Warning:** Stages missing a context file: {', '.join(missing_ctx)}")
    if not missing_ctx and audit["stages"]:
        lines.append("- All discovered stages have a context/spec file.")

    return "\n".join(lines) + "\n"


def render_instrumentation_plan(
    audit: dict[str, Any],
    project_name: str,
    mode: str,
    harnesses: list[str],
    endpoint: str,
) -> str:
    """Render instrumentation_plan.md proposing exact Stage 03 target edits."""
    proposed_files = [
        ("`.otel/phoenix.env`", "Create", f"Sets `PHOENIX_ENDPOINT={endpoint}` and `PHOENIX_PROJECT_NAME={project_name}` for CLI shells"),
        ("`.otel/eval_rubric.yaml`", "Create", "Copy of approved Stage 02 eval rubric for this target pipeline"),
    ]
    if "claude_code" in harnesses:
        proposed_files.append(
            ("`.claude/settings.local.json`", "Create / Merge", f"Project-scoped Claude Code `env` override (`PHOENIX_PROJECT_NAME={project_name}`)")
        )
    if "codex" in harnesses:
        proposed_files.append(
            ("`.codex/config.toml`", "Create / Merge", "Project-scoped Codex telemetry metadata (if Codex is enabled)")
        )
    if mode == "sidecar":
        proposed_files.append(
            ("`.gitignore`", "Append (if needed)", "Ignore `.otel/` and `.claude/settings.local.json` so instrumentation stays local")
        )
    else:
        entry_doc = "AGENTS.md" if audit["root_files"]["AGENTS.md"]["exists"] else "CLAUDE.md"
        proposed_files.append(
            (f"`{entry_doc}`", "Append note", "Non-invasive 4-line Telemetry section pointing to `.otel/phoenix.env`")
        )

    lines = [
        "# Stage 02 Target Instrumentation Plan (Draft — Awaiting Approval)",
        "",
        f"- **Target Workspace Path:** `{audit['target_path']}`",
        f"- **Phoenix Endpoint:** `{endpoint}`",
        f"- **Phoenix Project Name:** `{project_name}`",
        f"- **Instrumentation Mode:** `{mode}`",
        f"- **Harnesses Observed:** {', '.join(f'`{h}`' for h in harnesses)}",
        "",
        "## Proposed Target Files & Edits (Executed in Stage 03 After Approval)",
        "| Target File | Action | Purpose |",
        "| :--- | :--- | :--- |",
    ]
    for path_label, action, purpose in proposed_files:
        lines.append(f"| {path_label} | {action} | {purpose} |")

    lines.extend([
        "",
        "## Target ICM Stages Mapped to Eval",
        "| Stage | Expected Output(s) | Deterministic Check | LLM Judge Focus |",
        "| :--- | :--- | :--- | :--- |",
    ])
    for st in audit["stages"]:
        exp = "; ".join(st["outputs"]) if st["outputs"] else "`outputs/` non-empty"
        lines.append(f"| `{st['name']}` | {exp} | Expected output files exist & non-empty | Stage instruction adherence & groundedness |")
    if not audit["stages"]:
        lines.append("| _root / ad-hoc_ | _customize manually_ | No unhandled tool errors | Instruction adherence |")

    lines.extend([
        "",
        "## Human Gate Checklist (Stage 02)",
        f"- [ ] Confirm `Phoenix Project Name` (`{project_name}`).",
        f"- [ ] Confirm `Instrumentation Mode` (`{mode}`).",
        "- [ ] Confirm proposed target files above and customized `outputs/eval_rubric.yaml`.",
    ])
    return "\n".join(lines) + "\n"


def render_eval_rubric(audit: dict[str, Any], project_name: str, endpoint: str) -> str:
    """Render eval_rubric.yaml without requiring external YAML packages."""
    lines = [
        f"# Eval Rubric for {project_name}",
        f'project_name: "{project_name}"',
        f'phoenix_endpoint: "{endpoint}"',
        f'target_workspace: "{audit["target_path"]}"',
        "",
        "shadow_tokens:",
        '  enabled_for_harnesses: ["antigravity"]',
        '  tokenizer: "tiktoken"',
        '  pricing_table: "00_reference/model_pricing.json"',
        "",
        "deterministic_checks:",
        '  - name: "no_unhandled_tool_errors"',
        '    description: "Check TOOL spans for error status or non-zero exit codes"',
        "    max_error_rate: 0.15",
        '  - name: "max_tool_turns_per_stage"',
        '    description: "Flag runaway tool loops"',
        "    threshold: 25",
        "",
        "target_stages:",
    ]
    if audit["stages"]:
        for st in audit["stages"]:
            lines.append(f'  - stage: "{st["name"]}"')
            decl = st["outputs"][0] if st["outputs"] else "outputs/"
            safe_decl = decl.replace('"', '\\"')
            lines.append(f'    expected_output: "{safe_decl}"')
    else:
        lines.append('  - stage: "root"')
        lines.append('    expected_output: "manual_review"')

    lines.extend([
        "",
        "llm_judge_evals:",
        "  enabled: true",
        '  judge_model: "gemini-2.5-flash"',
        "  criteria:",
        '    - name: "stage_instruction_adherence"',
        "      prompt_template: |",
        "        Evaluate whether the agent followed the stage instructions and produced a valid, grounded output without fabricating file paths or tool outputs.",
        "        Input: {input}",
        "        Output: {output}",
        "        Respond with label PASS or FAIL and a one-sentence explanation.",
        '    - name: "tool_efficiency"',
        "      prompt_template: |",
        "        Evaluate whether the agent solved the task cleanly without redundant retries or unnecessary context reads.",
        "        Input: {input}",
        "        Output: {output}",
        "        Respond with label EFFICIENT or WASTEFUL and a one-sentence explanation.",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage 02 audit for an external ICM workspace.")
    parser.add_argument("--target", required=True, type=Path, help="Path to target ICM workspace root.")
    parser.add_argument("--project-name", default=None, help="Phoenix project name (default: icm-<target-dir>).")
    parser.add_argument("--endpoint", default="http://localhost:6006", help="Local Phoenix endpoint.")
    parser.add_argument("--mode", choices=("sidecar", "tracked"), default="sidecar")
    parser.add_argument(
        "--harnesses",
        nargs="+",
        default=["antigravity", "claude_code"],
        choices=("antigravity", "claude_code", "codex", "gemini_cli"),
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    target = args.target.expanduser().resolve()
    if not target.is_dir():
        raise SystemExit(f"Error: target directory not found: {target}")

    project_name = args.project_name or slugify(target.name)
    generated_at = datetime.now(timezone.utc).isoformat()
    audit = audit_target_workspace(target)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    audit_path = args.output_dir / "target_audit.md"
    plan_path = args.output_dir / "instrumentation_plan.md"
    rubric_path = args.output_dir / "eval_rubric.yaml"

    audit_path.write_text(render_target_audit(audit, generated_at), encoding="utf-8")
    plan_path.write_text(
        render_instrumentation_plan(audit, project_name, args.mode, args.harnesses, args.endpoint),
        encoding="utf-8",
    )
    rubric_path.write_text(render_eval_rubric(audit, project_name, args.endpoint), encoding="utf-8")

    print(f"Wrote {audit_path}")
    print(f"Wrote {plan_path}")
    print(f"Wrote {rubric_path}")
    print(f"Discovered {len(audit['stages'])} stage(s) in {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
