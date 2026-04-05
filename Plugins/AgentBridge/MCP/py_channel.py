"""
Python Editor Scripting 执行通道（Channel A）。

通过 Remote Control API 的 /remote/script/run 端点执行 Python 脚本。
适用于在 UE5 Editor 进程内执行 Python Editor Scripting。

前提：
  - UE5 Editor 已启动
  - Python Editor Scripting Plugin 已启用
  - Remote Control API 已启动（端口 30010）
"""

import json
import urllib.request
import urllib.error


DEFAULT_RC_URL = "http://localhost:30010"


def execute_editor_python(script: str, rc_url: str = None, timeout_ms: int = 30000) -> dict:
    """
    通过 Remote Control API 在 UE5 Editor 中执行 Python 脚本。

    Args:
        script: Python 脚本内容
        rc_url: Remote Control API URL（默认 http://localhost:30010）
        timeout_ms: 超时毫秒数

    Returns:
        执行结果 dict
    """
    url = f"{rc_url or DEFAULT_RC_URL}/remote/script/run"
    payload = json.dumps({
        "scriptText": script
    }).encode('utf-8')

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        timeout_sec = timeout_ms / 1000.0
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            body = resp.read().decode('utf-8')
            return json.loads(body) if body else {"status": "success"}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else str(e)
        raise RuntimeError(f"Python Editor Scripting 执行失败 (HTTP {e.code}): {error_body}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"无法连接 UE5 Editor (Remote Control API): {e.reason}")


def check_editor_connection(rc_url: str = None) -> bool:
    """检查 UE5 Editor 是否可达"""
    url = f"{rc_url or DEFAULT_RC_URL}/remote/info"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False
