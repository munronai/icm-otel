#!/usr/bin/env python3
"""Interactive deterministic CLI orchestrator for icm-otel (zero LLM required)."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent
STATE_DIR = ROOT_DIR / ".icm-otel"
PROFILES_FILE = STATE_DIR / "projects.json"

STAGE_01_SCRIPT = ROOT_DIR / "01_preflight_and_server" / "scripts" / "preflight_check.py"
STAGE_02_SCRIPT = ROOT_DIR / "02_target_audit_and_plan" / "scripts" / "audit_target.py"
STAGE_03_SCRIPT = ROOT_DIR / "03_apply_otel_config" / "scripts" / "apply_config.py"
STAGE_04_SCRIPT = ROOT_DIR / "04_ingest_and_eval" / "scripts" / "ingest_and_eval.py"
STAGE_05_SCRIPT = ROOT_DIR / "05_compare_and_report" / "scripts" / "generate_scorecard.py"
STAGE_06_SCRIPT = ROOT_DIR / "06_extend_eval_rubric" / "scripts" / "extend_rubric.py"


def ask_menu(title: str, options: list[str], allow_zero: bool = False) -> int:
    """Present a numbered menu and return the user's numeric selection."""
    print(f"\n=== {title} ===")
    for idx, label in enumerate(options, start=1):
        print(f"  [{idx}] {label}")
    if allow_zero:
        print("  [0] Back / Exit")
    while True:
        raw = input("Choose an option: ").strip()
        if allow_zero and raw == "0":
            return 0
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw)
        print("Invalid selection. Enter one of the listed numbers.")


def _python_for_uv_stages() -> list[str]:
    """Choose the best Python runner (uv run / .venv / sys.executable)."""
    venv_py = ROOT_DIR / ".venv" / "bin" / "python"
    if venv_py.exists():
        return [str(venv_py)]
    if shutil.which("uv"):
        return ["uv", "run", "python"]
    return [sys.executable]


def _run_step(cmd: list[str], env: dict[str, str] | None = None) -> int:
    """Run a deterministic pipeline script streaming output to the terminal."""
    print(f"\n$ {' '.join(cmd)}")
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    proc = subprocess.run(cmd, cwd=str(ROOT_DIR), env=merged_env, check=False)
    return proc.returncode


def _phoenix_get_json(endpoint: str, path: str) -> Any | None:
    """Perform a lightweight GET request against local Arize Phoenix REST API."""
    url = endpoint.rstrip("/") + path
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return None


def phoenix_is_up(endpoint: str) -> bool:
    """Return True if local Phoenix responds."""
    return _phoenix_get_json(endpoint, "/v1/projects?limit=1") is not None


def list_phoenix_projects_rest(endpoint: str) -> list[str]:
    """Return project names via Phoenix REST API."""
    payload = _phoenix_get_json(endpoint, "/v1/projects?limit=100")
    if not isinstance(payload, dict):
        return []
    return [str(item["name"]) for item in payload.get("data", []) if isinstance(item, dict) and "name" in item]


def count_project_spans_rest(endpoint: str, project_name: str, limit: int = 500) -> int | None:
    """Count recent spans in a Phoenix project (up to limit) via REST."""
    quoted = urllib.parse.quote(project_name, safe="")
    payload = _phoenix_get_json(endpoint, f"/v1/projects/{quoted}/spans?limit={limit}")
    if not isinstance(payload, dict):
        return None
    data = payload.get("data")
    return len(data) if isinstance(data, list) else 0


