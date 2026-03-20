// AgentBridge.TestConfig.cs
// AGENT + UE5 可操作层 — Gauntlet C# 测试会话配置
//
// UE5 官方模块：Gauntlet（外部测试会话编排框架，基于 UAT）
//
// 本文件定义 CI/CD 中的测试会话：
//   - 启动 UE5 Editor 进程
//   - 在 Editor 内运行 AgentBridge L1/L2/L3 测试
//   - 收集测试结果
//   - 判定通过/失败
//   - 停止 Editor 进程
//
// 三层测试：
//   L1 Simple Test (15 个)：Query 7 + Write 4 + UITool 4
//   L2 Automation Spec (5 个)：ClosedLoop 3 + UITool 2
//   L3 Functional Test：FTEST_ 地图完整 Demo
//
// 注意：L3 UI 工具测试（L1.UITool + L2.UITool）依赖 Automation Driver，
// Automation Driver 需要实际的 Editor UI 渲染——不能使用 -NullRHI。
// 因此提供两种 AllTests 配置：带 UI 和无 UI。
//
// 调用方式：
//   RunUAT.bat RunGauntlet ^
//       -project=MyGame.uproject ^
//       -Test=AgentBridge.AllTests ^
//       -build=editor ^
//       -platform=Win64 ^
//       -unattended
//
// 文件位置：
//   项目根目录/Gauntlet/AgentBridge.TestConfig.cs

using AutomationTool;
using Gauntlet;
using System;
using System.Collections.Generic;
using System.IO;

namespace AgentBridge.Gauntlet
{
    // ============================================================
    // 测试配置 1: 全部测试（含 L3 UI 工具，需要 UI 渲染）
    // ============================================================

    /// <summary>
    /// 运行 AgentBridge 全部 Automation Test（L1 + L2 + L3），包含 UI 工具测试。
    /// 需要 GPU / Editor UI 渲染（Automation Driver 依赖 UI）。
    /// 适用于每日构建或有 GPU 的 CI 节点。
    /// </summary>
    public class AllTests : UnrealTestConfiguration
    {
        public AllTests()
        {
            // 测试过滤：运行 Project.AgentBridge 下的全部测试
            // 包含 L1.Query(7) + L1.Write(4) + L1.UITool(4) + L2.ClosedLoop(3) + L2.UITool(2)
            AutomationTestFilter = "Project.AgentBridge";

            // 超时：最长 15 分钟
            // L3 UITool 测试涉及 Automation Driver UI 操作 + 交叉比对，需要更多时间
            MaxDuration = 900;

            MaxInstances = 1;

            // 不使用 -NullRHI——L3 UI 工具测试需要 Editor UI 渲染
            // Automation Driver 依赖实际的 Slate Widget 树
            AdditionalCommandLineArgs = "-Unattended -NoSound -NoSplash";
        }

        public override void InitRoles(UnrealTestContext Context)
        {
            Context.SetRole(new UnrealTestRole
            {
                Type = UnrealTargetRole.Editor,
                Platform = Context.GetPlatform(),
                Configuration = UnrealTargetConfiguration.Development,
                CommandLineArgs = AdditionalCommandLineArgs,
                Controllers = new List<string> { "AgentBridgeGauntletController" }
            });
        }

        public override void ProcessResults(UnrealTestContext Context, IEnumerable<UnrealRoleResult> RoleResults)
        {
            base.ProcessResults(Context, RoleResults);

            foreach (var Result in RoleResults)
            {
                if (Result.ExitCode != 0)
                {
                    Context.SetTestResult(TestResult.Failed,
                        $"AgentBridge tests failed with exit code {Result.ExitCode}");
                    return;
                }
            }

            Context.SetTestResult(TestResult.Passed, "All AgentBridge tests passed (including L3 UI tools)");
        }

        private string AdditionalCommandLineArgs;
    }

    // ============================================================
    // 测试配置 2: 冒烟测试（L1 + L2，无 UI 依赖，可用 -NullRHI）
    // ============================================================

    /// <summary>
    /// 运行 AgentBridge 冒烟测试（L1 + L2，不含 L3 UI 工具的实际执行部分）。
    /// 使用 -NullRHI，适用于无 GPU 的 CI 节点。
    /// L1.UITool 测试在 -NullRHI 下会 graceful degradation（SKIP 而非 FAIL）。
    /// </summary>
    public class SmokeTests : UnrealTestConfiguration
    {
        public SmokeTests()
        {
            AutomationTestFilter = "Project.AgentBridge.L1+Project.AgentBridge.L2";

            // 超时：最长 5 分钟
            // L1.UITool 测试在 Driver 不可用时自动 SKIP，不会占用太多时间
            MaxDuration = 300;

            MaxInstances = 1;

            // -NullRHI：无 GPU 渲染（CI 服务器）
            // L1.UITool 测试会检测 Automation Driver 不可用 → AddWarning + return true
            AdditionalCommandLineArgs = "-NullRHI -Unattended -NoSound -NoSplash";
        }

        public override void InitRoles(UnrealTestContext Context)
        {
            Context.SetRole(new UnrealTestRole
            {
                Type = UnrealTargetRole.Editor,
                Platform = Context.GetPlatform(),
                Configuration = UnrealTargetConfiguration.Development,
                CommandLineArgs = AdditionalCommandLineArgs,
                Controllers = new List<string> { "AgentBridgeGauntletController" }
            });
        }

        private string AdditionalCommandLineArgs;
    }

    // ============================================================
    // 测试配置 3: Spec 执行验证
    // ============================================================

    /// <summary>
    /// 在 CI/CD 中执行指定的 Spec 文件并验证结果。
    /// 如果 Spec 中包含 execution_method: ui_tool 的 Actor，需要 UI 渲染（不使用 -NullRHI）。
    /// 
    /// 调用方式：
    ///   RunUAT RunGauntlet -Test=AgentBridge.SpecExecution -SpecPath="AgentSpecs/warehouse.yaml"
    /// </summary>
    public class SpecExecution : UnrealTestConfiguration
    {
        public SpecExecution()
        {
            MaxDuration = 300;
            MaxInstances = 1;

            // 不使用 -NullRHI——Spec 可能包含 L3 UI 工具操作
            AdditionalCommandLineArgs = "-Unattended -NoSound -NoSplash";
        }

        public override void InitRoles(UnrealTestContext Context)
        {
            string SpecPath = Context.GetParam("SpecPath", "");

            string ExtraArgs = AdditionalCommandLineArgs;
            if (!string.IsNullOrEmpty(SpecPath))
            {
                ExtraArgs += $" -AgentBridgeSpec=\"{SpecPath}\"";
            }

            Context.SetRole(new UnrealTestRole
            {
                Type = UnrealTargetRole.Editor,
                Platform = Context.GetPlatform(),
                Configuration = UnrealTargetConfiguration.Development,
                CommandLineArgs = ExtraArgs,
                Controllers = new List<string> { "AgentBridgeGauntletController" }
            });
        }

        private string AdditionalCommandLineArgs;
    }
}
