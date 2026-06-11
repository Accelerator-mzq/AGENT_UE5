# -*- coding: utf-8 -*-
"""velocity log:逐 story、逐自修轮的时间戳事件流(Phase 15 扇出成本估算的实测依据)。"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def append_event(run_dir, event: Dict[str, Any]) -> None:
    """追加一条事件(自动盖 UTC 时间戳),.part 原子写。"""
    path = Path(run_dir) / "velocity_log.json"
    log = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"events": []}
    stamped = dict(event)
    stamped["ts"] = datetime.now(timezone.utc).isoformat()
    log["events"].append(stamped)
    tmp = path.with_suffix(".json.part")
    tmp.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)
