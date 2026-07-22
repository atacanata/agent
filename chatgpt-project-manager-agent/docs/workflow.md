# İş Akışı

## 1. ChatGPT talimatı

Ajan doğru ChatGPT sohbetini Windows-MCP ile doğrular ve yalnız son tamamlanmış asistan mesajını alır. Mesaj tamamlanmadan işe başlamaz.

## 2. Tur başlatma

ChatGPT talimatı UTF-8 metin dosyasına kaydedilir:

```powershell
.\scripts\start.ps1 begin --config .\project.toml --instruction-file .\instruction.txt
```

## 3. Uygulama

Ajan proje yolunu, dalı ve mevcut değişiklikleri kontrol eder. ChatGPT'nin izin verdiği kapsam dışında değişiklik yapmaz.

Windows-MCP bu aşamada proje dosyalarını değiştiren ana araç değildir. Kod ve test işlemleri ajanın normal proje araçlarıyla yürütülür.

## 4. Kanıt toplama

```powershell
.\scripts\start.ps1 collect --config .\project.toml
```

Toplanan kanıt:

- dal ve HEAD,
- `git status --short`,
- `git diff --binary`,
- değişen dosyalar,
- yapılandırılmış test komutları,
- gerçek çıkış kodları ve çıktılar.

## 5. Hakem raporu

```powershell
.\scripts\start.ps1 report --config .\project.toml --output .\state\chatgpt-report.md
```

Ajan raporu doğru ChatGPT sohbetine gönderir. ZIP veya GitHub bağlantısı gerekiyorsa rapora ekler; yüklenmeyen dosyayı yüklenmiş gibi bildirmez.

## 6. Cevabı bekleme

Cevap bitişi üç sinyalle doğrulanır:

- son mesaj sabit,
- üretimi durdur düğmesi yok,
- mesaj kutusu tekrar hazır.

## 7. Kararı kaydetme

ChatGPT cevabı dosyaya alınır:

```powershell
.\scripts\start.ps1 record-response --config .\project.toml --response-file .\chatgpt-response.txt
```

ChatGPT cevabının ilk anlamlı satırı karar olmalıdır. Açık karar yoksa sistem `UNCLEAR` döndürür ve ajan tahmin yapmaz.

## 8. Döngü

- `CONTINUE`, `REVISE`, `INSPECT`, `APPROVED`: yeni tur
- `ASK_USER`: kullanıcı kararı beklenir
- `HOLD`: işlem durur
- `BLOCKED`: engel raporlanır
- `DONE`: görev biter
