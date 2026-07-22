$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Sanal ortam bulunamadı. Önce scripts\install.ps1 çalıştırın."
}

& $Python -m chatgpt_pm_agent @args
exit $LASTEXITCODE
