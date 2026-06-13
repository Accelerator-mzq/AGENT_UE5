# -*- coding: utf-8 -*-
"""demo_plan 生成 CLI(runbook 驱动用,无人值守窗口之前的准备步骤)。

用法:
  # 首切——从 skill_graph + contract 生成完整 demo_plan
  python Plugins/AgentBridge/Scripts/demo_plan_main.py --run-dir ProjectState/runs/<run_id>

  # amend 模式——追加呈现批(不读 skill_graph/contract)
  python Plugins/AgentBridge/Scripts/demo_plan_main.py --run-dir <dir> \
      --amend-presentation --ladder <阶梯实例.json>

  # amend 模式——把 feedback/ 下 open 条目切为一个反馈批
  python Plugins/AgentBridge/Scripts/demo_plan_main.py --run-dir <dir> \
      --amend-feedback

行为:
  首切:读 run 目录的 skill_graph.json + root_skill_contract.json,
  未解决 capability_gaps 或缺 source_run_id 时 fail-closed,
  经 jsonschema 校验后写 demo_plan.json + stories/*.json(.part 原子写)。
  amend:读现有 plan + stories 状态,追加呈现/反馈批,schema 校验后原子落盘。
"""
import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = SCRIPTS_DIR.parent
PROJECT_ROOT = PLUGIN_ROOT.parents[1]


def _load(name):
    """加载 Compiler/demo_plan 自包含模块(与测试同款 importlib 模式)。

    机制模块缺失属安装/环境损坏,统一 [FAIL] 风格 + 退出码 2
    (选 print+sys.exit 而非抛异常:CLI 自包含,main 不另包 _load,操作者直接看到原因)。
    """
    module_path = PLUGIN_ROOT / "Compiler" / "demo_plan" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        print(f"[FAIL] 机制模块缺失: {name}({module_path})", file=sys.stderr)
        sys.exit(2)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _atomic_write(path: Path, data) -> None:
    """与 story_store 同款事务形状(.part 暂存 + os.replace 原子换名)。"""
    tmp = path.with_suffix(".json.part")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def _rel(p) -> str:
    """路径归一化为正斜杠相对串(Windows 反斜杠 → 正斜杠,落盘口径统一)。"""
    return str(p).replace("\\", "/")


