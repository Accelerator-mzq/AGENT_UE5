# -*- coding: utf-8 -*-
"""demo_plan 生成 CLI(runbook 驱动用,无人值守窗口之前的准备步骤)。

用法:
  python Plugins/AgentBridge/Scripts/demo_plan_main.py --run-dir ProjectState/runs/<run_id>

行为:
  读 run 目录的 skill_graph.json + root_skill_contract.json,
  未解决 capability_gaps 或缺 source_run_id 时 fail-closed,
  经 jsonschema 校验后写 demo_plan.json + stories/*.json(.part 原子写)。
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 14 demo_plan 生成")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--manifest", default=None,
                        help="施工规范路径(缺省项目层默认位置;相对路径基准为进程 cwd)")
    args = parser.parse_args()
    run_dir = Path(args.run_dir)

    # 输入缺件/损坏不许裸 traceback:runbook 操作者要直接看到原因(统一 [FAIL]+退出码 2)
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

    def rel(p):
        return str(p).replace("\\", "/")

    # source_gdd 可能是字符串(简单路径)或对象 {file_path: ..., scope_summary: ...}
    raw_gdd = contract.get("source_gdd", "")
    gdd_path = raw_gdd["file_path"] if isinstance(raw_gdd, dict) else raw_gdd

    paths = {
        "gdd_path": gdd_path,
        "contract_path": rel(run_dir / "root_skill_contract.json"),
        "skill_graph_path": rel(run_dir / "skill_graph.json"),
        "construction_manifest_path": rel(ml.DEFAULT_MANIFEST_REL),
        "doc_extra_paths": [rel(run_dir / "demo_plan.json"), rel(run_dir / "velocity_log.json")],
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

    def atomic_write(path: Path, data):
        # 与 story_store 同款事务形状(.part 暂存 + os.replace 原子换名);CLI 自包含故意不抽公共
        tmp = path.with_suffix(".json.part")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, path)

    atomic_write(run_dir / "demo_plan.json", out["plan"])
    for story in out["stories"]:
        atomic_write(stories_dir / f"{story['story_id']}.json", story)

    total = len(out["stories"])
    print(f"[OK] demo_plan 落盘: {len(out['plan']['batches'])} 批 / {total} story → {run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
