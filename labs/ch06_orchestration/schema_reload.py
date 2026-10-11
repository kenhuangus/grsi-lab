"""Schema / structure gates before hot-reload of tool contracts or skill packages."""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from labs.ch06_orchestration.harness_store import HarnessStore


class SchemaReloadError(ValueError):
    """Raised when a candidate package fails schema or AST gates."""


_REQUIRED_TOOL_FIELDS = ("name", "parameters")


@dataclass
class ReloadResult:
    accepted: bool
    reason: str
    schema: dict[str, Any] | None = None
    version: str | None = None


def _validate_tool_schema(schema: dict[str, Any]) -> None:
    if not isinstance(schema, dict):
        raise SchemaReloadError("tool schema must be an object")
    for field in _REQUIRED_TOOL_FIELDS:
        if field not in schema:
            raise SchemaReloadError(f"tool schema missing field: {field}")
    name = schema["name"]
    if not isinstance(name, str) or not name.strip():
        raise SchemaReloadError("tool name must be a non-empty string")
    params = schema["parameters"]
    if not isinstance(params, dict):
        raise SchemaReloadError("parameters must be an object")
    if schema.get("egress") is True and not schema.get("egress_hosts"):
        raise SchemaReloadError("egress tools require declared egress_hosts")
    # Listing eval/held_out under blocked_paths is allowed; writable_paths must not widen into them.
    writable = set(schema.get("writable_paths") or [])
    for path in writable:
        if str(path).startswith(("eval/", "held_out/", "ledger/", "metric_cards/")):
            raise SchemaReloadError(f"tool schema widens into locked path: {path}")


def validate_python_skill(source: str) -> None:
    """AST gate: refuse exec/eval/os.system and top-level network imports used for egress."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise SchemaReloadError(f"skill AST parse failed: {exc}") from exc

    banned_calls = {"exec", "eval", "compile", "__import__"}
    banned_attrs = {"system", "popen", "walk"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in banned_calls:
                raise SchemaReloadError(f"banned call in skill: {func.id}")
            if isinstance(func, ast.Attribute) and func.attr in banned_attrs:
                raise SchemaReloadError(f"banned attribute call in skill: {func.attr}")
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in {"socket", "subprocess", "ctypes"}:
                    raise SchemaReloadError(f"banned import in skill: {alias.name}")
        if isinstance(node, ast.ImportFrom) and node.module in {
            "socket",
            "subprocess",
            "ctypes",
        }:
            raise SchemaReloadError(f"banned import in skill: {node.module}")


def reload_tool_schema(
    schema: dict[str, Any] | str,
    *,
    skill_source: str | None = None,
    store: HarnessStore | None = None,
) -> ReloadResult:
    """Validate and accept a tool schema (and optional skill source) for hot-reload.

    When ``store`` is provided, the accepted schema version is persisted on the
    harness store so later mutate calls can require registration.
    """
    if isinstance(schema, str):
        try:
            schema = json.loads(schema)
        except json.JSONDecodeError as exc:
            raise SchemaReloadError(f"invalid JSON tool schema: {exc}") from exc
    if not isinstance(schema, dict):
        raise SchemaReloadError("tool schema must be an object")

    _validate_tool_schema(schema)
    if skill_source is not None:
        validate_python_skill(skill_source)

    version: str | None = None
    if store is not None:
        version = store.register_schema(dict(schema))

    return ReloadResult(
        True,
        "schema reload accepted",
        schema=dict(schema),
        version=version,
    )
