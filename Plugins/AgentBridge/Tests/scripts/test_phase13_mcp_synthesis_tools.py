# -*- coding: utf-8 -*-
"""SKS-11: MCP 合成工具对注册完整(定义/分发/handler 三处)+ handler 集成测试。

集成测试隔离约束:绝不污染真实 SkillTemplates 模板树——合法包落盘前用
monkeypatch 把 handler 实际使用的 skill_synthesis 模块实例(包导入
Compiler.stages.skill_synthesis,与 handler 顶部 import 是同一 sys.modules
实例)的 DEFAULT_TEMPLATES_ROOT 指到 tmp_path;文件末尾的 test_zz_* 守卫
断言真实树无 synthesized/ 残留。

server.py 的 TOOL_DISPATCH 不在此 import 验证——import server 可能拉起
Bridge 重依赖,分发登记由任务 Step 4 的 grep 验证。
"""
import importlib.util
import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
MCP_DIR = PLUGIN_ROOT / "MCP"
# 真实模板树的 synthesized 隔离区:任何测试都不允许在这里留下残留
REAL_SYNTHESIZED_DIR = PLUGIN_ROOT / "SkillTemplates" / "synthesized"


# ---------------------------------------------------------------------------
# SKS-11: 三处注册检查(定义 + handler;分发由 grep 验证)
# ---------------------------------------------------------------------------

def test_sks11_tools_registered():
    sys.path.insert(0, str(MCP_DIR))
    try:
        import tool_definitions
        importlib.reload(tool_definitions)
        assert "compiler_skill_synthesis_prepare" in tool_definitions.ALL_TOOLS
        assert "compiler_skill_synthesis_save" in tool_definitions.ALL_TOOLS
        # TOOL_COUNT 自动等于 ALL_TOOLS 长度(无漏登记)
        assert tool_definitions.TOOL_COUNT == len(tool_definitions.ALL_TOOLS)
        import compiler_tools
        importlib.reload(compiler_tools)
        assert callable(compiler_tools.compiler_skill_synthesis_prepare)
        assert callable(compiler_tools.compiler_skill_synthesis_save)
    finally:
        sys.path.remove(str(MCP_DIR))


# ---------------------------------------------------------------------------
# 集成测试公共构造
# ---------------------------------------------------------------------------

def _import_compiler_tools():
    """导入 MCP/compiler_tools(MCP 目录不在默认 sys.path,需手动注入)。"""
    if str(MCP_DIR) not in sys.path:
        sys.path.insert(0, str(MCP_DIR))
    import compiler_tools
    return compiler_tools


def _import_skill_synthesis():
    """导入 handler 实际使用的 skill_synthesis 包模块实例(monkeypatch 注入用)。

    compiler_tools 顶部 `from Compiler.stages import skill_synthesis`——这里
    返回的是同一 sys.modules 实例,patch 其属性对 handler 立即生效。
    """
    if str(PLUGIN_ROOT) not in sys.path:
        sys.path.insert(0, str(PLUGIN_ROOT))
    from Compiler.stages import skill_synthesis
    return skill_synthesis


