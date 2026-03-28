[CmdletBinding()]
param(
    [string]$EngineRoot = "",
    [string]$ProjectPath = "",
    [string]$RcUrl = "http://localhost:30010/remote/info",
    [int]$RcTimeoutSec = 300,
    [switch]$ForceCloseExisting,
    [switch]$ClearPackageRestoreData,
    [switch]$ValidateOnly,
    [switch]$CloseAfterReady,
    [string]$RcOutputPath = "",
    [string[]]$ExtraEditorArgs = @()
)

$ErrorActionPreference = "Stop"

function Get-DefaultEngineRoot {
    <#
        自动探测可用的 UE5 Editor 根目录。
        优先 Source Build 注册表，再看 Epic Launcher 安装目录，最后走兜底路径。
    #>
    $candidates = New-Object System.Collections.Generic.List[string]

    $buildsKey = "HKCU:\SOFTWARE\Epic Games\Unreal Engine\Builds"
    if (Test-Path $buildsKey) {
        $buildProps = Get-ItemProperty -Path $buildsKey
        foreach ($prop in $buildProps.PSObject.Properties) {
            if ($prop.Name -in @("PSPath", "PSParentPath", "PSChildName", "PSDrive", "PSProvider")) {
                continue
            }

            if ($prop.Value -is [string] -and -not [string]::IsNullOrWhiteSpace($prop.Value)) {
                $normalizedBuildPath = ($prop.Value -replace "/", [IO.Path]::DirectorySeparatorChar)
                $candidates.Add($normalizedBuildPath.TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar))
            }
        }
    }

    foreach ($installKey in @(
        "HKLM:\SOFTWARE\WOW6432Node\EpicGames\Unreal Engine",
        "HKLM:\SOFTWARE\EpicGames\Unreal Engine"
    )) {
        if (-not (Test-Path $installKey)) {
            continue
        }

        $installDir = (Get-ItemProperty -Path $installKey -ErrorAction SilentlyContinue).INSTALLDIR
        if ([string]::IsNullOrWhiteSpace($installDir)) {
            continue
        }

        Get-ChildItem -Path $installDir -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -like "UE_*" } |
            ForEach-Object {
                $candidates.Add($_.FullName.TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar))
            }
    }

    foreach ($fallback in @(
        "E:\GameProject\UE5-SourceCode-5.5.4\UnrealEngine",
        "E:\Epic Games\UE_5.5",
        "C:\Program Files\Epic Games\UE_5.5"
    )) {
        $candidates.Add($fallback)
    }

    $seen = New-Object "System.Collections.Generic.HashSet[string]" ([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($candidate in $candidates) {
        if ([string]::IsNullOrWhiteSpace($candidate)) {
            continue
        }

        $normalized = $candidate.Trim()
        if (-not $seen.Add($normalized)) {
            continue
        }

        $editorExe = Join-Path $normalized "Engine\\Binaries\\Win64\\UnrealEditor.exe"
        if (Test-Path $editorExe) {
            return $normalized
        }
    }

    throw "未能自动探测到 Unreal Engine 根目录。请显式传入 -EngineRoot。"
}

function Get-UnrealEditorProcessInfo {
    <#
        返回当前 UnrealEditor 进程的关键信息。
        这里同时读取 CommandLine 和 MainWindowTitle，方便识别“项目浏览器”fallback。
    #>
    $cimByPid = @{}
    Get-CimInstance Win32_Process |
        Where-Object { $_.Name -like "UnrealEditor*" } |
        ForEach-Object {
            $cimByPid[[int]$_.ProcessId] = $_
        }

    $processList = Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ProcessName -like "UnrealEditor*" }

    foreach ($proc in $processList) {
        $cim = $cimByPid[[int]$proc.Id]
        [PSCustomObject]@{
            ProcessId       = [int]$proc.Id
            ProcessName     = $proc.ProcessName
            MainWindowTitle = $proc.MainWindowTitle
            CommandLine     = if ($cim) { $cim.CommandLine } else { "" }
        }
    }
}

function Test-IsProjectBrowser {
    param(
        [string]$WindowTitle
    )

    if ([string]::IsNullOrWhiteSpace($WindowTitle)) {
        return $false
    }

    return (
        $WindowTitle -like "*项目浏览器*" -or
        $WindowTitle -like "*Project Browser*" -or
        $WindowTitle -like "*虚幻项目浏览器*"
    )
}

function Test-RcReady {
    param(
        [string]$Url
    )

    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 5
        return [PSCustomObject]@{
            Ready      = $true
            StatusCode = [int]$response.StatusCode
            Body       = [string]$response.Content
            Error      = ""
        }
    }
    catch {
        return [PSCustomObject]@{
            Ready      = $false
            StatusCode = 0
            Body       = ""
            Error      = $_.Exception.Message
        }
    }
}

