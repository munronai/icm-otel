#!/usr/bin/env python3
"""Stage 01 preflight check for local Arize Phoenix and harness OTel hooks."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STAGE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = STAGE_DIR / "outputs"
DEFAULT_ENDPOINT = "http://localhost:6006"

CLI_BINARIES = [
    "uv",
    "uvx",
    "python3",
    "node",
    "npx",
    "claude",
    "codex",
    "agy",
    "gemini",
    "docker",
]


def check_binaries() -> dict[str, str | None]:
    """Locate required and optional CLI binaries on PATH."""
    return {name: shutil.which(name) for name in CLI_BINARIES}


def check_phoenix_server(endpoint: str, skip_network: bool = False) -> dict[str, Any]:
    """Check whether the local Arize Phoenix HTTP server is reachable."""
    if skip_network:
        return {"endpoint": endpoint, "reachable": None, "status": "skipped"}

    url = endpoint.rstrip("/") + "/"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            return {
                "endpoint": endpoint,
                "reachable": 200 <= resp.status < 400,
                "http_status": resp.status,
                "status": "ok" if 200 <= resp.status < 400 else "unexpected_status",
            }
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {
            "endpoint": endpoint,
            "reachable": False,
            "status": "unreachable",
            "error": str(exc),
        }


def _safe_read_text(path: Path) -> tuple[str | None, str | None]:
    """Read text safely without failing on missing files or sandbox permissions."""
    try:
        if not path.exists():
            return None, "missing"
        return path.read_text(encoding="utf-8", errors="replace"), None
    except PermissionError as exc:
        return None, f"permission_denied: {exc}"
    except OSError as exc:
        return None, f"os_error: {exc}"


def _inspect_arize_config(home: Path) -> dict[str, Any]:
    """Inspect ~/.arize/harness/config.json without exposing secret values."""
    cfg_path = home / ".arize" / "harness" / "config.json"
    text, err = _safe_read_text(cfg_path)
    if err:
        return {"path": str(cfg_path), "configured": False, "status": err}
    try:
        data = json.loads(text or "{}")
    except json.JSONDecodeError:
        return {"path": str(cfg_path), "configured": False, "status": "invalid_json"}

    # Redact any key-like fields while confirming presence.
    sanitized = {}
    for k, v in data.items():
        if any(tok in k.lower() for tok in ("key", "token", "secret", "password")):
            sanitized[k] = "<redacted>" if v else None
        else:
            sanitized[k] = v
    return {
        "path": str(cfg_path),
        "configured": True,
        "status": "ok",
        "details": sanitized,
    }


def _inspect_hook_file(path: Path, markers: tuple[str, ...]) -> dict[str, Any]:
    """Check whether a harness config file exists and references Arize/OTel hooks."""
    text, err = _safe_read_text(path)
    if err:
        return {"path": str(path), "exists": False, "hook_detected": False, "status": err}
    lower = (text or "").lower()
    matched = [m for m in markers if m in lower]
    return {
        "path": str(path),
        "exists": True,
        "hook_detected": len(matched) > 0,
        "matched_markers": matched,
        "status": "ok" if matched else "no_arize_hook_found",
    }


def check_harness_configs(home: Path | None = None) -> dict[str, Any]:
    """Inspect global Arize and agent harness config files."""
    base = home or Path.home()
    logs_dir = base / ".arize" / "harness" / "logs"
    log_files: list[str] = []
    try:
        if logs_dir.is_dir():
            log_files = sorted(p.name for p in logs_dir.iterdir() if p.is_file())
    except OSError:
        log_files = []

    return {
        "arize_global": _inspect_arize_config(base),
        "antigravity": _inspect_hook_file(
            base / ".gemini" / "config" / "hooks.json",
            ("arize", "phoenix", "posttooluse", "postinvocation"),
        ),
        "claude_code": _inspect_hook_file(
            base / ".claude" / "settings.json",
            ("arize", "phoenix", "hooks"),
        ),
        "codex": _inspect_hook_file(
            base / ".codex" / "config.toml",
            ("arize", "phoenix", "hooks"),
        ),
        "gemini_cli_optional": _inspect_hook_file(
            base / ".gemini" / "settings.json",
            ("arize", "telemetry", "otlp"),
        ),
        "harness_logs": log_files,
    }


def render_report(manifest: dict[str, Any]) -> str:
    """Format a concise Markdown preflight report with next actions."""
    phoenix = manifest["phoenix"]
    bins = manifest["binaries"]
    harnesses = manifest["harnesses"]

    lines = [
        "# Stage 01 Preflight Report",
        "",
        f"- **Generated (UTC):** {manifest['generated_at']}",
        f"- **Phoenix Endpoint:** `{phoenix['endpoint']}` — **{phoenix['status']}**",
        "",
        "## 1. Local Binaries",
        "| Binary | Path |",
        "| :--- | :--- |",
    ]
    for name, path in bins.items():
        lines.append(f"| `{name}` | `{path or 'NOT FOUND'}` |")

    lines.extend([
        "",
        "## 2. Global Harness Hooks",
        "| Surface | Config File | Status |",
        "| :--- | :--- | :--- |",
    ])
    for key in ("arize_global", "antigravity", "claude_code", "codex", "gemini_cli_optional"):
        info = harnesses[key]
        lines.append(f"| `{key}` | `{info['path']}` | **{info['status']}** |")

    actions: list[str] = []
    if not bins.get("uv"):
        actions.append("Install `uv`: `brew install uv`")
    if phoenix.get("reachable") is False:
        actions.append("Start Phoenix in a dedicated terminal: `uvx arize-phoenix serve`")
    for h_key, flag in (("antigravity", "antigravity"), ("claude_code", "claude"), ("codex", "codex")):
        if not harnesses[h_key].get("hook_detected"):
            actions.append(
                f"Wire `{flag}` hooks: `curl -sSL https://raw.githubusercontent.com/Arize-ai/coding-harness-tracing/main/install.sh | bash -s -- {flag}`"
            )
    if harnesses["codex"].get("hook_detected"):
        actions.append("Confirm Codex `/hooks` trust approval was granted interactively inside `codex`.")

    lines.extend(["", "## 3. Recommended Next Actions"])
    if actions:
        for item in actions:
            lines.append(f"- {item}")
    else:
        lines.append("- All checks passed. Run a 1-turn smoke prompt per harness and verify spans at `http://localhost:6006`.")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage 01 preflight check for icm-otel.")
    parser.add_argument("--endpoint", default=os.environ.get("PHOENIX_ENDPOINT", DEFAULT_ENDPOINT))
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--skip-network", action="store_true", help="Skip HTTP check to Phoenix.")
    args = parser.parse_args()

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "binaries": check_binaries(),
        "phoenix": check_phoenix_server(args.endpoint, skip_network=args.skip_network),
        "harnesses": check_harness_configs(),
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.output_dir / "env_manifest.json"
    report_path = args.output_dir / "preflight_report.md"

    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(render_report(manifest), encoding="utf-8")

    print(f"Wrote {manifest_path}")
    print(f"Wrote {report_path}")

    phoenix_ok = manifest["phoenix"].get("reachable") is True
    hooks_ok = all(
        manifest["harnesses"][k].get("hook_detected")
        for k in ("antigravity", "claude_code", "codex")
    )
    return 0 if (phoenix_ok and hooks_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
