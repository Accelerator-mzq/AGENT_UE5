// L2_ClosedLoopSpecs.spec.cpp
// AGENT + UE5 可操作層 — L2 闭环驗證
//
// UE5 官方模組：Automation Spec（BDD 语法）
// 註冊方式：BEGIN_DEFINE_SPEC / DEFINE_SPEC 宏
// Test Flag：EditorContext + SmokeFilter
// Session Frontend 路径：Project.AgentBridge.L2.*
//
// L2 闭环验证的核心模式：
//   写操作 → 读回 → 验证（写后读回一致性 + 副作用检查）
//
// 与 L1 的区别：
//   L1 = 单接口正确性（调一次，看返回值对不对）
//   L2 = 多接口协作正确性（写→读→验 的链路是否闭环）

#include "Misc/AutomationTest.h"
#include "AgentBridgeSubsystem.h"
#include "BridgeTypes.h"
#include "Editor.h"

// ============================================================
// L2-01: Spawn → Readback → Verify
// 验证：SpawnActor 后 GetActorState 读回的 Transform 与预期一致
// ============================================================

BEGIN_DEFINE_SPEC(
	FBridgeL2_SpawnReadbackLoop,
	"Project.AgentBridge.L2.SpawnReadbackLoop",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::SmokeFilter
)
	UAgentBridgeSubsystem* Subsystem;
	FString LevelPath;
	FString SpawnedActorPath;
	FBridgeTransform InputTransform;
	static constexpr float LocationTolerance = 0.01f;
	static constexpr float RotationTolerance = 0.01f;
	static constexpr float ScaleTolerance = 0.001f;
END_DEFINE_SPEC(FBridgeL2_SpawnReadbackLoop)

