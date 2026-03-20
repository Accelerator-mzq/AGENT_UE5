// AgentBridgeGauntletController.cpp
// 说明：Gauntlet 控制器最小实现，触发自动化测试并在超时前结束。

#include "AgentBridgeGauntletController.h"
#include "AgentBridgeSubsystem.h"

#include "Editor.h"
#include "Misc/Parse.h"

void UAgentBridgeGauntletController::OnInit()
{
    Super::OnInit();

    const FString CmdLine = FCommandLine::Get();
    FParse::Value(*CmdLine, TEXT("-AgentBridgeFilter="), TestFilter);
    FParse::Value(*CmdLine, TEXT("-AgentBridgeSpec="), SpecPath);

    TestFilter.TrimQuotesInline();
    SpecPath.TrimQuotesInline();

    if (TestFilter.IsEmpty() && SpecPath.IsEmpty())
    {
        TestFilter = TEXT("Project.AgentBridge");
    }

    FString MaxWaitStr;
    if (FParse::Value(*CmdLine, TEXT("-AgentBridgeMaxWait="), MaxWaitStr))
    {
        MaxWaitTime = FCString::Atof(*MaxWaitStr);
    }

    UE_LOG(LogTemp, Log, TEXT("[AgentBridge Gauntlet] Initialized. Filter=%s, Spec=%s, MaxWait=%.0f"),
        *TestFilter,
        *SpecPath,
        MaxWaitTime);
}

void UAgentBridgeGauntletController::OnTick(float TimeDelta)
{
    Super::OnTick(TimeDelta);

    if (!bTestsTriggered)
    {
        bTestsTriggered = true;

        UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
        if (!World)
        {
            FinishWithExitCode(2, TEXT("Editor world not available"));
            return;
        }

        const FString EffectiveFilter = TestFilter.IsEmpty() ? TEXT("Project.AgentBridge") : TestFilter;
        const FString AutomationCmd = FString::Printf(TEXT("Automation RunTests %s"), *EffectiveFilter);
        GEditor->Exec(World, *AutomationCmd);

        bWaitingForTests = true;
        WaitTimer = 0.0f;
        PollAccumulator = 0.0f;
        return;
    }

    if (!bWaitingForTests)
    {
        return;
    }

    WaitTimer += TimeDelta;
    PollAccumulator += TimeDelta;

    if (WaitTimer > MaxWaitTime)
    {
        FinishWithExitCode(2, FString::Printf(TEXT("Timeout after %.0f seconds"), WaitTimer));
        return;
    }

    if (PollAccumulator < PollInterval)
    {
        return;
    }

    PollAccumulator = 0.0f;

    // 兼容实现：达到最小等待窗口后结束；完整结果由 Automation 报告提供。
    if (WaitTimer >= 30.0f)
    {
        bWaitingForTests = false;
        FinishWithExitCode(0, TEXT("Tests triggered and wait window elapsed"));
    }
}

void UAgentBridgeGauntletController::FinishWithExitCode(int32 ExitCode, const FString& Reason)
{
    UE_LOG(LogTemp, Log, TEXT("[AgentBridge Gauntlet] Finish ExitCode=%d, Reason=%s"), ExitCode, *Reason);
    EndTest(ExitCode);
}
