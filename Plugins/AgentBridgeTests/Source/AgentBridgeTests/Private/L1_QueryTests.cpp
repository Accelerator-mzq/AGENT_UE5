// L1_QueryTests.cpp
// AGENT + UE5 可操作層 — L1 單接口驗證：查詢接口
//
// UE5 官方模組：Automation Test Framework
// 註冊方式：IMPLEMENT_SIMPLE_AUTOMATION_TEST 宏
// Test Flag：EditorContext + ProductFilter
// Session Frontend 路径：Project.AgentBridge.L1.Query.*
//
// 每个测试调用 UAgentBridgeSubsystem 的对应接口，
// 验证返回值的 status、data 结构是否符合预期。
// 这是通道 C（C++ 直接调用）的测试路径。

#include "Misc/AutomationTest.h"
#include "AgentBridgeSubsystem.h"
#include "BridgeTypes.h"
#include "Editor.h"

// ============================================================
// 辅助宏：获取 Subsystem + 基础断言
// ============================================================

#define GET_SUBSYSTEM_OR_FAIL() \
	UAgentBridgeSubsystem* Subsystem = GEditor ? GEditor->GetEditorSubsystem<UAgentBridgeSubsystem>() : nullptr; \
	if (!Subsystem) \
	{ \
		AddError(TEXT("AgentBridgeSubsystem not available. Is AgentBridge plugin enabled?")); \
		return false; \
	}

#define TEST_STATUS_SUCCESS(Response) \
	TestEqual(TEXT("Status should be success"), BridgeStatusToString(Response.Status), TEXT("success")); \
	TestTrue(TEXT("IsSuccess() should return true"), Response.IsSuccess()); \
	TestTrue(TEXT("Errors should be empty"), Response.Errors.Num() == 0);

// ============================================================
// T1-01: GetCurrentProjectState
// UE5 依赖: FPaths + FApp::GetBuildVersion + UEditorLevelLibrary
// ============================================================

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FBridgeL1_GetCurrentProjectState,
	"Project.AgentBridge.L1.Query.GetCurrentProjectState",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter
)

bool FBridgeL1_GetCurrentProjectState::RunTest(const FString& Parameters)
{
	GET_SUBSYSTEM_OR_FAIL();

	FBridgeResponse Response = Subsystem->GetCurrentProjectState();

	TEST_STATUS_SUCCESS(Response);

	// 验证 data 结构
	TestTrue(TEXT("Data should be valid"), Response.Data.IsValid());
	if (Response.Data.IsValid())
	{
		TestTrue(TEXT("Data should contain project_name"),
			Response.Data->HasField(TEXT("project_name")));
		TestTrue(TEXT("Data should contain engine_version"),
			Response.Data->HasField(TEXT("engine_version")));
		TestTrue(TEXT("Data should contain current_level"),
			Response.Data->HasField(TEXT("current_level")));
		TestTrue(TEXT("Data should contain editor_mode"),
			Response.Data->HasField(TEXT("editor_mode")));

		// engine_version 不应为空
		FString EngineVersion = Response.Data->GetStringField(TEXT("engine_version"));
		TestFalse(TEXT("engine_version should not be empty"), EngineVersion.IsEmpty());

		// editor_mode 应为 "editing" 或 "pie"
		FString Mode = Response.Data->GetStringField(TEXT("editor_mode"));
		TestTrue(TEXT("editor_mode should be 'editing' or 'pie'"),
			Mode == TEXT("editing") || Mode == TEXT("pie"));
	}

	return true;
}

// ============================================================
// T1-02: ListLevelActors
// UE5 依赖: UEditorLevelLibrary::GetAllLevelActors()
// ============================================================

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FBridgeL1_ListLevelActors,
	"Project.AgentBridge.L1.Query.ListLevelActors",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter
)

