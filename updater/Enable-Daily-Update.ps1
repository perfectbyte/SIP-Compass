# Optional. Right-click > Run with PowerShell to refresh public fund data every night at 11:30 PM.
# Runs as your user while you are logged in; stores no password. Run a manual update first.
$ErrorActionPreference = 'Stop'
$runner = Join-Path $PSScriptRoot 'Run-Updater.ps1'
if (-not (Test-Path -LiteralPath $runner)) { throw 'Run-Updater.ps1 is missing.' }
$taskName = 'SIP Compass - Daily Public Data'
$arguments = '-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "' + $runner + '" -Quiet'
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $arguments -WorkingDirectory $PSScriptRoot
$trigger = New-ScheduledTaskTrigger -Daily -At '23:30'
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 2)
$principal = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description 'Refresh public SIP Compass fund data.' -Force | Out-Null
Write-Host 'Daily update enabled for 11:30 PM. Missed runs start when the PC is next on.'
Write-Host "To remove it: Unregister-ScheduledTask -TaskName '$taskName'"
