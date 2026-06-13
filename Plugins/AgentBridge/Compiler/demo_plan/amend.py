# -*- coding: utf-8 -*-
"""demo_plan 批次追加(amend):呈现批(阶梯数据驱动)与反馈批共用一个机制入口。

防固化硬约束(Phase 15 spec §9):
本模块零游戏领域语义——只消费 rung_id/story_slug/supersedes/severity 等结构字段,
"棋盘""token"等语义只存在于项目层阶梯实例/反馈条目里。
纯函数、确定性:同(现 plan + 阶梯/反馈)输入同输出;
自包含,不 import 包内其他模块(story_store 同款先例,importlib 单文件加载友好)。
"""
from typing import Any, Dict, List

# schema 版本常量(与 planner.py 保持同版本锁定)
PLAN_SCHEMA_VERSION = "1.1.0"
STORY_SCHEMA_VERSION = "1.1.0"


def _last_verified_tail(plan: Dict[str, Any], stories_by_id: Dict[str, Any]) -> str:
    """plan 顺序上最后一个全 verified 批的末位 story_id;无 → None(调用处 fail-closed)。

    扫描全部批,最后一个全 verified 批(可越过中间的 pending 批)作为锚点,与 spec §4.5 一致。
    """
    tail = None
    for batch in plan["batches"]:
        ids = batch["story_ids"]
        # 批内所有 story 都是 verified 才算全 verified 批
        if ids and all(stories_by_id[s]["status"] == "verified" for s in ids):
            tail = ids[-1]
    return tail


def _base_materials(paths: Dict[str, Any]) -> Dict[str, Any]:
    """materials 公共骨架(模板字段一律 null:呈现/反馈/文档工单不绑模板)。"""
    return {
        "gdd_path": paths["gdd_path"],
        "gdd_anchors": [],
        "contract_path": paths["contract_path"],
        "skill_graph_path": paths["skill_graph_path"],
        "template_id": None,
        "template_source": None,
        "template_dir": None,
        "construction_manifest_path": paths["construction_manifest_path"],
        "extra_paths": [],
    }


def _doc_story(batch_id: str, member_ids: List[str], manifest_version: str,
               paths: Dict[str, Any]) -> Dict[str, Any]:
    """批末文档 story(与 planner._doc_story 同形;自包含模块故意复写,不抽公共)。"""
    materials = _base_materials(paths)
    # doc_extra_paths 由调用方注入,缺省空列表
    materials["extra_paths"] = list(paths.get("doc_extra_paths", []))
    return {
        "story_schema_version": STORY_SCHEMA_VERSION,
        "story_id": f"story-{batch_id}-docs",
        "batch_id": batch_id,
        "story_kind": "documentation",
        "evidence_class": "Config",
        "depends_on": list(member_ids),  # 依赖批内所有 member story
        "materials": materials,
        "acceptance_criteria": [
            # 节号对应施工规范第 6 节;与 planner._doc_story 故意各持一份,同步时两处一并更新
            "维护文档包按施工规范 §6 写入 demo plugin 的 Docs/ 目录(设计/架构/changelog)",
            "文档只描述已 verified 的实现;结构性内容自 run 产物投影,头部标注生成物口径",
            "文档中引用的类/资产经机器引用对账存在",
        ],
        "status": "pending",
        "attempts": 0,
        "manifest_version": manifest_version,
    }


