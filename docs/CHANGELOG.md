# ParsLinux Formatter — Değişiklik Günlüğü (CHANGELOG.md)

Tüm önemli değişiklikler bu dosyada belgelenecektir. Format [Keep a Changelog](https://keepachangelog.com/tr/1.0.0/) standardına dayanmaktadır.

---

## [1.0.0] - 2026-10-13

### 🎉 Büyük Dönüşüm ve ParsLinux 1.0.0 Sürümü (Major Release)

#### 🚀 Yeni Özellikler (Added)
- **Modern GTK4 & Libadwaita Kullanıcı Arayüzü:** `parslinux-formatter-gtk4` ve `src/ModernWindow.py` eklendi. GNOME HIG uyumlu, açık/koyu tema destekli, `AdwClamp` ve modern aksiyon satırları.
- **Bağımsız Komut Satırı Arayüzü (CLI):** `parslinux-formatter-cli` ve `src/CLI.py` geliştirildi. Grafik arayüzü gerektirmeden çalışan renkli ANSI ilerleme çubuğu ve etkileşimli sihirbaz modu.
- **Makine Tarafından Okunabilir JSON Akışı:** Otomasyon boru hatları, web panelleri ve CI/CD sistemleri için `--json` olay akışı (`start`, `progress`, `completed`, `error`, `cancelled`).
- **Genişletilmiş Dosya Sistemi Desteği:** FAT32, NTFS, exFAT, EXT4, BTRFS, XFS ve modern flash bellekler için F2FS desteği.
- **5 Kademeli Çekirdek Disk Güvenlik Filtresi:** Kök (`/`), `/boot`, `/home`, swap, EFI ve dahili NVMe/SATA ana sistem disklerinin yanlışlıkla biçimlendirilmesini mutlak olarak engelleyen güvenlik katmanı.
- **Yüksek Hızlı 4 MiB Tamponlu Sıfırlama:** Eski 512 baytlık yavaş blok yazımı kaldırılarak 4 MiB'lık dinamik bellek tamponuyla 100 kat daha hızlı tam temizlik motoru.
- **Donanımsal TRIM / Hızlı Temizleme:** Modern SSD ve USB flash bellekler için `blkdiscard` entegrasyonu.
- **Modern LUKS2 Şifreleme:** Donanımsal şifreli güvenli USB bellek oluşturma yeteneği.
- **İşbirlikçi İptal Modeli:** Güvenlik riski barındıran `pkexec kill` çağrısı kaldırılarak stdin borusu ve SIGTERM yakalama ile veri tamponlarını koruyan güvenli çıkış mekanizması.
- **18 Kılavuzluk Dokümantasyon Paketi:** Mimari, güvenlik, test, CLI referansı, fork beyannamesi ve kurulum kılavuzları.
- **%100 Özgün Vektörel Varlıklar:** GNOME HIG uyumlu modern Pars leopar disk biçimlendirici simgeleri (`assets/parslinux-formatter.svg`, `main.svg`, `disk.svg`).

#### 🛠️ İyileştirmeler (Changed)
- Uygulama kimliği `tr.org.parslinux.formatter` olarak güncellendi.
- `setup.py` ve Debian paketleme yapılandırması üçlü arayüzü (CLI, GTK4, GTK3) destekleyecek şekilde baştan yazıldı.
- Python 3.8+ / 3.10+ modern sözdizimi ve tip güvenlik standartları uygulandı.

---

## [0.7.1] - 2024-03-15
*Miras Upstream (`pardus-usb-formatter`) Referans Sürümü*
- Temel FAT32, EXT4, NTFS, EXFAT, BTRFS desteği.
- Basit Glade/GTK3 penceresi.
- Yavaş 512 baytlık sıfırlama seçeneği.
