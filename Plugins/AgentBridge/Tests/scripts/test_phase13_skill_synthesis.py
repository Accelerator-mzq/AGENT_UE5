# -*- coding: utf-8 -*-
"""SKS-09/10: 合成 save 落盘与重试闭环;审阅清单生成。

额外覆盖前序审查教训:
  - save 拒绝规范外多余文件名(含路径分隔符的穿越 key)
  - 审阅清单对坏 manifest 容错(标"损坏"而非崩掉)
  - 审阅清单按 review_status 分组(pending 在前,approved 归"已审批"段)
  - T5 复审遗留锁测试:运行期 approve 后 registry_scan 立即可见
    (锁住"惰性重建+审批门"组合语义,防将来加缓存悄悄回退)
"""
import importlib.util
from pathlib import Path

import pytest
import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def _load(name):
    """动态加载 Compiler/stages 下的单文件模块(未安装为包,经 importlib 加载)。"""
    spec = importlib.util.spec_from_file_location(
        name, PLUGIN_ROOT / "Compiler" / "stages" / f"{name}.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _legal_package():
    """复用校验器测试中的最小合法 6 文件包构造,避免两份测试漂移。"""
    validator_test = importlib.util.spec_from_file_location(
        "vt", Path(__file__).resolve().parent / "test_phase13_synthesis_validator.py"
    )
    module = importlib.util.module_from_spec(validator_test)
    validator_test.loader.exec_module(module)
    return module._legal_package()


def _approve_on_disk(package_dir: Path) -> None:
    """模拟人审动作:把落盘 manifest 的 review_status 改为 approved。"""
    manifest_path = package_dir / "manifest.yaml"
    text = manifest_path.read_text(encoding="utf-8")
    manifest_path.write_text(
        text.replace("review_status: pending_review", "review_status: approved"),
        encoding="utf-8",
    )


class TestSkillSynthesis:
    def test_sks09_save_rejects_then_accepts(self, tmp_path):
        """SKS-09: 非法包返回错误不落盘;修正后通过并落盘 pending_review。"""
        ss = _load("skill_synthesis")
        bad = _legal_package()
        del bad["domain_prompt.md"]
        result = ss.save_synthesized_package(
            capability_id="gameplay-auction",
            six_files=bad,
            templates_root=tmp_path,
            family_whitelist={"property_economy_spec"},
        )
        assert result["status"] == "rejected"
        assert any("domain_prompt.md" in e for e in result["errors"])
        assert not (tmp_path / "synthesized" / "gameplay-auction").exists()

        good = _legal_package()
        result = ss.save_synthesized_package(
            capability_id="gameplay-auction",
            six_files=good,
            templates_root=tmp_path,
            family_whitelist={"property_economy_spec"},
        )
        assert result["status"] == "saved"
        package_dir = tmp_path / "synthesized" / "gameplay-auction"
        assert (package_dir / "manifest.yaml").is_file()
        manifest = yaml.safe_load((package_dir / "manifest.yaml").read_text(encoding="utf-8"))
        assert manifest["review_status"] == "pending_review"

    def test_sks09b_prepare_payload_contains_exemplars_and_whitelist(self, tmp_path):
        """SKS-09b: prepare 载荷含 gap 上下文、6 文件规范、范例模板、白名单。"""
        ss = _load("skill_synthesis")
        payload = ss.build_synthesis_prepare_payload(
            capability_id="gameplay-auction",
            gap={"capability_id": "gameplay-auction", "domain_type": "gameplay",
                 "reason": "no_template", "source_anchor": "§2.4 地产拍卖"},
            gdd_excerpt="## 2.4 地产拍卖\n玩家拒购时地产进入英式拍卖……",
            constraints={"max_players": 6},
            templates_root=PLUGIN_ROOT / "SkillTemplates",
        )
        assert payload["capability_id"] == "gameplay-auction"
        assert "manifest.yaml" in payload["file_spec"]
        assert len(payload["exemplars"]) >= 1
        assert "property_economy_spec" in payload["family_whitelist"]
        assert payload["gdd_excerpt"].startswith("## 2.4")
        # Minor: exemplar _dir 必须是相对 templates_root 的路径(载荷不泄露绝对盘符路径)
        assert not Path(payload["exemplars"][0]["_dir"]).is_absolute(), \
            f"_dir 应为相对路径,实际: {payload['exemplars'][0]['_dir']}"

    def test_sks10_review_checklist_lists_packages(self, tmp_path):
        """SKS-10: 审阅清单列出全部待审包及重点文件。"""
        ss = _load("skill_synthesis")
        ss.save_synthesized_package(
            capability_id="gameplay-auction",
            six_files=_legal_package(),
            templates_root=tmp_path,
            family_whitelist={"property_economy_spec"},
        )
        run_dir = tmp_path / "run"
        path = ss.generate_synthesis_review(run_dir, templates_root=tmp_path)
        text = Path(path).read_text(encoding="utf-8")
        assert "gameplay-auction" in text
        assert "output_schema.json" in text
        assert "review_status" in text

    # ---- 审查教训 1: save 落盘只接受 6 个规范文件名 ----

    def test_save_rejects_extra_keys(self, tmp_path):
        """six_files 含规范外多余 key 时应 rejected,错误文案列出多余文件名,不落盘。"""
        ss = _load("skill_synthesis")
        package = _legal_package()
        package["extra_notes.md"] = "agent 多塞的文件"
        result = ss.save_synthesized_package(
            capability_id="gameplay-auction",
            six_files=package,
            templates_root=tmp_path,
            family_whitelist={"property_economy_spec"},
        )
        assert result["status"] == "rejected"
        assert any("extra_notes.md" in e for e in result["errors"]), \
            f"期望错误文案列出多余文件名,实际: {result['errors']}"
        assert not (tmp_path / "synthesized").exists()

    def test_save_rejects_path_traversal_key(self, tmp_path):
        """six_files 的 key 含路径分隔符(穿越企图)时应 rejected,且不在任何位置落盘。"""
        ss = _load("skill_synthesis")
        package = _legal_package()
        package["../evil.yaml"] = "穿越企图"
        result = ss.save_synthesized_package(
            capability_id="gameplay-auction",
            six_files=package,
            templates_root=tmp_path,
            family_whitelist={"property_economy_spec"},
        )
        assert result["status"] == "rejected"
        assert any("../evil.yaml" in e for e in result["errors"]), \
            f"期望错误文案列出非法文件名,实际: {result['errors']}"
        assert not (tmp_path / "synthesized").exists()
        assert not (tmp_path / "evil.yaml").exists()

    def test_save_rejects_traversal_capability_id(self, tmp_path):
        """Spec 审查实证漏洞: capability_id 为 '../../evil' 时必须 rejected,
        且任何位置零触盘(此前实测会逃出 synthesized/ 落盘到上两级目录)。

        恶意包 manifest 与穿越 id 自洽(template_id/binding 均替换),
        确保不是被 template_id 比对碰巧拦下,而是被 capability_id 格式校验拦下。"""
        ss = _load("skill_synthesis")
        # 用 tmp_path 的二级子目录做 root,使逃逸目标仍落在 tmp_path 沙箱内可断言
        root = tmp_path / "a" / "b"
        root.mkdir(parents=True)
        evil = _legal_package()
        evil["manifest.yaml"] = evil["manifest.yaml"].replace(
            "gameplay-auction", "../../evil"
        )
        result = ss.save_synthesized_package(
            capability_id="../../evil",
            six_files=evil,
            templates_root=root,
            family_whitelist={"property_economy_spec"},
        )
        assert result["status"] == "rejected"
        assert any("capability_id" in e for e in result["errors"]), \
            f"期望 capability_id 格式错误,实际: {result['errors']}"
        # root/synthesized/../../evil 规范化后 = tmp_path/a/evil —— 全链路零触盘
        assert not (root / "synthesized").exists()
        assert not (tmp_path / "a" / "evil").exists()
        assert not (tmp_path / "evil").exists()

    def test_prepare_rejects_traversal_capability_id(self):
        """prepare 的 capability_id 来自 skill_graph gaps,非法即编程错误:
        立即抛 ValueError(fail-fast),防 naming_rules 带穿越路径误导 agent。"""
        ss = _load("skill_synthesis")
        with pytest.raises(ValueError, match="capability_id"):
            ss.build_synthesis_prepare_payload(
                capability_id="../../evil",
                gap={"capability_id": "../../evil", "domain_type": "gameplay"},
                gdd_excerpt="x",
                constraints={},
                templates_root=PLUGIN_ROOT / "SkillTemplates",
            )

    # ---- Important 2: six_files value 非字符串经 save 不抛异常 ----

    def test_save_non_string_value_rejected_no_crash(self, tmp_path):
        """agent 经 MCP 透传 dict value 时 save 必须返回 rejected 结构化错误,
        而非 AttributeError 穿透(实测漏洞)。"""
        ss = _load("skill_synthesis")
        package = _legal_package()
        package["domain_prompt.md"] = {"oops": "agent 传了结构化值"}
        result = ss.save_synthesized_package(
            capability_id="gameplay-auction",
            six_files=package,
            templates_root=tmp_path,
            family_whitelist={"property_economy_spec"},
        )
        assert result["status"] == "rejected"
        assert any("domain_prompt.md" in e for e in result["errors"]), \
            f"期望含文件名的错误,实际: {result['errors']}"
        assert not (tmp_path / "synthesized").exists()

    # ---- Important 1: save 事务性(temp-then-swap) ----

    def test_save_transactional_no_partial_package_on_io_failure(self, tmp_path, monkeypatch):
        """第 4 个文件写入抛 IOError 时:最终目录不存在、temp 目录被清理、
        返回 status=failed 结构化错误(IO/环境错误,与内容性 rejected 区分)。"""
        ss = _load("skill_synthesis")
        package = _legal_package()  # monkeypatch 前构造,避免干扰计数

        real_write_text = Path.write_text
        calls = {"n": 0}

        def flaky_write_text(self, *args, **kwargs):
            calls["n"] += 1
            if calls["n"] == 4:
                raise IOError("磁盘写入失败(模拟)")
            return real_write_text(self, *args, **kwargs)

        monkeypatch.setattr(Path, "write_text", flaky_write_text)
        result = ss.save_synthesized_package(
            capability_id="gameplay-auction",
            six_files=package,
            templates_root=tmp_path,
            family_whitelist={"property_economy_spec"},
        )
        assert result["status"] == "failed", f"期望 failed,实际: {result}"
        assert result["errors"], "期望结构化错误信息"
        # 半成品零残留:最终目录与 temp 目录均不存在
        assert not (tmp_path / "synthesized" / "gameplay-auction").exists()
        assert not (tmp_path / "synthesized" / ".tmp-gameplay-auction").exists()

    def test_crashed_temp_dir_invisible_to_registry_and_review(self, tmp_path):
        """锁测试:伪造换名前进程被杀的残留 temp 目录(manifest 暂存为 .part),
        registry_scan 与审阅清单都不应看到它(manifest.yaml 是发现锚点)。"""
        ss = _load("skill_synthesis")
        rs = _load("registry_scan")
        package = _legal_package()
        temp_dir = tmp_path / "synthesized" / ".tmp-gameplay-auction"
        temp_dir.mkdir(parents=True)
        for name, content in package.items():
            staged = "manifest.yaml.part" if name == "manifest.yaml" else name
            (temp_dir / staged).write_text(content, encoding="utf-8")

        assert "gameplay-auction" not in rs.scan_capability_registry(tmp_path)
        path = ss.generate_synthesis_review(tmp_path / "run", templates_root=tmp_path)
        text = Path(path).read_text(encoding="utf-8")
        assert ".tmp-gameplay-auction" not in text

    # ---- Important 3: approved 包防覆盖 ----

    def test_save_rejects_overwrite_of_approved_package(self, tmp_path):
        """已审批包是人审资产:再次 save 同 capability_id 必须 rejected 且内容未变。"""
        ss = _load("skill_synthesis")
        ss.save_synthesized_package(
            capability_id="gameplay-auction",
            six_files=_legal_package(),
            templates_root=tmp_path,
            family_whitelist={"property_economy_spec"},
        )
        package_dir = tmp_path / "synthesized" / "gameplay-auction"
        _approve_on_disk(package_dir)
        before = (package_dir / "manifest.yaml").read_text(encoding="utf-8")

        result = ss.save_synthesized_package(
            capability_id="gameplay-auction",
            six_files=_legal_package(),
            templates_root=tmp_path,
            family_whitelist={"property_economy_spec"},
        )
        assert result["status"] == "rejected"
        assert any("已审批" in e for e in result["errors"]), \
            f"期望'已审批'拒绝文案,实际: {result['errors']}"
        after = (package_dir / "manifest.yaml").read_text(encoding="utf-8")
        assert after == before, "approved 包内容不得被覆盖"

    def test_save_allows_overwrite_of_pending_package(self, tmp_path):
        """pending_review 的现存包允许覆盖(agent 重试语义),内容更新生效。"""
        ss = _load("skill_synthesis")
        ss.save_synthesized_package(
            capability_id="gameplay-auction",
            six_files=_legal_package(),
            templates_root=tmp_path,
            family_whitelist={"property_economy_spec"},
        )
        updated = _legal_package()
        updated["domain_prompt.md"] = "拍卖规则 v2:补充荷兰式拍卖的降价步长设计。"
        result = ss.save_synthesized_package(
            capability_id="gameplay-auction",
            six_files=updated,
            templates_root=tmp_path,
            family_whitelist={"property_economy_spec"},
        )
        assert result["status"] == "saved"
        on_disk = (tmp_path / "synthesized" / "gameplay-auction" / "domain_prompt.md") \
            .read_text(encoding="utf-8")
        assert on_disk == updated["domain_prompt.md"]

    # ---- Minor 锁测试 ----

    def test_lock_file_spec_matches_validator_required_files(self):
        """FILE_SPEC(落盘白名单)与 validator.REQUIRED_FILES(校验集)必须恒等,
        防两边单独演化导致'校验通过但落盘缺文件'或反之。"""
        ss = _load("skill_synthesis")
        sv = _load("synthesis_validator")
        assert set(ss.FILE_SPEC) == sv.REQUIRED_FILES

    def test_lock_load_sibling_returns_cached_single_instance(self):
        """_load_sibling 同名模块必须返回同一实例(模块级缓存),
        防每次调用重复 exec_module 的加载开销与实例分裂。"""
        ss = _load("skill_synthesis")
        first = ss._load_sibling("synthesis_validator")
        second = ss._load_sibling("synthesis_validator")
        assert first is second

    # ---- 审查教训 2: 审阅清单对坏 manifest 容错 ----

    def test_review_tolerates_corrupt_manifest(self, tmp_path):
        """synthesized 区存在坏 manifest 时,清单标'损坏'而非生成崩掉。"""
        ss = _load("skill_synthesis")
        # 一个正常包 + 一个 manifest 损坏的包
        ss.save_synthesized_package(
            capability_id="gameplay-auction",
            six_files=_legal_package(),
            templates_root=tmp_path,
            family_whitelist={"property_economy_spec"},
        )
        broken_dir = tmp_path / "synthesized" / "gameplay-broken"
        broken_dir.mkdir(parents=True)
        (broken_dir / "manifest.yaml").write_text("{{ 非法 yaml: [", encoding="utf-8")

        path = ss.generate_synthesis_review(tmp_path / "run", templates_root=tmp_path)
        text = Path(path).read_text(encoding="utf-8")
        # 坏包被标记损坏,好包正常列出,二者共存
        assert "gameplay-broken" in text
        assert "损坏" in text
        assert "gameplay-auction" in text

    # ---- 审查教训 3: 审阅清单按 review_status 分组 ----

    def test_review_groups_pending_before_approved(self, tmp_path):
        """pending_review 包排在前(人审待办),approved 包归'已审批'段。"""
        ss = _load("skill_synthesis")
        # 包 1: 保持 pending_review
        ss.save_synthesized_package(
            capability_id="gameplay-auction",
            six_files=_legal_package(),
            templates_root=tmp_path,
            family_whitelist={"property_economy_spec"},
        )
        # 包 2: 落盘后模拟人审改 approved(manifest 文本替换 capability 标识)
        stock = _legal_package()
        stock["manifest.yaml"] = stock["manifest.yaml"].replace(
            "gameplay-auction", "gameplay-stock"
        )
        ss.save_synthesized_package(
            capability_id="gameplay-stock",
            six_files=stock,
            templates_root=tmp_path,
            family_whitelist={"property_economy_spec"},
        )
        _approve_on_disk(tmp_path / "synthesized" / "gameplay-stock")

        path = ss.generate_synthesis_review(tmp_path / "run", templates_root=tmp_path)
        text = Path(path).read_text(encoding="utf-8")
        # 已审批段存在,且 pending 包出现在已审批段之前
        assert "已审批" in text
        assert text.index("gameplay-auction") < text.index("已审批")
        assert text.index("已审批") < text.index("gameplay-stock")

    # ---- T5 复审遗留锁测试: 运行期 approve 立即对 registry_scan 可见 ----

    def test_t5_lock_approve_immediately_visible_to_registry_scan(self, tmp_path):
        """save 落盘 pending 时注册表不可见;改 approved 后无需任何刷新动作,
        下一次 scan_capability_registry 立即可见且 template_source=synthesized。"""
        ss = _load("skill_synthesis")
        rs = _load("registry_scan")
        result = ss.save_synthesized_package(
            capability_id="gameplay-auction",
            six_files=_legal_package(),
            templates_root=tmp_path,
            family_whitelist={"property_economy_spec"},
        )
        assert result["status"] == "saved"

        # pending_review: 对注册表不可见(第二道 gate 未过)
        registry = rs.scan_capability_registry(tmp_path)
        assert "gameplay-auction" not in registry

        # 人审 approve 后: 立即可见(惰性重建,无缓存)
        _approve_on_disk(tmp_path / "synthesized" / "gameplay-auction")
        registry = rs.scan_capability_registry(tmp_path)
        assert "gameplay-auction" in registry
        assert registry["gameplay-auction"]["template_source"] == "synthesized"
        assert registry["gameplay-auction"]["instance_id"] == "skill-auction"
