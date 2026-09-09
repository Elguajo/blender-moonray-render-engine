param(
    [string]$DistroName = "MoonRay-Rocky9",
    [string]$DownloadDir = "$env:USERPROFILE\Downloads\MoonRayHostBootstrap",
    # WSL stores the distro ext4 VHDX here. Phase 03 builds MoonRay, so this
    # defaults to a large data volume instead of %LOCALAPPDATA% on C:, and it
    # sits beside the repository rather than inside it so that archiving or
    # copying the project never drags a multi-hundred-GB VHDX along.
    # The filesystem inside the VHDX is still Linux-native ext4; this is NOT a
    # /mnt/c build tree and does not violate the Phase 02 filesystem rule.
    [string]$DistroLocation = "D:\01_DEV\moonray-blender-wsl\MoonRay-Rocky9"
)

$ErrorActionPreference = "Stop"

# wsl.exe emits UTF-16LE by default, which corrupts every Tee-Object evidence
# capture below. WSL_UTF8 makes it emit UTF-8 instead.
$env:WSL_UTF8 = "1"
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }

function Write-Step($msg) {
    Write-Host ""
    Write-Host "==> $msg" -ForegroundColor Cyan
}

function Invoke-Wsl {
    # PowerShell 5.1 wraps every native-command stderr line in an ErrorRecord.
    # With $ErrorActionPreference = "Stop" that turns wsl.exe's harmless
    # first-boot chatter (e.g. "Failed to get unit file state for
    # cloud-init.service") into a terminating error even on exit code 0.
    # Run wsl.exe with the preference relaxed and judge it by $LASTEXITCODE.
    param([Parameter(Mandatory = $true)][string[]]$WslArgs)
    $previous = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = & wsl.exe @WslArgs 2>&1 | Out-String
        $script:WslExitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previous
    }
    return $output
}

