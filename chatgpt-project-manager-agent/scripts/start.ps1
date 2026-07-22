$ErrorActionPreference = "Stop"

[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding

$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$EntryPoint = Join-Path $Root "src\chatgpt_pm_agent.py"

if (-not (Test-Path $Python)) {
    throw "Sanal ortam bulunamadı. Önce scripts\install.ps1 çalıştırın."
}

if (-not (Test-Path $EntryPoint)) {
    throw "Ana program dosyası bulunamadı: $EntryPoint"
}

& $Python $EntryPoint @args
exit $LASTEXITCODE