def build_presentation_amend(plan: Dict[str, Any], stories_by_id: Dict[str, Any],
                             ladder: Dict[str, Any], manifest_version: str,
                             paths: Dict[str, Any]) -> Dict[str, Any]:
    """追加呈现批:每 rung 一批(presentation-<rung_id>),批内 story 按阶梯顺序链式依赖。

    返回 {"plan": 新 plan, "new_stories": [...]}(stories_by_id 不修改);
    已存在的 presentation 批跳过(幂等),其末位 story 作为下一批锚点。

    fail-closed 规则:
    - 无任何全 verified 基底批 → 抛 ValueError("基底...")
    - pending 的增量批不参与锚点计算,呈现批只锚在最后一个全 verified 批的末位 doc
    """
    # 现有批次索引:batch_id → batch dict
    existing = {b["batch_id"]: b for b in plan["batches"]}

    # 找最后一个全 verified 批的末位 story(锚点)
    anchor = _last_verified_tail(plan, stories_by_id)
    if anchor is None:
        raise ValueError(
            "amend: 没有全 verified 的基底批,呈现批必须建立在可玩基底上(fail-closed)"
        )

    new_batches: List[Dict[str, Any]] = []
    new_stories: List[Dict[str, Any]] = []

    # prev_tail 跟踪跨批的链尾——初始为全 verified 基底的末位
    prev_tail = anchor

    # 按 rung_id 数值升序处理,保证确定性(输入顺序无关)
    for rung in sorted(ladder["rungs"], key=lambda r: int(r["rung_id"])):
        batch_id = f"presentation-{rung['rung_id']}"

        if batch_id in existing:
            # 幂等:已有此批次则跳过,但更新 prev_tail 为该批末位,供后续批锚定
            prev_tail = existing[batch_id]["story_ids"][-1]
            continue

        member_ids: List[str] = []

        for entry in rung["stories"]:
            story_id = f"story-{batch_id}-{entry['story_slug']}"

            # 每个呈现 story 的 materials 携带阶梯路径和 supersedes 信息
            materials = _base_materials(paths)
            materials["gdd_anchors"] = list(rung.get("gdd_anchors", []))
            materials["ladder_rung_path"] = paths["ladder_path"]
            materials["supersedes_paths"] = list(rung.get("supersedes", []))

            # 链式依赖:批内第一个 story 依赖上一批末位(prev_tail);后续依赖前一个
            if member_ids:
                depends_on = [member_ids[-1]]  # 批内链式:依赖前一成员
            else:
                depends_on = [prev_tail]       # 跨批锚点:依赖上一批末位

            story = {
                "story_schema_version": STORY_SCHEMA_VERSION,
                "story_id": story_id,
                "batch_id": batch_id,
                "story_kind": "presentation",
                "evidence_class": entry["evidence_class"],
                "depends_on": depends_on,
                "interaction_claims": list(entry.get("interaction_claims", [])),
                "materials": materials,
                "acceptance_criteria": list(entry["requirements"]) + [
                    "demo plugin 编译通过且全部已冻结层冒烟不退化(证据: smoke_report)",
                    f"按 evidence_class={entry['evidence_class']} 提交全部必交证据并通过机器校验",
                    "宣称交互逐条有 InteractionSemantics 用例对应且通过(行为校验门禁)",
                    "设计取舍零提问: 未定点给默认值并记入 provisional_decisions",
                ],
                "status": "pending",
                "attempts": 0,
                "manifest_version": manifest_version,
            }
            new_stories.append(story)
            member_ids.append(story_id)

        # 防御性 fail-closed:rung 无 stories(schema 已 minItems 1,但纯函数自守)
        if not member_ids:
            raise ValueError(
                f"amend: rung {rung['rung_id']} 无 stories,阶梯数据不合法(fail-closed)"
            )

        # 批末文档 story:依赖批内所有 member story
        doc = _doc_story(batch_id, member_ids, manifest_version, paths)
        new_stories.append(doc)

        new_batches.append({
            "batch_id": batch_id,
            "story_ids": member_ids + [doc["story_id"]],
        })

        # 更新 prev_tail 为本批末位 doc story
        prev_tail = doc["story_id"]

    # 构造新 plan(浅拷贝,追加新批次)
    new_plan = dict(plan)
    new_plan["plan_schema_version"] = PLAN_SCHEMA_VERSION
    new_plan["batches"] = list(plan["batches"]) + new_batches

    return {"plan": new_plan, "new_stories": new_stories}
