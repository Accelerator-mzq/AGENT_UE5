"""HUD 总监裁决试点主脚本。

3 专家（UX/UI程序/美术）各自发现维度 → 立场 → 中立总监语义整合裁决，
产出 HUD fragment + 裁决记录（与单专家版的对比在后续步骤生成）。

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


# 中立总监 system prompt（试点内联；CCGS 无对应 persona，本项目编译链特有）
ARBITER_PROMPT = (
    "你是中立的设计整合者，不偏向 UX / UI 程序 / 美术任何一方。"
    "给你三位专家对一组 HUD 设计维度的各自主张。"
    "对每个维度，识别三方是“说法不同但意思相同”（合并成一个连贯统一的表述），"
    "还是“存在真实设计分歧”（择优选择并说明理由；若三方诉求真实对立、"
    "无法在不牺牲某方硬需求下调和，则标记 unresolved=true）。"
    "必须遵守给定的 GDD locked 约束，不得违反。只输出 JSON，不要解释文字。"
)


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


def _call(client, system_prompt: str, user_prompt: str, diag: dict | None = None) -> dict:
    """调用 LLM 并返回解析后的 dict。

    diag: 可选诊断字典，调用者传入后此函数会向其写入：
      - diag["raw"]    原始 LLM 文本（解析前）
      - diag["reason"] 异常信息（仅 call_error 时）
      调用者可通过检查 diag 内容判断空结果的真因。
    """
    try:
        raw = client.call([
            {"role": "system", "content": system_prompt + "\n只返回一个合法 JSON object。"},
            {"role": "user", "content": user_prompt},
        ])
        # 诊断留痕：拿到原始文本后立即写入 diag，无论后续解析是否成功
        if diag is not None:
            diag["raw"] = raw
    except Exception as exc:  # noqa: BLE001
        # 诊断留痕：网络/SDK 异常写入 diag
        if diag is not None:
            diag["reason"] = str(exc)
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


def arbitrate(client, ctx: str, dims: list, stances: dict, diag: dict | None = None) -> dict:
    """中立总监一次性裁决：读三方立场，逐维度语义整合。

    返回 {dimension_id: {final_choice, integration_note, unresolved}}。
    失败时（网络错误/JSON 解析失败/格式异常）返回空 dict 或剔除异常项，
    交由 assemble_arbitration_result 以 arbiter_missing 兜底留痕（可追溯，不崩溃）。

    diag: 可选诊断字典，透传给 _call，最终持有裁决调用的原始 LLM 文本，
          以及额外补充 out_keys（解析后顶层 keys）以便判断格式遵从情况。
    """
    dim_ids = [d.get("dimension_id", "") for d in dims if d.get("dimension_id")]
    # 诊断留痕：把 diag 透传给 _call，原始 LLM 文本将写入 diag["raw"]
    out = _call(client, ARBITER_PROMPT,
                ctx + f"\n## 待裁决维度全集\n{json.dumps(dim_ids, ensure_ascii=False)}\n"
                f"## 三方立场\n{json.dumps(stances, ensure_ascii=False)}\n"
                "## 任务\n对每个维度做语义整合裁决。"
                "输出 JSON: {\"arbitration\":{\"hud.xxx\":"
                "{\"final_choice\":\"..\",\"integration_note\":\"..\",\"unresolved\":false}}}",
                diag)
    # 诊断留痕：记录解析后的顶层 keys，以便区分"格式不遵从"（key 不叫 arbitration）和"真空"
    if diag is not None:
        diag["out_keys"] = list(out.keys()) if isinstance(out, dict) else None
    result = out.get("arbitration", {})
    if not isinstance(result, dict):
        return {}
    # 仅保留 value 为 dict 的裁决项；异常项剔除后由 assemble_arbitration_result 走 arbiter_missing 兜底留痕
    return {k: v for k, v in result.items() if isinstance(v, dict)}


def run_pilot() -> int:
    from Plugins.AgentBridge.Compiler.stages.llm_client import load_llm_client_from_config
    client = load_llm_client_from_config()
    if client is None:
        print("ERROR: llm_client 加载失败（需带 anthropic SDK 的解释器）")
        return 1
    print("LLM:", client.model)

    contract = _load("root_skill_contract.json")
    ctx = _context_block(contract)
    log: dict = {"experts": EXPERT_PRIORITY}

    # 阶段1 各自发现 → 合并
    discovered = [(e, discover(client, e, ctx)) for e in EXPERT_PRIORITY]
    merged = core.merge_discovered_dimensions(discovered)
    log["discovered_per_expert"] = {e: [d.get("dimension_id") for d in dl] for e, dl in discovered}
    log["merged_dimensions"] = merged

    # 阶段2 各自立场
    stances = {e: stance(client, e, ctx, merged) for e in EXPERT_PRIORITY}
    log["stances"] = stances

    # 阶段3 中立总监裁决（一次性，语义整合，无字符串比较）
    arb_diag: dict = {}
    arbitration = arbitrate(client, ctx, merged, stances, arb_diag)
    log["arbitration"] = arbitration
    log["arbitration_diag"] = arb_diag   # 诊断留痕：裁决调用的原始 LLM 文本（截断/格式不遵从/真空均可辨）

    # 阶段4 装配（正常/unresolved/missing 三情况由 core 处理）
    final, gaps = core.assemble_arbitration_result(merged, arbitration, stances)
    log["capability_gaps"] = gaps

    fragment = {
        "fragment_version": "2.0",
        "skill_instance_id": "skill-baseline-hud",
        "template_id": "baseline.hud.realization_eligible",
        "domain_type": "baseline",
        "phase_scope": "phase11_hud_arbiter_pilot",
        "status": "completed",
        "emitted_families": ["hud_spec"],
        "spec_fragments": {"hud_spec": {
            "capability": "HUD",
            "realization_class": "realization_eligible",
            "required_elements": contract.get("constraint_fields", {}).get("ui.required_hud_fields", {}).get("value", []),
            "selected_realization": final,
        }},
        "capability_gaps": gaps,
        "metadata": {"generator": "HUD-Arbiter-Pilot", "promotable": False, "mode": "arbiter_pilot"},
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "hud_arbiter_fragment.json").write_text(
        json.dumps(fragment, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT_DIR / "hud_arbiter_log.json").write_text(
        json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print("已落盘 arbiter fragment + log；维度数:", len(merged), "| 未解分歧/遗漏数:", len(gaps))
    return 0


if __name__ == "__main__":
    sys.exit(run_pilot())
