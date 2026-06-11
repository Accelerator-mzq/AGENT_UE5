# -*- coding: utf-8 -*-
"""SKS-14/15: anchor 强制留痕(合成开启时)与 synthesized run promote 拦截。

隔离约束:
  - 集成测试 monkeypatch pipeline_orchestrator.PROJECT_RUNS_DIR 到 tmp_path,
    防止 v2 save_stage 把产物写进真实 ProjectState/runs(文件末尾 zz 守卫兜底);
  - promote 守卫只测纯函数 + _evaluate_promotable 接线,不走真实 batch 落盘。
"""
import importlib
import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
MCP_DIR = PLUGIN_ROOT / "MCP"
# 真实 run 产物根:任何测试都不允许在这里留下残留(zz 守卫用)
REAL_RUNS_DIR = PLUGIN_ROOT.parents[1] / "ProjectState" / "runs"
_RUNS_BEFORE = sorted(p.name for p in REAL_RUNS_DIR.iterdir()) if REAL_RUNS_DIR.exists() else []


class TestAnchorEnforcement:
    def test_sks14_missing_anchor_listed(self):
        """SKS-14: 纯函数 _capabilities_missing_anchor 列出无出处能力。"""
        sys.path.insert(0, str(PLUGIN_ROOT / "MCP"))
        try:
            import compiler_tools
            importlib.reload(compiler_tools)
            contract = {
                "gameplay_capabilities": [
                    {"capability_id": "gameplay-a", "activation": "required",
                     "source_anchor": "2.1 棋盘"},
                    {"capability_id": "gameplay-b", "activation": "required"},
                    {"capability_id": "gameplay-c", "activation": "optional"},
                ],
                "baseline_capabilities": [
                    {"capability_id": "baseline-x", "activation": "required",
                     "source_anchor": ""},
                ],
            }
            missing = compiler_tools._capabilities_missing_anchor(contract)
            assert missing == ["baseline-x", "gameplay-b"]
        finally:
            sys.path.remove(str(PLUGIN_ROOT / "MCP"))


