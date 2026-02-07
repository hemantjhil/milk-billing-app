$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

$icon = Join-Path $root "app.ico"
$png = Join-Path $root "milk.png"
if (-not (Test-Path $icon) -and (Test-Path $png)) {
    python -c "from PIL import Image; Image.open(r'$png').save(r'$icon', format='ICO')"
}
if (Test-Path $icon) {
    python -m PyInstaller --noconsole --onefile --name "MilkBillingSystem" --icon "$icon" app.py
} else {
    python -m PyInstaller --noconsole --onefile --name "MilkBillingSystem" app.py
}

Write-Host "EXE created at: $root\dist\MilkBillingSystem.exe"
