# SIP Compass updater launcher for Windows.
# Finds Python 3.10+ and runs update_data.py, writing data.js next to SIP-Compass.html.
param([switch]$Quiet)
$ErrorActionPreference = 'Stop'
$appFolder = Split-Path $PSScriptRoot -Parent

# The folder must be writable (not inside a zip, OneDrive "online-only" placeholder, or Program Files).
$probe = Join-Path $appFolder ('.sip-write-check-' + [Guid]::NewGuid().ToString('N'))
try { [IO.File]::WriteAllText($probe, 'ok'); Remove-Item -LiteralPath $probe -Force }
catch {
    Write-Host 'This folder cannot be written to:'
    Write-Host "  $appFolder"
    Write-Host 'Extract or copy the whole SIP Compass folder somewhere normal, such as Documents, and run this again.'
    exit 1
}

$candidates = @(
    "$env:USERPROFILE\anaconda3\python.exe",
    "$env:USERPROFILE\miniconda3\python.exe",
    "$env:LOCALAPPDATA\anaconda3\python.exe",
    "$env:ProgramData\anaconda3\python.exe"
)
foreach ($name in @('python', 'python3', 'py')) {
    $found = Get-Command $name -ErrorAction SilentlyContinue
    if ($found -and $found.Source -notlike '*\WindowsApps\*') { $candidates += $found.Source }
}
$uvRoot = "$env:APPDATA\uv\python"
if (Test-Path -LiteralPath $uvRoot) {
    $candidates += Get-ChildItem -LiteralPath $uvRoot -Filter 'cpython-3*' -Directory | ForEach-Object { Join-Path $_.FullName 'python.exe' }
}
$chosen = $null; $pythonArgs = @()
foreach ($candidate in ($candidates | Select-Object -Unique)) {
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { continue }
    $probeArgs = @()
    if ([IO.Path]::GetFileName($candidate) -eq 'py.exe') { $probeArgs += '-3' }
    try {
        & $candidate @probeArgs -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>$null
        if ($LASTEXITCODE -eq 0) { $chosen = $candidate; $pythonArgs = $probeArgs; break }
    } catch { continue }
}
if (-not $chosen) {
    Write-Host 'Python 3.10 or later was not found.'
    Write-Host 'Install it from https://www.python.org/downloads/ (tick "Add python.exe to PATH"), then run this again.'
    Write-Host 'SIP Compass itself still works without this step; the updater only adds local data.'
    exit 1
}
Write-Host 'Updating public fund data. Your saved goals and holdings are not read.'
Write-Host ('Python: ' + $chosen)
Write-Host ('Folder: ' + $appFolder)
& $chosen @pythonArgs (Join-Path $PSScriptRoot 'update_data.py') --output $appFolder
$result = $LASTEXITCODE
if ($result -eq 0) { Write-Host 'Update complete. Reload SIP-Compass.html in your browser.' }
elseif ($result -eq 2) { Write-Host 'Update finished with some sources unavailable. Usable data was kept; see update-report.json.' }
else { Write-Host 'Update failed. Your previous data.js was kept. See the message above.' }
exit $result
