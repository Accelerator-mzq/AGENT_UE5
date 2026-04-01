// Copyright Epic Games, Inc. All Rights Reserved.

#include "BoardgamePrototypeBoardActor.h"

#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Engine/CollisionProfile.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "Misc/FileHelper.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
	// 证据截图优先可读性：棋盘保持浅色，X/O 用高对比度颜色区分。
	const FLinearColor BoardTintColor(0.82f, 0.82f, 0.78f, 1.0f);
	const FLinearColor PieceXTintColor(0.14f, 0.40f, 0.90f, 1.0f);
	const FLinearColor PieceOTintColor(0.95f, 0.46f, 0.14f, 1.0f);

	UMaterialInterface* LoadBasicShapeMaterial()
	{
		return LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
	}

	UMaterialInterface* LoadBoardMaterial()
	{
		return LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial_Inst.BasicShapeMaterial_Inst"));
	}

	UMaterialInterface* LoadPieceMaterial(const FString& PieceSymbol)
	{
		const TCHAR* MaterialPath =
			PieceSymbol == TEXT("O")
				? TEXT("/Engine/TemplateResources/MI_Template_BaseOrange.MI_Template_BaseOrange")
				: TEXT("/Engine/TemplateResources/MI_Template_BaseBlue.MI_Template_BaseBlue");
		return LoadObject<UMaterialInterface>(nullptr, MaterialPath);
	}

	bool TryApplyTintMaterial(UStaticMeshComponent* MeshComponent, const FLinearColor& TintColor)
	{
		if (!MeshComponent)
		{
			return false;
		}

		UMaterialInterface* BaseMaterial = MeshComponent->GetMaterial(0);
		if (!BaseMaterial)
		{
			BaseMaterial = LoadBasicShapeMaterial();
		}
		if (!BaseMaterial)
		{
			return false;
		}

		TArray<FMaterialParameterInfo> VectorParameterInfos;
		TArray<FGuid> ParameterIds;
		BaseMaterial->GetAllVectorParameterInfo(VectorParameterInfos, ParameterIds);

		static const FName CandidateParameterNames[] = {
			TEXT("Color"),
			TEXT("BaseColor"),
			TEXT("Tint"),
			TEXT("TintColor"),
		};

		FName SelectedParameterName = NAME_None;
		for (const FName& CandidateParameterName : CandidateParameterNames)
		{
			const bool bMatched = VectorParameterInfos.ContainsByPredicate(
				[&CandidateParameterName](const FMaterialParameterInfo& Info)
				{
					return Info.Name == CandidateParameterName;
				});
			if (bMatched)
			{
				SelectedParameterName = CandidateParameterName;
				break;
			}
		}

		if (SelectedParameterName.IsNone())
		{
			return false;
		}

		UMaterialInstanceDynamic* DynamicMaterial = UMaterialInstanceDynamic::Create(BaseMaterial, MeshComponent);
		if (!DynamicMaterial)
		{
			return false;
		}

		DynamicMaterial->SetVectorParameterValue(SelectedParameterName, TintColor);
		MeshComponent->SetMaterial(0, DynamicMaterial);
		return true;
	}
}

ABoardgamePrototypeBoardActor::ABoardgamePrototypeBoardActor()
{
	PrimaryActorTick.bCanEverTick = false;

	if (UStaticMeshComponent* MeshComponent = GetStaticMeshComponent())
	{
		static ConstructorHelpers::FObjectFinder<UStaticMesh> PlaneMesh(TEXT("/Engine/BasicShapes/Plane.Plane"));
		if (PlaneMesh.Succeeded())
		{
			MeshComponent->SetStaticMesh(PlaneMesh.Object);
		}
		MeshComponent->SetMobility(EComponentMobility::Movable);
		MeshComponent->SetCollisionProfileName(UCollisionProfile::BlockAll_ProfileName);
		MeshComponent->SetGenerateOverlapEvents(false);
	}
	ApplyBoardVisualStyle();

	StatusTextComponent = CreateDefaultSubobject<UTextRenderComponent>(TEXT("StatusTextComponent"));
	StatusTextComponent->SetupAttachment(GetStaticMeshComponent());
	StatusTextComponent->SetHorizontalAlignment(EHorizTextAligment::EHTA_Center);
	StatusTextComponent->SetTextRenderColor(FColor::White);
	StatusTextComponent->SetWorldSize(40.0f);
	StatusTextComponent->SetRelativeLocation(FVector(0.0f, 0.0f, 120.0f));

	Rows = 3;
	Cols = 3;
	CellSizeX = 100.0f;
	CellSizeY = 100.0f;
	BoardOrigin = FVector::ZeroVector;
	CurrentPlayer = TEXT("X");
	ResultState = TEXT("running");
	MoveCounter = 0;
	BoardCells.Init(TEXT(""), Rows * Cols);
}

