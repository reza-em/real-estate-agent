$ErrorActionPreference = "Stop"

if (-not (Test-Path ".env")) {
    throw "Create .env from .env.example and add your OPENAI_API_KEY before building."
}

$Python = ".\.venv-win\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    py -m venv .venv-win
}

& $Python -m pip install --upgrade pip
& $Python -m pip install -r requirements.txt pyinstaller
& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --name RealEstateAgent `
    --collect-all streamlit `
    --collect-all pydeck `
    --add-data "main.py;." `
    --add-data "app\ui\assets;app\ui\assets" `
    --add-data ".env;." `
    desktop_launcher.py

Write-Host "Built: dist\RealEstateAgent.exe"
