"""
Handoff Runner
从 Handoff 生成 Run Plan 并执行

这是 Handoff 最小闭环的核心桥接文件：
- 读取 approved Handoff
- 生成 Run Plan
- 桥接到现有 Bridge 接口执行
- 输出执行报告

不修改现有 orchestrator.py 的 run(spec_path) 入口，
而是作为新增的并行入口。
"""

import os
from datetime import datetime
from typing import Dict, Any, List
from .run_plan_builder import build_run_plan_from_handoff

_DEFAULT_LEVEL_PATH = "/Game/Maps/TestMap"
_AGENT_BRIDGE_SUBSYSTEM_PATH = "/Script/AgentBridge.Default__AgentBridgeSubsystem"


def run_from_handoff(
    handoff_path: str,
    report_output_dir: str = None,
    bridge_mode: str = "simulated"
) -> Dict[str, Any]:
    """
    从 Handoff 执行

    Args:
        handoff_path: Handoff 文件路径
        report_output_dir: 报告输出目录（可选）
        bridge_mode: Bridge 调用模式
            - "simulated": 模拟执行（第一阶段默认）
            - "bridge_python": 调用现有 Python Bridge
            - "bridge_rc_api": 调用 Remote Control API

    Returns:
        执行结果
    """
    # 1. 读取 Handoff
    handoff = load_handoff(handoff_path)

    # 2. 生成 Run Plan
    run_plan = build_run_plan_from_handoff(handoff)

    # 3. 执行 Run Plan
    result = execute_run_plan(run_plan, bridge_mode)

    # 4. 生成执行报告
    report = build_execution_report(handoff, run_plan, result)

    # 5. 保存报告（如果指定了输出目录）
    if report_output_dir:
        save_execution_report(report, report_output_dir)

    return result


