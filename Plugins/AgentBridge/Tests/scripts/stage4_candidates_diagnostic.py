"""
Stage 4 Candidates 诊断脚本。

目标：
  - 验证当前问题更像“prompt 太重”还是“provider 本身就不稳”
  - 对比小请求基线、分批输入、压缩输入、完整输入
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
    """加载 session 及 Stage 1-3 产物。"""
    session = CompilerSession.load(Path(session_path))
    return {
        "session": session,
        "root_skill_contract": pipeline_orchestrator._load_stage_artifact(session, 1) or {},
        "clarification_gate_report": pipeline_orchestrator._load_stage_artifact(session, 2) or {},
        "skill_graph": pipeline_orchestrator._load_stage_artifact(session, 3) or {},
    }


def _load_discovery_result(discovery_path: str | Path) -> Dict[str, Any]:
    """读取单节点 Discovery 成功结果。"""
    payload = json.loads(Path(discovery_path).read_text(encoding="utf-8"))
    result = payload.get("result", {})
    if not isinstance(result, dict) or not result:
        raise ValueError("discovery 结果为空，无法构造 Candidates 诊断输入。")
    return result


def _resolve_node(skill_graph: Dict[str, Any], node_id: str) -> Dict[str, Any]:
    """根据 node_id 查找节点。"""
    for node in skill_graph.get("nodes", []):
        if node.get("instance_id") == node_id:
            return node
    raise ValueError(f"未找到节点：{node_id}")


def _node_summary(node: Dict[str, Any]) -> Dict[str, Any]:
    """保留 Candidates 所需的最小节点摘要。"""
    return {
        "instance_id": node.get("instance_id", ""),
        "template_id": node.get("template_id", ""),
        "domain_type": node.get("domain_type", ""),
        "capability_id": node.get("capability_id", ""),
        "allows_design_space_discovery": node.get("allows_design_space_discovery", False),
        "dependencies": node.get("dependencies", []),
        "coupling": node.get("coupling", []),
    }


def _build_full_context(
    bundle: Dict[str, Any],
    node: Dict[str, Any],
    discovery_result: Dict[str, Any],
) -> Dict[str, Any]:
    """构造当前主链的完整 Candidates 上下文。"""
    context_bundle = agent_protocol.build_context_bundle(
        node=node,
        root_skill_contract=bundle["root_skill_contract"],
        clarification_gate_report=bundle["clarification_gate_report"],
        skill_graph=bundle["skill_graph"],
        coupled_domain_summaries={},
    )
    full_context = dict(context_bundle)
    full_context["design_space_report"] = discovery_result
    return full_context


def _build_compact_context(
    bundle: Dict[str, Any],
    node: Dict[str, Any],
    discovery_result: Dict[str, Any],
) -> Dict[str, Any]:
    """压缩版 Candidates 上下文：保留所有维度，但去掉大块弱相关信息。"""
    full_context = _build_full_context(bundle, node, discovery_result)
    return {
        "structural": {
            "root_skill_contract_id": full_context.get("structural", {}).get("root_skill_contract_id", ""),
            "skill_graph_node": {
                "current_node": _node_summary(node),
                "dependency_nodes": full_context.get("structural", {}).get("skill_graph_node", {}).get("dependency_nodes", []),
                "coupling_nodes": full_context.get("structural", {}).get("skill_graph_node", {}).get("coupling_nodes", []),
            },
        },
        "semantic": {
            "coupled_domain_summaries": full_context.get("semantic", {}).get("coupled_domain_summaries", {}),
        },
        "design_space_report": {
            "discovery_dimensions": discovery_result.get("discovery_dimensions", []),
            "locked_dimensions": discovery_result.get("locked_dimensions", []),
        },
    }


def _build_batch_context(
    bundle: Dict[str, Any],
    node: Dict[str, Any],
    discovery_result: Dict[str, Any],
    dimension_index: int = 0,
) -> Dict[str, Any]:
    """按维度分批的 Candidates 上下文：一次只保留一个 discovery 维度。"""
    dimensions = discovery_result.get("discovery_dimensions", []) or []
    if not dimensions:
        raise ValueError("discovery_dimensions 为空，无法构造 batch Candidates 输入。")
    if dimension_index < 0 or dimension_index >= len(dimensions):
        raise ValueError(f"dimension_index 越界：{dimension_index}")

    compact_context = _build_compact_context(bundle, node, discovery_result)
    compact_context["design_space_report"] = {
        "discovery_dimensions": [dimensions[dimension_index]],
        "locked_dimensions": discovery_result.get("locked_dimensions", []),
    }
    return compact_context


def _build_messages(
    provider: agent_protocol.LLMProvider,
    node: Dict[str, Any],
    prompts: Dict[str, Any],
    context_bundle: Dict[str, Any],
) -> List[Dict[str, str]]:
    """构造当前变体要发送给 LLM 的消息。"""
    phase_instruction = provider._phase_instruction("candidates", {})
    system_prompt = provider._build_strict_system_prompt(
        prompts.get("system_prompt", ""),
        "candidates",
    )
    user_message = provider._build_user_message(
        phase="candidates",
        domain_prompt=prompts.get("domain_prompt", ""),
        context_bundle=context_bundle,
        phase_instruction=phase_instruction,
        node=node,
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]


def _raw_call_once(client: Any, messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """执行一次最原始的 provider 调用。"""
    started_at = time.time()
    try:
        raw_response = client.call(messages)
        elapsed_sec = round(time.time() - started_at, 2)
        return {
            "status": "ok",
            "elapsed_sec": elapsed_sec,
            "response_chars": len(raw_response or ""),
            "response_preview": (raw_response or "")[:800],
            "starts_with_json": (raw_response or "").lstrip().startswith("{"),
        }
    except Exception as exc:
        elapsed_sec = round(time.time() - started_at, 2)
        return {
            "status": "error",
            "elapsed_sec": elapsed_sec,
            "error": str(exc),
        }


def _phase_generate_once(
    provider: agent_protocol.LLMProvider,
    node: Dict[str, Any],
    prompts: Dict[str, Any],
    context_bundle: Dict[str, Any],
    bundle: Dict[str, Any],
) -> Dict[str, Any]:
    """执行一次真实的 Candidates phase generate。"""
    started_at = time.time()
    try:
        result = provider.generate(
            phase="candidates",
            context_bundle=context_bundle,
            template_prompts=prompts,
            node=node,
            design_space_report=context_bundle.get("design_space_report", {}),
            root_skill_contract=bundle["root_skill_contract"],
            clarification_gate_report=bundle["clarification_gate_report"],
            skill_graph=bundle["skill_graph"],
        )
        elapsed_sec = round(time.time() - started_at, 2)
        normalized = agent_protocol.normalize_phase_output("candidates", result)
        validation_errors = agent_protocol.validate_phase_output_for_acceptance("candidates", normalized)
        return {
            "status": "ok",
            "elapsed_sec": elapsed_sec,
            "validation_errors": validation_errors,
            "candidate_group_count": len(normalized.get("candidates", []) or []),
            "parsed_preview": normalized,
        }
    except Exception as exc:
        elapsed_sec = round(time.time() - started_at, 2)
        return {
            "status": "error",
            "elapsed_sec": elapsed_sec,
            "error": str(exc),
        }


def _run_provider_stability_probe(client: Any, repeats: int) -> Dict[str, Any]:
    """小请求基线：验证 provider 自身稳定性。"""
    messages = [
        {"role": "system", "content": "你必须只返回一个合法 JSON object。禁止解释文字。"},
        {"role": "user", "content": "请只返回 {\"ok\": true, \"msg\": \"hello\"}"},
    ]
    runs = [_raw_call_once(client, messages) for _ in range(repeats)]
    return {
        "label": "provider_small_probe",
        "message_lengths": {
            "system_chars": len(messages[0]["content"]),
            "user_chars": len(messages[1]["content"]),
        },
        "raw_runs": runs,
    }


def _run_variant(
    label: str,
    client: Any,
    provider: agent_protocol.LLMProvider,
    node_for_message: Dict[str, Any],
    prompts: Dict[str, Any],
    context_bundle: Dict[str, Any],
    bundle: Dict[str, Any],
    raw_repeats: int,
    run_phase_generate: bool,
) -> Dict[str, Any]:
    """执行一个 Candidates 负载变体。"""
    messages = _build_messages(provider, node_for_message, prompts, context_bundle)
    raw_runs = [_raw_call_once(client, messages) for _ in range(raw_repeats)]
    result = {
        "label": label,
        "message_lengths": {
            "system_chars": len(messages[0]["content"]),
            "user_chars": len(messages[1]["content"]),
        },
        "context_stats": {
            "discovery_dimension_count": len(
                (context_bundle.get("design_space_report", {}) or {}).get("discovery_dimensions", []) or []
            ),
            "locked_dimension_count": len(
                (context_bundle.get("design_space_report", {}) or {}).get("locked_dimensions", []) or []
            ),
            "top_level_keys": list(context_bundle.keys()),
        },
        "raw_runs": raw_runs,
    }
    if run_phase_generate:
        result["phase_generate"] = _phase_generate_once(
            provider=provider,
            node=node_for_message,
            prompts=prompts,
            context_bundle=context_bundle,
            bundle=bundle,
        )
    return result


def _build_parser() -> argparse.ArgumentParser:
    """构造 CLI 参数。"""
    parser = argparse.ArgumentParser(description="Stage 4 Candidates prompt/provider 对照实验")
    parser.add_argument(
        "--session-path",
        default=str(PROJECT_ROOT / "ProjectState" / "runs" / "run-20260416-092018-f6b8" / "session.json"),
        help="session.json 路径",
    )
    parser.add_argument(
        "--discovery-path",
        default=str(PROJECT_ROOT / "ProjectState" / "Reports" / "2026-04-16" / "stage4_segmented_single_node_discovery.json"),
        help="已通过的单节点 Discovery 结果路径",
    )
    parser.add_argument(
        "--node-id",
        default="skill-board-topology",
        help="目标节点",
    )
    parser.add_argument(
        "--baseline-repeats",
        type=int,
        default=3,
        help="provider 小请求基线重复次数",
    )
    parser.add_argument(
        "--variant-raw-repeats",
        type=int,
        default=1,
        help="每个 Candidates 变体的原始调用重复次数",
    )
    parser.add_argument(
        "--output",
        default=str(PROJECT_ROOT / "ProjectState" / "Reports" / "2026-04-16" / "stage4_candidates_prompt_vs_provider_diagnostic.json"),
        help="输出 JSON 路径",
    )
    return parser


def main() -> int:
    """CLI 主入口。"""
    parser = _build_parser()
    args = parser.parse_args()

    try:
        bundle = _load_session_bundle(args.session_path)
        discovery_result = _load_discovery_result(args.discovery_path)
        node = _resolve_node(bundle["skill_graph"], args.node_id)
        node_summary = _node_summary(node)
        prompts = domain_skill_runtime._resolve_template_prompts(node.get("template_id", ""))
        llm_client = load_llm_client_from_config()
        if llm_client is None:
            raise RuntimeError("当前 llm_config 未成功加载，无法执行诊断。")
        provider = agent_protocol.LLMProvider(llm_client)

        full_context = _build_full_context(bundle, node, discovery_result)
        compact_context = _build_compact_context(bundle, node, discovery_result)
        batch_context = _build_batch_context(bundle, node, discovery_result, dimension_index=0)

        payload = {
            "mode": "stage4_candidates_prompt_vs_provider_diagnostic",
            "config_snapshot": {
                "provider": getattr(llm_client, "provider", ""),
                "model": getattr(llm_client, "model", ""),
                "base_url": getattr(llm_client, "base_url", ""),
                "timeout_sec": getattr(llm_client, "timeout_sec", None),
            },
            "node_id": node.get("instance_id", ""),
            "baseline": _run_provider_stability_probe(llm_client, args.baseline_repeats),
            "variants": [
                _run_variant(
                    label="candidates_batch_single_dimension",
                    client=llm_client,
                    provider=provider,
                    node_for_message=node_summary,
                    prompts=prompts,
                    context_bundle=batch_context,
                    bundle=bundle,
                    raw_repeats=args.variant_raw_repeats,
                    run_phase_generate=True,
                ),
                _run_variant(
                    label="candidates_compact_all_dimensions",
                    client=llm_client,
                    provider=provider,
                    node_for_message=node_summary,
                    prompts=prompts,
                    context_bundle=compact_context,
                    bundle=bundle,
                    raw_repeats=args.variant_raw_repeats,
                    run_phase_generate=False,
                ),
                _run_variant(
                    label="candidates_full_all_dimensions",
                    client=llm_client,
                    provider=provider,
                    node_for_message=node,
                    prompts=prompts,
                    context_bundle=full_context,
                    bundle=bundle,
                    raw_repeats=args.variant_raw_repeats,
                    run_phase_generate=False,
                ),
            ],
        }

        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"status": "ok", "output_path": str(output_path.resolve())}, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        error_payload = {
            "status": "error",
            "error": str(exc),
        }
        print(json.dumps(error_payload, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
