// L1_WriteTests.cpp
// AGENT + UE5 可操作層 — L1 單接口驗證：寫接口
//
// UE5 官方模組：Automation Test Framework
// 註冊方式：IMPLEMENT_SIMPLE_AUTOMATION_TEST 宏
// Test Flag：EditorContext + ProductFilter
// Session Frontend 路径：Project.AgentBridge.L1.Write.*
//
// 写接口测试要点：
//   1. 参数校验（空参数 / 无效 Transform → validation_error）
//   2. dry_run 模式（不实际执行，返回 success + 空 created_objects）
//   3. 实际执行（返回 created/modified + actual_transform + dirty_assets）
//   4. Transaction 验证（bTransaction=true，可 Undo）
//   5. 写后读回（actual_transform 来自 UE5 API 读回，非复制输入）

#include "Misc/AutomationTest.h"
#include "AgentBridgeSubsystem.h"
#include "BridgeTypes.h"
#include "Editor.h"
#include "EditorLevelLibrary.h"
#include "Engine/StaticMeshActor.h"

// 复用 L1_QueryTests 中的辅助宏
#define GET_SUBSYSTEM_OR_FAIL() \
	UAgentBridgeSubsystem* Subsystem = GEditor ? GEditor->GetEditorSubsystem<UAgentBridgeSubsystem>() : nullptr; \
	if (!Subsystem) \
	{ \
		AddError(TEXT("AgentBridgeSubsystem not available")); \
		return false; \
	}

#define TEST_STATUS_SUCCESS(Response) \
	TestEqual(TEXT("Status should be success"), BridgeStatusToString(Response.Status), TEXT("success")); \
	TestTrue(TEXT("IsSuccess() should return true"), Response.IsSuccess());

// 测试用默认 Transform
static FBridgeTransform MakeTestTransform(float X = 500.0f, float Y = 300.0f, float Z = 0.0f)
{
	FBridgeTransform T;
	T.Location = FVector(X, Y, Z);
	T.Rotation = FRotator(0.0f, 45.0f, 0.0f);
	T.RelativeScale3D = FVector(1.0f, 1.0f, 1.0f);
	return T;
}

// ============================================================
// T1-08: SpawnActor
// UE5 依赖: UEditorLevelLibrary::SpawnActorFromClass + FScopedTransaction
// ============================================================

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FBridgeL1_SpawnActor,
	"Project.AgentBridge.L1.Write.SpawnActor",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter
)

