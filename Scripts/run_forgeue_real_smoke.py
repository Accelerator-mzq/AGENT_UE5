"""ForgeUE Manifest 真机导入验收 smoke 脚本(L3,外部驱动)。

用法:
    python Scripts/run_forgeue_real_smoke.py --bridge-mode bridge_rc_api
    python Scripts/run_forgeue_real_smoke.py --bridge-mode simulated

bridge_python:不能纯外部 driver(要在 Editor 内 Python Console 跑),本脚本不支持。
bridge_rc_api:通过 RC HTTP 触发 Editor 内 endpoint,推荐 L3 默认模式。
simulated:离线 sanity check,不入 UE Editor。

产出(L3 完整证据包,符合 spec §7 / §9 落盘约定):
    ProjectState/Reports/<date>/forgeue_real_smoke/
    ├── evidence_manifest.json         L4 wrapper(复用 evidence_manifest.schema.json,test_type=smoke_test)
    ├── op_evidence/<asset_entry_id>.json  L1 逐条(符合 forgeue_import_evidence.schema.json)
    ├── assertions.json                EditorAssetLibrary.does_asset_exist 校验
    ├── unreal.log.snippet.txt         msc 手动复制 / controller 截取
    └── screenshots/                   手动截图(controller 接管时可能跳过)

实际 RC object_path / function name / parameter keys 用 Plan T5 实测真实值
(snake_case,非 spec/plan v1.0 写错的 CamelCase 占位)。
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import sys
import uuid
from pathlib import Path

# 项目根目录:本脚本位于 <root>/Scripts/,上溯一级即为项目根
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 加 bridge/ + orchestrator/ 到 sys.path(沿用现有 Scripts/run_*.py 模式)
sys.path.insert(0, str(PROJECT_ROOT / "Plugins" / "AgentBridge" / "Scripts" / "bridge"))
sys.path.insert(0, str(PROJECT_ROOT / "Plugins" / "AgentBridge" / "Scripts" / "orchestrator"))


# fixture 目录(manifest.json + import_plan.json 的位置)
FIXTURE_DIR = PROJECT_ROOT / "Plugins" / "AgentBridge" / "Tests" / "fixtures" / "forgeue_manifest"
MANIFEST_PATH = FIXTURE_DIR / "manifest.json"
PLAN_PATH = FIXTURE_DIR / "import_plan.json"

# Plan T5 实测真实 endpoint 路径(snake_case,非 spec v1.0 CamelCase 占位)
RC_OBJECT_PATH = "/AgentBridge/Python/forgeue_rc_endpoint_PY.Default__AgentBridgeForgeUEEndpoint"
RC_FUNCTION_NAME = "import_assets_from_manifest"

# UE 内置 EditorAssetLibrary(CamelCase BlueprintCallable)
EDITOR_ASSET_LIB = "/Script/EditorScriptingUtilities.Default__EditorAssetLibrary"


def _make_run_id() -> str:
    """生成 evidence_manifest.schema.json 兼容的 run_id(yyyy-mm-dd_xxxxxxxx)。"""
    today = _dt.date.today().isoformat()
    short = hashlib.sha1(uuid.uuid4().bytes).hexdigest()[:8]
    return f"{today}_{short}"


def _now_iso_utc() -> str:
    """返回当前 UTC 时间 ISO 8601 含毫秒 + Z 后缀。

    对齐 importer.py 中 _now_iso_utc 实现,避开 Python 3.13 utcnow deprecation。
    """
    return _dt.datetime.now(_dt.UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _trigger_via_simulated() -> dict:
    """跑 importer simulated 路径(纯离线,不依赖 UE Editor)。"""
    import forgeue_manifest_importer as importer  # 位于 orchestrator/ 下
    return importer.import_from_manifest(
        manifest_path=str(MANIFEST_PATH),
        plan_path=str(PLAN_PATH),
        bridge_mode="simulated",
    )


def _trigger_via_rc_api() -> dict:
    """通过 RC HTTP 触发 UE Editor 内 forgeue_rc_endpoint。

    endpoint 接收 manifest_path / plan_path / overwrite_existing 三个参数,
    返回 JSON 字符串(ReturnValue 字段),再解析为 dict 返回。
    """
    import remote_control_client as rc  # 位于 bridge/ 下
    result_json = rc.call_function(
        object_path=RC_OBJECT_PATH,
        function_name=RC_FUNCTION_NAME,
        parameters={
            "manifest_path": str(MANIFEST_PATH),
            "plan_path": str(PLAN_PATH),
            "overwrite_existing": True,
        },
    )
    return_value = result_json.get("ReturnValue", "")
    if not return_value:
        raise RuntimeError(f"RC ReturnValue 空:{result_json}")
    return json.loads(return_value)


def _verify_uassets_exist(expected_packages: list[str]) -> dict[str, bool]:
    """逐个 RC 查 EditorAssetLibrary.DoesAssetExist,返 {package: exists} 字典。

    仅在 bridge_rc_api 模式调用(真机 UE Editor 在线时)。
    """
    import remote_control_client as rc
    results: dict[str, bool] = {}
    for pkg in expected_packages:
        r = rc.call_function(
            object_path=EDITOR_ASSET_LIB,
            function_name="DoesAssetExist",   # UE 内置 CamelCase BlueprintCallable
            parameters={"AssetPath": pkg},
        )
        results[pkg] = bool(r.get("ReturnValue", False))
    return results


def _write_evidence_pack(
    report_dir: Path,
    run_id: str,
    payload: dict,
    assertions: dict[str, bool],
    bridge_mode: str,
) -> None:
    """落盘完整 evidence pack:op_evidence 6 份 + assertions.json + evidence_manifest.json。

    产出路径:
        report_dir/op_evidence/<asset_entry_id>.json   (符合 forgeue_import_evidence.schema.json)
        report_dir/assertions.json
        report_dir/evidence_manifest.json              (L4 wrapper,test_type=smoke_test)
    """
    op_dir = report_dir / "op_evidence"
    op_dir.mkdir(parents=True, exist_ok=True)

    # 1. 逐条 op evidence 写盘(符合 forgeue_import_evidence.schema.json)
    for op in payload.get("asset_results", []):
        out = op_dir / f"{op.get('asset_entry_id', 'unknown')}.json"
        out.write_text(json.dumps(op, ensure_ascii=False, indent=2), encoding="utf-8")

    # 2. 校验结果写盘(L3 自产,不在 schema 内)
    (report_dir / "assertions.json").write_text(
        json.dumps(assertions, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 3. 构造 evidence_manifest.json(复用 evidence_manifest.schema.json,test_type=smoke_test)
    timestamp = _now_iso_utc()
    evidence_items = []
    for op in payload.get("asset_results", []):
        evidence_items.append({
            "type": "report",
            "path": f"op_evidence/{op.get('asset_entry_id')}.json",
            "description": f"{op.get('asset_kind')} import op evidence",
            "timestamp": op.get("timestamp", timestamp),
        })
    evidence_items.append({
        "type": "assertion_result",
        "path": "assertions.json",
        "description": "EditorAssetLibrary.DoesAssetExist 6/6 校验结果",
        "timestamp": timestamp,
    })

    passed = sum(1 for v in assertions.values() if v)
    failed = sum(1 for v in assertions.values() if not v)

    manifest_evidence = {
        "run_id": run_id,
        "created_at": timestamp,
        "test_type": "smoke_test",
        "test_scope": f"ForgeUE Manifest Real-UE Import Bridge ({bridge_mode})",
        "evidence_items": evidence_items,
        "summary": {
            "total_checks": passed + failed,
            "passed": passed,
            "failed": failed,
            "warnings": 0,
        },
        "status": "pass" if failed == 0 else "fail",
    }
    (report_dir / "evidence_manifest.json").write_text(
        json.dumps(manifest_evidence, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    """L3 smoke 主流程:触发导入 → 校验 → 落证据 → 打印摘要 → 返回 exit code。"""
    parser = argparse.ArgumentParser(description="ForgeUE Real-UE smoke (L3)")
    parser.add_argument(
        "--bridge-mode",
        required=True,
        choices=["simulated", "bridge_rc_api"],
        help="L3 入口只支持 simulated(离线 sanity) / bridge_rc_api(真机)",
    )
    args = parser.parse_args()

    run_id = _make_run_id()
    report_dir = (
        PROJECT_ROOT
        / "ProjectState"
        / "Reports"
        / _dt.date.today().isoformat()
        / "forgeue_real_smoke"
    )
    report_dir.mkdir(parents=True, exist_ok=True)

    print(f"[L3 smoke] run_id={run_id} bridge_mode={args.bridge_mode}")
    print(f"[L3 smoke] report_dir={report_dir}")

    # --- Step 1: 触发导入 ---
    if args.bridge_mode == "simulated":
        payload = _trigger_via_simulated()
    else:
        # bridge_rc_api:要求 UE Editor 在线 + RC API 已启动
        payload = _trigger_via_rc_api()

    # --- Step 2: 构造 assertions ---
    if args.bridge_mode == "bridge_rc_api":
        # 真机模式:用 EditorAssetLibrary.DoesAssetExist 逐条校验 uasset 存在
        expected_pkgs = [
            op.get("uasset_package_path", "")
            for op in payload.get("asset_results", [])
        ]
        expected_pkgs = [p for p in expected_pkgs if p]
        assertions = _verify_uassets_exist(expected_pkgs)
    else:
        # simulated 模式:标 simulated-pass(无真实 uasset 落盘)
        # 用 target_object_path 作 key(manifest 中已定义),所有条目标 True
        assertions = {
            op.get("target_object_path", ""): True
            for op in payload.get("asset_results", [])
        }

    # --- Step 3: 落证据包 ---
    _write_evidence_pack(report_dir, run_id, payload, assertions, args.bridge_mode)

    # --- Step 4: 打印摘要 ---
    passed = sum(1 for v in assertions.values() if v)
    total = len(assertions)
    print(f"[L3 smoke] payload status={payload.get('status')}")
    print(f"[L3 smoke] assertions: passed={passed} / total={total}")
    print(
        f"[L3 smoke] evidence_manifest.status={'pass' if all(assertions.values()) else 'fail'}"
    )

    # --- Step 5: exit code ---
    # assertions 全过 + payload 整体 success/partial 才算 0
    if all(assertions.values()) and payload.get("status") in ("success", "partial"):
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