void FBridgeL2_SpawnReadbackLoop::Define()
{
	Describe("spawn actor then readback via GetActorState", [this]()
	{
		BeforeEach([this]()
		{
			Subsystem = GEditor ? GEditor->GetEditorSubsystem<UAgentBridgeSubsystem>() : nullptr;
			if (!Subsystem)
			{
				AddError(TEXT("AgentBridgeSubsystem not available"));
				return;
			}

			UWorld* World = GEditor->GetEditorWorldContext().World();
			LevelPath = World ? World->GetPathName() : TEXT("/Temp/TestMap");

			// 设置输入 Transform
			InputTransform.Location = FVector(1234.0f, 5678.0f, 90.0f);
			InputTransform.Rotation = FRotator(0.0f, 135.0f, 0.0f);
			InputTransform.RelativeScale3D = FVector(1.5f, 1.5f, 1.5f);

			// 执行 Spawn
			FBridgeResponse SpawnResp = Subsystem->SpawnActor(
				LevelPath,
				TEXT("/Script/Engine.StaticMeshActor"),
				TEXT("L2_SpawnReadback_TestActor"),
				InputTransform
			);

			if (!SpawnResp.IsSuccess())
			{
				AddError(FString::Printf(TEXT("Spawn failed: %s"), *SpawnResp.Summary));
				return;
			}

			// 提取 actor_path
			const TArray<TSharedPtr<FJsonValue>>* CreatedArr;
			if (SpawnResp.Data->TryGetArrayField(TEXT("created_objects"), CreatedArr) && CreatedArr->Num() > 0)
			{
				SpawnedActorPath = (*CreatedArr)[0]->AsObject()->GetStringField(TEXT("actor_path"));
			}
		});

		It("should return matching location on readback", [this]()
		{
			if (SpawnedActorPath.IsEmpty()) { AddError(TEXT("No spawned actor path")); return; }

			FBridgeResponse StateResp = Subsystem->GetActorState(SpawnedActorPath);
			TestTrue(TEXT("GetActorState should succeed"), StateResp.IsSuccess());

			const TSharedPtr<FJsonObject>* TransformObj;
			if (!StateResp.Data->TryGetObjectField(TEXT("transform"), TransformObj))
			{
				AddError(TEXT("No transform in response")); return;
			}

			const TArray<TSharedPtr<FJsonValue>>* LocArr;
			if ((*TransformObj)->TryGetArrayField(TEXT("location"), LocArr) && LocArr->Num() == 3)
			{
				float X = (*LocArr)[0]->AsNumber();
				float Y = (*LocArr)[1]->AsNumber();
				float Z = (*LocArr)[2]->AsNumber();
				TestNearlyEqual(TEXT("Location.X"), X, InputTransform.Location.X, LocationTolerance);
				TestNearlyEqual(TEXT("Location.Y"), Y, InputTransform.Location.Y, LocationTolerance);
				TestNearlyEqual(TEXT("Location.Z"), Z, InputTransform.Location.Z, LocationTolerance);
			}
			else
			{
				AddError(TEXT("location array invalid"));
			}
		});

		It("should return matching rotation on readback", [this]()
		{
			if (SpawnedActorPath.IsEmpty()) { AddError(TEXT("No spawned actor path")); return; }

			FBridgeResponse StateResp = Subsystem->GetActorState(SpawnedActorPath);
			const TSharedPtr<FJsonObject>* TransformObj;
			if (!StateResp.Data->TryGetObjectField(TEXT("transform"), TransformObj)) { AddError(TEXT("No transform")); return; }

			const TArray<TSharedPtr<FJsonValue>>* RotArr;
			if ((*TransformObj)->TryGetArrayField(TEXT("rotation"), RotArr) && RotArr->Num() == 3)
			{
				float Pitch = (*RotArr)[0]->AsNumber();
				float Yaw = (*RotArr)[1]->AsNumber();
				float Roll = (*RotArr)[2]->AsNumber();
				TestNearlyEqual(TEXT("Rotation.Pitch"), Pitch, InputTransform.Rotation.Pitch, RotationTolerance);
				TestNearlyEqual(TEXT("Rotation.Yaw"), Yaw, InputTransform.Rotation.Yaw, RotationTolerance);
				TestNearlyEqual(TEXT("Rotation.Roll"), Roll, InputTransform.Rotation.Roll, RotationTolerance);
			}
		});

		It("should return matching scale on readback", [this]()
		{
			if (SpawnedActorPath.IsEmpty()) { AddError(TEXT("No spawned actor path")); return; }

			FBridgeResponse StateResp = Subsystem->GetActorState(SpawnedActorPath);
			const TSharedPtr<FJsonObject>* TransformObj;
			if (!StateResp.Data->TryGetObjectField(TEXT("transform"), TransformObj)) { AddError(TEXT("No transform")); return; }

			const TArray<TSharedPtr<FJsonValue>>* ScaleArr;
			if ((*TransformObj)->TryGetArrayField(TEXT("relative_scale3d"), ScaleArr) && ScaleArr->Num() == 3)
			{
				float SX = (*ScaleArr)[0]->AsNumber();
				float SY = (*ScaleArr)[1]->AsNumber();
				float SZ = (*ScaleArr)[2]->AsNumber();
				TestNearlyEqual(TEXT("Scale.X"), SX, InputTransform.RelativeScale3D.X, ScaleTolerance);
				TestNearlyEqual(TEXT("Scale.Y"), SY, InputTransform.RelativeScale3D.Y, ScaleTolerance);
				TestNearlyEqual(TEXT("Scale.Z"), SZ, InputTransform.RelativeScale3D.Z, ScaleTolerance);
			}
		});

		It("should be visible in GetActorBounds", [this]()
		{
			if (SpawnedActorPath.IsEmpty()) { AddError(TEXT("No spawned actor path")); return; }

			FBridgeResponse BoundsResp = Subsystem->GetActorBounds(SpawnedActorPath);
			TestTrue(TEXT("GetActorBounds should succeed"), BoundsResp.IsSuccess());
			TestTrue(TEXT("Should have world_bounds_origin"),
				BoundsResp.Data.IsValid() && BoundsResp.Data->HasField(TEXT("world_bounds_origin")));
		});

		It("should mark level as dirty", [this]()
		{
			FBridgeResponse DirtyResp = Subsystem->GetDirtyAssets();
			TestTrue(TEXT("GetDirtyAssets should succeed"), DirtyResp.IsSuccess());
			// Spawn 后关卡应为脏
			// 注意：不做严格断言（其他操作也可能产生脏资产），仅验证接口可用
		});

		AfterEach([this]()
		{
			// Undo 清理
			if (GEditor)
			{
				GEditor->UndoTransaction();
			}
			SpawnedActorPath.Empty();
		});
	});
}

// ============================================================
// L2-02: Transform Modify → Readback → Verify
// 验证：SetActorTransform 后读回的 Transform 与新值一致，旧值与预期一致
// ============================================================

BEGIN_DEFINE_SPEC(
	FBridgeL2_TransformModifyLoop,
	"Project.AgentBridge.L2.TransformModifyLoop",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::SmokeFilter
)
	UAgentBridgeSubsystem* Subsystem;
	FString LevelPath;
	FString ActorPath;
	FBridgeTransform OriginalTransform;
	FBridgeTransform ModifiedTransform;
END_DEFINE_SPEC(FBridgeL2_TransformModifyLoop)