bool FBridgeL1_SpawnActor::RunTest(const FString& Parameters)
{
	GET_SUBSYSTEM_OR_FAIL();

	UWorld* World = GEditor->GetEditorWorldContext().World();
	FString LevelPath = World ? World->GetPathName() : TEXT("/Temp/TestMap");
	FString ActorClass = TEXT("/Script/Engine.StaticMeshActor");
	FString ActorName = TEXT("L1_TestSpawnActor");
	FBridgeTransform Transform = MakeTestTransform(1000.0f, 2000.0f, 0.0f);

	// --- 测试 1: 参数校验 ---
	{
		FBridgeResponse EmptyClass = Subsystem->SpawnActor(LevelPath, TEXT(""), ActorName, Transform);
		TestEqual(TEXT("Empty class → validation_error"),
			BridgeStatusToString(EmptyClass.Status), TEXT("validation_error"));

		FBridgeResponse EmptyName = Subsystem->SpawnActor(LevelPath, ActorClass, TEXT(""), Transform);
		TestEqual(TEXT("Empty name → validation_error"),
			BridgeStatusToString(EmptyName.Status), TEXT("validation_error"));

		FBridgeTransform ZeroScale;
		ZeroScale.Location = FVector::ZeroVector;
		ZeroScale.Rotation = FRotator::ZeroRotator;
		ZeroScale.RelativeScale3D = FVector::ZeroVector;
		FBridgeResponse ZeroScaleResp = Subsystem->SpawnActor(LevelPath, ActorClass, ActorName, ZeroScale);
		TestEqual(TEXT("Zero scale → validation_error"),
			BridgeStatusToString(ZeroScaleResp.Status), TEXT("validation_error"));
	}

	// --- 测试 2: dry_run ---
	{
		FBridgeResponse DryRun = Subsystem->SpawnActor(LevelPath, ActorClass, ActorName, Transform, /*bDryRun=*/true);
		TEST_STATUS_SUCCESS(DryRun);
		TestTrue(TEXT("Dry run summary should mention dry run"),
			DryRun.Summary.Contains(TEXT("Dry run")));
	}

	// --- 测试 3: 实际执行 ---
	FBridgeResponse Response = Subsystem->SpawnActor(LevelPath, ActorClass, ActorName, Transform);
	TEST_STATUS_SUCCESS(Response);

	if (Response.Data.IsValid())
	{
		// created_objects 应包含新 Actor
		const TArray<TSharedPtr<FJsonValue>>* CreatedArr;
		if (Response.Data->TryGetArrayField(TEXT("created_objects"), CreatedArr))
		{
			TestTrue(TEXT("created_objects should have 1 entry"), CreatedArr->Num() == 1);
			if (CreatedArr->Num() > 0)
			{
				TSharedPtr<FJsonObject> Ref = (*CreatedArr)[0]->AsObject();
				TestTrue(TEXT("Should have actor_name"), Ref.IsValid() && Ref->HasField(TEXT("actor_name")));
				TestTrue(TEXT("Should have actor_path"), Ref.IsValid() && Ref->HasField(TEXT("actor_path")));
			}
		}

		// actual_transform 应存在
		TestTrue(TEXT("Should have actual_transform"),
			Response.Data->HasField(TEXT("actual_transform")));

		// dirty_assets 应包含关卡路径
		const TArray<TSharedPtr<FJsonValue>>* DirtyArr;
		if (Response.Data->TryGetArrayField(TEXT("dirty_assets"), DirtyArr))
		{
			TestTrue(TEXT("dirty_assets should not be empty"), DirtyArr->Num() > 0);
		}
	}

	// --- 测试 4: Transaction 标记 ---
	TestTrue(TEXT("bTransaction should be true"), Response.bTransaction);

	// --- 测试 5: 写后读回一致性 ---
	if (Response.Data.IsValid())
	{
		const TSharedPtr<FJsonObject>* ActualObj;
		if (Response.Data->TryGetObjectField(TEXT("actual_transform"), ActualObj))
		{
			const TArray<TSharedPtr<FJsonValue>>* LocArr;
			if ((*ActualObj)->TryGetArrayField(TEXT("location"), LocArr) && LocArr->Num() == 3)
			{
				float ActualX = (*LocArr)[0]->AsNumber();
				float ActualY = (*LocArr)[1]->AsNumber();
				// 容差验证（location ≤ 0.01）
				TestNearlyEqual(TEXT("Readback X should match input"), ActualX, 1000.0f, 0.01f);
				TestNearlyEqual(TEXT("Readback Y should match input"), ActualY, 2000.0f, 0.01f);
			}
		}
	}

	// --- 清理: Undo 撤销 spawn ---
	if (GEditor)
	{
		GEditor->UndoTransaction();
		AddInfo(TEXT("Undo executed to clean up spawned actor"));
	}

	return true;
}

// ============================================================
// T1-09: SetActorTransform
// UE5 依赖: AActor::SetActorLocationAndRotation + FScopedTransaction
// ============================================================

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FBridgeL1_SetActorTransform,
	"Project.AgentBridge.L1.Write.SetActorTransform",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter
)