class TestPromoteGuard:
    def test_sks15_synthesized_graph_refused(self, tmp_path):
        """SKS-15: skill_graph 含 synthesized 节点时 promote 守卫拒绝。"""
        sys.path.insert(0, str(PLUGIN_ROOT / "MCP"))
        try:
            import evidence_tools
            importlib.reload(evidence_tools)
            run_dir = tmp_path / "run-x"
            run_dir.mkdir()
            (run_dir / "skill_graph.json").write_text(json.dumps({
                "nodes": [{"instance_id": "skill-auction", "template_source": "synthesized"}],
                "metadata": {},
            }), encoding="utf-8")
            reasons = evidence_tools._synthesized_promote_blockers(run_dir)
            assert reasons and "synthesized" in reasons[0]
        finally:
            sys.path.remove(str(PLUGIN_ROOT / "MCP"))

    def test_sks15b_unresolved_gaps_refused(self, tmp_path):
        """SKS-15b: 合成关闭/未完成时 gap 保留的 run 同样被 promote 守卫拒绝。"""
        sys.path.insert(0, str(PLUGIN_ROOT / "MCP"))
        try:
            import evidence_tools
            importlib.reload(evidence_tools)
            run_dir = tmp_path / "run-y"
            run_dir.mkdir()
            (run_dir / "skill_graph.json").write_text(json.dumps({
                "nodes": [],
                "metadata": {"capability_gaps": [
                    {"capability_id": "gameplay-auction", "domain_type": "gameplay",
                     "reason": "no_template"}
                ]},
            }), encoding="utf-8")
            reasons = evidence_tools._synthesized_promote_blockers(run_dir)
            assert reasons and "capability_gaps" in reasons[0]
        finally:
            sys.path.remove(str(PLUGIN_ROOT / "MCP"))

    def test_sks15c_clean_or_missing_graph_not_blocked(self, tmp_path):
        """SKS-15c: 干净 graph(官方节点+零 gap)与缺 graph 文件都不触发守卫。"""
        sys.path.insert(0, str(PLUGIN_ROOT / "MCP"))
        try:
            import evidence_tools
            importlib.reload(evidence_tools)
            run_dir = tmp_path / "run-clean"
            run_dir.mkdir()
            (run_dir / "skill_graph.json").write_text(json.dumps({
                "nodes": [{"instance_id": "skill-board", "template_source": "official"}],
                "metadata": {"capability_gaps": []},
            }), encoding="utf-8")
            assert evidence_tools._synthesized_promote_blockers(run_dir) == []
            assert evidence_tools._synthesized_promote_blockers(tmp_path / "run-nope") == []
        finally:
            sys.path.remove(str(PLUGIN_ROOT / "MCP"))

    def test_sks15e_corrupted_graph_fail_closed(self, tmp_path, monkeypatch):
        """SKS-15e: skill_graph.json 损坏时 fail-closed——不可判定即不许 promote,
        走 PROMOTE_REJECTED 拒绝路径而非 TOOL_EXECUTION_FAILED。"""
        sys.path.insert(0, str(PLUGIN_ROOT / "MCP"))
        try:
            import evidence_tools
            importlib.reload(evidence_tools)
            # 防止 _create_batch_from_snapshot 污染真实 ProjectState/batches/
            monkeypatch.setattr(evidence_tools, "BATCHES_ROOT", tmp_path / "batches")
            run_dir = tmp_path / "run-broken"
            run_dir.mkdir()
            (run_dir / "skill_graph.json").write_text("{损坏的 JSON", encoding="utf-8")

            # 纯函数:返回带路径的拒绝理由,不抛异常
            reasons = evidence_tools._synthesized_promote_blockers(run_dir)
            assert reasons and "损坏不可判定" in reasons[0]
            assert "skill_graph.json" in reasons[0]

            # promote 主流程:同样的早退拒绝路径(零 batch 落盘副作用)
            snapshot = {
                "run_id": "run-20260611-000000-abcd",
                "run_dir": run_dir,
                "fast_mode": False,
                "status": "completed",
                "constraint_violations": 0,
                "pipeline_stages_completed": [1, 2, 3, 4, 5, 6, 7],
                "session_version": "2.0",
                "generator_provider": "llm",
                "metadata_promotable": True,
            }
            result = evidence_tools._create_batch_from_snapshot(
                snapshot, "pytest", "", False, False
            )
            assert result["status"] == "failed"
            assert any(
                error.startswith("PROMOTE_REJECTED") and "损坏不可判定" in error
                for error in result["errors"]
            ), result["errors"]
            assert not any("TOOL_EXECUTION_FAILED" in error for error in result["errors"])
        finally:
            sys.path.remove(str(PLUGIN_ROOT / "MCP"))

    def test_sks15d_guard_wired_into_evaluate_promotable(self, tmp_path):
        """SKS-15d: 守卫接进 _evaluate_promotable(与 fast_mode/heuristic 同一拒绝路径)。"""
        sys.path.insert(0, str(PLUGIN_ROOT / "MCP"))
        try:
            import evidence_tools
            importlib.reload(evidence_tools)
            run_dir = tmp_path / "run-z"
            run_dir.mkdir()
            (run_dir / "skill_graph.json").write_text(json.dumps({
                "nodes": [{"instance_id": "skill-auction", "template_source": "synthesized"}],
                "metadata": {},
            }), encoding="utf-8")
            # 除合成轴外全部满足 promote 条件:守卫必须是唯一拒绝原因
            snapshot = {
                "run_id": "run-20260611-000000-abcd",
                "run_dir": run_dir,
                "fast_mode": False,
                "status": "completed",
                "constraint_violations": 0,
                "pipeline_stages_completed": [1, 2, 3, 4, 5, 6, 7],
                "session_version": "2.0",
                "generator_provider": "llm",
                "metadata_promotable": True,
            }
            verdict = evidence_tools._evaluate_promotable(snapshot)
            assert verdict["promotable"] is False
            assert any("synthesized" in reason for reason in verdict["reasons"])
        finally:
            sys.path.remove(str(PLUGIN_ROOT / "MCP"))


