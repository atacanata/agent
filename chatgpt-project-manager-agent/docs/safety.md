# Güvenlik Modeli

## Yetki ayrımı

ChatGPT karar verir; yerel ajan uygular. ChatGPT'nin arayüzdeki cevabı tek başına işletim sistemi yetkisi değildir. Ajan ayrıca yerel güvenlik kurallarına uyar.

## Windows-MCP araç beyaz listesi

İlk sürümde yalnız şunlar açılır:

- Snapshot
- App
- Click
- Type
- Shortcut
- Clipboard
- Wait
- WaitFor

Windows-MCP üzerinden şu araçlar açılmaz:

- PowerShell
- Registry
- FileSystem
- Process

Kod ve test çalıştırma, hedef proje içinde ajanın kontrollü terminal ve dosya araçlarıyla yapılır.

## Açık kullanıcı onayı gereken işlemler

- commit
- push
- merge
- PR açma
- dosya/klasör silme
- mevcut kullanıcı değişikliklerini geri alma
- `git reset`, `clean`, zorla checkout
- sistem genelinde kalıcı ayar
- kimlik bilgisi veya gizli dosya paylaşımı

## Sohbet doğrulaması

Proje raporu yanlış ChatGPT sohbetine gönderilmemelidir. Sohbet başlığı tek başına yeterli değilse proje adı, proje yolu veya önceki talimattan tanıdık bir metin de doğrulanır.

## Kanıt bütünlüğü

- Test komutu ve çıkış kodu birlikte kaydedilir.
- Başarısız test saklanmaz veya başarılıya çevrilmez.
- Diff aşırı uzunsa kesildiği açıkça belirtilir.
- Görsel değerlendirme yapılmadıysa doğrulanmış gibi yazılmaz.
- ChatGPT'nin yarım veya hata vermiş cevabı uygulanmaz.

## Sonsuz döngü

`project.toml` içindeki `max_cycles` üst sınırdır. Sınır aşıldığında ajan yeni tur başlatmadan kullanıcıya durum raporu verir.
