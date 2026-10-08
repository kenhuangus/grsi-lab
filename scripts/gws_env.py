"""Shared optional GWS env bootstrap for maintainer scripts.

Does not hardcode personal accounts. Set via environment or `.env`:
  GOOGLE_WORKSPACE_CLI_ACCOUNT
  GOOGLE_WORKSPACE_CLI_CONFIG_DIR
  GWS_CMD  — path to gws executable/cmd
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path


def configure_gws_env() -> Path:
    """Ensure GWS env vars are present; return resolved gws command path."""
    if "GOOGLE_WORKSPACE_CLI_CONFIG_DIR" not in os.environ:
        ken_cfg = Path.home() / ".config" / "gws-profiles" / "kenhuangus"
        if ken_cfg.exists():
            os.environ["GOOGLE_WORKSPACE_CLI_CONFIG_DIR"] = str(ken_cfg)
        else:
            default_cfg = Path.home() / ".config" / "gws-profiles" / "default"
            os.environ["GOOGLE_WORKSPACE_CLI_CONFIG_DIR"] = str(default_cfg)
    # Account must be supplied by the operator for publish scripts.
    gws = os.environ.get("GWS_CMD")
    if gws:
        return Path(gws)
    # Prefer the real Windows binary over npm's gws.cmd shim. The .cmd wrapper
    # re-parses --json through cmd.exe and breaks on quotes/newlines in bodies.
    candidates = [
        Path.home()
        / "AppData/Roaming/npm/node_modules/@googleworkspace/cli/bin/gws.exe",
        Path.home() / "AppData/Roaming/npm/gws.cmd",
        Path.home() / "AppData/Roaming/npm/gws",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    which = shutil.which("gws")
    if which:
        return Path(which)
    raise FileNotFoundError(
        "gws CLI not found. Install @googleworkspace/cli and set GWS_CMD if needed."
    )
