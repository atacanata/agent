# ChatGPT Project Manager Agent

Windows-MCP kullanan yerel bir modelin, ChatGPT'yi proje yöneticisi ve başhakem olarak kullanması için hazırlanmış çalışma iskeleti.

Bu projede yalnız iki karar tarafı vardır:

- **ChatGPT:** hedefi, kapsamı ve kabul ölçütlerini belirler; kanıtları denetler; devam, düzeltme, bekleme veya tamamlanma kararı verir.
- **Yerel ajan:** ChatGPT'nin talimatını uygular; test ve kanıt toplar; sonucu aynı ChatGPT sohbetine gönderir; yeni kararı uygular.

Claude veya üçüncü bir uygulayıcı ajan yoktur.

## Akış

```text
ChatGPT talimatı
    ↓
Yerel ajan + proje araçları
    ↓
Kod/değişiklik + test + gerçek kanıt
    ↓
Windows-MCP ile ChatGPT raporu
    ↓
ChatGPT hakem kararı
    ↺
```

Windows-MCP yalnız ChatGPT arayüzü ve gerekli Windows uygulamaları için kullanılır. Kod ve dosya işlemlerinde ajanın normal proje araçları tercih edilir.

## Güvenli varsayılanlar

- ChatGPT'nin cevabı tamamlanmadan uygulanmaz.
- Doğru sohbet doğrulanmadan mesaj gönderilmez.
- Kullanıcı onayı olmadan `commit`, `push`, `merge`, dosya silme veya mevcut değişiklikleri geri alma yapılmaz.
- Başarısız test başarılı gibi raporlanmaz.
- Görsel olarak doğrulanamayan sonuç açıkça belirtilir.
- Windows-MCP yerel `stdio` ile ve araç beyaz listesiyle çalıştırılır.

## Kurulum

Gereksinimler:

- Windows 11
- Python 3.11+
- Git
- OpenCode veya MCP destekleyen eşdeğer yerel ajan istemcisi
- Windows-MCP
- Yerel model sunucusu

PowerShell betikleri bu oturumda engelliyse önce yalnız mevcut pencere için izin ver:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
```

Ardından:

```powershell
cd chatgpt-project-manager-agent
.\scripts\install.ps1
Copy-Item .\config\project.example.toml .\project.toml
```

Kurulum yalnız Python sanal ortamını oluşturur ve standart kütüphane testlerini çalıştırır. İnternetten `pip`, `pytest` veya başka paket indirmez.

`project.toml` zaten varsa tekrar kopyalama. İçindeki proje yolunu ve ChatGPT sohbet başlığını düzenle.

## Windows-MCP

Güvenli başlangıç:

```powershell
uvx windows-mcp serve --transport stdio --tools "Snapshot,App,Click,Type,Shortcut,Clipboard,Wait,WaitFor"
```

`PowerShell`, `Registry`, `FileSystem` ve `Process` Windows-MCP üzerinden açılmaz. Yerel ajanın proje içi terminal ve dosya araçları ayrı yetki katmanıdır.

OpenCode örneği `config/opencode.example.json` içindedir.

## Kullanım

```powershell
.\scripts\start.ps1 init --config .\project.toml
.\scripts\start.ps1 begin --config .\project.toml --instruction-file .\instruction.txt
.\scripts\start.ps1 collect --config .\project.toml
.\scripts\start.ps1 report --config .\project.toml --output .\state\chatgpt-report.md
.\scripts\start.ps1 record-response --config .\project.toml --response-file .\chatgpt-response.txt
```

Bu komutlar deterministic yardımcı katmandır. ChatGPT penceresini bulma, doğru sohbeti doğrulama, mesajı gönderme ve cevabın bitişini bekleme davranışı `AGENTS.md` içindeki ajana aittir.

## İlk canlı test

Gerçek proje yerine geçici bir Git deposunda şu akışı sınayın:

1. ChatGPT'den yalnız bir metin dosyası oluşturma talimatı alın.
2. Yerel ajan değişikliği yapsın.
3. Test ve `git diff` kanıtı toplansın.
4. Rapor ChatGPT'ye gönderilsin.
5. ChatGPT düzeltme isterse ikinci tur çalışsın.
6. ChatGPT `DONE` dediğinde durulsun.

Bu sürüm bir MVP güvenlik ve kanıt iskeletidir. ChatGPT arayüzündeki öğe adları uygulama ve dil sürümüne göre değişebileceği için Windows-MCP etkileşimleri önce deneme sohbetinde doğrulanmalıdır.
