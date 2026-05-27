"""
Agent 交互协议 — Prompt-First Generator-Evaluator 门控模型。

实现 Doc 14 (14_Agent_Interaction_Protocol.md) 定义的交互模型：
  - GeneratorProvider 抽象：LLM 为主路径，Heuristic 为显式 fallback
  - SkillTemplate prompt 文件是 LLMProvider 的唯一 Generator 输入源
  - 结构化 Context Bundle 组装
  - Generator 调用 + schema 校验 + 格式修复
  - Evaluator 调用 + 质量维度评分
  - 重试循环（最多 2 轮重试，含首次共 3 次）
  - Trace 记录（审计 sidecar）

核心约束：
  - Generator 必须由 LLM 驱动，代码不硬编码任何设计知识
  - 无 LLM provider 时 Stage 4 拒绝执行，除非显式 allow_heuristic_fallback=True
  - heuristic_fallback 产物自动标记 promotable=False
  - SkillTemplate 的 system_prompt.md / domain_prompt.md / evaluator_prompt.md 是真正的驱动源
"""

from __future__ import annotations

import json
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import yaml


# ---------------------------------------------------------------------------
# 异常
# ---------------------------------------------------------------------------

class ProviderNotAvailable(Exception):
    """LLM provider 未配置且不允许 heuristic fallback 时抛出。"""
    pass


def _now_iso() -> str:
    """统一当前时间格式。"""
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# SkillTemplate Prompt 加载
# ---------------------------------------------------------------------------

def load_template_prompts(template_path: str | Path) -> Dict[str, str]:
    """
    从 SkillTemplate 目录读取 prompt 文件。

    返回 dict 含:
      system_prompt, domain_prompt, evaluator_prompt, manifest (YAML parsed)
    缺失的文件对应值为空字符串。
    """
    root = Path(template_path)
    prompts: Dict[str, str] = {}

    for name in ("system_prompt.md", "domain_prompt.md", "evaluator_prompt.md"):
        path = root / name
        if path.exists():
            prompts[name.replace(".md", "")] = path.read_text(encoding="utf-8")
        else:
            prompts[name.replace(".md", "")] = ""

    manifest_path = root / "manifest.yaml"
    if manifest_path.exists():
        prompts["manifest_raw"] = manifest_path.read_text(encoding="utf-8")
        prompts["manifest"] = yaml.safe_load(prompts["manifest_raw"]) or {}
    else:
        prompts["manifest_raw"] = ""
        prompts["manifest"] = {}

    input_selector_path = root / "input_selector.yaml"
    if input_selector_path.exists():
        prompts["input_selector_raw"] = input_selector_path.read_text(encoding="utf-8")
        prompts["input_selector"] = yaml.safe_load(prompts["input_selector_raw"]) or {}
    else:
        prompts["input_selector_raw"] = ""
        prompts["input_selector"] = {}

    return prompts


# ---------------------------------------------------------------------------
# Context Bundle 组装
# ---------------------------------------------------------------------------

