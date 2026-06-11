# -*- coding: utf-8 -*-
"""Phase 13 验收用 MCP stdio 驱动器。

用途:在没有 harness 级 MCP 连接的会话里,经**真实 MCP stdio 协议**驱动
agentbridge server(C:\\Python312\\python.exe 启动,因 mcp 包装在 py312)。
每次调用独立拉起 server 进程(server 无内存态,session 状态全在磁盘),
initialize → tools/call → 输出结果 JSON。

用法:
  C:\\Python312\\python.exe ProjectState/Reports/2026-06-11/mcp_driver.py <tool_name> [args.json 路径或内联 JSON]

留档原因:验收判据 6 要求"经 MCP 驱动"留证——本驱动器即 Claude Code 端的
MCP 传输层证据(与 Codex 端经 ~/.codex/config.toml 注册的同一 server 等价)。
"""
import asyncio
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SERVER_PY = PROJECT_ROOT / "Plugins" / "AgentBridge" / "MCP" / "server.py"
PY312 = r"C:\Python312\python.exe"


async def call(tool_name: str, arguments: dict) -> None:
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    params = StdioServerParameters(
        command=PY312,
        args=[str(SERVER_PY)],
        cwd=str(PROJECT_ROOT),
        env=None,  # 继承当前环境;server.py 自行处理 sys.path
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            # MCP 返回 content 列表;agentbridge 统一返回单条 text(JSON 字符串)
            for item in result.content:
                if getattr(item, "type", "") == "text":
                    print(item.text)


def main() -> int:
    # Windows 控制台默认 GBK,payload 含 GBK 不可编码字符时 print 会炸——强制 UTF-8
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) < 2:
        print("用法: mcp_driver.py <tool_name> [args.json 路径或内联 JSON]", file=sys.stderr)
        return 2
    tool_name = sys.argv[1]
    arguments: dict = {}
    if len(sys.argv) > 2:
        raw = sys.argv[2]
        path = Path(raw)
        text = path.read_text(encoding="utf-8") if path.is_file() else raw
        arguments = json.loads(text)
    asyncio.run(call(tool_name, arguments))
    return 0


if __name__ == "__main__":
    sys.exit(main())
