[CmdletBinding()]
param(
    [string]$EngineRoot = "E:\Epic Games\UE_5.5",
    [string]$ProjectPath = "",
    [switch]$ForceCloseExisting,
    [switch]$ValidateOnly,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$EditorArgs
)

$ErrorActionPreference = "Stop"
$DoubleQuote = [string][char]34

if ([string]::IsNullOrWhiteSpace($ProjectPath)) {
    $workspaceRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path
    $ProjectPath = Join-Path $workspaceRoot "Mvpv4TestCodex.uproject"
}

$ResolvedProjectPath = (Resolve-Path $ProjectPath).Path
$ProjectRoot = Split-Path $ResolvedProjectPath -Parent
$EditorExe = Join-Path $EngineRoot "Engine\\Binaries\\Win64\\UnrealEditor-Cmd.exe"

if (-not (Test-Path $EditorExe)) {
    throw "UnrealEditor-Cmd.exe not found: $EditorExe"
}

if (-not (Test-Path $ResolvedProjectPath)) {
    throw ".uproject not found: $ResolvedProjectPath"
}

$ExistingCmdProcesses = @(
    Get-CimInstance Win32_Process |
        Where-Object { $_.Name -like "UnrealEditor-Cmd*" }
)

$FormattedArgs = New-Object System.Collections.Generic.List[string]
$FormattedArgs.Add($DoubleQuote + $ResolvedProjectPath + $DoubleQuote)

foreach ($Arg in $EditorArgs) {
    if ([string]::IsNullOrWhiteSpace($Arg)) {
        continue
    }

    if ($Arg -match '^(-[^=]+)=(.*)$') {
        $Prefix = $matches[1]
        $Value = $matches[2]

        if ([string]::IsNullOrWhiteSpace($Value)) {
            $FormattedArgs.Add($Arg)
            continue
        }

        if ($Value.StartsWith($DoubleQuote) -and $Value.EndsWith($DoubleQuote)) {
            $FormattedArgs.Add($Arg)
            continue
        }

        if ($Value -match '\s') {
            $FormattedArgs.Add($Prefix + "=" + $DoubleQuote + $Value + $DoubleQuote)
            continue
        }

        $FormattedArgs.Add($Arg)
        continue
    }

    if ($Arg.StartsWith($DoubleQuote) -and $Arg.EndsWith($DoubleQuote)) {
        $FormattedArgs.Add($Arg)
        continue
    }

    if ($Arg -match '\s') {
        $FormattedArgs.Add($DoubleQuote + $Arg + $DoubleQuote)
        continue
    }

    $FormattedArgs.Add($Arg)
}

$ArgumentString = $FormattedArgs -join " "

if ($ValidateOnly) {
    Write-Host "[UE-Cmd] ValidateOnly=TRUE" -ForegroundColor Cyan
    Write-Host "[UE-Cmd] EditorExe=$EditorExe"
    Write-Host "[UE-Cmd] ProjectPath=$ResolvedProjectPath"
    Write-Host "[UE-Cmd] ArgumentString=$ArgumentString"
    Write-Host "[UE-Cmd] ExistingCmdEditorCount=$($ExistingCmdProcesses.Count)"

    foreach ($Process in $ExistingCmdProcesses) {
        Write-Host "[UE-Cmd] Existing PID=$($Process.ProcessId)"
        Write-Host "[UE-Cmd] Existing CommandLine=$($Process.CommandLine)"
    }

    exit 0
}

if ($ExistingCmdProcesses.Count -gt 0) {
    if ($ForceCloseExisting) {
        foreach ($Process in $ExistingCmdProcesses) {
            Write-Host "[UE-Cmd] Closing UnrealEditor-Cmd PID=$($Process.ProcessId)" -ForegroundColor Yellow
            Stop-Process -Id $Process.ProcessId -Force -ErrorAction Stop
        }

        Start-Sleep -Seconds 2
    }
    else {
        throw "UnrealEditor-Cmd is already running. Close it first or use -ForceCloseExisting."
    }
}

$StdoutPath = Join-Path $env:TEMP ("ue_cmd_stdout_{0}.log" -f ([guid]::NewGuid().ToString("N")))
$StderrPath = Join-Path $env:TEMP ("ue_cmd_stderr_{0}.log" -f ([guid]::NewGuid().ToString("N")))

Write-Host "[UE-Cmd] Launching: $EditorExe $ArgumentString" -ForegroundColor Cyan

$LaunchedProcess = Start-Process `
    -FilePath $EditorExe `
    -ArgumentList $ArgumentString `
    -WorkingDirectory $ProjectRoot `
    -RedirectStandardOutput $StdoutPath `
    -RedirectStandardError $StderrPath `
    -PassThru

Start-Sleep -Seconds 1

try {
    $ActualCommandLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($LaunchedProcess.Id)").CommandLine
}
catch {
    $ActualCommandLine = "[process exited before command line probe]"
}

Write-Host "[UE-Cmd] PID=$($LaunchedProcess.Id)"
Write-Host "[UE-Cmd] ActualCommandLine=$ActualCommandLine"

$LaunchedProcess.WaitForExit()
$LaunchedProcess.Refresh()
$ExitCode = if ($null -ne $LaunchedProcess.ExitCode) { [int]$LaunchedProcess.ExitCode } else { 0 }

if (Test-Path $StdoutPath) {
    Get-Content -Encoding UTF8 $StdoutPath
}

if (Test-Path $StderrPath) {
    Get-Content -Encoding UTF8 $StderrPath
}

Write-Host "[UE-Cmd] ExitCode=$ExitCode" -ForegroundColor Cyan

if (Test-Path $StdoutPath) {
    Remove-Item -LiteralPath $StdoutPath -Force -ErrorAction SilentlyContinue
}

if (Test-Path $StderrPath) {
    Remove-Item -LiteralPath $StderrPath -Force -ErrorAction SilentlyContinue
}

exit $ExitCode