function Wait-RcReady {
    param(
        [int]$TimeoutSec,
        [string]$Url,
        [int]$ExpectedProcessId
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    $lastRcError = ""

    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 5

        $editorProcess = Get-Process -Id $ExpectedProcessId -ErrorAction SilentlyContinue
        if (-not $editorProcess) {
            throw "UnrealEditor 进程已退出，RC API 未就绪。"
        }

        if (Test-IsProjectBrowser -WindowTitle $editorProcess.MainWindowTitle) {
            throw "检测到 UnrealEditor 停在项目浏览器页面，未真正进入 .uproject。"
        }

        $rcState = Test-RcReady -Url $Url
        if ($rcState.Ready) {
            return $rcState
        }

        $lastRcError = $rcState.Error
    }

    if ([string]::IsNullOrWhiteSpace($lastRcError)) {
        throw "等待 RC API 超时（${TimeoutSec}s），地址：$Url"
    }

    throw "等待 RC API 超时（${TimeoutSec}s），地址：$Url，最后错误：$lastRcError"
}

function Close-UnrealEditorProcesses {
    param(
        [array]$ProcessInfos
    )

    foreach ($info in $ProcessInfos) {
        Write-Host "[UE-Start] Closing UnrealEditor PID=$($info.ProcessId) Title='$($info.MainWindowTitle)'" -ForegroundColor Yellow
        Stop-Process -Id $info.ProcessId -Force -ErrorAction Stop
    }

    Start-Sleep -Seconds 2
}

function Clear-PackageRestoreArtifacts {
    param(
        [string]$ResolvedProjectPath
    )

    $projectRoot = Split-Path $ResolvedProjectPath -Parent
    $autosaveRoot = Join-Path $projectRoot "Saved\\Autosaves"
    $tempAutosaveRoot = Join-Path $autosaveRoot "Temp"
    $targets = New-Object System.Collections.Generic.List[string]

    $packageRestoreData = Join-Path $autosaveRoot "PackageRestoreData.json"
    if (Test-Path $packageRestoreData) {
        $targets.Add($packageRestoreData)
    }

    if (Test-Path $tempAutosaveRoot) {
        Get-ChildItem -LiteralPath $tempAutosaveRoot -Filter "Untitled_*_Auto*.umap" -ErrorAction SilentlyContinue |
            ForEach-Object {
                $targets.Add($_.FullName)
            }
    }

    if ($targets.Count -eq 0) {
        Write-Host "[UE-Start] No package-restore artifacts found." -ForegroundColor DarkGray
        return
    }

    foreach ($target in $targets) {
        if (Test-Path $target) {
            Remove-Item -LiteralPath $target -Force -ErrorAction Stop
            Write-Host "[UE-Start] Cleared package-restore artifact: $target" -ForegroundColor Yellow
        }
    }
}

function Get-RcCompatibleLaunchArgs {
    param(
        [string]$ResolvedProjectPath,
        [string[]]$UserExtraArgs
    )

    $sanitizedExtraArgs = @()
    foreach ($arg in $UserExtraArgs) {
        if ([string]::IsNullOrWhiteSpace($arg)) {
            continue
        }

        $trimmed = $arg.Trim()
        if ($trimmed -ieq "-NullRHI") {
            throw (
                "RC 校验会话不支持 -NullRHI。UE5.5.4 的 WebRemoteControl 在 !FApp::CanEverRender() " +
                "时会直接禁用 HTTP 服务；请改用可渲染会话。"
            )
        }

        if ($trimmed -ieq "-RCWebControlDisable") {
            throw "RC 校验会话不能同时传入 -RCWebControlDisable。"
        }

        $sanitizedExtraArgs += $trimmed
    }

    return @(
        $ResolvedProjectPath,
        "-NoSplash",
        "-Unattended",
        "-NoSound",
        "-RCWebControlEnable",
        "-ExecCmds=WebControl.StartServer"
    ) + $sanitizedExtraArgs
}

function Write-RcBodyToFile {
    param(
        [string]$TargetPath,
        [string]$Body
    )

    if ([string]::IsNullOrWhiteSpace($TargetPath)) {
        return
    }

    $targetDir = Split-Path $TargetPath -Parent
    if (-not [string]::IsNullOrWhiteSpace($targetDir)) {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    }

    $Body | Set-Content -Path $TargetPath -Encoding UTF8
    Write-Host "[UE-Start] 已写出 RC 响应：$TargetPath" -ForegroundColor Green
}

# 解析并固定项目路径，避免后续相对路径和空格路径混用。
if ([string]::IsNullOrWhiteSpace($ProjectPath)) {
    $defaultProjectPath = Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path "Mvpv4TestCodex.uproject"
    $resolvedProjectPath = (Resolve-Path $defaultProjectPath).Path
}
else {
    $resolvedProjectPath = (Resolve-Path $ProjectPath).Path
}

if ([string]::IsNullOrWhiteSpace($EngineRoot)) {
    $resolvedEngineRoot = Get-DefaultEngineRoot
}
else {
    $resolvedEngineRoot = (Resolve-Path $EngineRoot).Path
}