def build_context_bundle(
    node: Dict[str, Any],
    root_skill_contract: Dict[str, Any],
    clarification_gate_report: Dict[str, Any],
    skill_graph: Dict[str, Any],
    coupled_domain_summaries: Optional[Dict[str, Any]] = None,
    prior_feedback: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """组装 Generator 的结构化输入包。分 structural 和 semantic 两层。"""
    instance_id = node.get("instance_id", "")

    # structural: 硬约束
    constraint_fields = root_skill_contract.get("constraint_fields", {})
    variant_fields = root_skill_contract.get("variant_fields", {})

    # 从 Skill Graph 中找耦合节点
    coupling_nodes = []
    dependency_nodes = []
    for edge in skill_graph.get("edges", []):
        if edge.get("from") == instance_id or edge.get("to") == instance_id:
            peer = edge["to"] if edge["from"] == instance_id else edge["from"]
            if edge.get("type") == "dependency":
                dependency_nodes.append(peer)
            elif edge.get("type") == "coupling":
                coupling_nodes.append(peer)

    # 从 clarification gate 中提取与本节点相关项
    gate_items = []
    for item in clarification_gate_report.get("items", []):
        gate_items.append(item)

    # semantic: 软信号
    soft_intents = root_skill_contract.get("soft_intents", {})
    gameplay_feel = soft_intents.get("gameplay_feel", [])
    design_tensions = soft_intents.get("design_tensions", [])

    return {
        "structural": {
            "root_skill_contract_id": root_skill_contract.get("contract_id", ""),
            "skill_graph_node": {
                "current_node": node,
                "dependency_nodes": dependency_nodes,
                "coupling_nodes": coupling_nodes,
            },
            "constraint_fields": constraint_fields,
            "variant_fields": variant_fields,
            "clarification_gate_items": gate_items,
        },
        "semantic": {
            "gameplay_feel_targets": gameplay_feel,
            "design_tensions": design_tensions,
            "coupled_domain_summaries": coupled_domain_summaries or {},
        },
        "prior_feedback": prior_feedback,
    }


# ---------------------------------------------------------------------------
# Trace 记录
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_short(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def create_trace(
    skill_instance_id: str,
    phase: str,
    role: str,
    attempt: int,
    input_data: Dict[str, Any],
    output_data: Dict[str, Any],
    provider_type: str = "unknown",
    token_usage: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    """创建一条 Agent 调用 trace 记录。"""
    return {
        "trace_id": f"trace-{skill_instance_id}-{phase}-{role}-{attempt}",
        "skill_instance_id": skill_instance_id,
        "phase": phase,
        "role": role,
        "attempt": attempt,
        "timestamp": _now_iso(),
        "provider_type": provider_type,
        "input": {
            "context_bundle_hash": _sha256_short(json.dumps(input_data, default=str)),
            "prior_feedback": input_data.get("prior_feedback"),
        },
        "output": output_data,
        "token_usage": token_usage or {"input_tokens": 0, "output_tokens": 0},
    }


# ---------------------------------------------------------------------------
# Evaluator 质量维度
# ---------------------------------------------------------------------------

DISCOVERY_DIMENSIONS = [
    "dimension_coverage",
    "non_obviousness",
    "constraint_correctness",
    "coupling_awareness",
    "granularity",
]

CANDIDATES_DIMENSIONS = [
    "real_divergence",
    "tradeoff_authenticity",
    "bounds_compliance",
    "quantity_sufficient",
    "complexity_assessment",
]

CONVERGENCE_DIMENSIONS = [
    "rationale_depth",
    "rejection_quality",
    "cross_dimension_consistency",
    "provisional_correctness",
]


def _default_evaluator_dimensions(phase: str) -> List[str]:
    """返回指定阶段的默认评审维度列表。"""
    if phase == "discovery":
        return DISCOVERY_DIMENSIONS
    elif phase == "candidates":
        return CANDIDATES_DIMENSIONS
    elif phase == "convergence":
        return CONVERGENCE_DIMENSIONS
    return []


def _is_html_response_text(text: str) -> bool:
    """检测返回内容是否明显是 HTML 页面，而不是模型 JSON。"""
    normalized = (text or "").lstrip().lower()
    return normalized.startswith("<!doctype html") or normalized.startswith("<html")


def normalize_phase_output(phase: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """按阶段对输出做轻量字段归一化，兼容常见别名。"""
    if not isinstance(payload, dict):
        return payload

    normalized = dict(payload)
    if phase == "discovery":
        if "discovery_dimensions" not in normalized and "open_dimensions" in normalized:
            normalized["discovery_dimensions"] = normalized.get("open_dimensions", [])
        normalized.setdefault("locked_dimensions", normalized.get("locked_dimensions", []))
        return normalized

    if phase == "candidates":
        if "candidates" not in normalized and "dimensions" in normalized:
            normalized["candidates"] = normalized.get("dimensions", [])
        return normalized

    if phase == "convergence":
        if "converged_choices" not in normalized and "convergence_decisions" in normalized:
            normalized["converged_choices"] = normalized.get("convergence_decisions", [])
        if "cross_dimension_consistency" not in normalized:
            normalized["cross_dimension_consistency"] = normalized.get("consistency", {})

        converged_choices = normalized.get("converged_choices", [])
        if isinstance(converged_choices, list):
            patched_choices = []
            for choice in converged_choices:
                if not isinstance(choice, dict):
                    patched_choices.append(choice)
                    continue
                patched = dict(choice)
                if "chosen_candidate" not in patched and "selected_candidate_id" in patched:
                    patched["chosen_candidate"] = patched.get("selected_candidate_id", "")
                patched_choices.append(patched)
            normalized["converged_choices"] = patched_choices
        return normalized

    return normalized


def validate_phase_output_for_acceptance(phase: str, output: Dict[str, Any]) -> List[str]:
    """按阶段校验输出是否满足最小可接受结构。"""
    if not isinstance(output, dict):
        return ["输出必须是 JSON object。"]

    errors: List[str] = []
    if output.get("empty_response"):
        errors.append("模型返回了空响应。")
    if output.get("parse_error"):
        errors.append("输出不是合法 JSON。")

    raw_response = output.get("raw_response", "")
    if isinstance(raw_response, str) and _is_html_response_text(raw_response):
        errors.append("输出看起来是 HTML 页面，不是模型 JSON。")

    normalized = normalize_phase_output(phase, output)
    if phase == "discovery":
        dimensions = normalized.get("discovery_dimensions", [])
        if not isinstance(dimensions, list) or not dimensions:
            errors.append("discovery_dimensions 必须是非空数组。")
        locked_dimensions = normalized.get("locked_dimensions", [])
        if not isinstance(locked_dimensions, list):
            errors.append("locked_dimensions 必须是数组。")
        return errors

    if phase == "candidates":
        candidates = normalized.get("candidates", [])
        if not isinstance(candidates, list) or not candidates:
            errors.append("candidates 必须是非空数组。")
            return errors
        for index, group in enumerate(candidates):
            if not isinstance(group, dict):
                errors.append(f"candidates[{index}] 必须是 object。")
                continue
            if not group.get("dimension_id"):
                errors.append(f"candidates[{index}] 缺少 dimension_id。")
            group_candidates = group.get("candidates", [])
            if not isinstance(group_candidates, list) or not group_candidates:
                errors.append(f"candidates[{index}].candidates 必须是非空数组。")
        return errors

    if phase == "convergence":
        choices = normalized.get("converged_choices", [])
        if not isinstance(choices, list) or not choices:
            errors.append("converged_choices 必须是非空数组。")
            return errors
        for index, choice in enumerate(choices):
            if not isinstance(choice, dict):
                errors.append(f"converged_choices[{index}] 必须是 object。")
                continue
            if not choice.get("dimension_id"):
                errors.append(f"converged_choices[{index}] 缺少 dimension_id。")
            if not choice.get("chosen_candidate"):
                errors.append(f"converged_choices[{index}] 缺少 chosen_candidate。")
            if not choice.get("rationale"):
                errors.append(f"converged_choices[{index}] 缺少 rationale。")
            rejected = choice.get("rejected_alternatives", [])
            if not isinstance(rejected, list):
                errors.append(f"converged_choices[{index}].rejected_alternatives 必须是数组。")
        consistency = normalized.get("cross_dimension_consistency", {})
        if consistency is not None and not isinstance(consistency, dict):
            errors.append("cross_dimension_consistency 必须是 object。")
        return errors

    return errors


# ---------------------------------------------------------------------------
# 默认启发式 Evaluator（无 LLM 时使用）
# ---------------------------------------------------------------------------

def heuristic_evaluate_discovery(output: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """启发式 Discovery Evaluator。检查结构完整性和基本质量。"""
    validation_errors = validate_phase_output_for_acceptance("discovery", output)
    if validation_errors:
        return {
            "phase": "discovery",
            "overall_verdict": "fail",
            "scores": {
                "format_validity": {
                    "score": 0.0,
                    "verdict": "fail",
                }
            },
            "specific_feedback": validation_errors,
            "retry_hint": "只返回合法 JSON，并保证 discovery_dimensions 为非空数组。",
        }

    output = normalize_phase_output("discovery", output)
    dimensions = output.get("discovery_dimensions", [])
    locked = output.get("locked_dimensions", [])
    scores = {}

    dim_count = len(dimensions)
    scores["dimension_coverage"] = {
        "score": min(1.0, dim_count / 3.0),
        "verdict": "pass" if dim_count >= 2 else "fail",
    }

    high_freedom = sum(1 for d in dimensions if d.get("design_freedom") == "high")
    scores["non_obviousness"] = {
        "score": min(1.0, high_freedom / max(1, dim_count) + 0.4),
        "verdict": "pass" if high_freedom > 0 else "revise",
    }

    scores["constraint_correctness"] = {
        "score": 1.0 if locked else 0.5,
        "verdict": "pass",
    }

    has_coupling = any(d.get("coupled_dimensions") for d in dimensions)
    scores["coupling_awareness"] = {
        "score": 0.8 if has_coupling else 0.5,
        "verdict": "pass",
    }

    granularity_ok = 2 <= dim_count <= 10
    scores["granularity"] = {
        "score": 0.9 if granularity_ok else 0.4,
        "verdict": "pass" if granularity_ok else "fail",
    }

    all_pass = all(s["verdict"] != "fail" for s in scores.values())
    min_score = min(s["score"] for s in scores.values()) if scores else 0
    overall = "pass" if all_pass and min_score >= 0.6 else "revise"

    return {
        "phase": "discovery",
        "overall_verdict": overall,
        "scores": scores,
        "specific_feedback": [],
        "retry_hint": None if overall == "pass" else "improve_coverage",
    }


def heuristic_evaluate_candidates(output: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """启发式 Candidates Evaluator。"""
    validation_errors = validate_phase_output_for_acceptance("candidates", output)
    if validation_errors:
        return {
            "phase": "candidates",
            "overall_verdict": "fail",
            "scores": {
                "format_validity": {
                    "score": 0.0,
                    "verdict": "fail",
                }
            },
            "specific_feedback": validation_errors,
            "retry_hint": "只返回合法 JSON，并保证 candidates 为非空数组。",
        }

    output = normalize_phase_output("candidates", output)
    candidates = output.get("candidates", [])
    scores = {}

    min_per_dim = min((len(cg.get("candidates", [])) for cg in candidates), default=0)
    scores["real_divergence"] = {
        "score": 0.8 if min_per_dim >= 2 else 0.4,
        "verdict": "pass" if min_per_dim >= 2 else "fail",
    }

    has_tradeoffs = all(
        c.get("trade_offs") for cg in candidates for c in cg.get("candidates", [])
    )
    scores["tradeoff_authenticity"] = {
        "score": 0.8 if has_tradeoffs else 0.4,
        "verdict": "pass" if has_tradeoffs else "revise",
    }

    all_satisfy = all(
        c.get("satisfies_bounds", True) for cg in candidates for c in cg.get("candidates", [])
    )
    scores["bounds_compliance"] = {
        "score": 1.0 if all_satisfy else 0.0,
        "verdict": "pass" if all_satisfy else "fail",
    }

    scores["quantity_sufficient"] = {
        "score": 0.9 if min_per_dim >= 2 else 0.3,
        "verdict": "pass" if min_per_dim >= 2 else "fail",
    }

    scores["complexity_assessment"] = {
        "score": 0.8,
        "verdict": "pass",
    }

    all_pass = all(s["verdict"] != "fail" for s in scores.values())
    overall = "pass" if all_pass else "revise"

    return {
        "phase": "candidates",
        "overall_verdict": overall,
        "scores": scores,
        "specific_feedback": [],
        "retry_hint": None if overall == "pass" else "improve_divergence",
    }


def heuristic_evaluate_convergence(output: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """启发式 Convergence Evaluator。"""
    validation_errors = validate_phase_output_for_acceptance("convergence", output)
    if validation_errors:
        return {
            "phase": "convergence",
            "overall_verdict": "fail",
            "scores": {
                "format_validity": {
                    "score": 0.0,
                    "verdict": "fail",
                }
            },
            "specific_feedback": validation_errors,
            "retry_hint": "只返回合法 JSON，并保证 converged_choices 为非空数组。",
        }

    output = normalize_phase_output("convergence", output)
    choices = output.get("converged_choices", [])
    scores = {}

    has_rationale = all(c.get("rationale") for c in choices)
    scores["rationale_depth"] = {
        "score": 0.8 if has_rationale else 0.3,
        "verdict": "pass" if has_rationale else "fail",
    }

    has_rejections = all(c.get("rejected_alternatives") for c in choices)
    scores["rejection_quality"] = {
        "score": 0.8 if has_rejections else 0.5,
        "verdict": "pass" if has_rejections else "revise",
    }

    consistency = output.get("cross_dimension_consistency", {})
    no_conflicts = len(consistency.get("conflicts", [])) == 0
    scores["cross_dimension_consistency"] = {
        "score": 1.0 if no_conflicts else 0.4,
        "verdict": "pass" if no_conflicts else "revise",
    }

    scores["provisional_correctness"] = {
        "score": 0.9,
        "verdict": "pass",
    }

    all_pass = all(s["verdict"] != "fail" for s in scores.values())
    overall = "pass" if all_pass else "revise"

    return {
        "phase": "convergence",
        "overall_verdict": overall,
        "scores": scores,
        "specific_feedback": [],
        "retry_hint": None if overall == "pass" else "improve_rationale",
    }


# ---------------------------------------------------------------------------
# GeneratorProvider 抽象
# ---------------------------------------------------------------------------

class GeneratorProvider(ABC):
    """Generator provider 抽象基类。"""

    @property
    @abstractmethod
    def provider_type(self) -> str:
        """返回 provider 类型标识：'llm' 或 'heuristic_fallback'。"""
        ...

    @abstractmethod
    def generate(
        self,
        phase: str,
        context_bundle: Dict[str, Any],
        template_prompts: Dict[str, str],
        node: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        执行 Generator 调用。

        参数:
          phase: 'discovery' | 'candidates' | 'convergence'
          context_bundle: build_context_bundle() 的输出
          template_prompts: load_template_prompts() 的输出
          node: Skill Graph 节点
          **kwargs: 阶段特定参数（如 design_space_report, realization_candidates）
        """
        ...


class LLMProvider(GeneratorProvider):
    """
    LLM 驱动的 Generator — 读 SkillTemplate prompt，调 LLM，解析结构化输出。

    这是 Stage 4 的规范主路径。SkillTemplate 的 prompt 文件是唯一的设计知识来源，
    代码不硬编码任何维度、候选或收敛逻辑。
    """

    def __init__(
        self,
        llm_client: Any = None,
        *,
        router: Any = None,                  # CapabilityRouter | None — 用 Any 避免 import 循环
        policy: Any = None,                  # ProviderPolicy | None
        batch_concurrency: int = 3,
        retry_policy: Any = None,            # RetryPolicySpec | None — F1 follow-up 注入口
    ) -> None:
        """
        参数:
          llm_client:  老路径 LLM 客户端(deprecated,Phase 12 后由 router 替代),保留以维持向后兼容。
          router:      新路径 CapabilityRouter(Phase 12 Stage 4 candidates 必走)。
          policy:      新路径 ProviderPolicy。
          batch_concurrency:  candidates 分批并发上限,默认 3。
          retry_policy:  RetryPolicySpec 注入口(F1 follow-up 2026-05-27);默认 None 表示用
                       RetryPolicySpec() 默认值(max_attempts=3, backoff_base_s=2.0, jitter (100,500))。
                       测试场景可注 jitter_ms=(0,1)+backoff_base_s=0.01 把测试时长压到 ms 级。

        至少要传 llm_client 或 router 其一,否则 generate() 会 raise ProviderNotAvailable
        (与旧行为一致)。
        """
        self._client = llm_client
        self._router = router
        self._policy = policy
        self._batch_concurrency = batch_concurrency
        self._retry_policy = retry_policy

    @property
    def provider_type(self) -> str:
        return "llm"

    def generate(
        self,
        phase: str,
        context_bundle: Dict[str, Any],
        template_prompts: Dict[str, str],
        node: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        # Phase 12:candidates 阶段且 router 已配 → 走新分批路径
        if phase == "candidates" and self._router is not None and self._policy is not None:
            return self._generate_candidates_via_batch(
                context_bundle=context_bundle,
                template_prompts=template_prompts,
                node=node,
            )

        if self._client is None:
            raise ProviderNotAvailable(
                "LLM client 未配置。Stage 4 要求 LLM 驱动 Generator。"
                "如果是 CI/测试环境，请在 session 中设置 allow_heuristic_fallback=True。"
            )

        # 组装 prompt
        system_prompt = self._build_strict_system_prompt(
            template_prompts.get("system_prompt", ""),
            phase,
        )
        domain_prompt = template_prompts.get("domain_prompt", "")

        # 按阶段选择指令
        phase_instruction = self._phase_instruction(phase, kwargs)

        # 组装 messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": self._build_user_message(
                phase=phase,
                domain_prompt=domain_prompt,
                context_bundle=context_bundle,
                phase_instruction=phase_instruction,
                node=node,
            )},
        ]

        # 调用 LLM
        raw_response = self._client.call(messages)

        # 解析结构化输出
        parsed = self._parse_or_repair_response(
            raw_response=raw_response,
            phase=phase,
            original_messages=messages,
        )
        if isinstance(parsed, dict):
            parsed = normalize_phase_output(phase, parsed)
            parsed.setdefault("metadata", {})
            parsed["metadata"]["generator_type"] = "llm"
            parsed["metadata"]["generated_at"] = _now_iso()
            parsed["metadata"]["promotable"] = True
        return parsed

    def _generate_candidates_via_batch(
        self,
        *,
        context_bundle: Dict[str, Any],
        template_prompts: Dict[str, str],
        node: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Phase 12 新路径:把 candidates 阶段委托给 LLMBatchExecutor 按 dimension 分批。

        Context 来源:context_bundle["design_space_report"] 必含 discovery_dimensions
        (上一阶段 Stage 3 Discovery 的产物)。本方法把 dimensions 转成 batch 输入。

        返回 payload(供 normalize_phase_output 后落 design_space_report):
          - candidates: list[dict]               — 每 dim 的 parsed_payload
          - per_dimension_batch_metadata: list   — 服务 T09 schema 扩字段
          - metadata.promotable: True iff 全 7 dim status="success"
        """
        import asyncio
        from pydantic import BaseModel

        from .candidates_batch_orchestrator import LLMBatchExecutor, RetryPolicySpec

        class CandidatesDimSchema(BaseModel):
            """单 dim 的 candidates 输出 schema(Stage 4 当前最小契约)。
            实际生产 prompt 会要求更细的字段;本类作为最小可解析骨架。"""
            dimension_id: str
            candidates: list

        # 从 context_bundle 提 dimensions(优先 design_space_report.discovery_dimensions)
        dsr = context_bundle.get("design_space_report", {})
        discovery_dims = dsr.get("discovery_dimensions") or context_bundle.get("dimensions", [])
        # 兼容 context_bundle 顶层就传 dimensions(测试常用)
        system_prompt_text = self._build_strict_system_prompt(
            template_prompts.get("system_prompt", ""),
            "candidates",
        )
        phase_instruction = self._phase_instruction("candidates", {})

        # 为每个 dim 装 prompt_messages:system + per-dim user
        batch_input = []
        for dim in discovery_dims:
            dim_id = dim.get("dimension_id") if isinstance(dim, dict) else None
            if not dim_id:
                continue
            user_content = (
                f"{phase_instruction}\n\n"
                f"目标维度:{dim_id} ({dim.get('name', '')})\n"
                f"描述:{dim.get('description', '')}\n"
                f"约束:{json.dumps(dim.get('variant_bounds', {}), ensure_ascii=False)}\n"
                f"请按 schema 给出该维度的候选 list,只返回 JSON。"
            )
            batch_input.append({
                "dimension_id": dim_id,
                "prompt_messages": [
                    {"role": "system", "content": system_prompt_text},
                    {"role": "user", "content": user_content},
                ],
            })

        executor = LLMBatchExecutor()
        # F1 follow-up:retry_policy 优先用 LLMProvider 构造时注入的,否则用默认值
        effective_retry_policy = self._retry_policy or RetryPolicySpec()
        report = asyncio.run(executor.run_candidates_batch(
            dimensions=batch_input,
            router=self._router,
            policy=self._policy,
            schema=CandidatesDimSchema,
            retry_policy=effective_retry_policy,
            concurrency=self._batch_concurrency,
        ))

        return {
            "candidates": [
                b.parsed_payload for b in report.per_dimension if b.parsed_payload
            ],
            "per_dimension_batch_metadata": [
                {
                    "dimension_id": b.dimension_id,
                    "model": b.model or "unknown",
                    "attempt_count": b.attempt_count,
                    "duration_ms": b.duration_ms,
                    "usage": b.usage or {},
                    "status": b.status,
                    "error_class": b.error_class,
                    "raw_response_id": b.raw_response_id,
                }
                for b in report.per_dimension
            ],
            "metadata": {
                "generator_type": "llm",
                "generated_at": _now_iso(),
                "promotable": report.promotable,
            },
        }

    def _build_strict_system_prompt(self, system_prompt: str, phase: str) -> str:
        """把 JSON-only 约束注入 system prompt。"""
        strict_rules = (
            "\n\n# 输出硬约束\n"
            "你必须只返回一个合法 JSON object。\n"
            "禁止输出 Markdown、代码块、解释文字、前后缀、致歉语。\n"
            "如果你无法确定，也必须返回符合结构的 JSON object，而不是空字符串。\n"
            f"当前阶段必须满足的最小结构如下：\n{self._phase_json_contract(phase)}\n"
        )
        return (system_prompt or "").strip() + strict_rules

    def _phase_instruction(self, phase: str, kwargs: Dict[str, Any]) -> str:
        """按阶段生成指令片段。"""
        if phase == "discovery":
            return (
                "请基于上述领域边界和约束，识别本域的可设计维度。"
                "对每个维度给出 dimension_id、name、description、design_freedom(high/medium/low)、"
                "variant_bounds（如有）、coupled_dimensions（如有）。"
                "同时列出 locked_dimensions（与 Constraint Fields 对应的不可变维度）。"
                "输出格式为 JSON，包含 discovery_dimensions 和 locked_dimensions 两个数组。"
            )
        elif phase == "candidates":
            return (
                "基于已发现的维度，为每个可设计维度生成 2-4 个候选方向。"
                "每个候选必须包含 candidate_id、name、description、trade_offs(pros/cons)、"
                "satisfies_bounds(bool)、estimated_complexity(low/medium/high)。"
                "输出格式为 JSON，包含 candidates 数组（按维度分组）。"
            )
        elif phase == "convergence":
            return (
                "从候选方向中为每个维度选择最终方向。"
                "每个选择必须包含 dimension_id、chosen_candidate、rationale、"
                "rejected_alternatives(含 rejection_reason)、provisional(bool)。"
                "同时检查跨维度一致性，输出 cross_dimension_consistency。"
                "输出格式为 JSON，包含 converged_choices 数组和 cross_dimension_consistency 对象。"
            )
        return ""

    def _phase_json_contract(self, phase: str) -> str:
        """返回阶段级 JSON 结构契约，供主 prompt 与 repair prompt 复用。"""
        if phase == "discovery":
            return json.dumps(
                {
                    "discovery_dimensions": [
                        {
                            "dimension_id": "string",
                            "name": "string",
                            "description": "string",
                            "design_freedom": "high|medium|low",
                            "variant_bounds": {},
                            "coupled_dimensions": [],
                        }
                    ],
                    "locked_dimensions": [],
                },
                ensure_ascii=False,
                indent=2,
            )
        if phase == "candidates":
            return json.dumps(
                {
                    "candidates": [
                        {
                            "dimension_id": "string",
                            "candidates": [
                                {
                                    "candidate_id": "string",
                                    "name": "string",
                                    "description": "string",
                                    "trade_offs": {
                                        "pros": [],
                                        "cons": [],
                                    },
                                    "satisfies_bounds": True,
                                    "estimated_complexity": "low|medium|high",
                                }
                            ],
                        }
                    ]
                },
                ensure_ascii=False,
                indent=2,
            )
        return json.dumps(
            {
                "converged_choices": [
                    {
                        "dimension_id": "string",
                        "chosen_candidate": "string",
                        "rationale": "string",
                        "rejected_alternatives": [
                            {
                                "candidate_id": "string",
                                "rejection_reason": "string",
                            }
                        ],
                        "provisional": False,
                    }
                ],
                "cross_dimension_consistency": {
                    "conflicts": [],
                },
            },
            ensure_ascii=False,
            indent=2,
        )

    def _build_user_message(
        self,
        phase: str,
        domain_prompt: str,
        context_bundle: Dict[str, Any],
        phase_instruction: str,
        node: Dict[str, Any],
    ) -> str:
        """组装发送给 LLM 的 user message。"""
        parts = [
            f"## 领域 Prompt\n\n{domain_prompt}",
            f"\n## 当前节点\n\n```json\n{json.dumps(node, ensure_ascii=False, indent=2)}\n```",
            f"\n## Context Bundle\n\n```json\n{json.dumps(context_bundle, ensure_ascii=False, indent=2, default=str)}\n```",
            f"\n## 任务：{phase}\n\n{phase_instruction}",
            f"\n## 输出格式硬约束\n\n只返回一个 JSON object，结构必须满足：\n```json\n{self._phase_json_contract(phase)}\n```",
        ]
        return "\n".join(parts)

    def _parse_or_repair_response(
        self,
        raw_response: str,
        phase: str,
        original_messages: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """先解析，再按阶段结构做 repair；空响应直接视为失败。"""
        normalized_raw = (raw_response or "").strip()
        if not normalized_raw:
            return {
                "parse_error": True,
                "empty_response": True,
                "raw_response": "",
            }

        parsed = normalize_phase_output(phase, self._parse_response(normalized_raw, phase))
        validation_errors = validate_phase_output_for_acceptance(phase, parsed)
        if not validation_errors:
            return parsed

        # 明显拿到了 HTML 页面时，不再浪费 repair 配额，直接作为 provider 失败线索返回。
        if _is_html_response_text(normalized_raw):
            parsed["validation_errors"] = validation_errors
            return parsed

        last_parsed = parsed
        for repair_attempt in range(1, 3):
            repair_messages = self._build_repair_messages(
                phase=phase,
                raw_response=normalized_raw,
                validation_errors=validation_errors,
            )
            repaired_response = self._client.call(repair_messages)
            repaired_text = (repaired_response or "").strip()
            if not repaired_text:
                last_parsed = {
                    "parse_error": True,
                    "empty_response": True,
                    "raw_response": "",
                    "repair_attempt": repair_attempt,
                }
                continue

            last_parsed = normalize_phase_output(phase, self._parse_response(repaired_text, phase))
            validation_errors = validate_phase_output_for_acceptance(phase, last_parsed)
            if not validation_errors:
                return last_parsed

        last_parsed["validation_errors"] = validation_errors
        return last_parsed

    def _build_repair_messages(
        self,
        phase: str,
        raw_response: str,
        validation_errors: List[str],
    ) -> List[Dict[str, str]]:
        """构造 schema-aware repair 消息。"""
        return [
            {
                "role": "system",
                "content": (
                    "你是 JSON 修复器。"
                    "你的唯一任务是把上一条错误输出修复成一个合法 JSON object。"
                    "禁止解释，禁止 Markdown，禁止额外文字。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"当前阶段：{phase}\n"
                    f"必须满足的 JSON 结构：\n{self._phase_json_contract(phase)}\n\n"
                    f"当前校验错误：\n- " + "\n- ".join(validation_errors) + "\n\n"
                    f"待修复的原始输出：\n{raw_response}"
                ),
            },
        ]

    def _parse_response(self, raw_response: str, phase: str) -> Dict[str, Any]:
        """从 LLM 原始输出中解析 JSON。"""
        # 尝试直接解析
        try:
            return json.loads(raw_response)
        except json.JSONDecodeError:
            pass

        # 尝试提取 ```json ... ``` 块
        import re
        json_match = re.search(r"```json\s*(.*?)\s*```", raw_response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 兜底尝试提取任意 fenced code block。
        fenced_match = re.search(r"```\s*(.*?)\s*```", raw_response, re.DOTALL)
        if fenced_match:
            try:
                return json.loads(fenced_match.group(1))
            except json.JSONDecodeError:
                pass

        # 解析失败
        return {"parse_error": True, "raw_response": raw_response[:2000]}


class HeuristicFallbackProvider(GeneratorProvider):
    """
    确定性 fallback Generator — 包装旧的 discovery/realization/convergence 启发式引擎。

    硬约束：
      - 产物 metadata 自动标记 generator_type = "heuristic_fallback"
      - 使用此 provider 的 run 自动 promotable = False
      - 仅允许在 allow_heuristic_fallback=True 时使用
    """

    @property
    def provider_type(self) -> str:
        return "heuristic_fallback"

    def generate(
        self,
        phase: str,
        context_bundle: Dict[str, Any],
        template_prompts: Dict[str, str],
        node: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        # 延迟导入，避免循环依赖
        from . import discovery_fallback
        from . import realization_fallback
        from . import convergence_fallback

        root_skill_contract = context_bundle.get("structural", {})
        # 还原完整 root_skill_contract（从 context_bundle 中）
        full_rsc = kwargs.get("root_skill_contract", {})
        clarification_gate_report = kwargs.get("clarification_gate_report", {})
        skill_graph = kwargs.get("skill_graph", {})

        if phase == "discovery":
            result = discovery_fallback.create_design_space_report(
                node=node,
                root_skill_contract=full_rsc,
                clarification_gate_report=clarification_gate_report,
                source_graph_id=skill_graph.get("graph_id", ""),
            )
        elif phase == "candidates":
            design_space_report = kwargs.get("design_space_report", {})
            result = realization_fallback.create_realization_candidates(
                design_space_report=design_space_report,
            )
        elif phase == "convergence":
            realization_candidates = kwargs.get("realization_candidates", {})
            phase_scope = kwargs.get("phase_scope", "phase1_local_multiplayer")
            result = convergence_fallback.create_converged_realization_pack(
                node=node,
                realization_candidates=realization_candidates,
                phase_scope=phase_scope,
            )
        else:
            raise ValueError(f"未知 phase: {phase}")

        # 标记 fallback 来源
        if isinstance(result, dict):
            result.setdefault("metadata", {})
            result["metadata"]["generator_type"] = "heuristic_fallback"
            result["metadata"]["promotable"] = False

        return result


# ---------------------------------------------------------------------------
# Provider 解析
# ---------------------------------------------------------------------------

def resolve_provider(
    allow_heuristic_fallback: bool = False,
    llm_client: Any = None,
    *,
    router: Any = None,
    policy: Any = None,
    batch_concurrency: int = 3,
    retry_policy: Any = None,           # F1 follow-up:RetryPolicySpec 注入口
) -> GeneratorProvider:
    """
    解析 Generator provider。

    规则(优先级从高到低):
      1. 有 router + policy → LLMProvider(router, policy, batch_concurrency, retry_policy) — Phase 12 新路径
      2. 有 llm_client → LLMProvider(llm_client=...) — 老路径
      3. allow_heuristic_fallback=True → HeuristicFallbackProvider
      4. 否则 raise ProviderNotAvailable

    retry_policy 仅作用于新路径(router+policy);老路径忽略。
    """
    # Phase 12 新路径优先:有 router + policy 直接走 LLMProvider 新分批入口
    if router is not None and policy is not None:
        return LLMProvider(
            router=router, policy=policy,
            batch_concurrency=batch_concurrency,
            retry_policy=retry_policy,
        )

    if llm_client is not None:
        return LLMProvider(llm_client=llm_client)

    if allow_heuristic_fallback:
        return HeuristicFallbackProvider()

    raise ProviderNotAvailable(
        "Stage 4 要求 LLM provider 驱动 Generator（Doc 14 §4 硬约束）。"
        "当前未配置 LLM client。"
        "如需使用确定性 fallback（仅限 CI/测试/fast_mode），"
        "请设置 allow_heuristic_fallback=True。"
        "注意：heuristic fallback 产出的 run 自动 promotable=False。"
    )


# ---------------------------------------------------------------------------
# Generator-Evaluator 循环
# ---------------------------------------------------------------------------

class AgentPhaseRunner:
    """
    单阶段 Generator-Evaluator 循环执行器。

    与旧版的关键区别：Generator 由 provider.generate() 驱动，
    而非接收裸 callable。
    """

    def __init__(
        self,
        phase: str,
        provider: GeneratorProvider,
        evaluator_fn: Optional[Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]] = None,
        max_retries: int = 2,
        pass_threshold: float = 0.6,
        format_repair_max: int = 2,
    ):
        self.phase = phase
        self.provider = provider
        self.evaluator_fn = evaluator_fn or self._default_evaluator()
        self.max_retries = max_retries
        self.pass_threshold = pass_threshold
        self.format_repair_max = format_repair_max

    def _default_evaluator(self) -> Callable:
        """根据 phase 选择默认启发式 evaluator。"""
        if self.phase == "discovery":
            return heuristic_evaluate_discovery
        elif self.phase == "candidates":
            return heuristic_evaluate_candidates
        elif self.phase == "convergence":
            return heuristic_evaluate_convergence
        return lambda output, ctx: {"overall_verdict": "pass", "scores": {}, "specific_feedback": []}

    def run(
        self,
        context_bundle: Dict[str, Any],
        template_prompts: Dict[str, str],
        node: Dict[str, Any],
        skill_instance_id: str = "",
        **generator_kwargs: Any,
    ) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        执行 Generator-Evaluator 循环。

        返回:
          (result, traces, final_eval)
        """
        traces: List[Dict[str, Any]] = []
        last_output = None
        last_eval = None
        feedback = context_bundle.get("prior_feedback")

        for attempt in range(1, self.max_retries + 2):
            # 注入 feedback
            gen_input = dict(context_bundle)
            if feedback:
                gen_input["prior_feedback"] = feedback

            # Generator 调用（通过 Provider）
            try:
                gen_output = self.provider.generate(
                    phase=self.phase,
                    context_bundle=gen_input,
                    template_prompts=template_prompts,
                    node=node,
                    **generator_kwargs,
                )
            except Exception as exc:
                failure_eval = {
                    "phase": self.phase,
                    "overall_verdict": "fail",
                    "scores": {},
                    "specific_feedback": [f"provider 调用失败: {str(exc)}"],
                    "retry_hint": "检查 provider 配置、base_url 和输出格式约束。",
                }
                traces.append(create_trace(
                    skill_instance_id=skill_instance_id,
                    phase=self.phase,
                    role="generator",
                    attempt=attempt,
                    input_data=gen_input,
                    output_data={"error": str(exc), "schema_valid": False},
                    provider_type=self.provider.provider_type,
                ))
                return None, traces, failure_eval
            last_output = gen_output
            phase_validation_errors = validate_phase_output_for_acceptance(self.phase, gen_output)

            traces.append(create_trace(
                skill_instance_id=skill_instance_id,
                phase=self.phase,
                role="generator",
                attempt=attempt,
                input_data=gen_input,
                output_data={
                    "parsed_json": gen_output,
                    "schema_valid": not phase_validation_errors,
                    "validation_errors": phase_validation_errors,
                },
                provider_type=self.provider.provider_type,
            ))

            # Evaluator 调用
            eval_result = self.evaluator_fn(gen_output, gen_input)
            last_eval = eval_result

            traces.append(create_trace(
                skill_instance_id=skill_instance_id,
                phase=self.phase,
                role="evaluator",
                attempt=attempt,
                input_data={"generator_output": gen_output},
                output_data=eval_result,
                provider_type="heuristic",
            ))

            # 判定
            if eval_result.get("overall_verdict") == "pass":
                return gen_output, traces, eval_result

            # 准备重试 feedback
            feedback = {
                "evaluation_result": eval_result,
                "specific_feedback": eval_result.get("specific_feedback", []),
                "retry_hint": eval_result.get("retry_hint"),
            }

        # 耗尽重试，返回最后一次产出
        return last_output, traces, last_eval


# ---------------------------------------------------------------------------
# Stage 4 三阶段编排
# ---------------------------------------------------------------------------

def run_agent_stage4_for_node(
    node: Dict[str, Any],
    context_bundle: Dict[str, Any],
    template_prompts: Dict[str, str],
    provider: GeneratorProvider,
    root_skill_contract: Dict[str, Any],
    clarification_gate_report: Dict[str, Any],
    skill_graph: Dict[str, Any],
    discovery_evaluator: Optional[Callable] = None,
    candidates_evaluator: Optional[Callable] = None,
    convergence_evaluator: Optional[Callable] = None,
    max_retries: int = 2,
    phase_scope: str = "phase1_local_multiplayer",
) -> Dict[str, Any]:
    """
    对单个 discovery-capable 节点执行三阶段 Agent 协议。

    关键变化（vs 旧版）：
      - generator 由 provider 驱动，不再接收裸 callable
      - template_prompts 从 SkillTemplate 目录加载
      - 全部 kwargs 透传给 provider.generate()
    """
    instance_id = node.get("instance_id", "")
    all_traces: List[Dict[str, Any]] = []
    eval_results: Dict[str, Any] = {}

    # 公共 kwargs（传给 HeuristicFallbackProvider 用）
    common_kwargs = {
        "root_skill_contract": root_skill_contract,
        "clarification_gate_report": clarification_gate_report,
        "skill_graph": skill_graph,
    }

    # Phase 1: Discovery
    discovery_runner = AgentPhaseRunner(
        phase="discovery",
        provider=provider,
        evaluator_fn=discovery_evaluator,
        max_retries=max_retries,
    )
    design_space, d_traces, d_eval = discovery_runner.run(
        context_bundle=context_bundle,
        template_prompts=template_prompts,
        node=node,
        skill_instance_id=instance_id,
        **common_kwargs,
    )
    all_traces.extend(d_traces)
    eval_results["discovery"] = d_eval

    if design_space is None:
        return {
            "status": "failed",
            "failure_reason": "stage4_discovery_failed",
            "traces": all_traces,
            "evaluation_results": eval_results,
        }

    # Phase 2: Candidates — 把 discovery 结果注入 context
    candidates_context = dict(context_bundle)
    candidates_context["design_space_report"] = design_space

    candidates_runner = AgentPhaseRunner(
        phase="candidates",
        provider=provider,
        evaluator_fn=candidates_evaluator,
        max_retries=max_retries,
    )
    candidates, c_traces, c_eval = candidates_runner.run(
        context_bundle=candidates_context,
        template_prompts=template_prompts,
        node=node,
        skill_instance_id=instance_id,
        design_space_report=design_space,
        **common_kwargs,
    )
    all_traces.extend(c_traces)
    eval_results["candidates"] = c_eval

    if candidates is None:
        return {
            "status": "failed",
            "failure_reason": "stage4_candidates_failed",
            "traces": all_traces,
            "evaluation_results": eval_results,
        }

    # Phase 3: Convergence
    convergence_context = dict(context_bundle)
    convergence_context["design_space_report"] = design_space
    convergence_context["realization_candidates"] = candidates
    convergence_context["phase_scope"] = phase_scope

    convergence_runner = AgentPhaseRunner(
        phase="convergence",
        provider=provider,
        evaluator_fn=convergence_evaluator,
        max_retries=max_retries,
    )
    converged, cv_traces, cv_eval = convergence_runner.run(
        context_bundle=convergence_context,
        template_prompts=template_prompts,
        node=node,
        skill_instance_id=instance_id,
        realization_candidates=candidates,
        phase_scope=phase_scope,
        **common_kwargs,
    )
    all_traces.extend(cv_traces)
    eval_results["convergence"] = cv_eval

    if converged is None:
        return {
            "status": "failed",
            "failure_reason": "stage4_convergence_failed",
            "traces": all_traces,
            "evaluation_results": eval_results,
        }

    return {
        "status": "completed",
        "design_space_report": design_space,
        "realization_candidates": candidates,
        "converged_realization_pack": converged,
        "traces": all_traces,
        "evaluation_results": eval_results,
        "provider_type": provider.provider_type,
        "failure_reason": None,
    }