def _run_amend(args, run_dir: Path) -> int:
    """amend 模式:读现 plan + stories 状态,追加呈现/反馈批,schema 校验后原子落盘。

    与首切同口径:输入缺件/损坏不许裸 traceback,统一 [FAIL] + 退出码 2。
    """
    import jsonschema
    # --amend-presentation 必须同时提供 --ladder
    if args.amend_presentation and not args.ladder:
        print("[FAIL] --amend-presentation 需要 --ladder <阶梯实例路径>", file=sys.stderr)
        return 2
    # 读取现有 plan + stories
    try:
        plan = json.loads((run_dir / "demo_plan.json").read_text(encoding="utf-8"))
        stories_by_id = {}
        for sp in sorted((run_dir / "stories").glob("story-*.json")):
            story = json.loads(sp.read_text(encoding="utf-8"))
            stories_by_id[story["story_id"]] = story
    except (FileNotFoundError, OSError, json.JSONDecodeError) as exc:
        print(f"[FAIL] run 目录产物不可读: {exc}", file=sys.stderr)
        return 2
    if not stories_by_id:
        print("[FAIL] stories/ 为空,amend 需要已有切批产物", file=sys.stderr)
        return 2

    ml = _load("manifest_loader")
    amend = _load("amend")
    _, manifest_version = ml.load_construction_manifest(
        PROJECT_ROOT, path=Path(args.manifest) if args.manifest else None)

    # 公共路径自既有 story 的 materials 继承(amend 不重新推导 GDD/契约路径,保持同 run 一致)
    sample = next(iter(stories_by_id.values()))
    paths = {
        "gdd_path": sample["materials"]["gdd_path"],
        "contract_path": sample["materials"]["contract_path"],
        "skill_graph_path": sample["materials"]["skill_graph_path"],
        "construction_manifest_path": sample["materials"]["construction_manifest_path"],
        "doc_extra_paths": [_rel(run_dir / "demo_plan.json"), _rel(run_dir / "velocity_log.json")],
        "ladder_path": _rel(args.ladder) if args.ladder else None,
        "feedback_dir": _rel(run_dir / "feedback"),
    }

    # feedback 目录缺失要给操作者直白原因,否则会吃成"没有 open 条目"的间接报错
    if args.amend_feedback and not (run_dir / "feedback").exists():
        print("[FAIL] feedback/ 目录不存在,尚无反馈条目可切批", file=sys.stderr)
        return 2

    entries = []
    try:
        if args.amend_presentation:
            # 读取并校验阶梯实例 schema
            ladder_schema = json.loads(
                (PLUGIN_ROOT / "Schemas" / "presentation_ladder.schema.json").read_text(encoding="utf-8"))
            ladder = json.loads(Path(args.ladder).read_text(encoding="utf-8"))
            jsonschema.validate(ladder, ladder_schema)
            out = amend.build_presentation_amend(plan, stories_by_id, ladder, manifest_version, paths)
        else:
            # amend_feedback:收集 feedback/ 下所有 open 条目
            for ep in sorted((run_dir / "feedback").glob("fb-*.json")):
                entries.append(json.loads(ep.read_text(encoding="utf-8")))
            out = amend.build_feedback_amend(plan, stories_by_id, entries, manifest_version, paths)
    except (FileNotFoundError, OSError, json.JSONDecodeError) as exc:
        print(f"[FAIL] amend 输入不可读: {exc}", file=sys.stderr)
        return 2
    except (ValueError, jsonschema.ValidationError) as exc:
        print(f"[FAIL] amend 失败: {exc}", file=sys.stderr)
        return 2

    # 新产物 schema 自校验(与首切同口径,机器守门)
    schemas_dir = PLUGIN_ROOT / "Schemas"
    plan_schema = json.loads((schemas_dir / "demo_plan.schema.json").read_text(encoding="utf-8"))
    story_schema = json.loads((schemas_dir / "demo_story.schema.json").read_text(encoding="utf-8"))
    try:
        jsonschema.validate(out["plan"], plan_schema)
        for story in out["new_stories"]:
            jsonschema.validate(story, story_schema)
    except jsonschema.ValidationError as exc:
        print(f"[FAIL] amend 产物 schema 校验失败: {exc.message}(路径: {list(exc.path)})", file=sys.stderr)
        return 2

    # 落盘:先 stories 后 plan(plan 是顺序权威,最后原子换名)
    stories_dir = run_dir / "stories"
    stories_dir.mkdir(exist_ok=True)
    for story in out["new_stories"]:
        _atomic_write(stories_dir / f"{story['story_id']}.json", story)
    _atomic_write(run_dir / "demo_plan.json", out["plan"])
    # 反馈条目落盘:open 状态切为 in_batch
    # 注意:in_batch 流转在 plan 落盘后做;若此处中途崩溃,重试前须人工确认 plan 是否已含本批
    #       (amend 无幂等保护),否则同窗口反馈会被切成两批
    if args.amend_feedback:
        for entry in entries:
            if entry.get("status") == "open":
                entry["status"] = "in_batch"
                _atomic_write(run_dir / "feedback" / f"{entry['feedback_id']}.json", entry)

    added = len(out["plan"]["batches"]) - len(plan["batches"])
    print(f"[OK] amend 落盘: +{added} 批 / +{len(out['new_stories'])} story → {run_dir}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 14 demo_plan 生成")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--manifest", default=None,
                        help="施工规范路径(缺省项目层默认位置;相对路径基准为进程 cwd)")
    # amend 模式参数(--manifest 之后追加)
    parser.add_argument("--amend-presentation", action="store_true",
                        help="追加呈现批(读 --ladder 阶梯实例,幂等)")
    parser.add_argument("--amend-feedback", action="store_true",
                        help="把 run 目录 feedback/ 下 open 条目切为一个反馈批")
    parser.add_argument("--ladder", default=None,
                        help="呈现阶梯实例 JSON 路径(--amend-presentation 必填)")
    args = parser.parse_args()
    run_dir = Path(args.run_dir)

    # amend 分流:互斥检查 + 提前返回(不需要 skill_graph/contract)
    if args.amend_presentation and args.amend_feedback:
        print("[FAIL] --amend-presentation 与 --amend-feedback 互斥,一次只追加一类批", file=sys.stderr)
        return 2
    if args.amend_presentation or args.amend_feedback:
        return _run_amend(args, run_dir)

    # 首切路径:读 skill_graph + contract(输入缺件/损坏不许裸 traceback)
    try:
        graph = json.loads((run_dir / "skill_graph.json").read_text(encoding="utf-8"))
        contract = json.loads((run_dir / "root_skill_contract.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError) as exc:
        print(f"[FAIL] run 目录或必需产物不存在: {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"[FAIL] run 产物 JSON 不可解析: {exc}", file=sys.stderr)
        return 2

    gaps = (graph.get("metadata") or {}).get("capability_gaps") or []
    if gaps:
        print(f"[FAIL] 存在未解决 capability_gaps({len(gaps)} 条),先走合成+人审再切批", file=sys.stderr)
        return 2

    if not (graph.get("metadata") or {}).get("source_run_id"):
        print("[FAIL] skill_graph.metadata 缺 source_run_id,run 产物不完整(demo_plan schema 要求非空 run_id)", file=sys.stderr)
        return 2

    ml = _load("manifest_loader")
    planner = _load("planner")
    _, manifest_version = ml.load_construction_manifest(
        PROJECT_ROOT, path=Path(args.manifest) if args.manifest else None)

    # source_gdd 可能是字符串(简单路径)或对象 {file_path: ..., scope_summary: ...}
    raw_gdd = contract.get("source_gdd", "")
    gdd_path = raw_gdd["file_path"] if isinstance(raw_gdd, dict) else raw_gdd

    paths = {
        "gdd_path": gdd_path,
        "contract_path": _rel(run_dir / "root_skill_contract.json"),
        "skill_graph_path": _rel(run_dir / "skill_graph.json"),
        "construction_manifest_path": _rel(ml.DEFAULT_MANIFEST_REL),
        "doc_extra_paths": [_rel(run_dir / "demo_plan.json"), _rel(run_dir / "velocity_log.json")],
    }
    out = planner.build_demo_plan(graph, contract, manifest_version, paths)

    # schema 自校验(机器守门,与 validate_examples 同源 schema)
    import jsonschema
    schemas_dir = PLUGIN_ROOT / "Schemas"
    plan_schema = json.loads((schemas_dir / "demo_plan.schema.json").read_text(encoding="utf-8"))
    story_schema = json.loads((schemas_dir / "demo_story.schema.json").read_text(encoding="utf-8"))
    try:
        jsonschema.validate(out["plan"], plan_schema)
        for story in out["stories"]:
            jsonschema.validate(story, story_schema)
    except jsonschema.ValidationError as exc:
        print(f"[FAIL] 产物 schema 校验失败: {exc.message}(路径: {list(exc.path)})", file=sys.stderr)
        return 2

    stories_dir = run_dir / "stories"
    stories_dir.mkdir(exist_ok=True)

    _atomic_write(run_dir / "demo_plan.json", out["plan"])
    for story in out["stories"]:
        _atomic_write(stories_dir / f"{story['story_id']}.json", story)

    total = len(out["stories"])
    print(f"[OK] demo_plan 落盘: {len(out['plan']['batches'])} 批 / {total} story → {run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