void ABoardgamePrototypeBoardActor::BeginPlay()
{
	Super::BeginPlay();

	if (APlayerController* PlayerController = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr)
	{
		PlayerController->bEnableClickEvents = true;
		PlayerController->bShowMouseCursor = true;
	}

	UpdateStatusText();
}

void ABoardgamePrototypeBoardActor::NotifyActorOnClicked(FKey ButtonPressed)
{
	Super::NotifyActorOnClicked(ButtonPressed);

	if (!GetWorld())
	{
		return;
	}

	APlayerController* PlayerController = GetWorld()->GetFirstPlayerController();
	if (!PlayerController)
	{
		return;
	}

	FHitResult HitResult;
	if (PlayerController->GetHitResultUnderCursor(ECC_Visibility, false, HitResult))
	{
		ApplyMoveByWorldLocation(HitResult.Location);
	}
}

bool ABoardgamePrototypeBoardActor::LoadRuntimeConfigFromFile(const FString& RuntimeConfigPath)
{
	TSharedPtr<FJsonObject> RootObject;
	if (!LoadConfigJson(RuntimeConfigPath, RootObject))
	{
		return false;
	}

	LoadedRuntimeConfigPath = RuntimeConfigPath;
	const TSharedPtr<FJsonObject>* BoardObject = nullptr;
	if (RootObject->TryGetObjectField(TEXT("board"), BoardObject) && BoardObject && BoardObject->IsValid())
	{
		const TArray<TSharedPtr<FJsonValue>>* GridSizeValues = nullptr;
		if ((*BoardObject)->TryGetArrayField(TEXT("grid_size"), GridSizeValues) && GridSizeValues && GridSizeValues->Num() >= 2)
		{
			Rows = static_cast<int32>((*GridSizeValues)[0]->AsNumber());
			Cols = static_cast<int32>((*GridSizeValues)[1]->AsNumber());
		}

		const TArray<TSharedPtr<FJsonValue>>* CellSizeValues = nullptr;
		if ((*BoardObject)->TryGetArrayField(TEXT("cell_size_cm"), CellSizeValues) && CellSizeValues && CellSizeValues->Num() >= 2)
		{
			CellSizeX = static_cast<float>((*CellSizeValues)[0]->AsNumber());
			CellSizeY = static_cast<float>((*CellSizeValues)[1]->AsNumber());
		}

		const TArray<TSharedPtr<FJsonValue>>* BoardLocationValues = nullptr;
		if ((*BoardObject)->TryGetArrayField(TEXT("location"), BoardLocationValues) && BoardLocationValues && BoardLocationValues->Num() >= 3)
		{
			BoardOrigin = FVector(
				static_cast<float>((*BoardLocationValues)[0]->AsNumber()),
				static_cast<float>((*BoardLocationValues)[1]->AsNumber()),
				static_cast<float>((*BoardLocationValues)[2]->AsNumber()));
		}

		const TArray<TSharedPtr<FJsonValue>>* TotalSizeValues = nullptr;
		if ((*BoardObject)->TryGetArrayField(TEXT("total_size_cm"), TotalSizeValues) && TotalSizeValues && TotalSizeValues->Num() >= 2)
		{
			SetActorScale3D(FVector(
				static_cast<float>((*TotalSizeValues)[0]->AsNumber()) / 100.0f,
				static_cast<float>((*TotalSizeValues)[1]->AsNumber()) / 100.0f,
				0.1f));
		}

		SetActorLocation(BoardOrigin);
	}

	PieceScaleMap.Reset();
	PieceMeshPathMap.Reset();
	const TArray<TSharedPtr<FJsonValue>>* PieceCatalogValues = nullptr;
	if (RootObject->TryGetArrayField(TEXT("piece_catalog"), PieceCatalogValues) && PieceCatalogValues)
	{
		for (const TSharedPtr<FJsonValue>& PieceValue : *PieceCatalogValues)
		{
			const TSharedPtr<FJsonObject>* PieceObject = nullptr;
			if (!PieceValue->TryGetObject(PieceObject) || !PieceObject || !PieceObject->IsValid())
			{
				continue;
			}

			const FString Symbol = (*PieceObject)->GetStringField(TEXT("symbol"));
			const FString Shape = (*PieceObject)->GetStringField(TEXT("shape"));
			const TArray<TSharedPtr<FJsonValue>>* DimensionsValues = nullptr;
			FVector PieceScale = FVector(0.5f, 0.5f, 0.5f);
			if ((*PieceObject)->TryGetArrayField(TEXT("dimensions_cm"), DimensionsValues) && DimensionsValues && DimensionsValues->Num() >= 3)
			{
				PieceScale = FVector(
					static_cast<float>((*DimensionsValues)[0]->AsNumber()) / 100.0f,
					static_cast<float>((*DimensionsValues)[1]->AsNumber()) / 100.0f,
					static_cast<float>((*DimensionsValues)[2]->AsNumber()) / 100.0f);
			}

			PieceScaleMap.Add(Symbol, PieceScale);
			PieceMeshPathMap.Add(
				Symbol,
				Shape.Contains(TEXT("Sphere")) ? TEXT("/Engine/BasicShapes/Sphere.Sphere") : TEXT("/Engine/BasicShapes/Cube.Cube"));
		}
	}

	const TSharedPtr<FJsonObject>* TurnFlowObject = nullptr;
	if (RootObject->TryGetObjectField(TEXT("turn_flow_spec"), TurnFlowObject) && TurnFlowObject && TurnFlowObject->IsValid())
	{
		const TSharedPtr<FJsonObject>* DataObject = nullptr;
		if ((*TurnFlowObject)->TryGetObjectField(TEXT("data"), DataObject) && DataObject && DataObject->IsValid())
		{
			CurrentPlayer = (*DataObject)->GetStringField(TEXT("first_player"));
		}
	}

	ResetBoard();
	return true;
}