bool FBridgeL1_SetActorTransform::RunTest(const FString& Parameters)
{
	GET_SUBSYSTEM_OR_FAIL();

	UWorld* World = GEditor->GetEditorWorldContext().World();
	FString LevelPath = World ? World->GetPathName() : TEXT("/Temp/TestMap");

	// 先 spawn 一个测试 Actor
	FBridgeTransform InitTransform = MakeTestTransform(100.0f, 100.0f, 0.0f);
	FBridgeResponse SpawnResp = Subsystem->SpawnActor(
		LevelPath, TEXT("/Script/Engine.StaticMeshActor"),
		TEXT("L1_TestTransformActor"), InitTransform);

	if (!SpawnResp.IsSuccess())
	{
		AddError(TEXT("Cannot spawn test actor for SetActorTransform test"));
		return false;
	}

	// 获取 actor_path
	FString ActorPath;
	const TArray<TSharedPtr<FJsonValue>>* CreatedArr;
	if (SpawnResp.Data->TryGetArrayField(TEXT("created_objects"), CreatedArr) && CreatedArr->Num() > 0)
	{
		ActorPath = (*CreatedArr)[0]->AsObject()->GetStringField(TEXT("actor_path"));
	}

	if (ActorPath.IsEmpty())
	{
		AddError(TEXT("Spawned actor path is empty"));
		return false;
	}

	// --- 测试 1: 参数校验 ---
	{
		FBridgeResponse EmptyPath = Subsystem->SetActorTransform(TEXT(""), InitTransform);
		TestEqual(TEXT("Empty path → validation_error"),
			BridgeStatusToString(EmptyPath.Status), TEXT("validation_error"));
	}

	// --- 测试 2: dry_run ---
	{
		FBridgeTransform NewTransform = MakeTestTransform(999.0f, 888.0f, 50.0f);
		FBridgeResponse DryRun = Subsystem->SetActorTransform(ActorPath, NewTransform, /*bDryRun=*/true);
		TEST_STATUS_SUCCESS(DryRun);

		// dry_run 应返回 old_transform
		TestTrue(TEXT("Dry run should have old_transform"),
			DryRun.Data.IsValid() && DryRun.Data->HasField(TEXT("old_transform")));
	}

	// --- 测试 3: 实际执行 ---
	FBridgeTransform NewTransform;
	NewTransform.Location = FVector(500.0f, 600.0f, 70.0f);
	NewTransform.Rotation = FRotator(0.0f, 90.0f, 0.0f);
	NewTransform.RelativeScale3D = FVector(2.0f, 2.0f, 2.0f);

	FBridgeResponse Response = Subsystem->SetActorTransform(ActorPath, NewTransform);
	TEST_STATUS_SUCCESS(Response);

	if (Response.Data.IsValid())
	{
		// 应有 old_transform 和 actual_transform
		TestTrue(TEXT("Should have old_transform"), Response.Data->HasField(TEXT("old_transform")));
		TestTrue(TEXT("Should have actual_transform"), Response.Data->HasField(TEXT("actual_transform")));

		// modified_objects 应包含目标 Actor
		const TArray<TSharedPtr<FJsonValue>>* ModArr;
		if (Response.Data->TryGetArrayField(TEXT("modified_objects"), ModArr))
		{
			TestTrue(TEXT("modified_objects should have 1 entry"), ModArr->Num() == 1);
		}
	}

	// --- 测试 4: Transaction ---
	TestTrue(TEXT("bTransaction should be true"), Response.bTransaction);

	// --- 测试 5: 写后读回容差 ---
	if (Response.Data.IsValid())
	{
		const TSharedPtr<FJsonObject>* ActualObj;
		if (Response.Data->TryGetObjectField(TEXT("actual_transform"), ActualObj))
		{
			const TArray<TSharedPtr<FJsonValue>>* ScaleArr;
			if ((*ActualObj)->TryGetArrayField(TEXT("relative_scale3d"), ScaleArr) && ScaleArr->Num() == 3)
			{
				float ScaleX = (*ScaleArr)[0]->AsNumber();
				TestNearlyEqual(TEXT("Scale X should be 2.0"), ScaleX, 2.0f, 0.001f);
			}
		}
	}

	// --- 清理: Undo 两次（SetTransform + Spawn）---
	if (GEditor)
	{
		GEditor->UndoTransaction();
		GEditor->UndoTransaction();
		AddInfo(TEXT("Undo x2 executed to clean up"));
	}

	return true;
}

// ============================================================
// T1-10: ImportAssets (dry_run only — 无测试资源时不执行实际导入)
// UE5 依赖: IAssetTools::ImportAssetTasks + FScopedTransaction
// ============================================================

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FBridgeL1_ImportAssets,
	"Project.AgentBridge.L1.Write.ImportAssets",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter
)

