"""
Stage 4 分段验证脚本。

职责：
  - 用最小粒度验证 LLM Internal 路径
  - 支持 llm_probe / single_node_discovery / single_node_full_stage4 / subset_stage4
  - 默认只输出诊断结果，不修改主 session 状态
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Plugins.AgentBridge.Compiler.pipeline.session import CompilerSession
from Plugins.AgentBridge.Compiler.pipeline import pipeline_orchestrator as pipeline_orchestrator
from Plugins.AgentBridge.Compiler.stages import agent_protocol
from Plugins.AgentBridge.Compiler.stages import domain_skill_runtime
from Plugins.AgentBridge.Compiler.stages.llm_client import load_llm_client_from_config


def _load_session_bundle(session_path: str | Path) -> Dict[str, Any]:
    """加载 session 及其 Stage 1-3 输入。"""
    session = CompilerSession.load(Path(session_path))
    return {
        "session": session,
        "root_skill_contract": pipeline_orchestrator._load_stage_artifact(session, 1) or {},
        "clarification_gate_report": pipeline_orchestrator._load_stage_artifact(session, 2) or {},
        "skill_graph": pipeline_orchestrator._load_stage_artifact(session, 3) or {},
    }


def _resolve_node(skill_graph: Dict[str, Any], node_id: str) -> Dict[str, Any]:
    """按 node_id 查找节点。"""
    for node in skill_graph.get("nodes", []):
        if node.get("instance_id") == node_id:
            return node
    raise ValueError(f"未找到节点：{node_id}")


def _default_discovery_nodes(skill_graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    """返回按拓扑顺序排列的 discovery-capable 节点。"""
    ordered_nodes = domain_skill_runtime._topological_execution_order(skill_graph.get("nodes", []))
    return [node for node in ordered_nodes if node.get("allows_design_space_discovery", False)]


def _make_provider() -> agent_protocol.LLMProvider:
    """加载 llm_client 并包装成 Stage 4 provider。"""
    llm_client = load_llm_client_from_config()
    if llm_client is None:
        raise RuntimeError("当前 llm_config 未成功加载，无法执行分段验证。")
    return agent_protocol.LLMProvider(llm_client)


def _trace_summary(trace: Dict[str, Any]) -> Dict[str, Any]:
    """提取 trace 的高信号摘要。"""
    output = trace.get("output", {}) if isinstance(trace, dict) else {}
    preview = output.get("parsed_json")
    if isinstance(preview, dict):
        preview = {
            key: value
            for key, value in preview.items()
            if key in {"discovery_dimensions", "candidates", "converged_choices", "metadata"}
        }
    return {
        "trace_id": trace.get("trace_id"),
        "phase": trace.get("phase"),
        "role": trace.get("role"),
        "attempt": trace.get("attempt"),
        "error": output.get("error"),
        "schema_valid": output.get("schema_valid"),
        "overall_verdict": output.get("overall_verdict"),
        "retry_hint": output.get("retry_hint"),
        "parsed_json_preview": preview,
    }


def _write_output(payload: Dict[str, Any], output_path: str | Path | None) -> None:
    """把结果打印到 stdout，并按需落盘。"""
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    print(text)
    if output_path:
        target_path = Path(output_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(text, encoding="utf-8")


def _run_llm_probe() -> Dict[str, Any]:
    """验证 llm_client 最小直连。"""
    client = load_llm_client_from_config()
    if client is None:
        raise RuntimeError("当前 llm_config 未成功加载，无法执行 llm_probe。")

    started_at = time.time()
    response = client.call(
        [
            {"role": "system", "content": "你是一个只返回 JSON 的助手。"},
            {"role": "user", "content": "请只回复 {\"ok\": true, \"msg\": \"hello\"}"},
        ]
    )
    elapsed_sec = round(time.time() - started_at, 2)
    return {
        "mode": "llm_probe",
        "elapsed_sec": elapsed_sec,
        "response_preview": response[:600],
    }


def _run_single_node_discovery(bundle: Dict[str, Any], node_id: str, max_retries: int) -> Dict[str, Any]:
    """仅验证单节点 Discovery。"""
    skill_graph = bundle["skill_graph"]
    node = _resolve_node(skill_graph, node_id)
    provider = _make_provider()
    prompts = domain_skill_runtime._resolve_template_prompts(node.get("template_id", ""))
    context_bundle = agent_protocol.build_context_bundle(
        node=node,
        root_skill_contract=bundle["root_skill_contract"],
        clarification_gate_report=bundle["clarification_gate_report"],
        skill_graph=skill_graph,
        coupled_domain_summaries={},
    )

    runner = agent_protocol.AgentPhaseRunner(
        phase="discovery",
        provider=provider,
        max_retries=max_retries,
    )
    result, traces, final_eval = runner.run(
        context_bundle=context_bundle,
        template_prompts=prompts,
        node=node,
        skill_instance_id=node.get("instance_id", ""),
        root_skill_contract=bundle["root_skill_contract"],
        clarification_gate_report=bundle["clarification_gate_report"],
        skill_graph=skill_graph,
    )

    return {
        "mode": "single_node_discovery",
        "node_id": node_id,
        "status": "completed" if result is not None else "failed",
        "result": result,
        "trace_count": len(traces),
        "traces": [_trace_summary(trace) for trace in traces],
        "final_eval": final_eval,
    }


def _run_single_node_full_stage4(bundle: Dict[str, Any], node_id: str, max_retries: int) -> Dict[str, Any]:
    """验证单节点完整三阶段。"""
    skill_graph = bundle["skill_graph"]
    node = _resolve_node(skill_graph, node_id)
    provider = _make_provider()
    prompts = domain_skill_runtime._resolve_template_prompts(node.get("template_id", ""))
    context_bundle = agent_protocol.build_context_bundle(
        node=node,
        root_skill_contract=bundle["root_skill_contract"],
        clarification_gate_report=bundle["clarification_gate_report"],
        skill_graph=skill_graph,
        coupled_domain_summaries={},
    )

    result = agent_protocol.run_agent_stage4_for_node(
        node=node,
        context_bundle=context_bundle,
        template_prompts=prompts,
        provider=provider,
        root_skill_contract=bundle["root_skill_contract"],
        clarification_gate_report=bundle["clarification_gate_report"],
        skill_graph=skill_graph,
        max_retries=max_retries,
        phase_scope=bundle["session"].target_phase,
    )

    design_space = result.get("design_space_report", {})
    candidates = result.get("realization_candidates", {})
    converged = result.get("converged_realization_pack", {})
    return {
        "mode": "single_node_full_stage4",
        "node_id": node_id,
        "status": result.get("status"),
        "failure_reason": result.get("failure_reason"),
        "provider_type": result.get("provider_type"),
        "trace_count": len(result.get("traces", [])),
        "traces": [_trace_summary(trace) for trace in result.get("traces", [])],
        "evaluation_results": result.get("evaluation_results", {}),
        "design_space_dimension_count": len(design_space.get("discovery_dimensions", []) or []),
        "candidate_group_count": len(candidates.get("candidates", []) or []),
        "converged_choice_count": len(
            converged.get("converged_choices")
            or converged.get("convergence_decisions", [])
            or []
        ),
    }


def _run_subset_stage4(bundle: Dict[str, Any], node_ids: List[str], max_retries: int) -> Dict[str, Any]:
    """验证一小组节点的 Stage 4 三阶段。"""
    skill_graph = bundle["skill_graph"]
    ordered_nodes = domain_skill_runtime._topological_execution_order(skill_graph.get("nodes", []))
    selected_ids = set(node_ids)
    selected_nodes = [node for node in ordered_nodes if node.get("instance_id") in selected_ids]
    provider = _make_provider()

    converged_entries: List[Dict[str, Any]] = []
    status_map: Dict[str, str] = {}
    node_results: List[Dict[str, Any]] = []

    for node in selected_nodes:
        instance_id = node.get("instance_id", "")
        dependency_ids = node.get("dependencies", [])
        unmet_dependencies = [
            dependency_id
            for dependency_id in dependency_ids
            if dependency_id in selected_ids and status_map.get(dependency_id) != "completed"
        ]
        if unmet_dependencies:
            node_results.append(
                {
                    "node_id": instance_id,
                    "status": "skipped",
                    "reason": "dependencies_not_completed_in_subset",
                    "unmet_dependencies": unmet_dependencies,
                }
            )
            status_map[instance_id] = "skipped"
            continue

        prompts = domain_skill_runtime._resolve_template_prompts(node.get("template_id", ""))
        context_bundle = agent_protocol.build_context_bundle(
            node=node,
            root_skill_contract=bundle["root_skill_contract"],
            clarification_gate_report=bundle["clarification_gate_report"],
            skill_graph=skill_graph,
            coupled_domain_summaries=domain_skill_runtime._collect_coupled_summaries(
                node,
                converged_entries,
                status_map,
            ),
        )
        result = agent_protocol.run_agent_stage4_for_node(
            node=node,
            context_bundle=context_bundle,
            template_prompts=prompts,
            provider=provider,
            root_skill_contract=bundle["root_skill_contract"],
            clarification_gate_report=bundle["clarification_gate_report"],
            skill_graph=skill_graph,
            max_retries=max_retries,
            phase_scope=bundle["session"].target_phase,
        )
        if result.get("status") == "failed":
            node_results.append(
                {
                    "node_id": instance_id,
                    "status": "failed",
                    "failure_reason": result.get("failure_reason"),
                    "trace_count": len(result.get("traces", [])),
                    "traces": [_trace_summary(trace) for trace in result.get("traces", [])],
                }
            )
            status_map[instance_id] = "failed"
            continue

        fragment = domain_skill_runtime._build_discovered_fragment(
            node=node,
            root_skill_contract=bundle["root_skill_contract"],
            clarification_gate_report=bundle["clarification_gate_report"],
            design_space_report=result["design_space_report"],
            converged_pack=result["converged_realization_pack"],
            phase_scope=bundle["session"].target_phase,
        )
        acceptance_errors = domain_skill_runtime._validate_stage4_node_acceptance(
            design_space_report=result["design_space_report"],
            realization_candidates=result["realization_candidates"],
            converged_pack=result["converged_realization_pack"],
            fragment=fragment,
        )
        if acceptance_errors:
            node_results.append(
                {
                    "node_id": instance_id,
                    "status": "failed",
                    "failure_reason": "stage4_acceptance_failed",
                    "acceptance_errors": acceptance_errors,
                    "trace_count": len(result.get("traces", [])),
                    "traces": [_trace_summary(trace) for trace in result.get("traces", [])],
                }
            )
            status_map[instance_id] = "failed"
            continue

        converged_entries.append(result["converged_realization_pack"])
        status_map[instance_id] = "completed"
        node_results.append(
            {
                "node_id": instance_id,
                "status": "completed",
                "trace_count": len(result.get("traces", [])),
                "design_space_dimension_count": len(result["design_space_report"].get("discovery_dimensions", []) or []),
                "candidate_group_count": len(result["realization_candidates"].get("candidates", []) or []),
                "converged_choice_count": len(
                    result["converged_realization_pack"].get("converged_choices")
                    or result["converged_realization_pack"].get("convergence_decisions", [])
                    or []
                ),
            }
        )

    return {
        "mode": "subset_stage4",
        "selected_node_ids": [node.get("instance_id", "") for node in selected_nodes],
        "results": node_results,
    }


def _build_parser() -> argparse.ArgumentParser:
    """构建 CLI 参数。"""
    parser = argparse.ArgumentParser(description="Stage 4 分段验证脚本")
    parser.add_argument(
        "--mode",
        required=True,
        choices=[
            "llm_probe",
            "single_node_discovery",
            "single_node_full_stage4",
            "subset_stage4",
        ],
        help="选择验证模式",
    )
    parser.add_argument(
        "--session-path",
        default=str(PROJECT_ROOT / "ProjectState" / "runs" / "run-20260416-092018-f6b8" / "session.json"),
        help="session.json 路径",
    )
    parser.add_argument(
        "--node-id",
        default="skill-board-topology",
        help="单节点验证使用的 node_id",
    )
    parser.add_argument(
        "--node-ids",
        default="",
        help="subset_stage4 使用的逗号分隔 node_id 列表；为空时默认取前两个 discovery-capable 节点",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=2,
        help="AgentPhaseRunner 最大重试次数",
    )
    parser.add_argument(
        "--output",
        default="",
        help="可选：把结果 JSON 额外写入指定路径",
    )
    return parser


def main() -> int:
    """CLI 主入口。"""
    parser = _build_parser()
    args = parser.parse_args()

    try:
        if args.mode == "llm_probe":
            result = _run_llm_probe()
            _write_output(result, args.output or None)
            return 0

        bundle = _load_session_bundle(args.session_path)
        if args.mode == "single_node_discovery":
            result = _run_single_node_discovery(bundle, args.node_id, args.max_retries)
        elif args.mode == "single_node_full_stage4":
            result = _run_single_node_full_stage4(bundle, args.node_id, args.max_retries)
        else:
            node_ids = [item.strip() for item in args.node_ids.split(",") if item.strip()]
            if not node_ids:
                node_ids = [
                    node.get("instance_id", "")
                    for node in _default_discovery_nodes(bundle["skill_graph"])[:2]
                ]
            result = _run_subset_stage4(bundle, node_ids, args.max_retries)

        _write_output(result, args.output or None)
        return 0
    except Exception as exc:
        error_payload = {
            "status": "error",
            "mode": args.mode,
            "error": str(exc),
        }
        _write_output(error_payload, args.output or None)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
