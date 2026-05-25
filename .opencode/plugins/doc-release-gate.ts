// OpenCode plugin: 把 bash 工具调用与文件写入桥接到 doc_release_gate.py
// 文档参考: https://github.com/anomalyco/opencode 的 docs/plugins.mdx
//
// 功能:
//   1. 监听 tool.execute.before 事件
//   2. bash 工具: git commit/push/merge → 调用 gate.py check --action <name>，失败则阻塞
//   3. write/edit 工具: 治理面文件路径 → 调用 gate.py notify --path <path>，软提示不阻塞

import type { Plugin } from "@opencode-ai/plugin"

// 匹配 git commit / push / merge 命令（允许行首有空格）
const GIT_RE = /^\s*git\s+(commit|push|merge)\b/

// 匹配需要软提示的治理面文件路径
const NOTIFY_PATH_RE =
  /^(task\.md|Docs\/Current\/.*_Closeout\.md|ProjectState\/Reports\/.*)$/

/**
 * 调用 Python gate 脚本，返回退出码与 stderr 内容
 * @param $ Bun shell API（由 OpenCode plugin context 注入）
 * @param args 传给 gate.py 的参数列表
 */
async function runGate(
  $: any,
  args: string[],
): Promise<{ exitCode: number; stderr: string }> {
  // nothrow() 让非零退出码不抛异常，由调用方自行判断
  const result = await $`python Scripts/hooks/doc_release_gate.py ${args}`.nothrow()
  return {
    exitCode: result.exitCode ?? 0,
    stderr: result.stderr?.toString() ?? "",
  }
}

/**
 * DocReleaseGate: OpenCode plugin 入口
 * context 解构出 $ (Bun shell)，其余字段暂不使用
 */
export const DocReleaseGate: Plugin = async ({ $ }) => {
  return {
    // 监听每次工具调用前的事件
    "tool.execute.before": async (input, output) => {
      // ── 1. bash 工具：git commit / push / merge 硬拦截 ──
      if (input.tool === "bash") {
        const cmd = (output.args?.command ?? "") as string
        const m = GIT_RE.exec(cmd)
        if (m) {
          const action = m[1] // "commit" | "push" | "merge"
          const res = await runGate($, ["check", "--action", action])
          if (res.exitCode !== 0) {
            // 抛出错误 = 阻塞 tool 调用，OpenCode 会显示错误信息
            throw new Error(
              `[document-release] 阻止 git ${action}:\n${res.stderr}`,
            )
          }
        }
        return
      }

      // ── 2. write / edit 工具：治理面文件软提示（不阻塞）──
      if (input.tool === "write" || input.tool === "edit") {
        // write 工具用 file_path，edit 工具有时用 path，兼容两种字段名
        const path = (output.args?.file_path ?? output.args?.path ?? "") as string
        if (path && NOTIFY_PATH_RE.test(path)) {
          // notify 模式只记录日志/提示，失败也不阻塞
          await runGate($, ["notify", "--path", path])
        }
      }
    },
  }
}