function Test-Administrator {
    $currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentIdentity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

$IsAdmin = Test-Administrator

# Enabling or updating WSL needs elevation. Installing a distro image into an
# already-healthy WSL2 does not. Only demand Administrator when we actually
# have to touch the WSL platform itself.
$WslHealthy = $false
try {
    $wslVersionText = Invoke-Wsl @('--version')
    if ($script:WslExitCode -eq 0 -and $wslVersionText.Trim()) { $WslHealthy = $true }
} catch {
    $WslHealthy = $false
}

if (-not $WslHealthy -and -not $IsAdmin) {
    throw "WSL is not installed or not reporting a version. Re-run this script as Administrator so WSL can be installed/updated."
}

$EvidenceDir = Join-Path $PSScriptRoot "..\..\docs\evidence\phase02"
New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null
New-Item -ItemType Directory -Force -Path $DownloadDir | Out-Null

$log = Join-Path $EvidenceDir "windows-host.txt"
"Phase 02 Windows host evidence - $(Get-Date -Format o)" | Out-File $log -Encoding utf8
"Elevated: $IsAdmin" | Out-File $log -Encoding utf8 -Append

Write-Step "Capture Windows / hardware inventory"
Get-ComputerInfo |
    Select-Object WindowsProductName, WindowsVersion, OsBuildNumber, OsArchitecture, CsSystemType, CsProcessors, CsTotalPhysicalMemory |
    Format-List | Out-String | Tee-Object -FilePath $log -Append | Write-Host

"`n--- GPU (Windows) ---" | Tee-Object -FilePath $log -Append | Write-Host
if (Get-Command nvidia-smi.exe -ErrorAction SilentlyContinue) {
    nvidia-smi.exe | Out-String | Tee-Object -FilePath $log -Append | Write-Host
} else {
    "nvidia-smi.exe not found in Windows PATH; GPU evidence will be re-checked inside WSL." |
        Tee-Object -FilePath $log -Append | Write-Host
}

Write-Step "Ensure current WSL"
if (-not $WslHealthy) {
    Write-Host "WSL is not available yet. Installing WSL without a default Ubuntu distro..."
    Invoke-Wsl @('--install','--no-distribution') | Write-Host
    Write-Warning "WSL was installed. If Windows requests a restart, reboot and re-run this script."
}

Invoke-Wsl @('--version') | Tee-Object -FilePath $log -Append | Write-Host

if ($IsAdmin) {
    Invoke-Wsl @('--update') | Write-Host
    Invoke-Wsl @('--set-default-version','2') | Write-Host
} else {
    "Skipped 'wsl --update' / '--set-default-version' (not elevated); WSL already reports a healthy version." |
        Tee-Object -FilePath $log -Append | Write-Host
}

"`n--- WSL status before Rocky install ---" | Tee-Object -FilePath $log -Append | Write-Host
Invoke-Wsl @('--status') | Tee-Object -FilePath $log -Append | Write-Host
Invoke-Wsl @('--list','--verbose') | Tee-Object -FilePath $log -Append | Write-Host

Write-Step "Download pinned Rocky Linux 9.8 WSL image and checksum"
$base = "https://download.rockylinux.org/pub/rocky/9.8/images/x86_64"
$imageName = "Rocky-9-WSL-Base-9.8-20260525.0.x86_64.wsl"
$checksumName = "$imageName.CHECKSUM"
$imagePath = Join-Path $DownloadDir $imageName
$checksumPath = Join-Path $DownloadDir $checksumName

$ProgressPreference = "SilentlyContinue"
if (-not (Test-Path $imagePath)) {
    Invoke-WebRequest "$base/$imageName" -OutFile $imagePath -UseBasicParsing
}
Invoke-WebRequest "$base/$checksumName" -OutFile $checksumPath -UseBasicParsing

$checksumText = Get-Content $checksumPath -Raw
$expected = [regex]::Match($checksumText, '(?i)\b[a-f0-9]{64}\b').Value.ToLowerInvariant()
if (-not $expected) {
    throw "Could not parse Rocky SHA256 checksum from $checksumPath"
}

$actual = (Get-FileHash -Algorithm SHA256 $imagePath).Hash.ToLowerInvariant()
"Rocky image: $imageName" | Tee-Object -FilePath $log -Append | Write-Host
"Rocky image SHA256 expected: $expected" | Tee-Object -FilePath $log -Append | Write-Host
"Rocky image SHA256 actual:   $actual" | Tee-Object -FilePath $log -Append | Write-Host

if ($actual -ne $expected) {
    throw "Rocky WSL image SHA256 mismatch. Do not install it."
}

Write-Step "Install isolated Rocky Linux WSL distro"
$existing = (Invoke-Wsl @('--list','--quiet')) -split "`r?`n" | ForEach-Object { $_.Trim() }
if ($existing -contains $DistroName) {
    Write-Host "$DistroName already exists; skipping installation."
} else {
    New-Item -ItemType Directory -Force -Path $DistroLocation | Out-Null
    "Distro VHDX location: $DistroLocation" | Tee-Object -FilePath $log -Append | Write-Host
    Invoke-Wsl @('--install','--from-file',$imagePath,'--name',$DistroName,'--location',$DistroLocation) |
        Tee-Object -FilePath $log -Append | Write-Host
    if ($script:WslExitCode -ne 0) {
        throw "wsl --install --from-file failed with exit code $script:WslExitCode"
    }
}

Write-Step "Verify distro is WSL2"
Invoke-Wsl @('--list','--verbose') | Tee-Object -FilePath $log -Append | Write-Host

$line = (Invoke-Wsl @('--list','--verbose')) -split "`r?`n" | Where-Object { $_ -match [regex]::Escape($DistroName) }
if (-not $line) {
    throw "$DistroName was not found after installation."
}
if ($line -notmatch '\s2\s*$') {
    Write-Host "Converting $DistroName to WSL2..."
    Invoke-Wsl @('--set-version',$DistroName,'2') | Write-Host
}

Write-Step "Record distro VHDX location"
$basePathKey = Get-ChildItem "HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss" -ErrorAction SilentlyContinue |
    Where-Object { (Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue).DistributionName -eq $DistroName } |
    Select-Object -First 1
if ($basePathKey) {
    $actualBase = (Get-ItemProperty $basePathKey.PSPath).BasePath -replace '^\\\\\?\\', ''
    "Distro VHDX location (actual): $actualBase" | Tee-Object -FilePath $log -Append | Write-Host
    if ($actualBase -ne $DistroLocation) {
        "NOTE: distro is not at the requested location '$DistroLocation'. Move it with: wsl --manage $DistroName --move `"$DistroLocation`"" |
            Tee-Object -FilePath $log -Append | Write-Host
    }
} else {
    "WARN: could not resolve the VHDX location for $DistroName from the registry." |
        Tee-Object -FilePath $log -Append | Write-Host
}

Write-Step "Capture Rocky basics"
$rockyProbe = 'cat /etc/os-release; echo; uname -a; echo; echo "WSL_INTEROP=$WSL_INTEROP"; echo "DISPLAY=$DISPLAY"; echo "WAYLAND_DISPLAY=$WAYLAND_DISPLAY"'
Invoke-Wsl @('-d', $DistroName, '--', 'bash', '-lc', $rockyProbe) |
    Tee-Object -FilePath $log -Append | Write-Host
if ($script:WslExitCode -ne 0) {
    throw "Rocky probe inside $DistroName failed with exit code $script:WslExitCode"
}

Write-Step "Phase 02 Windows-side bootstrap complete"
Write-Host "Evidence: $log"
Write-Host ""
Write-Host "Next: open $DistroName and run scripts/linux/phase02_setup_host.sh from this project."