$editorExe = Join-Path $resolvedEngineRoot "Engine\\Binaries\\Win64\\UnrealEditor.exe"

if (-not (Test-Path $editorExe)) {
    throw "UnrealEditor.exe 不存在：$editorExe"
}

if (-not (Test-Path $resolvedProjectPath)) {
    throw ".uproject 不存在：$resolvedProjectPath"
}

$launchArgs = Get-RcCompatibleLaunchArgs -ResolvedProjectPath $resolvedProjectPath -UserExtraArgs $ExtraEditorArgs
$existingEditors = @(Get-UnrealEditorProcessInfo)
$projectBrowserEditors = @(
    $existingEditors | Where-Object {
        Test-IsProjectBrowser -WindowTitle $_.MainWindowTitle
    }
)
$matchingEditors = @(
    $existingEditors | Where-Object {
        $_.CommandLine -like "*$resolvedProjectPath*" -and
        -not (Test-IsProjectBrowser -WindowTitle $_.MainWindowTitle)
    }
)

if ($ValidateOnly) {
    Write-Host "[UE-Start] ValidateOnly=TRUE" -ForegroundColor Cyan
    Write-Host "[UE-Start] EngineRoot=$resolvedEngineRoot"
    Write-Host "[UE-Start] EditorExe=$editorExe"
    Write-Host "[UE-Start] ProjectPath=$resolvedProjectPath"
    Write-Host "[UE-Start] LaunchArgs=$($launchArgs -join ' ')"
    Write-Host "[UE-Start] RcUrl=$RcUrl"
    Write-Host "[UE-Start] ExistingEditorCount=$($existingEditors.Count)"

    foreach ($info in $existingEditors) {
        Write-Host "[UE-Start] Existing PID=$($info.ProcessId) Title='$($info.MainWindowTitle)'"
        Write-Host "[UE-Start] Existing CommandLine=$($info.CommandLine)"
    }

    exit 0
}

if ($ClearPackageRestoreData) {
    Clear-PackageRestoreArtifacts -ResolvedProjectPath $resolvedProjectPath
}

if ($existingEditors.Count -gt 0) {
    if ($ForceCloseExisting) {
        Close-UnrealEditorProcesses -ProcessInfos $existingEditors
        $existingEditors = @()
        $projectBrowserEditors = @()
        $matchingEditors = @()
    }
    elseif ($projectBrowserEditors.Count -gt 0) {
        throw "检测到 UnrealEditor 当前停在项目浏览器页面。请关闭该进程，或使用 -ForceCloseExisting 重新拉起项目。"
    }
    elseif ($matchingEditors.Count -gt 0) {
        Write-Host "[UE-Start] 目标项目对应的 UnrealEditor 已在运行，开始检查 RC API..." -ForegroundColor Yellow
        $existingRcState = Test-RcReady -Url $RcUrl
        if ($existingRcState.Ready) {
            Write-RcBodyToFile -TargetPath $RcOutputPath -Body $existingRcState.Body
            Write-Host "[UE-Start] RC API 已就绪，无需重复启动。" -ForegroundColor Green
            exit 0
        }

        throw (
            "目标项目进程已存在，但 RC API 尚未就绪。若该进程是旧的 -NullRHI/非 RC 兼容会话，" +
            "请改用 -ForceCloseExisting 重新拉起。"
        )
    }
    else {
        throw "检测到其他 UnrealEditor 进程正在运行。为避免误关用户会话，本脚本默认不再启动第二个实例。可改用 -ForceCloseExisting。"
    }
}

Write-Host "[UE-Start] EngineRoot=$resolvedEngineRoot" -ForegroundColor Cyan
Write-Host "[UE-Start] Launching: $editorExe $($launchArgs -join ' ')" -ForegroundColor Cyan
$launchedProcess = Start-Process -FilePath $editorExe -ArgumentList $launchArgs -WorkingDirectory (Split-Path $resolvedProjectPath -Parent) -PassThru

$rcState = Wait-RcReady -TimeoutSec $RcTimeoutSec -Url $RcUrl -ExpectedProcessId $launchedProcess.Id
Write-RcBodyToFile -TargetPath $RcOutputPath -Body $rcState.Body

Write-Host "[UE-Start] UnrealEditor started successfully." -ForegroundColor Green
Write-Host "[UE-Start] PID=$($launchedProcess.Id)"
Write-Host "[UE-Start] RC StatusCode=$($rcState.StatusCode)"
Write-Host "[UE-Start] RC Url=$RcUrl"

if ($CloseAfterReady) {
    Write-Host "[UE-Start] CloseAfterReady=TRUE，正在关闭当前拉起的 UnrealEditor 进程..." -ForegroundColor Yellow
    Stop-Process -Id $launchedProcess.Id -Force -ErrorAction Stop
}