def load_profiles() -> dict[str, Any]:
    """Load saved target ICM project profiles (auto-seeding from Stage 02 if present)."""
    if PROFILES_FILE.is_file():
        try:
            return json.loads(PROFILES_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass

    profiles: dict[str, Any] = {"active": None, "projects": {}}
    stage02_rubric = ROOT_DIR / "02_target_audit_and_plan" / "outputs" / "eval_rubric.yaml"
    if stage02_rubric.is_file():
        text = stage02_rubric.read_text(encoding="utf-8")
        m_proj = re.search(r'^project_name:\s*"?([^"\n]+)"?', text, re.MULTILINE)
        m_ws = re.search(r'^target_workspace:\s*"?([^"\n]+)"?', text, re.MULTILINE)
        m_ep = re.search(r'^phoenix_endpoint:\s*"?([^"\n]+)"?', text, re.MULTILINE)
        if m_proj and m_ws:
            pname = m_proj.group(1).strip()
            profiles["active"] = pname
            profiles["projects"][pname] = {
                "project_name": pname,
                "target_path": m_ws.group(1).strip(),
                "endpoint": m_ep.group(1).strip() if m_ep else "http://localhost:6006",
                "mode": "sidecar",
            }
    return profiles


def save_profiles(profiles: dict[str, Any]) -> None:
    """Persist saved target project profiles locally."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    PROFILES_FILE.write_text(json.dumps(profiles, indent=2) + "\n", encoding="utf-8")


def _slugify(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", name.strip().lower()).strip("-")
    return cleaned or "icm-project"


def select_or_add_project(profiles: dict[str, Any], cli_target: Path | None = None) -> dict[str, Any]:
    """Select an existing saved project or register a new target ICM workspace."""
    if cli_target is not None:
        resolved = cli_target.expanduser().resolve()
        if not resolved.is_dir():
            raise SystemExit(f"Target directory not found: {resolved}")
        for prof in profiles["projects"].values():
            if Path(prof["target_path"]).resolve() == resolved:
                profiles["active"] = prof["project_name"]
                save_profiles(profiles)
                return prof
        pname = _slugify(resolved.name)
        prof = {
            "project_name": pname,
            "target_path": str(resolved),
            "endpoint": "http://localhost:6006",
            "mode": "sidecar",
        }
        profiles["projects"][pname] = prof
        profiles["active"] = pname
        save_profiles(profiles)
        return prof

    projects = list(profiles["projects"].values())
    if projects:
        opts = [f"{p['project_name']} -> {p['target_path']}" for p in projects] + ["Add / point to a new target ICM workspace"]
        choice = ask_menu("Select Target ICM Project", opts)
        if choice <= len(projects):
            chosen = projects[choice - 1]
            profiles["active"] = chosen["project_name"]
            save_profiles(profiles)
            return chosen

    while True:
        raw_path = input("\nEnter path to target ICM workspace (e.g., /Users/munron/dev/my-icm): ").strip()
        target = Path(raw_path).expanduser().resolve()
        if target.is_dir():
            break
        print(f"Directory not found: {target}")

    default_name = _slugify(target.name)
    pname = input(f"Phoenix project name [{default_name}]: ").strip() or default_name
    mode_choice = ask_menu(
        "Instrumentation Mode",
        [
            "sidecar (Recommended: keeps .otel/ & .claude/settings.local.json gitignored)",
            "tracked (Commits .otel/ + adds short Telemetry note to layer-0 doc)",
        ],
    )
    mode = "sidecar" if mode_choice == 1 else "tracked"
    prof = {
        "project_name": pname,
        "target_path": str(target),
        "endpoint": "http://localhost:6006",
        "mode": mode,
    }
    profiles["projects"][pname] = prof
    profiles["active"] = pname
    save_profiles(profiles)
    return prof


def handle_stage_01(project: dict[str, Any]) -> None:
    """Run Stage 01 preflight and offer deterministic recovery if Phoenix or hooks fail."""
    endpoint = project["endpoint"]
    while True:
        rc = _run_step([sys.executable, str(STAGE_01_SCRIPT), "--endpoint", endpoint])
        if rc == 0:
            print("\nStage 01 passed: Phoenix and harness hooks are ready.")
            return

        print("\nStage 01 reported missing Phoenix reachability or harness hooks.")
        opts = [
            "Start Arize Phoenix locally in background (`uvx arize-phoenix serve`)",
            "Print global hook install commands (Antigravity, Claude Code, Codex)",
            "Re-run Stage 01 preflight check",
            "Continue anyway (e.g., if Codex is intentionally deferred)",
        ]
        sel = ask_menu("Stage 01 Recovery Menu", opts)
        if sel == 1:
            if not shutil.which("uvx"):
                print("`uvx` not found. Install uv first: `brew install uv`")
                continue
            log_path = STATE_DIR / "phoenix_server.log"
            STATE_DIR.mkdir(parents=True, exist_ok=True)
            with log_path.open("ab") as fh:
                subprocess.Popen(
                    ["uvx", "arize-phoenix", "serve"],
                    stdout=fh,
                    stderr=fh,
                    start_new_session=True,
                )
            print(f"Started Phoenix in background (logs: {log_path}). Waiting up to 12s...")
            for _ in range(12):
                if phoenix_is_up(endpoint):
                    print("Phoenix is now reachable!")
                    break
                time.sleep(1)
        elif sel == 2:
            print(
                "\nRun these in your shell:\n"
                "  curl -sSL https://raw.githubusercontent.com/Arize-ai/coding-harness-tracing/main/install.sh | bash -s -- antigravity\n"
                "  curl -sSL https://raw.githubusercontent.com/Arize-ai/coding-harness-tracing/main/install.sh | bash -s -- claude\n"
                "  curl -sSL https://raw.githubusercontent.com/Arize-ai/coding-harness-tracing/main/install.sh | bash -s -- codex\n"
                "If using Codex, open `codex`, run `/hooks`, and approve every `arize-hook-codex-*` entry."
            )
        elif sel == 3:
            continue
        else:
            return


def handle_stage_02(project: dict[str, Any]) -> bool:
    """Run Stage 02 audit & plan generation."""
    rc = _run_step([
        sys.executable,
        str(STAGE_02_SCRIPT),
        "--target", project["target_path"],
        "--project-name", project["project_name"],
        "--endpoint", project["endpoint"],
        "--mode", project["mode"],
    ])
    if rc != 0:
        print("Stage 02 audit failed.")
        return False
    plan_file = ROOT_DIR / "02_target_audit_and_plan" / "outputs" / "instrumentation_plan.md"
    if plan_file.is_file():
        print("\n--- Instrumentation Plan Summary ---")
        print(plan_file.read_text(encoding="utf-8"))
    return True


def handle_stage_03(project: dict[str, Any]) -> bool:
    """Preview dry-run and apply OTel & eval config to target workspace."""
    _run_step([
        sys.executable,
        str(STAGE_03_SCRIPT),
        "--target", project["target_path"],
        "--project-name", project["project_name"],
        "--endpoint", project["endpoint"],
        "--mode", project["mode"],
        "--dry-run",
    ])
    sel = ask_menu(
        "Stage 03 Confirmation",
        [
            f"Apply these config files to {project['target_path']}",
            "Apply + also create CLAUDE.md -> GEMINI.md symlink (if GEMINI.md exists)",
            "Cancel without modifying target",
        ],
    )
    if sel == 3:
        return False
    cmd = [
        sys.executable,
        str(STAGE_03_SCRIPT),
        "--target", project["target_path"],
        "--project-name", project["project_name"],
        "--endpoint", project["endpoint"],
        "--mode", project["mode"],
    ]
    if sel == 2:
        cmd.append("--claude-symlink")
    rc = _run_step(cmd)
    return rc == 0


def _tail_harness_logs() -> None:
    logs_dir = Path.home() / ".arize" / "harness" / "logs"
    if not logs_dir.is_dir():
        print(f"No hook logs directory found at {logs_dir}.")
        return
    logs = sorted(logs_dir.glob("*.log"))
    if not logs:
        print(f"No .log files found in {logs_dir}.")
        return
    for lf in logs:
        print(f"\n--- {lf.name} (last 15 lines) ---")
        lines = lf.read_text(encoding="utf-8", errors="replace").splitlines()
        for line in lines[-15:]:
            print(line)


def handle_monitor(project: dict[str, Any]) -> list[str]:
    """Watch Phoenix live while user runs target ICM pipeline; detect misrouted traces."""
    endpoint = project["endpoint"]
    target_proj = project["project_name"]
    if not phoenix_is_up(endpoint):
        print(f"Phoenix is not reachable at {endpoint}. Run Stage 01 first.")
        return [target_proj]

    all_projs = list_phoenix_projects_rest(endpoint)
    baseline = {p: (count_project_spans_rest(endpoint, p) or 0) for p in all_projs}
    base_target = baseline.get(target_proj, 0)

    print(
        f"\nMonitoring Phoenix ({endpoint}) for project '{target_proj}' (baseline spans: {base_target}).\n"
        f"Run your task inside: {project['target_path']}\n"
        f"  - Claude Code: cd {project['target_path']} && claude\n"
        f"  - Antigravity CLI: cd {project['target_path']} && source .otel/phoenix.env && agy\n"
        "Press Ctrl+C anytime when done (or to open recovery menu)."
    )

    try:
        while True:
            time.sleep(3)
            cur_projs = list_phoenix_projects_rest(endpoint)
            cur_target = count_project_spans_rest(endpoint, target_proj) or 0
            delta_target = cur_target - base_target
            other_deltas: dict[str, int] = {}
            for p in cur_projs:
                if p == target_proj:
                    continue
                cnt = count_project_spans_rest(endpoint, p) or 0
                d = cnt - baseline.get(p, 0)
                if d > 0:
                    other_deltas[p] = d

            stamp = time.strftime("%H:%M:%S")
            print(f"[{stamp}] '{target_proj}' spans: {cur_target} (+{max(0, delta_target)})", flush=True)

            if delta_target <= 0 and other_deltas:
                print(
                    f"\nAlert: '{target_proj}' has no new spans yet, while other project(s) received spans: {other_deltas}"
                )
                sel = ask_menu(
                    "Trace Routing Diagnosis Menu",
                    [
                        f"Evaluate the active project(s) that received spans ({', '.join(other_deltas.keys())})",
                        "Re-apply Stage 03 config (.otel/phoenix.env & .claude/settings.local.json)",
                        "Inspect ~/.arize/harness/logs/*.log",
                        "Keep watching",
                        "Stop monitoring and return to main menu",
                    ],
                )
                if sel == 1:
                    return list(other_deltas.keys())
                if sel == 2:
                    handle_stage_03(project)
                elif sel == 3:
                    _tail_harness_logs()
                elif sel == 5:
                    return [target_proj]
    except KeyboardInterrupt:
        print("\nStopped monitoring.")
        return [target_proj]


def handle_stage_04(project: dict[str, Any], override_projects: list[str] | None = None) -> bool:
    """Run Stage 04 with dependency & LLM-judge recovery menus."""
    py_cmd = _python_for_uv_stages()
    projects = override_projects or [project["project_name"]]

    eval_mode = ask_menu(
        "Stage 04 Evaluation Mode",
        [
            "Deterministic checks + Antigravity shadow tokens/cost (zero API key needed)",
            "Deterministic + Shadow cost + LLM-as-a-judge (Google Gemini)",
            "Deterministic + Shadow cost + LLM-as-a-judge (Local Ollama, zero API cost)",
            "Pull ALL Phoenix projects (--all-projects) with deterministic + shadow cost",
        ],
    )

    cmd = py_cmd + [str(STAGE_04_SCRIPT), "--endpoint", project["endpoint"]]
    target_rubric = Path(project["target_path"]) / ".otel" / "eval_rubric.yaml"
    if target_rubric.is_file():
        cmd.extend(["--rubric", str(target_rubric)])
    extra_env: dict[str, str] = {}

    if eval_mode == 4:
        cmd.append("--all-projects")
    else:
        cmd.extend(["--project", *projects])

    if eval_mode == 2:
        if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
            key = input("Enter GEMINI_API_KEY (leave blank to cancel): ").strip()
            if not key:
                return False
            extra_env["GEMINI_API_KEY"] = key
        model = input("Gemini judge model [gemini-2.5-flash]: ").strip() or "gemini-2.5-flash"
        cmd.extend(["--run-llm-eval", "--judge-provider", "google", "--judge-model", model])
    elif eval_mode == 3:
        model = input("Ollama model tag (e.g., llama3.2) [llama3.2]: ").strip() or "llama3.2"
        if not model.startswith("ollama/"):
            model = f"ollama/{model}"
        cmd.extend(["--run-llm-eval", "--judge-provider", "litellm", "--judge-model", model])

    rc = _run_step(cmd, env=extra_env)
    if rc != 0:
        sel = ask_menu(
            "Stage 04 Recovery Menu",
            [
                "Run `uv sync` to install/repair .venv dependencies, then retry",
                "Run Stage 04 with `--no-push` (skip uploading annotations to Phoenix)",
                "Return to main menu",
            ],
        )
        if sel == 1 and shutil.which("uv"):
            _run_step(["uv", "sync"])
            rc = _run_step(cmd, env=extra_env)
        elif sel == 2:
            rc = _run_step(cmd + ["--no-push"], env=extra_env)
    return rc == 0


def handle_stage_05() -> bool:
    """Run Stage 05 cross-harness scorecard generator."""
    rc = _run_step([sys.executable, str(STAGE_05_SCRIPT)])
    if rc == 0:
        scorecard = ROOT_DIR / "05_compare_and_report" / "outputs" / "scorecard.md"
        if scorecard.is_file():
            print("\n" + scorecard.read_text(encoding="utf-8"))
    return rc == 0


def handle_stage_06(project: dict[str, Any]) -> None:
    """Run Stage 06 interactive rubric extender."""
    py_cmd = _python_for_uv_stages()
    target_rubric = Path(project["target_path"]) / ".otel" / "eval_rubric.yaml"
    rubric_arg = target_rubric if target_rubric.is_file() else (ROOT_DIR / "02_target_audit_and_plan" / "outputs" / "eval_rubric.yaml")
    rc = _run_step(py_cmd + [str(STAGE_06_SCRIPT), "--rubric", str(rubric_arg)])
    if rc != 0:
        print("Tip: If PyYAML is missing, run `uv sync` first.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Interactive deterministic CLI for icm-otel.")
    parser.add_argument("--target", type=Path, default=None, help="Target ICM workspace path.")
    args = parser.parse_args()

    profiles = load_profiles()
    project = select_or_add_project(profiles, cli_target=args.target)

    while True:
        print(f"\nActive Target: {project['project_name']} ({project['target_path']}) | Mode: {project['mode']}")
        choice = ask_menu(
            "icm-otel Control Center",
            [
                "Guided Flow (Preflight -> Audit -> Apply -> Monitor -> Eval -> Scorecard)",
                "Stage 01: Check Phoenix server & global hooks",
                "Stage 02: Audit target ICM workspace & generate plan",
                "Stage 03: Apply OTel & eval config to target",
                "Live Monitor: Watch Phoenix while running target pipeline",
                "Stage 04: Ingest traces, shadow-cost backfill & evals",
                "Stage 05: Generate scorecard & ICM optimization notes",
                "Stage 06: Extend / customize eval rubric for this project",
                "Switch / Add target ICM project",
            ],
            allow_zero=True,
        )
        if choice == 0:
            return 0
        if choice == 1:
            handle_stage_01(project)
            handle_stage_02(project)
            if handle_stage_03(project):
                projs = handle_monitor(project)
                if handle_stage_04(project, override_projects=projs):
                    handle_stage_05()
        elif choice == 2:
            handle_stage_01(project)
        elif choice == 3:
            handle_stage_02(project)
        elif choice == 4:
            handle_stage_03(project)
        elif choice == 5:
            projs = handle_monitor(project)
            if ask_menu("Monitor finished. Run Stage 04 now?", ["Yes, run Stage 04", "No, back to menu"]) == 1:
                if handle_stage_04(project, override_projects=projs):
                    handle_stage_05()
        elif choice == 6:
            handle_stage_04(project)
        elif choice == 7:
            handle_stage_05()
        elif choice == 8:
            handle_stage_06(project)
        elif choice == 9:
            project = select_or_add_project(profiles)


if __name__ == "__main__":
    raise SystemExit(main())