def _legal_package():
    """复用校验器测试的最小合法 6 文件包构造,避免两份测试漂移。"""
    spec = importlib.util.spec_from_file_location(
        "vt", Path(__file__).resolve().parent / "test_phase13_synthesis_validator.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._legal_package()


def _make_run(tmp_path):
    """用现行 create_session 真实结构造最小 run 目录。

    v2.0 session + 手动登记 stage_1/stage_3 产物路径(模拟 Stage 1/3 已完成),
    与 save_stage 的登记方式同构(stage_outputs["stage_N"] = 产物绝对路径)。
    skill_graph 带一条 capability gap(含 source_anchor,覆盖 gdd_coverage
    未就绪的兜底路径)。返回 (session_path, run_dir)。
    """
    if str(PLUGIN_ROOT) not in sys.path:
        sys.path.insert(0, str(PLUGIN_ROOT))
    from Compiler.pipeline.session import create_session

    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    gdd_path = tmp_path / "gdd.md"
    gdd_path.write_text("## 2.4 地产拍卖\n玩家拒购时地产进入英式拍卖。\n", encoding="utf-8")

    skill_graph = {
        "metadata": {
            "capability_gaps": [
                {
                    "capability_id": "gameplay-auction",
                    "domain_type": "gameplay",
                    "reason": "no_template",
                    "source_anchor": "2.4 地产拍卖",
                }
            ]
        },
        "nodes": [],
        "edges": [],
    }
    graph_path = run_dir / "skill_graph.json"
    graph_path.write_text(json.dumps(skill_graph, ensure_ascii=False), encoding="utf-8")

    contract = {
        "constraint_fields": {
            "game.max_players": {"type": "constraint", "value": 6, "gdd_ref": "GDD 1 玩家人数"}
        }
    }
    contract_path = run_dir / "root_skill_contract.json"
    contract_path.write_text(json.dumps(contract, ensure_ascii=False), encoding="utf-8")

    session = create_session(
        str(gdd_path), "phase13_synthesis_test", str(run_dir), session_version="2.0"
    )
    session.stage_outputs["stage_1"] = str(contract_path)
    session.stage_outputs["stage_3"] = str(graph_path)
    session_path = session.save()
    return session_path, run_dir


def _make_official_manifest(templates_root: Path) -> None:
    """造一个正式库 manifest 提供 family 白名单。

    save handler 不传 family_whitelist,默认白名单来自对模板根的正式库扫描;
    tmp 模板根必须自带一个宣告 property_economy_spec 的人写模板,合法包才能过白名单。
    """
    pack_dir = templates_root / "baseline" / "example"
    pack_dir.mkdir(parents=True, exist_ok=True)
    (pack_dir / "manifest.yaml").write_text(
        "template_id: human.example.v1\ncan_emit_families:\n  - property_economy_spec\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# prepare handler 集成测试
# ---------------------------------------------------------------------------

class TestSynthesisPrepareHandler:
    def test_prepare_success_payload_fields_complete(self, tmp_path):
        """合法 gap:success 且载荷字段齐全;gdd_coverage 未就绪时摘录为空 + warning。"""
        ct = _import_compiler_tools()
        session_path, _run_dir = _make_run(tmp_path)
        result = ct.compiler_skill_synthesis_prepare(session_path, "gameplay-auction")
        assert result["status"] == "success", result
        payload = result["data"]
        for key in (
            "capability_id", "gap", "gdd_excerpt", "constraints", "file_spec",
            "exemplars", "family_whitelist", "naming_rules", "instructions",
        ):
            assert key in payload, f"载荷缺字段 {key}: {sorted(payload)}"
        assert payload["capability_id"] == "gameplay-auction"
        assert payload["gap"]["source_anchor"] == "2.4 地产拍卖"
        assert payload["constraints"]["game.max_players"]["value"] == 6
        assert "manifest.yaml" in payload["file_spec"]
        # gdd_coverage 是 Task 9 模块,当前未落地:摘录置空 + warning 提示
        # 注意:Task 9(gdd_coverage)落地后本断言需翻转为非空摘录
        # (anchor "2.4 地产拍卖" 应命中 _make_run 写入的 GDD 章节)——
        # 属预期 break,Task 9 执行者按此修,勿当回归 bug 处理。
        assert payload["gdd_excerpt"] == ""
        assert any("gdd_coverage" in w for w in result["warnings"]), result["warnings"]
        # 白名单来自真实正式库(只读扫描),应含既有 family
        assert "property_economy_spec" in payload["family_whitelist"]

    def test_prepare_unknown_capability_failed_with_known_gaps(self, tmp_path):
        """capability_id 不在 gaps:failed 且 data 给出 known_gaps 列表。"""
        ct = _import_compiler_tools()
        session_path, _run_dir = _make_run(tmp_path)
        result = ct.compiler_skill_synthesis_prepare(session_path, "gameplay-ghost")
        assert result["status"] == "failed"
        assert result["data"]["known_gaps"] == ["gameplay-auction"]
        assert result["errors"], "期望非空 errors"

    def test_prepare_missing_session_failed(self, tmp_path):
        """session.json 不存在:failed(照抄现行 _missing_file_response 语义)。"""
        ct = _import_compiler_tools()
        result = ct.compiler_skill_synthesis_prepare(
            str(tmp_path / "nope" / "session.json"), "gameplay-auction"
        )
        assert result["status"] == "failed"
        assert any("FILE_NOT_FOUND" in e for e in result["errors"])

    def test_prepare_missing_skill_graph_failed(self, tmp_path):
        """Stage 3 产物未登记:failed + PREREQUISITE_MISSING(先完成 Stage 3)。"""
        ct = _import_compiler_tools()
        session_path, run_dir = _make_run(tmp_path)
        (run_dir / "skill_graph.json").unlink()  # 登记还在,文件已不存在
        result = ct.compiler_skill_synthesis_prepare(session_path, "gameplay-auction")
        assert result["status"] == "failed"
        assert any("skill_graph" in e for e in result["errors"])


# ---------------------------------------------------------------------------
# save handler 集成测试
# ---------------------------------------------------------------------------

class TestSynthesisSaveHandler:
    def test_save_rejected_maps_to_failed_with_errors(self, tmp_path, monkeypatch):
        """非法包(缺件):rejected 透传为 failed + errors 非空,零落盘。"""
        ct = _import_compiler_tools()
        session_path, _run_dir = _make_run(tmp_path)
        templates_root = tmp_path / "templates"
        _make_official_manifest(templates_root)
        synth = _import_skill_synthesis()
        monkeypatch.setattr(synth, "DEFAULT_TEMPLATES_ROOT", templates_root)

        bad = _legal_package()
        del bad["domain_prompt.md"]
        result = ct.compiler_skill_synthesis_save(session_path, "gameplay-auction", bad)
        assert result["status"] == "failed"
        assert result["errors"], "rejected 的 errors 必须透传非空"
        assert any("domain_prompt.md" in e for e in result["errors"])
        assert result["data"]["synthesis_status"] == "rejected"
        assert "修正后重提" in result["summary"]
        assert not (templates_root / "synthesized").exists()

    def test_save_legal_package_success_with_review(self, tmp_path, monkeypatch):
        """合法包:success,落盘 tmp 模板根 synthesized/,人审清单落 run 目录。"""
        ct = _import_compiler_tools()
        session_path, run_dir = _make_run(tmp_path)
        templates_root = tmp_path / "templates"
        _make_official_manifest(templates_root)
        synth = _import_skill_synthesis()
        monkeypatch.setattr(synth, "DEFAULT_TEMPLATES_ROOT", templates_root)

        result = ct.compiler_skill_synthesis_save(
            session_path, "gameplay-auction", _legal_package()
        )
        assert result["status"] == "success", result
        data = result["data"]
        assert data["synthesis_status"] == "saved"
        package_dir = Path(data["package_dir"])
        assert package_dir == templates_root / "synthesized" / "gameplay-auction"
        assert (package_dir / "manifest.yaml").is_file()
        # 人审清单已刷新到 run 目录,且列出该包
        review_path = Path(data["review_path"])
        assert review_path == run_dir / "synthesis_review.md"
        assert "gameplay-auction" in review_path.read_text(encoding="utf-8")
        assert data["next"], "data 应带人审 next 指引"
        assert "人审清单已刷新" in result["summary"]
        assert any("未经人审" in w for w in result["warnings"])

    def test_save_six_files_not_dict_failed(self, tmp_path):
        """MCP 层把 six_files 传成字符串:failed + 明确文案,不触盘。"""
        ct = _import_compiler_tools()
        session_path, _run_dir = _make_run(tmp_path)
        result = ct.compiler_skill_synthesis_save(
            session_path, "gameplay-auction", "我不是 dict"
        )
        assert result["status"] == "failed"
        assert any("six_files" in e for e in result["errors"]), result["errors"]

    def test_save_environment_failed_distinguishable_from_rejected(
        self, tmp_path, monkeypatch
    ):
        """环境 failed:summary 与内容 rejected 可区分,synthesis_status 留原始值。"""
        ct = _import_compiler_tools()
        session_path, _run_dir = _make_run(tmp_path)
        synth = _import_skill_synthesis()

        def _fake_save(**_kwargs):
            # 模拟校验全过但落盘 IO 失败(skill_synthesis 的 failed 三态)
            return {"status": "failed", "errors": ["落盘失败(模拟 IO)"], "package_dir": ""}

        monkeypatch.setattr(synth, "save_synthesized_package", _fake_save)
        result = ct.compiler_skill_synthesis_save(
            session_path, "gameplay-auction", _legal_package()
        )
        assert result["status"] == "failed"
        assert result["data"]["synthesis_status"] == "failed"
        assert "环境" in result["summary"]
        assert "修正后重提" not in result["summary"]
        assert result["errors"] == ["落盘失败(模拟 IO)"]

    def test_save_review_refresh_failure_degrades_to_warning(
        self, tmp_path, monkeypatch
    ):
        """人审清单刷新抛异常:包已落盘,saved 仍映射 success,
        清单失败只降级为 warning(锁降级映射,防回退成整体 failed 掩盖落盘事实)。"""
        ct = _import_compiler_tools()
        session_path, _run_dir = _make_run(tmp_path)
        templates_root = tmp_path / "templates"
        _make_official_manifest(templates_root)
        synth = _import_skill_synthesis()
        monkeypatch.setattr(synth, "DEFAULT_TEMPLATES_ROOT", templates_root)

        def _broken_review(*_args, **_kwargs):
            raise OSError("清单写盘失败(模拟)")

        monkeypatch.setattr(synth, "generate_synthesis_review", _broken_review)
        result = ct.compiler_skill_synthesis_save(
            session_path, "gameplay-auction", _legal_package()
        )
        assert result["status"] == "success", result
        assert result["data"]["synthesis_status"] == "saved"
        assert result["data"]["review_path"] is None
        # 包确实已落盘
        assert (templates_root / "synthesized" / "gameplay-auction" / "manifest.yaml").is_file()
        assert any("清单" in w for w in result["warnings"]), result["warnings"]
        assert "人审清单已刷新" not in result["summary"]


# ---------------------------------------------------------------------------
# 残留守卫:必须放在文件最后(pytest 按定义顺序执行)
# ---------------------------------------------------------------------------

def test_zz_real_templates_tree_no_synthesized_residue():
    """全部用例跑完后,真实模板树必须无 synthesized/ 残留(测试不污染真实树)。"""
    assert not REAL_SYNTHESIZED_DIR.exists(), \
        f"真实模板树被污染,存在残留: {REAL_SYNTHESIZED_DIR}"
