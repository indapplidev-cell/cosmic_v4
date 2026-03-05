[CmdletBinding()]
param(
    [switch]$SkipEnv
)

<#
EN: Build the canonical Android diagnostic package and capture env.txt only from
build_android.sh --print-env.
RU: Собирает канонический диагностический пакет Android и получает env.txt
только через build_android.sh --print-env.

Example / Пример:
powershell -ExecutionPolicy Bypass -File builds\android\tools\make_diag_pack.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Convert-ToWslPath {
    <#
    EN: Convert an absolute Windows path like D:\repo\project into /mnt/d/repo/project.
    RU: Преобразует абсолютный Windows-путь вида D:\repo\project в /mnt/d/repo/project.
    #>
    param(
        [Parameter(Mandatory = $true)]
        [string]$WindowsPath
    )

    if ($WindowsPath -notmatch '^(?<drive>[A-Za-z]):\\(?<rest>.*)$') {
        throw "Expected an absolute Windows path, got: $WindowsPath"
    }

    $drive = $Matches.drive.ToLowerInvariant()
    $rest = $Matches.rest -replace '\\', '/'
    return "/mnt/$drive/$rest"
}

function Assert-FileExists {
    <#
    EN: Stop the script with a clear message when a required file is missing.
    RU: Останавливает скрипт с понятным сообщением, если обязательный файл отсутствует.
    #>
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [string]$RelativePath
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required file is missing: $RelativePath`nResolved path: $Path"
    }
}

$root = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\..\.."))
$logDir = Join-Path $root "builds\android\logs"
$diagDir = Join-Path $logDir "diag_pack"
$zipPath = Join-Path $logDir "diag_pack.zip"

$requiredFiles = @(
    "builds\android\logs\build_android.log"
    "builds\android\logs\offline_audit_report.md"
    "builds\android\logs\offline_audit.json"
    "builds\android\ANDROID_TOOLCHAIN.lock"
    "builds\android\ANDROID_SOURCES_SDL.lock"
    "builds\android\ANDROID_SOURCES_ARCHIVES.lock"
    "builds\android\workdir\buildozer.spec"
    "builds\android\tools\toolchain_env.sh"
    "builds\android\tools\build_android.sh"
    "builds\android\tools\doctor_android.sh"
)

$missingFiles = @()

foreach ($relativePath in $requiredFiles) {
    $resolvedPath = Join-Path $root $relativePath
    if (-not (Test-Path -LiteralPath $resolvedPath -PathType Leaf)) {
        $missingFiles += $resolvedPath
    }
}

if ($missingFiles.Count -gt 0) {
    [Console]::Error.WriteLine("DIAG PACK: missing required artifacts")
    foreach ($missingFile in $missingFiles) {
        [Console]::Error.WriteLine("- $missingFile")
    }
    [Console]::Error.WriteLine("Run: bash builds/android/tools/build_android.sh android debug || true; bash builds/android/offline_audit.sh builds/android/logs/build_android.log")
    exit 2
}

if (Test-Path -LiteralPath $diagDir) {
    Remove-Item -LiteralPath $diagDir -Recurse -Force
}

if (Test-Path -LiteralPath $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}

New-Item -ItemType Directory -Path $diagDir -Force | Out-Null

foreach ($relativePath in $requiredFiles) {
    Copy-Item -LiteralPath (Join-Path $root $relativePath) -Destination $diagDir -Force
}

$envPath = Join-Path $diagDir "env.txt"
if (-not $SkipEnv) {
    $rootWsl = Convert-ToWslPath -WindowsPath $root
    $bashCommand = "cd $rootWsl`nbash builds/android/tools/build_android.sh --print-env"

    $envOutput = & wsl.exe bash -lc $bashCommand 2>&1 | ForEach-Object { "$_" }
    $exitCode = $LASTEXITCODE

    $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllLines($envPath, $envOutput, $utf8NoBom)

    if ($exitCode -ne 0) {
        $tailLines = @($envOutput | Select-Object -Last 50)
        $tailText = if ($tailLines.Count -gt 0) {
            [string]::Join([Environment]::NewLine, $tailLines)
        }
        else {
            "<no output>"
        }

        [Console]::Error.WriteLine("DIAG PACK: failed to capture env snapshot via build_android.sh --print-env")
        [Console]::Error.WriteLine($tailText)
        exit 3
    }
}

try {
    Compress-Archive -Path $diagDir -DestinationPath $zipPath -Force
}
catch {
    [Console]::Error.WriteLine("DIAG PACK: failed to create archive")
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 4
}

$zipItem = Get-Item -LiteralPath $zipPath
Write-Host "diag_pack.zip: $($zipItem.FullName)"
Write-Host "size_bytes: $($zipItem.Length)"
exit 0
