$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python bulunamadı. Python 3.11 veya daha yeni bir sürüm kurun."
}

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -e ".[dev]"
& ".\.venv\Scripts\python.exe" -m pytest -q

Write-Host "Kurulum ve testler tamamlandı."
Write-Host "Sonraki adım: config\project.example.toml dosyasını project.toml olarak kopyalayın."
