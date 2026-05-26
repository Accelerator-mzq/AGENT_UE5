"""L2 真机 smoke 测试:bridge_rc_api 通路真机调用 + uasset 真落盘验证。

Marker `real_ue` 要求 UE 5.5.4 Editor 在线 + RC API 端口 30010 可达,
默认 CI / 离线环境跳过(pytestmark skipif)。

测试 case:
1. RC endpoint 注册可见(/remote/object/describe 含 import_assets_from_manifest)
2. 端到端 6 asset 全 success(RC 触发 endpoint → 内核 _import_asset_by_kind → 6 helper 全实现)
3. uasset 真落盘验证(EditorAssetLibrary.DoesAssetExist 6/6 PASS)

实际 RC object_path / function name / parameter keys 都是 snake_case
(Plan T5 实测确认,Plan v1.0 中的 CamelCase 假设是错的)。
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

import pytest

# 让测试能找到 Scripts/orchestrator/ + bridge/ 目录(沿用现有 test_forgeue_manifest_importer.py 模式)
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
_BRIDGE_DIR = _PROJECT_ROOT / "Plugins" / "AgentBridge" / "Scripts" / "bridge"
if str(_BRIDGE_DIR) not in sys.path:
    sys.path.insert(0, str(_BRIDGE_DIR))

_FIXTURE_DIR = _PROJECT_ROOT / "Plugins" / "AgentBridge" / "Tests" / "fixtures" / "forgeue_manifest"
_MANIFEST_PATH = _FIXTURE_DIR / "manifest.json"
_PLAN_PATH = _FIXTURE_DIR / "import_plan.json"

# Plan T5 实测真实 endpoint 路径(spec/plan v1.0 中的 /Script/PythonGeneratedClass.* 是错的)
_RC_OBJECT_PATH = "/AgentBridge/Python/forgeue_rc_endpoint_PY.Default__AgentBridgeForgeUEEndpoint"
_RC_FUNCTION_NAME = "import_assets_from_manifest"  # snake_case,UE 保留 Python 原名

# UE 内置 EditorAssetLibrary(用 CamelCase BlueprintCallable 名)
_EDITOR_ASSET_LIB = "/Script/EditorScriptingUtilities.Default__EditorAssetLibrary"


def _ue_editor_alive() -> bool:
    """探测 UE Editor RC API 是否在线(port 30010 + endpoint 注册)。"""
    try:
        req = urllib.request.Request("http://localhost:30010/remote/info", method="GET")
        urllib.request.urlopen(req, timeout=2.0).read()
        return True
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


# 整文件级 skipif:离线时全部 skip,不需要单 case 加装饰器
pytestmark = pytest.mark.skipif(
    not _ue_editor_alive(),
    reason="L2 真机 smoke 要 UE 5.5.4 Editor 在线 + RC API 30010 可达(用 pytest -m real_ue 显式选择)",
)


@pytest.mark.real_ue
def test_rc_endpoint_describes_import_assets_from_manifest():
    """RC 通路验证:/remote/object/describe 必须含 import_assets_from_manifest 函数。"""
    import remote_control_client as rc

    info = rc._http_request("/remote/object/describe", {"objectPath": _RC_OBJECT_PATH})
    fn_names = [fn["Name"] for fn in info.get("Functions", [])]
    assert _RC_FUNCTION_NAME in fn_names, \
        f"endpoint 未注册 {_RC_FUNCTION_NAME}:实际函数 {fn_names}"


@pytest.mark.real_ue
def test_rc_endpoint_full_import_six_assets_all_success():
    """端到端 L2 smoke:RC 触发 6 asset 全 success(uasset 真落盘)。

    注意:UE Editor 必须加载最新 importer.py(Plan T6-T10 之后),否则
    部分 helper 是 NotImplementedError 占位会导致整批中断。
    """
    import remote_control_client as rc

    result_json = rc.call_function(
        object_path=_RC_OBJECT_PATH,
        function_name=_RC_FUNCTION_NAME,
        parameters={
            "manifest_path": str(_MANIFEST_PATH),
            "plan_path": str(_PLAN_PATH),
            "overwrite_existing": True,
        },
    )

    # RC 返回结构:ReturnValue 是 endpoint 返回的 JSON 字符串
    return_value = result_json.get("ReturnValue", "")
    assert return_value, f"RC call ReturnValue 为空:{result_json}"

    payload = json.loads(return_value)
    assert payload["status"] == "success", f"非全 success:{payload}"
    assert payload["bridge_mode"] == "bridge_python", \
        f"endpoint 内调 bridge_python 通路,实际 {payload.get('bridge_mode')!r}"
    assert payload.get("triggered_via") == "bridge_rc_api", \
        f"endpoint 应标 triggered_via=bridge_rc_api,实际 {payload.get('triggered_via')!r}"
    assert len(payload["asset_results"]) == 6

    # 6 种 kind 全 success
    kinds_status = {r["asset_kind"]: r["status"] for r in payload["asset_results"]}
    expected_kinds = {
        "texture", "sprite_sheet", "sound_wave",
        "static_mesh", "material", "file_media_source",
    }
    assert set(kinds_status.keys()) == expected_kinds, \
        f"kinds 覆盖不全:{set(kinds_status.keys())}"
    assert all(s == "success" for s in kinds_status.values()), \
        f"非全 success:{kinds_status}"


@pytest.mark.real_ue
def test_imported_uassets_exist_in_content_browser():
    """uasset 真落盘验证:EditorAssetLibrary.DoesAssetExist 6/6 PASS。"""
    import remote_control_client as rc

    # 6 个 target package path(对应 manifest 6 asset)
    expected_packages = [
        "/Game/Generated/Tavern/run_p4_full/T_run_p4_full_tex_albedo",        # texture
        "/Game/Generated/Tavern/run_p4_full/T_run_p4_full_tex_sprite",        # sprite_sheet
        "/Game/Generated/Tavern/run_p4_full/S_run_p4_full_sfx_click",         # sound_wave
        "/Game/Generated/Tavern/run_p4_full/SM_run_p4_full_mesh_cube",        # static_mesh
        "/Game/Generated/Tavern/run_p4_full/M_run_p4_full_material_simple",   # material
        "/Game/Generated/Tavern/run_p4_full/MS_run_p4_full_video_clip",       # file_media_source
    ]

    missing = []
    for pkg in expected_packages:
        result = rc.call_function(
            object_path=_EDITOR_ASSET_LIB,
            function_name="DoesAssetExist",  # UE 内置 CamelCase BlueprintCallable
            parameters={"AssetPath": pkg},
        )
        exists = result.get("ReturnValue", False)
        if not exists:
            missing.append(pkg)

    assert not missing, f"uasset 未落盘({len(missing)}/6):{missing}"
