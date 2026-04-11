"""
run_id 生成与解析。

格式约定：
  YYYY-MM-DD_<8位hex>
示例：
  2026-04-11_a3f7b2c1
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime


RUN_ID_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}_[a-f0-9]{8}$")


def generate_run_id() -> str:
    """生成标准化 run_id。"""
    date_part = datetime.now().strftime("%Y-%m-%d")
    uuid_short = uuid.uuid4().hex[:8]
    return f"{date_part}_{uuid_short}"


def validate_run_id(run_id: str) -> bool:
    """校验 run_id 是否符合标准格式。"""
    return bool(RUN_ID_PATTERN.fullmatch(run_id))


def parse_run_id(run_id: str) -> dict[str, str]:
    """解析 run_id，非法时抛出 ValueError。"""
    if not validate_run_id(run_id):
        raise ValueError(f"非法 run_id: {run_id}")

    date_part, uuid_short = run_id.split("_", 1)
    return {
        "date": date_part,
        "uuid_short": uuid_short,
    }
