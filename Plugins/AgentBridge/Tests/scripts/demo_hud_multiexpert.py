"""HUD 多专家协商试点主脚本。

3 专家（UX/UI程序/美术）各自发现维度 → 立场 → 多轮协商 → 收敛/降级，
产出 HUD fragment + 协商记录（与单专家版的对比在后续步骤生成）。

须用带 anthropic SDK 的解释器运行：
  C:\\Python312\\python.exe Plugins/AgentBridge/Tests/scripts/demo_hud_multiexpert.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Plugins.AgentBridge.Tests.scripts import hud_multiexpert_core as core  # noqa: E402

SRC_RUN = PROJECT_ROOT / "ProjectState" / "runs" / "run-20260417-051444-a2b8"
OUT_DIR = PROJECT_ROOT / "ProjectState" / "Reports" / "2026-05-31"
MAX_ROUNDS = 2  # 试点：限制协商轮数以控制 token 消耗
EXPERT_PRIORITY = ["ux-designer", "ui-programmer", "art-director"]

# 3 专家 system prompt（试点内联；推广时抽出为 SkillTemplate persona）
EXPERT_PROMPTS = {
    "ux-designer": (
        "你是游戏 UX 设计师。你只从用户体验角度参与 HUD 设计："
        "信息完整性、可读性、玩家认知负担、无障碍（色盲/文字缩放）、多玩家信息对称。"
        "你不决定视觉风格细节，也不评估底层实现可行性。"
        "必须遵守给定的 GDD locked 约束，不得违反。只输出 JSON，不要解释文字。"
    ),
    "ui-programmer": (
        "你是 UI 程序员。你只从实现角度参与 HUD 设计："
        "数据绑定可行性、刷新频率/触发时机、性能、UI 绝不持有或修改 gameplay 状态（只展示）。"
        "你不决定视觉美感，也不替 UX 定义信息取舍。"
        "必须遵守给定的 GDD locked 约束。只输出 JSON，不要解释文字。"
    ),
    "art-director": (
        "你是美术总监。你只从视觉角度参与 HUD 设计："
        "布局方向、视觉主题一致性、不遮挡棋盘、Monopoly 识别度、视觉层级。"
        "你不评估实现可行性，也不替 UX 定义信息密度的功能取舍。"
        "必须遵守给定的 GDD locked 约束。只输出 JSON，不要解释文字。"
    ),
}


def _load(name: str) -> dict:
    return json.loads((SRC_RUN / name).read_text(encoding="utf-8"))


def _parse_json(raw: str) -> dict:
    """从 LLM 文本中提取 JSON object（去除可能的 ``` 代码围栏）。"""
    text = (raw or "").strip()
    if text.startswith("```"):
        # 提取围栏内内容；无闭合围栏时截去前三个反引号
        inner = text.split("```", 2)[1] if "```" in text[3:] else text[3:]
        text = inner.lstrip("json").strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        return {}
    return json.loads(text[start:end + 1])


def _call(client, system_prompt: str, user_prompt: str) -> dict:
    try:
        raw = client.call([
            {"role": "system", "content": system_prompt + "\n只返回一个合法 JSON object。"},
            {"role": "user", "content": user_prompt},
        ])
    except Exception as exc:  # noqa: BLE001
        return {"call_error": True, "reason": str(exc)}
    try:
        return _parse_json(raw)
    except Exception:  # noqa: BLE001
        return {"parse_error": True, "raw": raw}


def _context_block(contract: dict) -> str:
    """给所有专家的共享上下文：GDD locked 约束 + HUD 必需字段。"""
    locked = contract.get("constraint_fields", {}).get("ui.required_hud_fields", {}).get("value", [])
    return (
        "## GDD 锁定约束（不可违反）\n"
        f"- HUD 必须显示字段: {locked}\n"
        "- 28 个格子在主相机下完整可见\n"
        "- HUD 不得遮挡购买/租金/监狱弹窗\n"
        "- 2-4 名玩家本地多人\n"
    )


def discover(client, expert: str, ctx: str) -> list:
    out = _call(client, EXPERT_PROMPTS[expert],
                ctx + "\n## 任务\n从你的专业视角，列出 HUD 的可设计维度。"
                "输出 JSON: {\"dimensions\":[{\"dimension_id\":\"hud.xxx\",\"name\":\"..\",\"description\":\"..\"}]}")
    return out.get("dimensions", [])


