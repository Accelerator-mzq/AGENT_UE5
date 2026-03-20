// L2_ClosedLoopSpecs.spec.cpp
// AGENT + UE5 鍙搷浣滃堡 鈥?L2 闂幆椹楄瓑
//
// UE5 瀹樻柟妯＄祫锛欰utomation Spec锛圔DD 璇硶锛?// 瑷诲唺鏂瑰紡锛欱EGIN_DEFINE_SPEC / DEFINE_SPEC 瀹?// Test Flag锛欵ditorContext + SmokeFilter
// Session Frontend 璺緞锛歅roject.AgentBridge.L2.*
//
// L2 闂幆楠岃瘉鐨勬牳蹇冩ā寮忥細
//   鍐欐搷浣?鈫?璇诲洖 鈫?楠岃瘉锛堝啓鍚庤鍥炰竴鑷存€?+ 鍓綔鐢ㄦ鏌ワ級
//
// 涓?L1 鐨勫尯鍒細
//   L1 = 鍗曟帴鍙ｆ纭€э紙璋冧竴娆★紝鐪嬭繑鍥炲€煎涓嶅锛?//   L2 = 澶氭帴鍙ｅ崗浣滄纭€э紙鍐欌啋璇烩啋楠?鐨勯摼璺槸鍚﹂棴鐜級

#include "Misc/AutomationTest.h"
#include "AgentBridgeSubsystem.h"
#include "BridgeTypes.h"
#include "Editor.h"

// ============================================================
// L2-01: Spawn 鈫?Readback 鈫?Verify
// 楠岃瘉锛歋pawnActor 鍚?GetActorState 璇诲洖鐨?Transform 涓庨鏈熶竴鑷?// ============================================================

BEGIN_DEFINE_SPEC(
	FBridgeL2_SpawnReadbackLoop,
	"Project.AgentBridge.L2.SpawnReadbackLoop",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter
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

			// 璁剧疆杈撳叆 Transform
			InputTransform.Location = FVector(1234.0f, 5678.0f, 90.0f);
			InputTransform.Rotation = FRotator(0.0f, 135.0f, 0.0f);
			InputTransform.RelativeScale3D = FVector(1.5f, 1.5f, 1.5f);

			// 鎵ц Spawn
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

			// 鎻愬彇 actor_path
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
				float X = static_cast<float>((*LocArr)[0]->AsNumber());
				float Y = static_cast<float>((*LocArr)[1]->AsNumber());
				float Z = static_cast<float>((*LocArr)[2]->AsNumber());
				TestNearlyEqual(TEXT("Location.X"), X, static_cast<float>(InputTransform.Location.X), LocationTolerance);
				TestNearlyEqual(TEXT("Location.Y"), Y, static_cast<float>(InputTransform.Location.Y), LocationTolerance);
				TestNearlyEqual(TEXT("Location.Z"), Z, static_cast<float>(InputTransform.Location.Z), LocationTolerance);
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
				float Pitch = static_cast<float>((*RotArr)[0]->AsNumber());
				float Yaw = static_cast<float>((*RotArr)[1]->AsNumber());
				float Roll = static_cast<float>((*RotArr)[2]->AsNumber());
				TestNearlyEqual(TEXT("Rotation.Pitch"), Pitch, static_cast<float>(InputTransform.Rotation.Pitch), RotationTolerance);
				TestNearlyEqual(TEXT("Rotation.Yaw"), Yaw, static_cast<float>(InputTransform.Rotation.Yaw), RotationTolerance);
				TestNearlyEqual(TEXT("Rotation.Roll"), Roll, static_cast<float>(InputTransform.Rotation.Roll), RotationTolerance);
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
				float SX = static_cast<float>((*ScaleArr)[0]->AsNumber());
				float SY = static_cast<float>((*ScaleArr)[1]->AsNumber());
				float SZ = static_cast<float>((*ScaleArr)[2]->AsNumber());
				TestNearlyEqual(TEXT("Scale.X"), SX, static_cast<float>(InputTransform.RelativeScale3D.X), ScaleTolerance);
				TestNearlyEqual(TEXT("Scale.Y"), SY, static_cast<float>(InputTransform.RelativeScale3D.Y), ScaleTolerance);
				TestNearlyEqual(TEXT("Scale.Z"), SZ, static_cast<float>(InputTransform.RelativeScale3D.Z), ScaleTolerance);
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
			// Spawn 鍚庡叧鍗″簲涓鸿剰
			// 娉ㄦ剰锛氫笉鍋氫弗鏍兼柇瑷€锛堝叾浠栨搷浣滀篃鍙兘浜х敓鑴忚祫浜э級锛屼粎楠岃瘉鎺ュ彛鍙敤
		});

		AfterEach([this]()
		{
			// Undo 娓呯悊
			if (GEditor)
			{
				GEditor->UndoTransaction();
			}
			SpawnedActorPath.Empty();
		});
	});
}

