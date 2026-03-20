// AgentBridgeCommandlet.cpp
// AGENT + UE5 可操作层 — Commandlet 无头执行实现
//
// UE5 官方模块：Command-Line / Commandlet
// 在无 GUI 环境下执行 Spec / Automation Test / 单个 Bridge 工具。

#include "AgentBridgeCommandlet.h"
#include "AgentBridgeSubsystem.h"
#include "BridgeTypes.h"

#include "Editor.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/Parse.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

UAgentBridgeCommandlet::UAgentBridgeCommandlet()
{
	IsClient = false;
	IsEditor = true;
	IsServer = false;
	LogToConsole = true;

	HelpDescription = TEXT("AGENT + UE5 可操作層: Headless execution of Specs, Automation Tests, or single Bridge tools.");
	HelpUsage = TEXT("UE5Editor-Cmd.exe Project.uproject -run=AgentBridge [-Spec=path] [-RunTests=filter] [-Tool=name] [-Report=path]");

	HelpParamNames.Add(TEXT("Spec"));
	HelpParamDescriptions.Add(TEXT("Path to a YAML Spec file to execute"));

	HelpParamNames.Add(TEXT("RunTests"));
	HelpParamDescriptions.Add(TEXT("Automation Test filter expression (e.g. Project.AgentBridge.L1)"));

	HelpParamNames.Add(TEXT("Tool"));
	HelpParamDescriptions.Add(TEXT("Single Bridge tool to execute (e.g. ListLevelActors, GetDirtyAssets)"));

	HelpParamNames.Add(TEXT("Report"));
	HelpParamDescriptions.Add(TEXT("Output path for JSON report"));
}

// ============================================================
// Main — Commandlet 入口
// ============================================================

int32 UAgentBridgeCommandlet::Main(const FString& Params)
{
	UE_LOG(LogTemp, Log, TEXT("[AgentBridge Commandlet] Starting with params: %s"), *Params);

	ParseParams(Params);

	int32 ExitCode = 0;

	if (!SpecPath.IsEmpty())
	{
		UE_LOG(LogTemp, Log, TEXT("[AgentBridge Commandlet] Mode: Execute Spec → %s"), *SpecPath);
		ExitCode = RunSpec();
	}
	else if (!TestFilter.IsEmpty())
	{
		UE_LOG(LogTemp, Log, TEXT("[AgentBridge Commandlet] Mode: Run Tests → %s"), *TestFilter);
		ExitCode = RunTests();
	}
	else if (!ToolName.IsEmpty())
	{
		UE_LOG(LogTemp, Log, TEXT("[AgentBridge Commandlet] Mode: Single Tool → %s"), *ToolName);
		ExitCode = RunSingleTool();
	}
	else
	{
		UE_LOG(LogTemp, Error, TEXT("[AgentBridge Commandlet] No mode specified. Use -Spec, -RunTests, or -Tool."));
		ExitCode = 2;
	}

	UE_LOG(LogTemp, Log, TEXT("[AgentBridge Commandlet] Finished with exit code: %d"), ExitCode);
	return ExitCode;
}

// ============================================================
// 参数解析
// ============================================================

void UAgentBridgeCommandlet::ParseParams(const FString& Params)
{
	TArray<FString> Tokens;
	TArray<FString> Switches;
	TMap<FString, FString> ParamMap;

	// UE5 标准参数解析
	const TCHAR* ParamsChar = *Params;
	FString Token;
	while (FParse::Token(ParamsChar, Token, false))
	{
		if (Token.StartsWith(TEXT("-")))
		{
			Token.RemoveFromStart(TEXT("-"));
			FString Key, Value;
			if (Token.Split(TEXT("="), &Key, &Value))
			{
				// 移除引号
				Value.TrimQuotesInline();
				ParamMap.Add(Key, Value);
			}
			else
			{
				Switches.Add(Token);
			}
		}
		else
		{
			Tokens.Add(Token);
		}
	}

	SpecPath = ParamMap.FindRef(TEXT("Spec"));
	TestFilter = ParamMap.FindRef(TEXT("RunTests"));
	ToolName = ParamMap.FindRef(TEXT("Tool"));
	ReportPath = ParamMap.FindRef(TEXT("Report"));
}

// ============================================================
// 模式 1：执行 Spec 文件
// ============================================================

