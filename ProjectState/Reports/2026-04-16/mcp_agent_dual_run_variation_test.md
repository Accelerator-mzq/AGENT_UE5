# MCP Agent 同输入双跑差异测试

## 结论

在相同 Stage 1-3 输入、相同节点 `skill-board-topology` 下，连续两次使用 MCP Agent 路径运行 Stage 4，已能在持久化 sidecar 中观察到明确差异。

## 运行对象

- run A: `D:\UnrealProjects\Mvpv4TestCodex\ProjectState\runs\run-20260416-083508-1afe\session.json`
- run B: `D:\UnrealProjects\Mvpv4TestCodex\ProjectState\runs\run-20260416-083638-92d3\session.json`

## 差异点

- Discovery 维度名称（run A）：棋盘视觉尺度, 角格地标强调, 路径阅读性
- Discovery 维度名称（run B）：棋盘俯视高度, 角格身份风格, 移动引导语言

- run A 最终 selected_realization：{"board_visual_scale": "均衡棋盘", "corner_landmark_emphasis": "角格地标道具", "route_readability": "中线引导路径"}
- run B 最终 selected_realization：{"board_camera_altitude": "高空俯视", "corner_identity_style": "图标型角格", "movement_guidance_language": "边框脉冲提示"}

这说明当前补上的 sidecar 已经能把 MCP Agent 的中间生成物和最终收敛结果持久化下来，后续可以基于这些文件继续做更系统的差异对比。

## 原始报告

- JSON: `D:\UnrealProjects\Mvpv4TestCodex\ProjectState\Reports\2026-04-16\mcp_agent_dual_run_variation_test.json`