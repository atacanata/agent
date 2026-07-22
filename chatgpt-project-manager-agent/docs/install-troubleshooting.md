# Kurulum Sorunları

## PowerShell betikleri engelleniyor

Yalnız açık PowerShell penceresi için:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
```

## Python paket indirme zaman aşımı

Güncel kurulum internetten Python paketi indirmez. Eski sürümde `pip` veya `pytest` indirme hatası görüldüyse depoyu güncelleyin:

```powershell
git pull
.\scripts\install.ps1
```

Mevcut `.venv` klasörünü silmek gerekmez. Sanal ortam bozulmuşsa yalnız proje içindeki `.venv` klasörü silinip kurulum yeniden çalıştırılabilir.

## Kurulum yanlışlıkla başarılı yazdı

Eski betik, dış programların başarısız çıkış kodunu kontrol etmiyordu. Güncel betik her Python ve test adımından sonra çıkış kodunu denetler; başarısızlık varsa başarı mesajı yazmaz.