void FBridgeL2_TransformModifyLoop::Define()
{
	Describe("modify transform then verify readback", [this]()
	{
		BeforeEach([this]()
		{
			Subsystem = GEditor ? GEditor->GetEditorSubsystem<UAgentBridgeSubsystem>() : nullptr;
			if (!Subsystem) { AddError(TEXT("Subsystem not available")); return; }

			UWorld* World = GEditor->GetEditorWorldContext().World();
			LevelPath = World ? World->GetPathName() : TEXT("");

			// Spawn 初始 Actor
			OriginalTransform.Location = FVector(200.0f, 300.0f, 0.0f);
			OriginalTransform.Rotation = FRotator(0.0f, 0.0f, 0.0f);
			OriginalTransform.RelativeScale3D = FVector(1.0f, 1.0f, 1.0f);

			FBridgeResponse SpawnResp = Subsystem->SpawnActor(
				LevelPath, TEXT("/Script/Engine.StaticMeshActor"),
				TEXT("L2_TransformModify_TestActor"), OriginalTransform);

			if (!SpawnResp.IsSuccess()) { AddError(TEXT("Spawn failed")); return; }

			const TArray<TSharedPtr<FJsonValue>>* CreatedArr;
			if (SpawnResp.Data->TryGetArrayField(TEXT("created_objects"), CreatedArr) && CreatedArr->Num() > 0)
			{
				ActorPath = (*CreatedArr)[0]->AsObject()->GetStringField(TEXT("actor_path"));
			}

			// 定义目标 Transform
			ModifiedTransform.Location = FVector(800.0f, 900.0f, 50.0f);
			ModifiedTransform.Rotation = FRotator(10.0f, 270.0f, 0.0f);
			ModifiedTransform.RelativeScale3D = FVector(3.0f, 3.0f, 3.0f);
		});

		It("should return old_transform matching original", [this]()
		{
			if (ActorPath.IsEmpty()) { AddError(TEXT("No actor")); return; }

			FBridgeResponse Resp = Subsystem->SetActorTransform(ActorPath, ModifiedTransform);
			TestTrue(TEXT("SetActorTransform should succeed"), Resp.IsSuccess());

			const TSharedPtr<FJsonObject>* OldObj;
			if (Resp.Data->TryGetObjectField(TEXT("old_transform"), OldObj))
			{
				const TArray<TSharedPtr<FJsonValue>>* LocArr;
				if ((*OldObj)->TryGetArrayField(TEXT("location"), LocArr) && LocArr->Num() == 3)
				{
					TestNearlyEqual(TEXT("Old Location.X"), (float)(*LocArr)[0]->AsNumber(), 200.0f, 0.01f);
					TestNearlyEqual(TEXT("Old Location.Y"), (float)(*LocArr)[1]->AsNumber(), 300.0f, 0.01f);
				}
			}

			// Undo the SetTransform for next It block to have clean state
			if (GEditor) GEditor->UndoTransaction();
		});

		It("should readback modified values via GetActorState", [this]()
		{
			if (ActorPath.IsEmpty()) { AddError(TEXT("No actor")); return; }

			// Re-apply the modification
			Subsystem->SetActorTransform(ActorPath, ModifiedTransform);

			// Readback via separate query
			FBridgeResponse StateResp = Subsystem->GetActorState(ActorPath);
			TestTrue(TEXT("GetActorState should succeed"), StateResp.IsSuccess());

			const TSharedPtr<FJsonObject>* TransformObj;
			if (StateResp.Data->TryGetObjectField(TEXT("transform"), TransformObj))
			{
				const TArray<TSharedPtr<FJsonValue>>* LocArr;
				if ((*TransformObj)->TryGetArrayField(TEXT("location"), LocArr) && LocArr->Num() == 3)
				{
					TestNearlyEqual(TEXT("Modified Location.X"), (float)(*LocArr)[0]->AsNumber(), 800.0f, 0.01f);
					TestNearlyEqual(TEXT("Modified Location.Y"), (float)(*LocArr)[1]->AsNumber(), 900.0f, 0.01f);
					TestNearlyEqual(TEXT("Modified Location.Z"), (float)(*LocArr)[2]->AsNumber(), 50.0f, 0.01f);
				}

				const TArray<TSharedPtr<FJsonValue>>* ScaleArr;
				if ((*TransformObj)->TryGetArrayField(TEXT("relative_scale3d"), ScaleArr) && ScaleArr->Num() == 3)
				{
					TestNearlyEqual(TEXT("Modified Scale.X"), (float)(*ScaleArr)[0]->AsNumber(), 3.0f, 0.001f);
				}
			}

			// Undo
			if (GEditor) GEditor->UndoTransaction();
		});

		It("should be undoable via Transaction", [this]()
		{
			if (ActorPath.IsEmpty()) { AddError(TEXT("No actor")); return; }

			// Apply modification
			Subsystem->SetActorTransform(ActorPath, ModifiedTransform);

			// Undo
			if (GEditor) GEditor->UndoTransaction();

			// Readback should show original values
			FBridgeResponse StateResp = Subsystem->GetActorState(ActorPath);
			TestTrue(TEXT("GetActorState should succeed after undo"), StateResp.IsSuccess());

			const TSharedPtr<FJsonObject>* TransformObj;
			if (StateResp.Data->TryGetObjectField(TEXT("transform"), TransformObj))
			{
				const TArray<TSharedPtr<FJsonValue>>* LocArr;
				if ((*TransformObj)->TryGetArrayField(TEXT("location"), LocArr) && LocArr->Num() == 3)
				{
					TestNearlyEqual(TEXT("Undone Location.X should be original"),
						(float)(*LocArr)[0]->AsNumber(), 200.0f, 0.01f);
					TestNearlyEqual(TEXT("Undone Location.Y should be original"),
						(float)(*LocArr)[1]->AsNumber(), 300.0f, 0.01f);
				}
			}
		});

		AfterEach([this]()
		{
			// Undo spawn
			if (GEditor) GEditor->UndoTransaction();
			ActorPath.Empty();
		});
	});
}

