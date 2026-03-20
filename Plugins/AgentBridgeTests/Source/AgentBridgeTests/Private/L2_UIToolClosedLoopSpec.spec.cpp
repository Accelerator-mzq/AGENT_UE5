// L2_UIToolClosedLoopSpec.spec.cpp
// AGENT + UE5 可操作層 — L2 闭环驗證：L3 UI 工具
//
// UE5 官方模組：Automation Spec (BDD) + Automation Driver
// 註冊方式：BEGIN_DEFINE_SPEC 宏
// Test Flag：EditorContext + ProductFilter
// Session Frontend 路径：Project.AgentBridge.L2.UITool.*
//
// L3 闭环验证的核心模式：
//   L3 执行 → L3 返回值
//                ↓
//   L1 独立读回 → L1 返回值
//                ↓
//   交叉比对：L3 声称的结果 vs L1 看到的真实状态
//   两者一致 → success，不一致 → mismatch（含字段级差异）
//
// 与 L1 UITool 测试的区别：
//   L1 = 单接口（参数校验 + dry_run + 单次执行）
//   L2 = 多步闭环（L3 操作 → L1 验证 → 交叉比对 → Undo → 再验证）

#include "Misc/AutomationTest.h"
#include "AgentBridgeSubsystem.h"
#include "AutomationDriverAdapter.h"
#include "BridgeTypes.h"
#include "Editor.h"
#include "EditorLevelLibrary.h"

// ============================================================
// L2-04: DragAssetToViewport → L1 ListLevelActors + GetActorState 交叉比对
// ============================================================

BEGIN_DEFINE_SPEC(
	FBridgeL2_UIToolDragVerify,
	"Project.AgentBridge.L2.UITool.DragAssetToViewportLoop",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter
)
	UAgentBridgeSubsystem* Subsystem;
	bool bDriverAvailable;
	FString AssetPath;
	FVector DropLocation;
	FBridgeResponse L3Response;
	int32 ActorCountBefore;
END_DEFINE_SPEC(FBridgeL2_UIToolDragVerify)

