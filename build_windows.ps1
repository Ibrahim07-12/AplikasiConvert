$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Error "Virtual environment belum ada. Jalankan: python -m venv .venv"
}

& ".venv\Scripts\python.exe" -m pip install -r requirements-desktop.txt
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& ".venv\Scripts\python.exe" -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --name Flux `
    --icon "frontend\icons\faviconapp.ico" `
    --add-data "app;app" `
    --add-data "frontend;frontend" `
    desktop_app.py

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Portable app selesai: dist\Flux\Flux.exe"