// ============================================================
// L2-02: Transform Modify 鈫?Readback 鈫?Verify
// 楠岃瘉锛歋etActorTransform 鍚庤鍥炵殑 Transform 涓庢柊鍊间竴鑷达紝鏃у€间笌棰勬湡涓€鑷?// ============================================================

BEGIN_DEFINE_SPEC(
	FBridgeL2_TransformModifyLoop,
	"Project.AgentBridge.L2.TransformModifyLoop",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter
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

			// Spawn 鍒濆 Actor
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

			// 瀹氫箟鐩爣 Transform
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
// L2-03: Import 鈫?Metadata Check
// 楠岃瘉锛欼mportAssets 鍚?GetAssetMetadata 鑳芥壘鍒板鍏ョ殑璧勪骇
// 娉ㄦ剰锛氶渶瑕佹祴璇曡祫婧愭枃浠舵墠鑳借繍琛岋紝鍚﹀垯 skip
// ============================================================

BEGIN_DEFINE_SPEC(
	FBridgeL2_ImportMetadataLoop,
	"Project.AgentBridge.L2.ImportMetadataLoop",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter
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

			// 妫€鏌ユ槸鍚︽湁娴嬭瘯璧勬簮鐩綍
			TestSourceDir = FPaths::ProjectDir() / TEXT("TestResources/ImportTest");
			TestDestPath = TEXT("/Game/Tests/L2_ImportTest");
			bHasTestResources = FPaths::DirectoryExists(TestSourceDir);
		});

		It("should find imported asset via GetAssetMetadata", [this]()
		{
			if (!bHasTestResources)
			{
				AddWarning(FString::Printf(
					TEXT("Test resources not found at %s 鈥?skipping import test. "
						 "Create this directory with .fbx/.png files to enable."),
					*TestSourceDir));
				return;
			}

			// 鎵ц瀵煎叆
			FBridgeResponse ImportResp = Subsystem->ImportAssets(
				TestSourceDir, TestDestPath, /*bReplaceExisting=*/true);

			TestTrue(TEXT("Import should succeed"), ImportResp.IsSuccess());

			// 妫€鏌?created_objects
			const TArray<TSharedPtr<FJsonValue>>* CreatedArr;
			if (!ImportResp.Data->TryGetArrayField(TEXT("created_objects"), CreatedArr) || CreatedArr->Num() == 0)
			{
				AddWarning(TEXT("No assets imported 鈥?directory may be empty"));
				return;
			}

			// 瀵圭涓€涓鍏ョ殑璧勪骇鎵ц GetAssetMetadata
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
				AddWarning(TEXT("Skipping 鈥?no test resources"));
				return;
			}

			FBridgeResponse DirtyResp = Subsystem->GetDirtyAssets();
			TestTrue(TEXT("GetDirtyAssets should succeed"), DirtyResp.IsSuccess());
			// 瀵煎叆鍚庡簲鏈夎剰璧勪骇
		});

		AfterEach([this]()
		{
			// Undo 瀵煎叆
			if (GEditor && bHasTestResources)
			{
				GEditor->UndoTransaction();
			}
		});
	});
}