def load_handoff(handoff_path: str) -> Dict[str, Any]:
    """加载 Handoff"""
    import yaml
    import json

    if not os.path.exists(handoff_path):
        raise FileNotFoundError(f"Handoff 文件不存在: {handoff_path}")

    ext = os.path.splitext(handoff_path)[1].lower()

    if ext in ['.yaml', '.yml']:
        with open(handoff_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    elif ext == '.json':
        with open(handoff_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        raise ValueError(f"不支持的文件格式: {ext}")


def execute_run_plan(run_plan: Dict[str, Any], bridge_mode: str = "simulated") -> Dict[str, Any]:
    """
    执行 Run Plan

    桥接到现有 Bridge 接口，不修改现有执行链。

    Args:
        run_plan: Run Plan 字典
        bridge_mode: Bridge 调用模式
    """
    workflow_sequence = run_plan.get("workflow_sequence", [])

    results = []
    all_success = True

    for step in workflow_sequence:
        step_id = step.get("step_id")
        workflow_type = step.get("workflow_type")
        params = step.get("params")

        print(f"  执行步骤: {step_id} ({workflow_type})")

        # 桥接到现有 Bridge 接口
        if workflow_type == "spawn_actor":
            result = execute_spawn_actor(params, bridge_mode)
        elif workflow_type == "set_actor_transform":
            result = execute_set_actor_transform(params, bridge_mode)
        else:
            result = {"status": "skipped", "reason": f"未实现的 workflow_type: {workflow_type}"}

        if result.get("status") != "success":
            all_success = False

        results.append({
            "step_id": step_id,
            "result": result
        })

    return {
        "run_plan_id": run_plan.get("run_plan_id"),
        "source_handoff_id": run_plan.get("source_handoff_id"),
        "status": "succeeded" if all_success else "failed",
        "step_results": results,
        "completed_at": datetime.now().isoformat()
    }


def execute_spawn_actor(params: Dict[str, Any], bridge_mode: str) -> Dict[str, Any]:
    """
    执行 spawn_actor

    桥接策略：
    - simulated: 返回模拟结果（第一阶段默认）
    - bridge_python: 调用现有 bridge.write_tools.spawn_actor
    - bridge_rc_api: 调用 Remote Control API
    """
    if bridge_mode == "simulated":
        # 模拟执行
        return {
            "status": "success",
            "actor_name": params.get("actor_name"),
            "actual_transform": params.get("transform"),
            "message": "模拟执行成功"
        }

    elif bridge_mode == "bridge_python":
        # 桥接到现有 Python Bridge
        # 不修改 bridge/write_tools.py，直接调用
        try:
            from bridge.write_tools import spawn_actor
            result = spawn_actor(
                level_path=params.get("level_path", _DEFAULT_LEVEL_PATH),
                actor_class=params.get("actor_class"),
                actor_name=params.get("actor_name"),
                transform=params.get("transform"),
                dry_run=bool(params.get("dry_run", False)),
            )
            return result
        except ImportError:
            return {
                "status": "failed",
                "error": "bridge.write_tools 不可用，请确认 Bridge 环境"
            }

    elif bridge_mode == "bridge_rc_api":
        # 桥接到 Remote Control API
        try:
            from bridge.remote_control_client import call_function
            # 这里调用 C++ Subsystem 的 SpawnActor，需要传入 objectPath + functionName
            rc_response = call_function(
                object_path=_AGENT_BRIDGE_SUBSYSTEM_PATH,
                function_name="SpawnActor",
                parameters={
                    "LevelPath": params.get("level_path", _DEFAULT_LEVEL_PATH),
                    "ActorClass": params.get("actor_class"),
                    "ActorName": params.get("actor_name"),
                    "Transform": _to_cpp_bridge_transform(params.get("transform")),
                    "bDryRun": bool(params.get("dry_run", False)),
                },
            )
            return _normalize_rc_call_response(rc_response)
        except ImportError:
            return {
                "status": "failed",
                "error": "bridge.remote_control_client 不可用"
            }

    else:
        return {"status": "failed", "error": f"未知的 bridge_mode: {bridge_mode}"}


def execute_set_actor_transform(params: Dict[str, Any], bridge_mode: str) -> Dict[str, Any]:
    """
    执行 set_actor_transform

    第一阶段只支持 simulated 模式
    """
    if bridge_mode == "simulated":
        return {
            "status": "success",
            "actor_path": params.get("actor_path"),
            "actual_transform": params.get("transform"),
            "message": "模拟执行成功"
        }
    else:
        # TODO: 桥接到现有 Bridge 接口
        return {"status": "skipped", "reason": "set_actor_transform 桥接待实现"}


def _normalize_rc_call_response(rc_response: Dict[str, Any]) -> Dict[str, Any]:
    """统一 RC API 返回结构，展开 ReturnValue 与 FJsonObjectWrapper 的 JsonString。"""
    response = rc_response
    if isinstance(rc_response, dict):
        return_value = rc_response.get("ReturnValue")
        if isinstance(return_value, dict):
            response = return_value

    if isinstance(response, dict):
        data = response.get("data")
        if isinstance(data, dict):
            json_string = data.get("JsonString")
            if isinstance(json_string, str) and json_string.strip():
                try:
                    import json
                    response = dict(response)
                    response["data"] = json.loads(json_string)
                except Exception:
                    # 保持原始响应，避免因解析失败导致主流程中断
                    pass

    return response


def _to_cpp_bridge_transform(transform: Dict[str, Any]) -> Dict[str, Any]:
    """将 handoff 的小写数组 Transform 转为 C++ FBridgeTransform 结构。"""
    if not isinstance(transform, dict):
        return {
            "Location": {"X": 0, "Y": 0, "Z": 0},
            "Rotation": {"Pitch": 0, "Yaw": 0, "Roll": 0},
            "RelativeScale3D": {"X": 1, "Y": 1, "Z": 1},
        }

    # 已经是 C++ 可识别结构时直接透传，避免重复转换
    if {"Location", "Rotation", "RelativeScale3D"}.issubset(transform.keys()):
        return transform

    location = _to_triplet(transform.get("location"), [0, 0, 0])
    rotation = _to_triplet(transform.get("rotation"), [0, 0, 0])
    scale = _to_triplet(transform.get("relative_scale3d"), [1, 1, 1])

    return {
        "Location": {"X": location[0], "Y": location[1], "Z": location[2]},
        "Rotation": {"Pitch": rotation[0], "Yaw": rotation[1], "Roll": rotation[2]},
        "RelativeScale3D": {"X": scale[0], "Y": scale[1], "Z": scale[2]},
    }


def _to_triplet(value: Any, default_value: List[float]) -> List[float]:
    """将输入规范化为长度 3 的数值列表。"""
    if isinstance(value, (list, tuple)) and len(value) == 3:
        return [value[0], value[1], value[2]]
    return [default_value[0], default_value[1], default_value[2]]


def build_execution_report(
    handoff: Dict[str, Any],
    run_plan: Dict[str, Any],
    result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    构建执行报告

    Args:
        handoff: 原始 Handoff
        run_plan: 执行的 Run Plan
        result: 执行结果

    Returns:
        执行报告
    """
    return {
        "report_version": "1.0",
        "report_type": "execution_report",
        "source_handoff_id": handoff.get("handoff_id"),
        "source_run_plan_id": run_plan.get("run_plan_id"),
        "handoff_mode": handoff.get("handoff_mode"),
        "execution_status": result.get("status"),
        "step_results": result.get("step_results", []),
        "summary": {
            "total_steps": len(result.get("step_results", [])),
            "succeeded": sum(1 for s in result.get("step_results", []) if s.get("result", {}).get("status") == "success"),
            "failed": sum(1 for s in result.get("step_results", []) if s.get("result", {}).get("status") == "failed"),
            "skipped": sum(1 for s in result.get("step_results", []) if s.get("result", {}).get("status") == "skipped")
        },
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "generator": "AgentBridge.Orchestrator.v0.1"
        }
    }


def save_execution_report(report: Dict[str, Any], output_dir: str) -> str:
    """
    保存执行报告

    Args:
        report: 执行报告
        output_dir: 输出目录

    Returns:
        保存的文件路径
    """
    import json

    os.makedirs(output_dir, exist_ok=True)

    handoff_id = report.get("source_handoff_id", "unknown")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"execution_report_{handoff_id}_{timestamp}.json"
    output_path = os.path.join(output_dir, filename)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"  报告已保存: {output_path}")
    return output_path


if __name__ == "__main__":
    # 测试代码
    test_handoff_path = "../../ProjectState/Handoffs/approved/handoff.test.001.yaml"
    test_report_dir = "../../ProjectState/Reports/"

    if os.path.exists(test_handoff_path):
        result = run_from_handoff(
            test_handoff_path,
            report_output_dir=test_report_dir,
            bridge_mode="simulated"
        )
        print(f"执行结果: {result['status']}")
    else:
        print(f"测试文件不存在: {test_handoff_path}")
        print("请先运行 compiler_main.py 生成 Handoff，然后移动到 approved/ 目录")