bool ABoardgamePrototypeBoardActor::ApplyMoveByCell(int32 Row, int32 Col)
{
	if (Row < 0 || Row >= Rows || Col < 0 || Col >= Cols)
	{
		return false;
	}

	if (ResultState != TEXT("running"))
	{
		return false;
	}

	const int32 CellIndex = Row * Cols + Col;
	if (!BoardCells.IsValidIndex(CellIndex) || !BoardCells[CellIndex].IsEmpty())
	{
		return false;
	}

	BoardCells[CellIndex] = CurrentPlayer;
	MoveCounter++;
	SpawnPieceActor(Row, Col, CurrentPlayer);

	FString Winner;
	if (DetectWin(Winner))
	{
		ResultState = FString::Printf(TEXT("%s_wins"), *Winner);
	}
	else if (DetectDraw())
	{
		ResultState = TEXT("draw");
	}
	else
	{
		CurrentPlayer = CurrentPlayer == TEXT("X") ? TEXT("O") : TEXT("X");
	}

	UpdateStatusText();
	return true;
}

bool ABoardgamePrototypeBoardActor::ApplyMoveByWorldLocation(const FVector& WorldLocation)
{
	int32 Row = INDEX_NONE;
	int32 Col = INDEX_NONE;
	if (!TryResolveCellFromWorldLocation(WorldLocation, Row, Col))
	{
		return false;
	}
	return ApplyMoveByCell(Row, Col);
}

FString ABoardgamePrototypeBoardActor::GetBoardRuntimeState() const
{
	TSharedRef<FJsonObject> RootObject = MakeShared<FJsonObject>();
	RootObject->SetStringField(TEXT("current_player"), CurrentPlayer);
	RootObject->SetStringField(TEXT("result_state"), ResultState);
	RootObject->SetStringField(TEXT("runtime_config_path"), LoadedRuntimeConfigPath);
	RootObject->SetNumberField(TEXT("rows"), Rows);
	RootObject->SetNumberField(TEXT("cols"), Cols);
	RootObject->SetNumberField(TEXT("move_count"), MoveCounter);

	TArray<TSharedPtr<FJsonValue>> BoardRows;
	for (int32 Row = 0; Row < Rows; ++Row)
	{
		TArray<TSharedPtr<FJsonValue>> BoardCols;
		for (int32 Col = 0; Col < Cols; ++Col)
		{
			BoardCols.Add(MakeShared<FJsonValueString>(BoardCells[Row * Cols + Col]));
		}
		BoardRows.Add(MakeShared<FJsonValueArray>(BoardCols));
	}
	RootObject->SetArrayField(TEXT("board"), BoardRows);

	FString JsonString;
	TSharedRef<TJsonWriter<>> JsonWriter = TJsonWriterFactory<>::Create(&JsonString);
	FJsonSerializer::Serialize(RootObject, JsonWriter);
	return JsonString;
}