void FBridgeL2_UIToolDragVerify::Define()
{
	Describe("drag asset to viewport then cross-verify with L1", [this]()
	{
		BeforeEach([this]()
		{
			Subsystem = GEditor ? GEditor->GetEditorSubsystem<UAgentBridgeSubsystem>() : nullptr;
			if (!Subsystem) { AddError(TEXT("Subsystem not available")); return; }

			bDriverAvailable = Subsystem->IsAutomationDriverAvailable();
			if (!bDriverAvailable)
			{
				AddWarning(TEXT("Automation Driver not available — L3 闭环测试将跳过执行步骤"));
			}

			AssetPath = TEXT("/Engine/BasicShapes/Cube");
			DropLocation = FVector(1500.0f, 1500.0f, 0.0f);

			// 记录操作前 Actor 数量
			FBridgeResponse ListResp = Subsystem->ListLevelActors();
			ActorCountBefore = 0;
			if (ListResp.Data.IsValid())
			{
				const TArray<TSharedPtr<FJsonValue>>* Arr;
				if (ListResp.Data->TryGetArrayField(TEXT("actors"), Arr))
				{
					ActorCountBefore = Arr->Num();
				}
			}

			// 执行 L3 拖拽（如果 Driver 可用）
			if (bDriverAvailable)
			{
				L3Response = Subsystem->DragAssetToViewport(AssetPath, DropLocation);
			}
		});

		It("L3 should report execution success", [this]()
		{
			if (!bDriverAvailable) { AddWarning(TEXT("Skipped — Driver unavailable")); return; }

			TestTrue(TEXT("L3 DragAssetToViewport should succeed"), L3Response.IsSuccess());

			if (L3Response.Data.IsValid())
			{
				TestTrue(TEXT("L3 data should contain tool_layer"),
					L3Response.Data->HasField(TEXT("tool_layer")));
				TestEqual(TEXT("tool_layer should be L3_UITool"),
					L3Response.Data->GetStringField(TEXT("tool_layer")), TEXT("L3_UITool"));
			}
		});

		It("L1 ListLevelActors should show actor count increased", [this]()
		{
			if (!bDriverAvailable) { AddWarning(TEXT("Skipped")); return; }
			if (!L3Response.IsSuccess()) { AddWarning(TEXT("L3 failed, skip L1 verify")); return; }

			FBridgeResponse ListAfter = Subsystem->ListLevelActors();
			TestTrue(TEXT("ListLevelActors should succeed"), ListAfter.IsSuccess());

			int32 CountAfter = 0;
			if (ListAfter.Data.IsValid())
			{
				const TArray<TSharedPtr<FJsonValue>>* Arr;
				if (ListAfter.Data->TryGetArrayField(TEXT("actors"), Arr))
				{
					CountAfter = Arr->Num();
				}
			}

			TestTrue(TEXT("Actor count should increase after drag"),
				CountAfter > ActorCountBefore);

			AddInfo(FString::Printf(TEXT("Actor count: before=%d, after=%d"),
				ActorCountBefore, CountAfter));
		});

		It("L3 created_actors should match L1 actor list (cross-verify)", [this]()
		{
			if (!bDriverAvailable) { AddWarning(TEXT("Skipped")); return; }
			if (!L3Response.IsSuccess()) { AddWarning(TEXT("L3 failed")); return; }

			// 执行正式交叉比对
			FBridgeUIVerification Verification = Subsystem->CrossVerifyUIOperation(
				L3Response, TEXT("ListLevelActors"), TEXT(""));

			// 核心断言：L3 和 L1 必须一致
			TestTrue(TEXT("L3 and L1 should be consistent"), Verification.bConsistent);

			EBridgeStatus FinalStatus = Verification.GetFinalStatus();
			TestEqual(TEXT("Final status should be success"),
				BridgeStatusToString(FinalStatus), TEXT("success"));

			// 记录比对详情
			AddInfo(FString::Printf(TEXT("Cross-verify: consistent=%s, final=%s, mismatches=%d"),
				Verification.bConsistent ? TEXT("true") : TEXT("false"),
				*BridgeStatusToString(FinalStatus),
				Verification.Mismatches.Num()));

			for (const FString& M : Verification.Mismatches)
			{
				AddError(FString::Printf(TEXT("MISMATCH: %s"), *M));
			}
		});

		It("L3 created actors should have valid state via L1 GetActorState", [this]()
		{
			if (!bDriverAvailable) { AddWarning(TEXT("Skipped")); return; }
			if (!L3Response.IsSuccess() || !L3Response.Data.IsValid()) { AddWarning(TEXT("L3 failed")); return; }

			// 从 L3 返回值中取出 created_actors 路径
			const TArray<TSharedPtr<FJsonValue>>* CreatedArr;
			if (!L3Response.Data->TryGetArrayField(TEXT("created_actors"), CreatedArr) || CreatedArr->Num() == 0)
			{
				AddWarning(TEXT("No created_actors in L3 response"));
				return;
			}

			for (const auto& CA : *CreatedArr)
			{
				FString ActorPath = CA->AsObject()->GetStringField(TEXT("actor_path"));

				// L1 独立读回：GetActorState
				FBridgeResponse StateResp = Subsystem->GetActorState(ActorPath);
				TestTrue(FString::Printf(TEXT("GetActorState should succeed for %s"), *ActorPath),
					StateResp.IsSuccess());

				if (StateResp.Data.IsValid())
				{
					// 验证 Transform 存在且有效
					TestTrue(TEXT("Should have transform"),
						StateResp.Data->HasField(TEXT("transform")));

					// 验证位置接近 DropLocation（拖拽后的实际位置可能与 DropLocation 有偏差）
					const TSharedPtr<FJsonObject>* TransformObj;
					if (StateResp.Data->TryGetObjectField(TEXT("transform"), TransformObj))
					{
						const TArray<TSharedPtr<FJsonValue>>* LocArr;
						if ((*TransformObj)->TryGetArrayField(TEXT("location"), LocArr) && LocArr->Num() == 3)
						{
							float ActualX = (*LocArr)[0]->AsNumber();
							float ActualY = (*LocArr)[1]->AsNumber();

							AddInfo(FString::Printf(TEXT("Dragged actor location: (%.1f, %.1f), expected near (%.1f, %.1f)"),
								ActualX, ActualY, DropLocation.X, DropLocation.Y));

							// 拖拽位置容差较大（UI 操作精度低于 L1 API）
							// 使用 100cm 容差（L1 语义工具用 0.01cm）
							TestNearlyEqual(TEXT("X should be near drop location"),
								ActualX, DropLocation.X, 100.0f);
							TestNearlyEqual(TEXT("Y should be near drop location"),
								ActualY, DropLocation.Y, 100.0f);
						}
					}
				}
			}
		});

		It("should be undoable and L1 confirms actor removed", [this]()
		{
			if (!bDriverAvailable) { AddWarning(TEXT("Skipped")); return; }
			if (!L3Response.IsSuccess()) { AddWarning(TEXT("L3 failed")); return; }

			// Undo
			if (GEditor) GEditor->UndoTransaction();

			// L1 验证 Actor 数量恢复
			FBridgeResponse ListAfterUndo = Subsystem->ListLevelActors();
			int32 CountAfterUndo = 0;
			if (ListAfterUndo.Data.IsValid())
			{
				const TArray<TSharedPtr<FJsonValue>>* Arr;
				if (ListAfterUndo.Data->TryGetArrayField(TEXT("actors"), Arr))
				{
					CountAfterUndo = Arr->Num();
				}
			}

			TestEqual(TEXT("Actor count should return to original after Undo"),
				CountAfterUndo, ActorCountBefore);
		});

		AfterEach([this]()
		{
			// 保险清理
			if (bDriverAvailable && GEditor)
			{
				GEditor->UndoTransaction();
			}
		});
	});
}