# ---------------------------------------------------------------------------
# handler 级集成测试公共构造(照 test_phase13_mcp_synthesis_tools 的 _make_run 模式)
# ---------------------------------------------------------------------------

GDD_TEXT = (
    "# 测试 GDD\n"
    "\n"
    "## 2.1 棋盘\n"
    "四十格环形棋盘。\n"
    "\n"
    "## 2.2 计分\n"
    "积分制胜负。\n"
)


def _import_compiler_tools():
    """导入 MCP/compiler_tools(MCP 目录不在默认 sys.path,需手动注入)。"""
    if str(MCP_DIR) not in sys.path:
        sys.path.insert(0, str(MCP_DIR))
    import compiler_tools
    return compiler_tools


def _make_stage1_session(tmp_path, monkeypatch, allow_synthesis):
    """造最小 v2 session,并把 v2 run 产物根重定向到 tmp(防真实树污染)。

    compiler_tools 顶部 `from Compiler.pipeline.pipeline_orchestrator import
    save_stage`——save_stage 运行时读模块全局 PROJECT_RUNS_DIR,patch 同一
    sys.modules 实例即对 handler 生效。返回 (session_path, run_dir)。
    """
    if str(PLUGIN_ROOT) not in sys.path:
        sys.path.insert(0, str(PLUGIN_ROOT))
    from Compiler.pipeline import pipeline_orchestrator
    from Compiler.pipeline.session import create_session

    runs_root = tmp_path / "runs"
    monkeypatch.setattr(pipeline_orchestrator, "PROJECT_RUNS_DIR", runs_root)

    gdd_path = tmp_path / "gdd.md"
    gdd_path.write_text(GDD_TEXT, encoding="utf-8")
    session = create_session(
        str(gdd_path), "phase13_anchor_test", str(tmp_path / "session_out"),
        session_version="2.0",
    )
    session.allow_skill_synthesis = allow_synthesis
    session_path = session.save()
    return session_path, runs_root / session.run_id


def _valid_contract(anchors=None):
    """最小合法 root skill contract;anchors = capability_id→source_anchor 映射。"""
    anchors = anchors or {}

    def _extra(capability_id):
        return (
            {"source_anchor": anchors[capability_id]}
            if capability_id in anchors else {}
        )

    return {
        "contract_version": "1.0",
        "contract_id": "rsc.testgame.phase1.20260611",
        "source_gdd": {"file_path": "gdd.md", "scope_summary": "测试用最小 GDD"},
        "game_identity": {
            "game_type": "board_game",
            "subgenre": "test",
            "presentation_model": "2d",
            "player_count_range": [2, 4],
            "win_condition": "score",
        },
        "phase_scope": {"current_phase": "phase1", "in_scope": [], "out_of_scope": []},
        "constraint_fields": {},
        "variant_fields": {},
        "baseline_capabilities": [
            {"capability_id": "baseline-x", "activation": "required",
             "realization_class": "presence_only", **_extra("baseline-x")},
        ],
        "gameplay_capabilities": [
            {"capability_id": "gameplay-a", "activation": "required",
             "allows_design_space_discovery": True, **_extra("gameplay-a")},
        ],
        "metadata": {"generated_at": "2026-06-11T00:00:00+00:00", "generator": "pytest"},
    }