void ABoardgamePrototypeBoardActor::ResetBoard()
{
	BoardCells.Init(TEXT(""), Rows * Cols);
	MoveCounter = 0;
	ResultState = TEXT("running");
	CurrentPlayer = TEXT("X");
	ClearSpawnedPieces();
	UpdateStatusText();
}

bool ABoardgamePrototypeBoardActor::TryResolveCellFromWorldLocation(const FVector& WorldLocation, int32& OutRow, int32& OutCol) const
{
	const float HalfWidth = static_cast<float>(Cols) * CellSizeX * 0.5f;
	const float HalfHeight = static_cast<float>(Rows) * CellSizeY * 0.5f;
	const FVector RelativeLocation = WorldLocation - BoardOrigin;

	if (RelativeLocation.X < -HalfWidth || RelativeLocation.X > HalfWidth)
	{
		return false;
	}
	if (RelativeLocation.Y < -HalfHeight || RelativeLocation.Y > HalfHeight)
	{
		return false;
	}

	OutCol = FMath::Clamp(FMath::FloorToInt((RelativeLocation.X + HalfWidth) / CellSizeX), 0, Cols - 1);
	OutRow = FMath::Clamp(FMath::FloorToInt((RelativeLocation.Y + HalfHeight) / CellSizeY), 0, Rows - 1);
	return true;
}

bool ABoardgamePrototypeBoardActor::DetectWin(FString& OutWinner) const
{
	const TArray<TArray<FIntPoint>> VictoryLines = {
		{FIntPoint(0, 0), FIntPoint(0, 1), FIntPoint(0, 2)},
		{FIntPoint(1, 0), FIntPoint(1, 1), FIntPoint(1, 2)},
		{FIntPoint(2, 0), FIntPoint(2, 1), FIntPoint(2, 2)},
		{FIntPoint(0, 0), FIntPoint(1, 0), FIntPoint(2, 0)},
		{FIntPoint(0, 1), FIntPoint(1, 1), FIntPoint(2, 1)},
		{FIntPoint(0, 2), FIntPoint(1, 2), FIntPoint(2, 2)},
		{FIntPoint(0, 0), FIntPoint(1, 1), FIntPoint(2, 2)},
		{FIntPoint(0, 2), FIntPoint(1, 1), FIntPoint(2, 0)},
	};

	for (const TArray<FIntPoint>& Line : VictoryLines)
	{
		const FString& FirstValue = BoardCells[Line[0].X * Cols + Line[0].Y];
		if (FirstValue.IsEmpty())
		{
			continue;
		}

		if (BoardCells[Line[1].X * Cols + Line[1].Y] == FirstValue &&
			BoardCells[Line[2].X * Cols + Line[2].Y] == FirstValue)
		{
			OutWinner = FirstValue;
			return true;
		}
	}

	return false;
}

bool ABoardgamePrototypeBoardActor::DetectDraw() const
{
	for (const FString& CellValue : BoardCells)
	{
		if (CellValue.IsEmpty())
		{
			return false;
		}
	}
	return true;
}

bool ABoardgamePrototypeBoardActor::SpawnPieceActor(int32 Row, int32 Col, const FString& PieceSymbol)
{
	if (!GetWorld())
	{
		return false;
	}

	const FString DesiredName = MakePieceActorName(PieceSymbol);
	FActorSpawnParameters SpawnParameters;
	SpawnParameters.Name = MakeUniqueObjectName(GetWorld(), AStaticMeshActor::StaticClass(), FName(*DesiredName));
	SpawnParameters.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

	AStaticMeshActor* PieceActor = GetWorld()->SpawnActor<AStaticMeshActor>(
		AStaticMeshActor::StaticClass(),
		GetCellWorldLocation(Row, Col),
		FRotator::ZeroRotator,
		SpawnParameters);
	if (!PieceActor)
	{
		return false;
	}

	PieceActor->SetActorLabel(DesiredName);
	if (UStaticMeshComponent* MeshComponent = PieceActor->GetStaticMeshComponent())
	{
		const FString* MeshPath = PieceMeshPathMap.Find(PieceSymbol);
		UStaticMesh* PieceMesh = LoadObject<UStaticMesh>(nullptr, MeshPath ? **MeshPath : TEXT("/Engine/BasicShapes/Cube.Cube"));
		if (PieceMesh)
		{
			MeshComponent->SetStaticMesh(PieceMesh);
		}

		const FVector* PieceScale = PieceScaleMap.Find(PieceSymbol);
		PieceActor->SetActorScale3D(PieceScale ? *PieceScale : FVector(0.5f, 0.5f, 0.5f));
		MeshComponent->SetCollisionProfileName(UCollisionProfile::NoCollision_ProfileName);
		ApplyPieceVisualStyle(MeshComponent, PieceSymbol);
	}

	SpawnedPieces.Add(PieceActor);
	return true;
}

