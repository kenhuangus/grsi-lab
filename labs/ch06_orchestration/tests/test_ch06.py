"""Accept + refuse paths for Chapter 6 orchestration lab."""

from __future__ import annotations

import pytest

from labs.ch06_orchestration.ablation import run_module_ablation
from labs.ch06_orchestration.bi_level_loop import BiLevelLoop, make_fixture_scorer
from labs.ch06_orchestration.harness_store import HarnessStore
from labs.ch06_orchestration.role_graph import RoleGraph, RoleSpec
from labs.ch06_orchestration.schema_reload import SchemaReloadError, reload_tool_schema


def test_harness_mutate_rollback_accept() -> None:
    store = HarnessStore(modules={"planner": {"lr": 0.1}})
    store.mutate("planner", {"lr": 0.9})
    assert store.modules["planner"]["lr"] == 0.9
    store.rollback("planner")
    assert store.modules["planner"]["lr"] == 0.1


def test_harness_refuse_unknown_module() -> None:
    store = HarnessStore(modules={"planner": {"lr": 0.1}})
    with pytest.raises(KeyError, match="Unknown module"):
        store.mutate("missing", {"lr": 1.0})


def test_harness_refuse_empty_patch() -> None:
    store = HarnessStore(modules={"planner": {"lr": 0.1}})
    with pytest.raises(ValueError, match="empty patch"):
        store.mutate("planner", {})


def test_harness_strips_self_score_fields() -> None:
    store = HarnessStore(modules={"planner": {"prompt": "base"}})
    with pytest.raises(ValueError, match="self-score"):
        store.mutate("planner", {"held_out": 0.99})
    store.mutate("planner", {"prompt": "better", "held_out": 0.99})
    assert store.modules["planner"]["prompt"] == "better"
    assert "held_out" not in store.modules["planner"]


def test_schema_reload_accept() -> None:
    store = HarnessStore()
    result = reload_tool_schema(
        {"name": "search", "parameters": {"q": {"type": "string"}}},
        skill_source="def run(q: str) -> str:\n    return q\n",
        store=store,
    )
    assert result.accepted is True
    assert result.version
    assert store.accepted_schema_version == result.version
    assert "search" in store.registered_schemas


def test_schema_reload_refuse_locked_writable() -> None:
    with pytest.raises(SchemaReloadError, match="locked path"):
        reload_tool_schema(
            {
                "name": "evil",
                "parameters": {},
                "writable_paths": ["held_out/labels.jsonl"],
            }
        )


def test_schema_reload_refuse_banned_skill() -> None:
    with pytest.raises(SchemaReloadError, match="banned"):
        reload_tool_schema(
            {"name": "x", "parameters": {}},
            skill_source="import subprocess\n",
        )


def test_mutate_refuse_when_schema_required_but_missing() -> None:
    store = HarnessStore(
        modules={"planner": {"prompt": "base"}},
        require_registered_schema=True,
    )
    with pytest.raises(ValueError, match="schema not registered"):
        store.mutate("planner", {"prompt": "better"})


def test_bi_level_keep_with_ablation() -> None:
    fixtures = {"base": 0.50, "better": 0.58}
    store = HarnessStore(
        modules={"planner": {"prompt": "base"}},
        backbone_pin="bb-1",
        require_registered_schema=True,
    )
    loop = BiLevelLoop(
        store,
        make_fixture_scorer(fixtures),
        noise_floor=0.01,
        max_policy_tokens=64,
    )
    result = loop.propose_and_evaluate(
        "planner",
        {"prompt": "better", "held_out": 0.99},
        tool_schema={"name": "search", "parameters": {}},
        backbone_pin="bb-1",
    )
    assert result.kept is True
    assert result.ablation is not None and result.ablation.passed
    assert "held_out" not in store.modules["planner"]
    assert store.accepted_schema_version is not None


def test_bi_level_refuse_noise_floor() -> None:
    fixtures = {"base": 0.50, "nudge": 0.52}
    store = HarnessStore(modules={"planner": {"prompt": "base"}}, backbone_pin="bb-1")
    loop = BiLevelLoop(
        store,
        make_fixture_scorer(fixtures),
        noise_floor=0.05,
        require_ablation=False,
    )
    result = loop.propose_and_evaluate(
        "planner",
        {"prompt": "nudge"},
        backbone_pin="bb-1",
    )
    assert result.kept is False
    assert "noise floor" in result.reason
    assert store.modules["planner"]["prompt"] == "base"


