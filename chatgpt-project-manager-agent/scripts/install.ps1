$ErrorActionPreference = "Stop"

[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python bulunamadı. Python 3.11 veya daha yeni bir sürüm kurun."
}

if (-not (Test-Path ".venv")) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        throw "Python sanal ortamı oluşturulamadı. Çıkış kodu: $LASTEXITCODE"
    }
}

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Sanal ortam Python çalıştırıcısı bulunamadı: $Python"
}

& $Python -c "import sys; assert sys.version_info >= (3, 11), sys.version"
if ($LASTEXITCODE -ne 0) {
    throw "Python 3.11 veya daha yeni bir sürüm gerekli."
}

& $Python -m compileall -q src tests
if ($LASTEXITCODE -ne 0) {
    throw "Kaynak kod derleme kontrolü başarısız oldu. Çıkış kodu: $LASTEXITCODE"
}

$env:PYTHONPATH = Join-Path $Root "src"
& $Python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) {
    throw "Birim testleri başarısız oldu. Çıkış kodu: $LASTEXITCODE"
}

Write-Host "Kurulum ve testler başarıyla tamamlandı."
Write-Host "Bu kurulum internetten Python paketi indirmez."
Write-Host "project.toml zaten varsa yeniden kopyalamanız gerekmez."
