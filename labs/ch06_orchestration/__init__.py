"""Chapter 6 lab — harness mutate, bi-level loop, schema reload, ablation, role graph."""

from labs.ch06_orchestration.ablation import AblationReport, run_module_ablation
from labs.ch06_orchestration.bi_level_loop import (
    BiLevelLoop,
    BiLevelResult,
    make_fixture_scorer,
    strip_self_score_fields,
)
from labs.ch06_orchestration.harness_store import HarnessStore, ModuleSnapshot
from labs.ch06_orchestration.role_graph import RoleGraph, RoleSpec
from labs.ch06_orchestration.schema_reload import SchemaReloadError, reload_tool_schema

__all__ = [
    "HarnessStore",
    "ModuleSnapshot",
    "BiLevelLoop",
    "BiLevelResult",
    "make_fixture_scorer",
    "strip_self_score_fields",
    "reload_tool_schema",
    "SchemaReloadError",
    "run_module_ablation",
    "AblationReport",
    "RoleGraph",
    "RoleSpec",
]