def test_bi_level_refuse_self_score_only_patch() -> None:
    fixtures = {"base": 0.50}
    store = HarnessStore(modules={"planner": {"prompt": "base"}}, backbone_pin="bb-1")
    loop = BiLevelLoop(
        store,
        make_fixture_scorer(fixtures),
        require_ablation=False,
    )
    result = loop.propose_and_evaluate(
        "planner",
        {"held_out": 0.99},
        backbone_pin="bb-1",
    )
    assert result.kept is False
    assert "self-score" in result.reason


def test_bi_level_refuse_token_ceiling() -> None:
    fixtures = {"base": 0.50, "huge": 0.90}
    store = HarnessStore(modules={"planner": {"prompt": "base"}}, backbone_pin="bb-1")
    loop = BiLevelLoop(
        store,
        make_fixture_scorer(fixtures),
        require_ablation=False,
        max_policy_tokens=3,
    )
    result = loop.propose_and_evaluate(
        "planner",
        {"prompt": "one two three four five six"},
        backbone_pin="bb-1",
    )
    assert result.kept is False
    assert "token ceiling" in result.reason
    assert store.modules["planner"]["prompt"] == "base"


def test_bi_level_refuse_backbone_pin_change() -> None:
    fixtures = {"base": 0.50, "better": 0.9}
    store = HarnessStore(modules={"planner": {"prompt": "base"}}, backbone_pin="bb-1")
    loop = BiLevelLoop(
        store,
        make_fixture_scorer(fixtures),
        require_ablation=False,
    )
    result = loop.propose_and_evaluate(
        "planner",
        {"prompt": "better"},
        backbone_pin="bb-2",
    )
    assert result.kept is False
    assert "backbone pin" in result.reason


def test_ablation_refuse_without_snapshot() -> None:
    fixtures = {"base": 0.5}
    store = HarnessStore(modules={"planner": {"prompt": "base"}})
    report = run_module_ablation(store, ["planner"], make_fixture_scorer(fixtures))
    assert report.passed is False
    assert "missing snapshot" in report.reason


def test_ablation_uses_external_fixture_not_held_out() -> None:
    fixtures = {"base": 0.50, "better": 0.60}
    store = HarnessStore(modules={"planner": {"prompt": "base"}})
    store.mutate("planner", {"prompt": "better", "held_out": 0.01})
    report = run_module_ablation(
        store,
        ["planner"],
        make_fixture_scorer(fixtures),
        min_attributable_delta=0.01,
    )
    assert report.passed is True
    assert report.rows[0].full_score == 0.60
    assert report.rows[0].ablated_score == 0.50


def test_role_graph_accept_and_wake() -> None:
    graph = RoleGraph()
    graph.add_role(
        RoleSpec(
            role_id="chief",
            package_path="roles/chief",
            eval_hook="eval/chief",
            rollback_unit="roles.chief",
            instructions="chief",
        )
    )
    graph.add_role(
        RoleSpec(
            role_id="specialist_repo_search",
            package_path="roles/search",
            eval_hook="eval/search",
            rollback_unit="roles.search",
            instructions="search",
            allowed_tools=["repo_search"],
        )
    )
    graph.declare_wake("chief", ["specialist_repo_search"])
    assert graph.can_wake("chief", "specialist_repo_search")
    assert not graph.detect_role_collapse()["collapsed"]


def test_role_graph_refuse_undeclared_merge() -> None:
    graph = RoleGraph()
    for rid in ("chief", "specialist"):
        graph.add_role(
            RoleSpec(
                role_id=rid,
                package_path=f"roles/{rid}",
                eval_hook=f"eval/{rid}",
                rollback_unit=f"roles.{rid}",
                instructions=rid,
            )
        )
    out = graph.merge_roles("chief", "specialist", declared=False)
    assert out["ok"] is False
    assert "undeclared" in out["reason"]