bool FBridgeL1_ListLevelActors::RunTest(const FString& Parameters)
{
	GET_SUBSYSTEM_OR_FAIL();

	// 无过滤
	FBridgeResponse Response = Subsystem->ListLevelActors();

	TEST_STATUS_SUCCESS(Response);

	TestTrue(TEXT("Data should be valid"), Response.Data.IsValid());
	if (Response.Data.IsValid())
	{
		TestTrue(TEXT("Data should contain actors array"),
			Response.Data->HasField(TEXT("actors")));

		const TArray<TSharedPtr<FJsonValue>>* ActorsArray;
		if (Response.Data->TryGetArrayField(TEXT("actors"), ActorsArray))
		{
			// 当前关卡至少应有默认 Actor（光源、天空等）
			// 不做硬编码数量检查，仅验证结构
			if (ActorsArray->Num() > 0)
			{
				TSharedPtr<FJsonObject> FirstActor = (*ActorsArray)[0]->AsObject();
				TestTrue(TEXT("Actor should have actor_name"),
					FirstActor.IsValid() && FirstActor->HasField(TEXT("actor_name")));
				TestTrue(TEXT("Actor should have actor_path"),
					FirstActor.IsValid() && FirstActor->HasField(TEXT("actor_path")));
				TestTrue(TEXT("Actor should have class"),
					FirstActor.IsValid() && FirstActor->HasField(TEXT("class")));
			}
		}
	}

	// 带过滤
	FBridgeResponse FilteredResponse = Subsystem->ListLevelActors(TEXT("Light"));
	TEST_STATUS_SUCCESS(FilteredResponse);

	return true;
}

// ============================================================
// T1-03: GetActorState
// UE5 依赖: AActor Transform / Collision / Tags
// ============================================================

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FBridgeL1_GetActorState,
	"Project.AgentBridge.L1.Query.GetActorState",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter
)

bool FBridgeL1_GetActorState::RunTest(const FString& Parameters)
{
	GET_SUBSYSTEM_OR_FAIL();

	// 先列出 Actor 获取一个有效路径
	FBridgeResponse ListResponse = Subsystem->ListLevelActors();
	if (!ListResponse.IsSuccess() || !ListResponse.Data.IsValid())
	{
		AddError(TEXT("Cannot list actors to find a test target"));
		return false;
	}

	const TArray<TSharedPtr<FJsonValue>>* ActorsArray;
	if (!ListResponse.Data->TryGetArrayField(TEXT("actors"), ActorsArray) || ActorsArray->Num() == 0)
	{
		AddWarning(TEXT("No actors in current level — skipping GetActorState test"));
		return true;
	}

	FString TestActorPath = (*ActorsArray)[0]->AsObject()->GetStringField(TEXT("actor_path"));

	// 测试正常路径
	FBridgeResponse Response = Subsystem->GetActorState(TestActorPath);
	TEST_STATUS_SUCCESS(Response);

	if (Response.Data.IsValid())
	{
		TestTrue(TEXT("Data should contain actor_name"), Response.Data->HasField(TEXT("actor_name")));
		TestTrue(TEXT("Data should contain actor_path"), Response.Data->HasField(TEXT("actor_path")));
		TestTrue(TEXT("Data should contain transform"), Response.Data->HasField(TEXT("transform")));
		TestTrue(TEXT("Data should contain collision"), Response.Data->HasField(TEXT("collision")));
		TestTrue(TEXT("Data should contain tags"), Response.Data->HasField(TEXT("tags")));

		// 验证 transform 结构
		const TSharedPtr<FJsonObject>* TransformObj;
		if (Response.Data->TryGetObjectField(TEXT("transform"), TransformObj))
		{
			TestTrue(TEXT("transform should contain location"), (*TransformObj)->HasField(TEXT("location")));
			TestTrue(TEXT("transform should contain rotation"), (*TransformObj)->HasField(TEXT("rotation")));
			TestTrue(TEXT("transform should contain relative_scale3d"), (*TransformObj)->HasField(TEXT("relative_scale3d")));
		}
	}

	// 测试不存在的 Actor
	FBridgeResponse NotFoundResponse = Subsystem->GetActorState(TEXT("/Game/NonExistent.Actor"));
	TestEqual(TEXT("Not found should return failed"),
		BridgeStatusToString(NotFoundResponse.Status), TEXT("failed"));
	TestTrue(TEXT("Should have error"), NotFoundResponse.Errors.Num() > 0);
	if (NotFoundResponse.Errors.Num() > 0)
	{
		TestEqual(TEXT("Error code should be ACTOR_NOT_FOUND"),
			NotFoundResponse.Errors[0].Code, TEXT("ACTOR_NOT_FOUND"));
	}

	// 测试空字符串参数
	FBridgeResponse EmptyResponse = Subsystem->GetActorState(TEXT(""));
	TestEqual(TEXT("Empty path should return validation_error"),
		BridgeStatusToString(EmptyResponse.Status), TEXT("validation_error"));

	return true;
}

// ============================================================
// T1-04: GetActorBounds
// UE5 依赖: AActor::GetActorBounds()
// ============================================================

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FBridgeL1_GetActorBounds,
	"Project.AgentBridge.L1.Query.GetActorBounds",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter
)

