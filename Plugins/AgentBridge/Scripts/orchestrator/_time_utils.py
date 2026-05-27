"""ForgeUE 真机 bridge 共用时间 utils(避开 Python 3.13 utcnow deprecation)。

被 forgeue_manifest_importer.py 和 Scripts/run_forgeue_real_smoke.py 共享,
原本两处各持一份副本(逐字节相同),FU-10 闭环时抽到此模块。

放置在 orchestrator/ 下原因:
- forgeue_manifest_importer.py 本身在 orchestrator/ 下
- run_forgeue_real_smoke.py 已将 orchestrator/ 加入 sys.path,改动最小
- 不能放 bridge/ — 受 CLAUDE.md 红线保护(不允许修改 bridge/ 核心文件)
"""
from __future__ import annotations

import datetime as _dt


def now_iso_utc() -> str:
    """返回当前 UTC 时间 ISO 8601 含毫秒 + Z 后缀。

    避开 Python 3.13 `datetime.utcnow()` deprecation;datetime.now(UTC) 返回
    timezone-aware datetime,isoformat 输出 +00:00 后缀,这里 replace 成 Z
    与 schema example 风格保持一致。

    命名从 _now_iso_utc(模块私有)改为 now_iso_utc(public),因为现在是
    被多模块 import 的公共 API。
    """
    return _dt.datetime.now(_dt.UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
