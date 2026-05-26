"""ForgeUE manifest 导入的 RC HTTP endpoint(Editor 内 startup 加载)。

注册一个 PythonScripted UCLASS:AgentBridgeForgeUEEndpoint,
含一个 BlueprintCallable UFUNCTION:import_assets_from_manifest。

外部通过 remote_control_client.call_function(
    object_path=<probe log 输出的真实 default object path>,
    function_name="import_assets_from_manifest",       # snake_case,UE 保留 Python 原名
    parameters={"manifest_path": "...", "plan_path": "...", "overwrite_existing": False}
) 触发。

实际 object_path 在 Editor 启动后由 [AgentBridge probe] log 给出。
实测真实值(commit a075ec4 验证):
    object_path  = "/AgentBridge/Python/forgeue_rc_endpoint_PY.Default__AgentBridgeForgeUEEndpoint"
    function_name = "import_assets_from_manifest"
    parameters keys = manifest_path / plan_path / overwrite_existing(全 snake_case)
spec/plan v1.0 的 /Script/PythonGeneratedClass.* + CamelCase 假设是错的,详见
ProjectState/Reports/2026-05-27/forgeue_rc_endpoint_verification.md "关键发现" 区段。

设计原则:
- endpoint 在 Editor 内,等价于 bridge_python 触发器
- 失败必须返回 JSON 字符串(含 status/error),不能让 RC HTTP 抛 500
"""
from __future__ import annotations

import json
import sys
import unreal

# 让 endpoint 能找到 forgeue_manifest_importer 共享内核
_ORCH_DIR = unreal.Paths.project_plugins_dir() + "AgentBridge/Scripts/orchestrator"
if _ORCH_DIR not in sys.path:
    sys.path.insert(0, _ORCH_DIR)

import forgeue_manifest_importer as importer  # noqa: E402  # 共享内核


@unreal.uclass()
class AgentBridgeForgeUEEndpoint(unreal.Object):
    """RC HTTP 入口对象;作为 PythonScripted UCLASS 注册到 UE 反射系统。"""

    @unreal.ufunction(
        ret=str,
        params=[str, str, bool],
        meta=dict(Category="AgentBridge|ForgeUE", BlueprintCallable=""),
    )
    def import_assets_from_manifest(
        self, manifest_path: str, plan_path: str, overwrite_existing: bool
    ) -> str:
        """RC 入口:同步执行整批导入,返回结构化 JSON 字符串。

        endpoint 内调 bridge_python 通路(因为 endpoint 本身在 Editor 内)。
        """
        try:
            result = importer.import_from_manifest(
                manifest_path=manifest_path,
                plan_path=plan_path or None,
                bridge_mode="bridge_python",
            )
            # 标注实际触发来源
            result["triggered_via"] = "bridge_rc_api"
            return json.dumps(result, ensure_ascii=False)
        except Exception as exc:
            return json.dumps(
                {"status": "error", "error_class": type(exc).__name__, "message": str(exc)},
                ensure_ascii=False,
            )


# ============================================================
# 自我探测:注册完成后立即 log 出 class path / default object path,
# 便于外部 RC 拼对 object_path(PythonScripted UCLASS 的真实路径由 UE 决定)
# ============================================================
try:
    _cls_path = AgentBridgeForgeUEEndpoint.static_class().get_path_name()
    _default_obj_path = AgentBridgeForgeUEEndpoint.get_default_object().get_path_name()
    unreal.log(f"[AgentBridge probe] class path = {_cls_path}")
    unreal.log(f"[AgentBridge probe] default obj path = {_default_obj_path}")
except Exception as _probe_exc:
    unreal.log_error(f"[AgentBridge probe] failed: {_probe_exc}")