bool FBridgeL1_GetActorBounds::RunTest(const FString& Parameters)
{
	GET_SUBSYSTEM_OR_FAIL();

	// 获取一个有效 Actor
	FBridgeResponse ListResponse = Subsystem->ListLevelActors();
	if (!ListResponse.IsSuccess()) { AddWarning(TEXT("No actors — skipping")); return true; }

	const TArray<TSharedPtr<FJsonValue>>* ActorsArray;
	if (!ListResponse.Data->TryGetArrayField(TEXT("actors"), ActorsArray) || ActorsArray->Num() == 0)
	{
		AddWarning(TEXT("No actors in level — skipping")); return true;
	}

	FString ActorPath = (*ActorsArray)[0]->AsObject()->GetStringField(TEXT("actor_path"));
	FBridgeResponse Response = Subsystem->GetActorBounds(ActorPath);

	TEST_STATUS_SUCCESS(Response);

	if (Response.Data.IsValid())
	{
		TestTrue(TEXT("Should contain actor_path"), Response.Data->HasField(TEXT("actor_path")));
		TestTrue(TEXT("Should contain world_bounds_origin"), Response.Data->HasField(TEXT("world_bounds_origin")));
		TestTrue(TEXT("Should contain world_bounds_extent"), Response.Data->HasField(TEXT("world_bounds_extent")));

		// origin 和 extent 应为 3 元素数组
		const TArray<TSharedPtr<FJsonValue>>* OriginArr;
		if (Response.Data->TryGetArrayField(TEXT("world_bounds_origin"), OriginArr))
		{
			TestEqual(TEXT("origin should have 3 elements"), OriginArr->Num(), 3);
		}
	}

	return true;
}

// ============================================================
// T1-05: GetAssetMetadata
// UE5 依赖: UEditorAssetLibrary
// ============================================================

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FBridgeL1_GetAssetMetadata,
	"Project.AgentBridge.L1.Query.GetAssetMetadata",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter
)

bool FBridgeL1_GetAssetMetadata::RunTest(const FString& Parameters)
{
	GET_SUBSYSTEM_OR_FAIL();

	// 测试不存在的资产
	FBridgeResponse Response = Subsystem->GetAssetMetadata(TEXT("/Game/NonExistent/SM_Nothing"));
	TEST_STATUS_SUCCESS(Response);  // 仍然是 success，只是 exists=false

	if (Response.Data.IsValid())
	{
		TestTrue(TEXT("Should contain exists field"), Response.Data->HasField(TEXT("exists")));
		TestFalse(TEXT("exists should be false"), Response.Data->GetBoolField(TEXT("exists")));
	}

	// 测试空参数
	FBridgeResponse EmptyResponse = Subsystem->GetAssetMetadata(TEXT(""));
	TestEqual(TEXT("Empty path should return validation_error"),
		BridgeStatusToString(EmptyResponse.Status), TEXT("validation_error"));

	return true;
}

// ============================================================
// T1-06: GetDirtyAssets
// UE5 依赖: FEditorFileUtils::GetDirtyContentPackages
// ============================================================

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FBridgeL1_GetDirtyAssets,
	"Project.AgentBridge.L1.Query.GetDirtyAssets",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter
)

bool FBridgeL1_GetDirtyAssets::RunTest(const FString& Parameters)
{
	GET_SUBSYSTEM_OR_FAIL();

	FBridgeResponse Response = Subsystem->GetDirtyAssets();

	TEST_STATUS_SUCCESS(Response);

	if (Response.Data.IsValid())
	{
		TestTrue(TEXT("Should contain dirty_assets array"),
			Response.Data->HasField(TEXT("dirty_assets")));
	}

	return true;
}

// ============================================================
// T1-07: RunMapCheck
// UE5 依赖: Console Command "MAP CHECK"
// ============================================================

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FBridgeL1_RunMapCheck,
	"Project.AgentBridge.L1.Query.RunMapCheck",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter
)

bool FBridgeL1_RunMapCheck::RunTest(const FString& Parameters)
{
	GET_SUBSYSTEM_OR_FAIL();

	FBridgeResponse Response = Subsystem->RunMapCheck();

	TEST_STATUS_SUCCESS(Response);

	if (Response.Data.IsValid())
	{
		TestTrue(TEXT("Should contain level_path"), Response.Data->HasField(TEXT("level_path")));
		TestTrue(TEXT("Should contain map_errors"), Response.Data->HasField(TEXT("map_errors")));
		TestTrue(TEXT("Should contain map_warnings"), Response.Data->HasField(TEXT("map_warnings")));
	}

	return true;
}