def stance(client, expert: str, ctx: str, dims: list) -> dict:
    dim_ids = [d.get("dimension_id", "") for d in dims if d.get("dimension_id")]
    out = _call(client, EXPERT_PROMPTS[expert],
                ctx + f"\n## 维度全集\n{dim_ids}\n## 任务\n对每个维度给出你主张的选择与理由。"
                "输出 JSON: {\"stance\":{\"hud.xxx\":{\"choice\":\"..\",\"reason\":\"..\"}}}")
    return {k: v.get("choice", "") for k, v in out.get("stance", {}).items() if isinstance(v, dict)}


def renegotiate(client, expert: str, ctx: str, all_stances: dict, conflicts: list) -> dict:
    out = _call(client, EXPERT_PROMPTS[expert],
                ctx + f"\n## 三方当前立场\n{json.dumps(all_stances, ensure_ascii=False)}\n"
                f"## 仍有分歧的维度\n{conflicts}\n## 任务\n查看其他专家立场，对分歧维度调整或坚持你的选择并说明理由。"
                "输出 JSON: {\"stance\":{\"hud.xxx\":{\"choice\":\"..\",\"reason\":\"..\"}}}")
    return {k: v.get("choice", "") for k, v in out.get("stance", {}).items() if isinstance(v, dict)}


def run_pilot() -> int:
    from Plugins.AgentBridge.Compiler.stages.llm_client import load_llm_client_from_config
    client = load_llm_client_from_config()
    if client is None:
        print("ERROR: llm_client 加载失败（需带 anthropic SDK 的解释器）")
        return 1
    print("LLM:", client.model)

    contract = _load("root_skill_contract.json")
    ctx = _context_block(contract)
    log: dict = {"max_rounds": MAX_ROUNDS, "experts": EXPERT_PRIORITY}

    # 阶段1 各自发现 → 合并
    discovered = [(e, discover(client, e, ctx)) for e in EXPERT_PRIORITY]
    merged = core.merge_discovered_dimensions(discovered)
    log["discovered_per_expert"] = {e: [d.get("dimension_id") for d in dl] for e, dl in discovered}
    log["merged_dimensions"] = merged
    owner_map = {d["dimension_id"]: core.resolve_owner(d["proposed_by"], EXPERT_PRIORITY) for d in merged}

    # 阶段2 各自立场
    stances = {e: stance(client, e, ctx, merged) for e in EXPERT_PRIORITY}
    log["round_0_stances"] = stances

    # 阶段3 多轮协商
    for rnd in range(1, MAX_ROUNDS + 1):
        conv = core.detect_convergence(stances)
        conflicts = [d for d, info in conv.items() if not info["converged"]]
        log[f"round_{rnd}_conflicts"] = conflicts
        if not conflicts:
            break
        stances = {e: {**stances[e], **renegotiate(client, e, ctx, stances, conflicts)} for e in EXPERT_PRIORITY}
        log[f"round_{rnd}_stances"] = stances

    # 阶段4 收敛/降级
    conv = core.detect_convergence(stances)
    final = {}
    gaps = []
    for did, info in conv.items():
        if info["converged"]:
            final[did] = next(iter(info["choices"].values())) if info["choices"] else ""
        else:
            final[did] = core.weighted_majority_fallback(info["choices"], owner_map.get(did, EXPERT_PRIORITY[0]))
            gaps.append({"dimension_id": did, "choices": info["choices"],
                         "resolved_by": "weighted_majority", "owner": owner_map.get(did)})
    log["final_convergence"] = conv
    log["downgraded_gaps"] = gaps

    fragment = {
        "fragment_version": "2.0",
        "skill_instance_id": "skill-baseline-hud",
        "template_id": "baseline.hud.realization_eligible",
        "domain_type": "baseline",
        "phase_scope": "phase11_hud_multiexpert_pilot",
        "status": "completed",
        "emitted_families": ["hud_spec"],
        "spec_fragments": {"hud_spec": {
            "capability": "HUD",
            "realization_class": "realization_eligible",
            "required_elements": contract.get("constraint_fields", {}).get("ui.required_hud_fields", {}).get("value", []),
            "selected_realization": final,
        }},
        "capability_gaps": gaps,
        "metadata": {"generator": "HUD-MultiExpert-Pilot", "promotable": False, "mode": "multiexpert_pilot"},
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "hud_multiexpert_fragment.json").write_text(
        json.dumps(fragment, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT_DIR / "hud_multiexpert_negotiation_log.json").write_text(
        json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print("已落盘 fragment + negotiation_log；维度数:", len(merged), "| 降级数:", len(gaps))
    return 0


if __name__ == "__main__":
    sys.exit(run_pilot())