int32 UAgentBridgeCommandlet::RunSpec()
{
	// 检查 Spec 文件存在
	if (!FPaths::FileExists(SpecPath))
	{
		UE_LOG(LogTemp, Error, TEXT("[AgentBridge Commandlet] Spec file not found: %s"), *SpecPath);
		return 2;
	}

	// 获取 Subsystem
	UAgentBridgeSubsystem* Subsystem = GEditor->GetEditorSubsystem<UAgentBridgeSubsystem>();
	if (!Subsystem)
	{
		UE_LOG(LogTemp, Error, TEXT("[AgentBridge Commandlet] AgentBridgeSubsystem not available"));
		return 2;
	}

	// 读取 Spec（YAML 解析）
	// 注意：UE5 C++ 没有内置 YAML 解析器
	// 方案 1：通过 IPythonScriptPlugin 调用 Python 的 Orchestrator
	// 方案 2：使用第三方 YAML 库（yaml-cpp）
	// 方案 3：将 Spec 转为 JSON 格式
	// 此处使用方案 1——调用 Python Orchestrator

	FString PythonCommand = FString::Printf(
		TEXT("import sys; sys.path.insert(0, '%s'); "
			 "from agent_ue5.orchestrator.orchestrator import run; "
			 "result = run('%s'); "
			 "print(result)"),
		*FPaths::ProjectDir(),
		*SpecPath
	);

	UE_LOG(LogTemp, Log, TEXT("[AgentBridge Commandlet] Invoking Python Orchestrator for Spec execution"));

	// 通过 IPythonScriptPlugin 执行 Python
	// 注意：需要 PythonScriptPlugin 已加载
	if (GEditor)
	{
		GEditor->Exec(GEditor->GetEditorWorldContext().World(),
			*FString::Printf(TEXT("py %s"), *PythonCommand));
	}

	// 收集报告
	TSharedPtr<FJsonObject> ReportJson = MakeShareable(new FJsonObject());
	ReportJson->SetStringField(TEXT("spec_path"), SpecPath);
	ReportJson->SetStringField(TEXT("execution_mode"), TEXT("commandlet"));
	ReportJson->SetStringField(TEXT("status"), TEXT("completed"));

	if (!ReportPath.IsEmpty())
	{
		FString ReportContent;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&ReportContent);
		FJsonSerializer::Serialize(ReportJson.ToSharedRef(), Writer);
		WriteReport(ReportContent);
	}

	return 0;
}

// ============================================================
// 模式 2：运行 Automation Test
// ============================================================

int32 UAgentBridgeCommandlet::RunTests()
{
	UAgentBridgeSubsystem* Subsystem = GEditor->GetEditorSubsystem<UAgentBridgeSubsystem>();
	if (!Subsystem)
	{
		UE_LOG(LogTemp, Error, TEXT("[AgentBridge Commandlet] AgentBridgeSubsystem not available"));
		return 2;
	}

	// 通过 Subsystem 触发 Automation Tests
	FBridgeResponse Response = Subsystem->RunAutomationTests(TestFilter, ReportPath);

	UE_LOG(LogTemp, Log, TEXT("[AgentBridge Commandlet] RunAutomationTests response: %s"), *Response.Summary);

	if (!ReportPath.IsEmpty())
	{
		WriteReport(Response.ToJsonString());
	}

	return Response.IsSuccess() ? 0 : 1;
}

// ============================================================
// 模式 3：执行单个 Bridge 工具
// ============================================================

int32 UAgentBridgeCommandlet::RunSingleTool()
{
	UAgentBridgeSubsystem* Subsystem = GEditor->GetEditorSubsystem<UAgentBridgeSubsystem>();
	if (!Subsystem)
	{
		UE_LOG(LogTemp, Error, TEXT("[AgentBridge Commandlet] AgentBridgeSubsystem not available"));
		return 2;
	}

	FBridgeResponse Response;

	// 分发到对应的 Subsystem 接口
	if (ToolName.Equals(TEXT("GetCurrentProjectState"), ESearchCase::IgnoreCase))
	{
		Response = Subsystem->GetCurrentProjectState();
	}
	else if (ToolName.Equals(TEXT("ListLevelActors"), ESearchCase::IgnoreCase))
	{
		Response = Subsystem->ListLevelActors();
	}
	else if (ToolName.Equals(TEXT("GetDirtyAssets"), ESearchCase::IgnoreCase))
	{
		Response = Subsystem->GetDirtyAssets();
	}
	else if (ToolName.Equals(TEXT("RunMapCheck"), ESearchCase::IgnoreCase))
	{
		Response = Subsystem->RunMapCheck();
	}
	else
	{
		UE_LOG(LogTemp, Error, TEXT("[AgentBridge Commandlet] Unknown tool: %s"), *ToolName);
		UE_LOG(LogTemp, Log, TEXT("  Available tools: GetCurrentProjectState, ListLevelActors, GetDirtyAssets, RunMapCheck"));
		UE_LOG(LogTemp, Log, TEXT("  Tools requiring parameters not supported in single-tool mode. Use -Spec instead."));
		return 2;
	}

	// 输出结果
	FString JsonResult = Response.ToJsonString();
	UE_LOG(LogTemp, Log, TEXT("[AgentBridge Commandlet] Result: %s"), *JsonResult);

	if (!ReportPath.IsEmpty())
	{
		WriteReport(JsonResult);
	}

	if (Response.Status == EBridgeStatus::Failed || Response.Status == EBridgeStatus::ValidationError)
	{
		return 2;
	}
	if (Response.Status == EBridgeStatus::Mismatch || Response.Status == EBridgeStatus::Warning)
	{
		return 1;
	}
	return 0;
}

// ============================================================
// 报告输出
// ============================================================

void UAgentBridgeCommandlet::WriteReport(const FString& JsonContent)
{
	if (ReportPath.IsEmpty()) return;

	// 确保目录存在
	FString Dir = FPaths::GetPath(ReportPath);
	if (!Dir.IsEmpty())
	{
		IFileManager::Get().MakeDirectory(*Dir, true);
	}

	if (FFileHelper::SaveStringToFile(JsonContent, *ReportPath, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM))
	{
		UE_LOG(LogTemp, Log, TEXT("[AgentBridge Commandlet] Report written to: %s"), *ReportPath);
	}
	else
	{
		UE_LOG(LogTemp, Error, TEXT("[AgentBridge Commandlet] Failed to write report to: %s"), *ReportPath);
	}
}