class TestRootSkillSaveHandler:
    def test_synthesis_on_missing_anchor_failed_nothing_saved(self, tmp_path, monkeypatch):
        """合成开启 + 缺 anchor:failed 列出清单,且零落盘。"""
        ct = _import_compiler_tools()
        session_path, run_dir = _make_stage1_session(tmp_path, monkeypatch, True)
        result = ct.compiler_root_skill_save(session_path, _valid_contract())
        assert result["status"] == "failed", result
        assert result["data"]["capabilities_missing_anchor"] == ["baseline-x", "gameplay-a"]
        assert any("source_anchor" in error for error in result["errors"])
        assert not (run_dir / "root_skill_contract.json").exists(), "强制失败必须发生在落盘前"

    def test_synthesis_off_missing_anchor_success_with_warning(self, tmp_path, monkeypatch):
        """合成关闭 + 缺 anchor:降级 warning,保存正常(既有测试不破的关键开关)。"""
        ct = _import_compiler_tools()
        session_path, run_dir = _make_stage1_session(tmp_path, monkeypatch, False)
        result = ct.compiler_root_skill_save(session_path, _valid_contract())
        assert result["status"] == "success", result
        assert any("source_anchor" in warning for warning in result["warnings"]), result["warnings"]
        assert (run_dir / "root_skill_contract.json").is_file()

    def test_full_anchor_success_writes_coverage_matrix(self, tmp_path, monkeypatch):
        """带全 anchor:success,run 目录出现矩阵 JSON + md,结构与 gdd_coverage 输出一致。"""
        ct = _import_compiler_tools()
        session_path, run_dir = _make_stage1_session(tmp_path, monkeypatch, True)
        contract = _valid_contract({"gameplay-a": "2.1 棋盘", "baseline-x": "2.2 计分"})
        result = ct.compiler_root_skill_save(session_path, contract)
        assert result["status"] == "success", result
        assert not any("source_anchor" in warning for warning in result["warnings"])

        matrix_path = run_dir / "gdd_coverage_matrix.json"
        assert matrix_path.is_file(), "覆盖矩阵 JSON 未落盘"
        assert (run_dir / "gdd_coverage_matrix.md").is_file(), "覆盖矩阵 markdown 未落盘"

        # 矩阵结构必须与 gdd_coverage 直接输出逐字段一致(sidecar 不二次加工)
        from Compiler.stages import gdd_coverage
        expected = gdd_coverage.build_coverage_matrix(
            gdd_coverage.split_gdd_sections(GDD_TEXT),
            contract["gameplay_capabilities"] + contract["baseline_capabilities"],
        )
        matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
        assert matrix == expected
        assert matrix["capabilities_without_anchor"] == []
        assert matrix["dangling_anchors"] == []
        assert matrix["unclaimed_count"] == 0

    def test_matrix_failure_degrades_to_warning(self, tmp_path, monkeypatch):
        """gdd_path 不可读:保存仍 success,矩阵降级 warning,不落矩阵文件。"""
        ct = _import_compiler_tools()
        session_path, run_dir = _make_stage1_session(tmp_path, monkeypatch, True)
        (tmp_path / "gdd.md").unlink()  # 模拟 GDD 不可读
        contract = _valid_contract({"gameplay-a": "2.1 棋盘", "baseline-x": "2.2 计分"})
        result = ct.compiler_root_skill_save(session_path, contract)
        assert result["status"] == "success", result
        assert any("覆盖矩阵生成失败" in warning for warning in result["warnings"]), result["warnings"]
        assert (run_dir / "root_skill_contract.json").is_file(), "矩阵失败不得阻塞契约落盘"
        assert not (run_dir / "gdd_coverage_matrix.json").exists()