void ABoardgamePrototypeBoardActor::UpdateStatusText()
{
	if (!StatusTextComponent)
	{
		return;
	}

	if (ResultState == TEXT("running"))
	{
		StatusTextComponent->SetText(FText::FromString(FString::Printf(TEXT("当前回合: %s"), *CurrentPlayer)));
	}
	else
	{
		StatusTextComponent->SetText(FText::FromString(FString::Printf(TEXT("结果: %s"), *ResultState)));
	}
}

void ABoardgamePrototypeBoardActor::ClearSpawnedPieces()
{
	for (TWeakObjectPtr<AActor>& PieceActor : SpawnedPieces)
	{
		if (PieceActor.IsValid())
		{
			PieceActor->Destroy();
		}
	}
	SpawnedPieces.Reset();
}

FVector ABoardgamePrototypeBoardActor::GetCellWorldLocation(int32 Row, int32 Col) const
{
	const float StartX = BoardOrigin.X - (static_cast<float>(Cols) * CellSizeX * 0.5f) + (CellSizeX * 0.5f);
	const float StartY = BoardOrigin.Y - (static_cast<float>(Rows) * CellSizeY * 0.5f) + (CellSizeY * 0.5f);
	return FVector(
		StartX + static_cast<float>(Col) * CellSizeX,
		StartY + static_cast<float>(Row) * CellSizeY,
		BoardOrigin.Z + 50.0f);
}

FString ABoardgamePrototypeBoardActor::MakePieceActorName(const FString& PieceSymbol) const
{
	int32 PieceCount = 0;
	for (const FString& CellValue : BoardCells)
	{
		if (CellValue == PieceSymbol)
		{
			PieceCount++;
		}
	}
	return FString::Printf(TEXT("Piece%s_%d"), *PieceSymbol, PieceCount);
}

void ABoardgamePrototypeBoardActor::ApplyBoardVisualStyle()
{
	if (UStaticMeshComponent* MeshComponent = GetStaticMeshComponent())
	{
		// 棋盘保持中性底色，并尽量保留基础形状材质自带的格纹可读性。
		if (UMaterialInterface* BoardMaterial = LoadBoardMaterial())
		{
			MeshComponent->SetMaterial(0, BoardMaterial);
		}
		TryApplyTintMaterial(MeshComponent, BoardTintColor);
	}
}

void ABoardgamePrototypeBoardActor::ApplyPieceVisualStyle(UStaticMeshComponent* MeshComponent, const FString& PieceSymbol)
{
	if (!MeshComponent)
	{
		return;
	}

	// 棋子优先使用引擎内置的稳定彩色材质，保证证据截图里 X/O 一眼可区分。
	if (UMaterialInterface* PieceMaterial = LoadPieceMaterial(PieceSymbol))
	{
		MeshComponent->SetMaterial(0, PieceMaterial);
		return;
	}

	const FLinearColor TargetColor = PieceSymbol == TEXT("O") ? PieceOTintColor : PieceXTintColor;
	TryApplyTintMaterial(MeshComponent, TargetColor);
}

bool ABoardgamePrototypeBoardActor::LoadConfigJson(const FString& RuntimeConfigPath, TSharedPtr<FJsonObject>& OutJson) const
{
	FString JsonString;
	if (!FFileHelper::LoadFileToString(JsonString, *RuntimeConfigPath))
	{
		return false;
	}

	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonString);
	return FJsonSerializer::Deserialize(Reader, OutJson) && OutJson.IsValid();
}