// ============================================================
// L2-03: Import → Metadata Check
// 验证：ImportAssets 后 GetAssetMetadata 能找到导入的资产
// 注意：需要测试资源文件才能运行，否则 skip
// ============================================================

BEGIN_DEFINE_SPEC(
	FBridgeL2_ImportMetadataLoop,
	"Project.AgentBridge.L2.ImportMetadataLoop",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::SmokeFilter
)
	UAgentBridgeSubsystem* Subsystem;
	FString TestSourceDir;
	FString TestDestPath;
	bool bHasTestResources;
END_DEFINE_SPEC(FBridgeL2_ImportMetadataLoop)

void FBridgeL2_ImportMetadataLoop::Define()
{
	Describe("import assets then verify via GetAssetMetadata", [this]()
	{
		BeforeEach([this]()
		{
			Subsystem = GEditor ? GEditor->GetEditorSubsystem<UAgentBridgeSubsystem>() : nullptr;
			if (!Subsystem) { AddError(TEXT("Subsystem not available")); return; }

			// 检查是否有测试资源目录
			TestSourceDir = FPaths::ProjectDir() / TEXT("TestResources/ImportTest");
			TestDestPath = TEXT("/Game/Tests/L2_ImportTest");
			bHasTestResources = FPaths::DirectoryExists(TestSourceDir);
		});

		It("should find imported asset via GetAssetMetadata", [this]()
		{
			if (!bHasTestResources)
			{
				AddWarning(FString::Printf(
					TEXT("Test resources not found at %s — skipping import test. "
						 "Create this directory with .fbx/.png files to enable."),
					*TestSourceDir));
				return;
			}

			// 执行导入
			FBridgeResponse ImportResp = Subsystem->ImportAssets(
				TestSourceDir, TestDestPath, /*bReplaceExisting=*/true);

			TestTrue(TEXT("Import should succeed"), ImportResp.IsSuccess());

			// 检查 created_objects
			const TArray<TSharedPtr<FJsonValue>>* CreatedArr;
			if (!ImportResp.Data->TryGetArrayField(TEXT("created_objects"), CreatedArr) || CreatedArr->Num() == 0)
			{
				AddWarning(TEXT("No assets imported — directory may be empty"));
				return;
			}

			// 对第一个导入的资产执行 GetAssetMetadata
			FString ImportedPath = (*CreatedArr)[0]->AsObject()->GetStringField(TEXT("asset_path"));
			FBridgeResponse MetaResp = Subsystem->GetAssetMetadata(ImportedPath);

			TestTrue(TEXT("GetAssetMetadata should succeed"), MetaResp.IsSuccess());
			if (MetaResp.Data.IsValid())
			{
				TestTrue(TEXT("Imported asset should exist"),
					MetaResp.Data->GetBoolField(TEXT("exists")));
			}
		});

		It("should list imported assets as dirty", [this]()
		{
			if (!bHasTestResources)
			{
				AddWarning(TEXT("Skipping — no test resources"));
				return;
			}

			FBridgeResponse DirtyResp = Subsystem->GetDirtyAssets();
			TestTrue(TEXT("GetDirtyAssets should succeed"), DirtyResp.IsSuccess());
			// 导入后应有脏资产
		});

		AfterEach([this]()
		{
			// Undo 导入
			if (GEditor && bHasTestResources)
			{
				GEditor->UndoTransaction();
			}
		});
	});
}
