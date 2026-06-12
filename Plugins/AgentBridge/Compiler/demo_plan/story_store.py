# -*- coding: utf-8 -*-
"""story 状态机:pending → in_progress → (verified | 校验失败回 in_progress)。
schema enum 中的 submitted 预留给 MCP 层在途态,store 不落盘该状态(submit 守卫容忍它属防御)。

落盘约定:每个 story 一个 JSON(ProjectState/runs/<run_id>/stories/<story_id>.json),
写入一律 .part 临时文件 + os.replace 原子替换(Phase 13 合成链同款事务形状)。
本模块零游戏领域语义;不 import 包内其他模块(自包含,经 importlib 单文件加载友好)。
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


class StoryStore:
    """story 状态机的落盘存取器。假设单写者顺序执行;并发 fetch/append 不保证唯一性与不丢事件(本期单驱动器场景)。"""

    def __init__(self, run_dir) -> None:
        self.run_dir = Path(run_dir)
        self.stories_dir = self.run_dir / "stories"
        self.plan_path = self.run_dir / "demo_plan.json"

    # ---- 基础 IO ----
    def _plan(self) -> Dict[str, Any]:
        return json.loads(self.plan_path.read_text(encoding="utf-8"))

    def _ordered_ids(self) -> List[str]:
        """全局顺序 = 批次序 × 批内序(plan 文件是唯一顺序权威)。"""
        return [sid for b in self._plan()["batches"] for sid in b["story_ids"]]

    def load(self, story_id: str) -> Dict[str, Any]:
        path = self.stories_dir / f"{story_id}.json"
        if not path.exists():
            raise ValueError(f"story 不存在: {story_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _write(self, story: Dict[str, Any]) -> None:
        path = self.stories_dir / f"{story['story_id']}.json"
        tmp = path.with_suffix(".json.part")
        tmp.write_text(json.dumps(story, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, path)

    # ---- 状态查询 ----
    def _deps_verified(self, story: Dict[str, Any]) -> bool:
        return all(self.load(d)["status"] == "verified" for d in story.get("depends_on", []))

    def next_available(self) -> Optional[Dict[str, Any]]:
        """plan 顺序上第一个 pending 且前置全 verified 的 story。"""
        for sid in self._ordered_ids():
            story = self.load(sid)
            if story["status"] == "pending" and self._deps_verified(story):
                return story
        return None

    # ---- 状态流转 ----
    def fetch(self, story_id: Optional[str]) -> Dict[str, Any]:
        """story_id 为空取下一个可发工单;in_progress 可幂等重入(断点续作);verified 拒发。"""
        if story_id is None:
            story = self.next_available()
            if story is None:
                raise ValueError("没有可发的 story(全部完成或被前置阻塞)")
        else:
            story = self.load(story_id)
        if story["status"] == "verified":
            raise ValueError(f"story 已 verified,不可重发: {story['story_id']}")
        if story["status"] == "pending":
            if not self._deps_verified(story):
                raise ValueError(f"前置 story 未全部 verified: {story['story_id']}")
            story["status"] = "in_progress"
            self._write(story)
        return story

    def submit(self, story_id: str, evidence: Dict[str, Any],
               validation: Dict[str, Any]) -> Dict[str, Any]:
        """validation 是 evidence_validator.validate_evidence 的结果(机制分离:store 只管状态)。"""
        story = self.load(story_id)
        if story["status"] not in ("in_progress", "submitted"):
            raise ValueError(f"story 状态不允许 submit: {story['status']}")
        if validation["status"] == "verified":
            story["status"] = "verified"
            story["evidence"] = evidence
            story["submit_errors"] = []
        else:
            story["status"] = "in_progress"
            story["attempts"] = int(story.get("attempts", 0)) + 1
            story["submit_errors"] = list(validation.get("errors", []))
        self._write(story)
        return story
