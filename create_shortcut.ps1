$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$exe = Join-Path $root "dist\MilkBillingSystem.exe"
$bat = Join-Path $root "run_app.bat"
$target = if (Test-Path $exe) { $exe } else { $bat }
$shortcutPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "Milk Billing System.lnk"

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $target
$shortcut.WorkingDirectory = $root
$icon = Join-Path $root "app.ico"
$png = Join-Path $root "milk.png"
if (Test-Path $icon) {
    $shortcut.IconLocation = $icon
} elseif (Test-Path $png) {
    $shortcut.IconLocation = $png
} else {
    $shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll, 1"
}
$shortcut.Description = "Milk Billing System"
$shortcut.Save()

Write-Host "Shortcut created at: $shortcutPath"