// ============================================================
// L2-05: TypeInDetailPanelField → L1 GetActorState 交叉比对
// ============================================================

BEGIN_DEFINE_SPEC(
	FBridgeL2_UIToolTypeVerify,
	"Project.AgentBridge.L2.UITool.TypeInFieldLoop",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter
)
	UAgentBridgeSubsystem* Subsystem;
	bool bDriverAvailable;
	FString SpawnedActorPath;
END_DEFINE_SPEC(FBridgeL2_UIToolTypeVerify)

void FBridgeL2_UIToolTypeVerify::Define()
{
	Describe("type in detail panel then cross-verify with L1 GetActorState", [this]()
	{
		BeforeEach([this]()
		{
			Subsystem = GEditor ? GEditor->GetEditorSubsystem<UAgentBridgeSubsystem>() : nullptr;
			if (!Subsystem) { AddError(TEXT("Subsystem not available")); return; }

			bDriverAvailable = Subsystem->IsAutomationDriverAvailable();

			// 用 L1 SpawnActor 准备测试 Actor
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			FString LevelPath = World ? World->GetPathName() : TEXT("");

			FBridgeTransform Transform;
			Transform.Location = FVector(500.0f, 500.0f, 0.0f);
			Transform.Rotation = FRotator::ZeroRotator;
			Transform.RelativeScale3D = FVector::OneVector;

			FBridgeResponse SpawnResp = Subsystem->SpawnActor(
				LevelPath, TEXT("/Script/Engine.StaticMeshActor"),
				TEXT("L2_UITool_TypeTest_Actor"), Transform);

			if (SpawnResp.IsSuccess() && SpawnResp.Data.IsValid())
			{
				const TArray<TSharedPtr<FJsonValue>>* Created;
				if (SpawnResp.Data->TryGetArrayField(TEXT("created_objects"), Created) && Created->Num() > 0)
				{
					SpawnedActorPath = (*Created)[0]->AsObject()->GetStringField(TEXT("actor_path"));
				}
			}
		});

		It("L1 GetActorState should succeed before L3 operation", [this]()
		{
			if (SpawnedActorPath.IsEmpty()) { AddError(TEXT("No spawned actor")); return; }

			FBridgeResponse Before = Subsystem->GetActorState(SpawnedActorPath);
			TestTrue(TEXT("GetActorState should succeed before L3 op"), Before.IsSuccess());
		});

		It("L3 TypeInDetailPanelField should execute without crash", [this]()
		{
			if (!bDriverAvailable) { AddWarning(TEXT("Skipped — Driver unavailable")); return; }
			if (SpawnedActorPath.IsEmpty()) { AddError(TEXT("No spawned actor")); return; }

			// 尝试在 Detail Panel 中输入 Actor Label
			FBridgeResponse L3Resp = Subsystem->TypeInDetailPanelField(
				SpawnedActorPath, TEXT("ActorLabel"), TEXT("L2_UITool_ModifiedLabel"));

			// 不做硬断言（Detail Panel 属性定位可能因 Editor 布局差异失败）
			// 仅验证不崩溃且返回有效响应
			TestTrue(TEXT("L3 should return valid response (success or failed, not crash)"),
				L3Resp.Status != EBridgeStatus::ValidationError);

			AddInfo(FString::Printf(TEXT("L3 TypeInDetailPanelField: status=%s"),
				*BridgeStatusToString(L3Resp.Status)));

			if (L3Resp.IsSuccess())
			{
				// 如果 L3 成功，做交叉比对
				FBridgeUIVerification Verify = Subsystem->CrossVerifyUIOperation(
					L3Resp, TEXT("GetActorState"), SpawnedActorPath);

				AddInfo(FString::Printf(TEXT("Cross-verify: consistent=%s, mismatches=%d"),
					Verify.bConsistent ? TEXT("true") : TEXT("false"),
					Verify.Mismatches.Num()));
			}
		});

		It("L1 GetActorState should still work after L3 operation", [this]()
		{
			if (SpawnedActorPath.IsEmpty()) { AddError(TEXT("No spawned actor")); return; }

			// L3 操作（无论成败）后，L1 读回必须仍然可用
			FBridgeResponse After = Subsystem->GetActorState(SpawnedActorPath);
			TestTrue(TEXT("GetActorState should still succeed after L3 op"), After.IsSuccess());
		});

		AfterEach([this]()
		{
			// Undo：TypeIn + Spawn = 最多 2 次
			if (GEditor)
			{
				GEditor->UndoTransaction();
				GEditor->UndoTransaction();
			}
			SpawnedActorPath.Empty();
		});
	});
}