bool FBridgeL1_ImportAssets::RunTest(const FString& Parameters)
{
	GET_SUBSYSTEM_OR_FAIL();

	// --- 测试 1: 参数校验 ---
	{
		FBridgeResponse EmptyDir = Subsystem->ImportAssets(TEXT(""), TEXT("/Game/Test"));
		TestEqual(TEXT("Empty source dir → validation_error"),
			BridgeStatusToString(EmptyDir.Status), TEXT("validation_error"));

		FBridgeResponse EmptyDest = Subsystem->ImportAssets(TEXT("/tmp/test"), TEXT(""));
		TestEqual(TEXT("Empty dest path → validation_error"),
			BridgeStatusToString(EmptyDest.Status), TEXT("validation_error"));
	}

	// --- 测试 2: dry_run（无论是否有真实文件，dry_run 总应成功）---
	{
		FBridgeResponse DryRun = Subsystem->ImportAssets(
			TEXT("/tmp/nonexistent_source"),
			TEXT("/Game/Test"),
			/*bReplaceExisting=*/false,
			/*bDryRun=*/true);
		TEST_STATUS_SUCCESS(DryRun);
	}

	// 注意：实际导入测试需要测试资源文件，在 CI 环境中不一定可用
	// 实际导入测试放在 L2 闭环中（有专用测试资源时执行）

	return true;
}

// ============================================================
// T1-11: CreateBlueprintChild (dry_run + 实际创建 + Undo)
// UE5 依赖: UBlueprintFactory + UAssetToolsHelpers + FScopedTransaction
// ============================================================

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FBridgeL1_CreateBlueprintChild,
	"Project.AgentBridge.L1.Write.CreateBlueprintChild",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter
)

bool FBridgeL1_CreateBlueprintChild::RunTest(const FString& Parameters)
{
	GET_SUBSYSTEM_OR_FAIL();

	FString ParentClass = TEXT("/Script/Engine.Actor");
	FString PackagePath = TEXT("/Game/Tests/BP_L1_TestChild");

	// --- 测试 1: 参数校验 ---
	{
		FBridgeResponse EmptyParent = Subsystem->CreateBlueprintChild(TEXT(""), PackagePath);
		TestEqual(TEXT("Empty parent → validation_error"),
			BridgeStatusToString(EmptyParent.Status), TEXT("validation_error"));

		FBridgeResponse EmptyPackage = Subsystem->CreateBlueprintChild(ParentClass, TEXT(""));
		TestEqual(TEXT("Empty package → validation_error"),
			BridgeStatusToString(EmptyPackage.Status), TEXT("validation_error"));
	}

	// --- 测试 2: dry_run ---
	{
		FBridgeResponse DryRun = Subsystem->CreateBlueprintChild(ParentClass, PackagePath, /*bDryRun=*/true);
		TEST_STATUS_SUCCESS(DryRun);
		TestTrue(TEXT("Dry run summary should mention dry run"),
			DryRun.Summary.Contains(TEXT("Dry run")));
	}

	// --- 测试 3: 不存在的父类 ---
	{
		FBridgeResponse BadParent = Subsystem->CreateBlueprintChild(
			TEXT("/Script/Engine.NonExistentClass"), PackagePath);
		TestEqual(TEXT("Bad parent → failed"),
			BridgeStatusToString(BadParent.Status), TEXT("failed"));
		if (BadParent.Errors.Num() > 0)
		{
			TestEqual(TEXT("Error code should be CLASS_NOT_FOUND"),
				BadParent.Errors[0].Code, TEXT("CLASS_NOT_FOUND"));
		}
	}

	// --- 测试 4: 实际创建 + Transaction ---
	{
		FBridgeResponse Response = Subsystem->CreateBlueprintChild(ParentClass, PackagePath);
		TEST_STATUS_SUCCESS(Response);
		TestTrue(TEXT("bTransaction should be true"), Response.bTransaction);

		if (Response.Data.IsValid())
		{
			const TArray<TSharedPtr<FJsonValue>>* CreatedArr;
			if (Response.Data->TryGetArrayField(TEXT("created_objects"), CreatedArr))
			{
				TestTrue(TEXT("Should have 1 created object"), CreatedArr->Num() == 1);
			}
		}

		// Undo 清理
		if (GEditor)
		{
			GEditor->UndoTransaction();
			AddInfo(TEXT("Undo executed to clean up created Blueprint"));
		}
	}

	return true;
}