class TestIntakeAliasForwarding:
    def test_alias_enforces_anchor_same_as_root_skill(self, tmp_path, monkeypatch):
        """I-1: compiler_intake_save(v2)必须与正名工具同享 anchor 强制——
        合成开启 + 缺 anchor 经 alias 同样 failed 且零落盘(封死绕行通道)。"""
        ct = _import_compiler_tools()
        session_path, run_dir = _make_stage1_session(tmp_path, monkeypatch, True)
        result = ct.compiler_intake_save(session_path, _valid_contract())
        assert result["status"] == "failed", result
        assert result["data"]["capabilities_missing_anchor"] == ["baseline-x", "gameplay-a"]
        assert not (run_dir / "root_skill_contract.json").exists(), "alias 绕行通道未封死"
        # 文案保留 alias 自己的 action_name(v1 调用方语义不变)
        assert "Stage 1 保存" in result["summary"], result["summary"]

    def test_alias_full_anchor_saves_matrix_too(self, tmp_path, monkeypatch):
        """I-1 补充: alias 成功路径同样落盘覆盖矩阵 sidecar。"""
        ct = _import_compiler_tools()
        session_path, run_dir = _make_stage1_session(tmp_path, monkeypatch, True)
        contract = _valid_contract({"gameplay-a": "2.1 棋盘", "baseline-x": "2.2 计分"})
        result = ct.compiler_intake_save(session_path, contract)
        assert result["status"] == "success", result
        assert (run_dir / "gdd_coverage_matrix.json").is_file()
        assert (run_dir / "gdd_coverage_matrix.md").is_file()


class TestCreateSessionSynthesisSwitch:
    def test_mcp_create_session_switch_persists_and_enforces(self, tmp_path, monkeypatch):
        """I-2: 经 MCP compiler_create_session 开启开关 → session.json 持久化 true、
        data 回显,且后续 root_skill_save 强制生效(验收 runbook 第 1 步可经 MCP 完成)。"""
        ct = _import_compiler_tools()
        if str(PLUGIN_ROOT) not in sys.path:
            sys.path.insert(0, str(PLUGIN_ROOT))
        from Compiler.pipeline import pipeline_orchestrator
        monkeypatch.setattr(pipeline_orchestrator, "PROJECT_RUNS_DIR", tmp_path / "runs")

        gdd_path = tmp_path / "gdd.md"
        gdd_path.write_text(GDD_TEXT, encoding="utf-8")
        created = ct.compiler_create_session(
            str(gdd_path), "phase13_anchor_test", str(tmp_path / "session_out"),
            session_version="2.0", allow_skill_synthesis=True,
        )
        assert created["status"] == "success", created
        assert created["data"]["allow_skill_synthesis"] is True

        session_path = created["data"]["session_path"]
        session_payload = json.loads(Path(session_path).read_text(encoding="utf-8"))
        assert session_payload.get("allow_skill_synthesis") is True

        result = ct.compiler_root_skill_save(session_path, _valid_contract())
        assert result["status"] == "failed", "MCP 开启开关后 anchor 强制必须生效"
        assert result["data"]["capabilities_missing_anchor"] == ["baseline-x", "gameplay-a"]

    def test_mcp_create_session_default_off(self, tmp_path):
        """I-2 补充: 不传参数默认 False,回显与持久化均为关闭(老调用方不变)。"""
        ct = _import_compiler_tools()
        gdd_path = tmp_path / "gdd.md"
        gdd_path.write_text(GDD_TEXT, encoding="utf-8")
        created = ct.compiler_create_session(
            str(gdd_path), "phase13_anchor_test", str(tmp_path / "session_out"),
            session_version="2.0",
        )
        assert created["status"] == "success", created
        assert created["data"]["allow_skill_synthesis"] is False
        session_payload = json.loads(
            Path(created["data"]["session_path"]).read_text(encoding="utf-8")
        )
        assert "allow_skill_synthesis" not in session_payload, "默认关闭不序列化,旧 session 字节级不变"


def test_zz_real_runs_dir_no_residue():
    """全部用例跑完后,真实 ProjectState/runs 必须无新增残留(测试不污染真实树)。"""
    runs_after = sorted(p.name for p in REAL_RUNS_DIR.iterdir()) if REAL_RUNS_DIR.exists() else []
    assert runs_after == _RUNS_BEFORE, f"真实 runs 目录被污染: {set(runs_after) - set(_RUNS_BEFORE)}"
