# ParsLinux Formatter — Claude & AI Ajan Geliştirici Kılavuzu (CLAUDE.md)

Bu kılavuz; Claude, Gemini ve diğer otonom AI kodlama asistanlarının **ParsLinux Formatter** (`parslinux-formatter`) kod tabanında güvenli, tutarlı ve etkili çalışabilmesi için özel olarak hazırlanmıştır.

---

## 1. Kod Tabanı Genel Özeti

ParsLinux Formatter, Python 3, GTK 4 / Libadwaita, GTK 3 (PyGObject) ve saf Python CLI motoru ile geliştirilmiş, Polkit ve Udev entegrasyonuna sahip bir disk biçimlendirme sistem aracıdır.

- **Ana Kaynak Kod**: `/src/`
  - `Main.py`: Klasik GTK3 uygulama döngüsü (`Gtk.Application`).
  - `MainWindow.py`: Klasik GTK3 grafik arayüz denetleyicisi.
  - `ModernWindow.py`: Modern GTK4 / Libadwaita arayüz denetleyicisi (`parslinux-formatter-gtk4`).
  - `CLI.py`: Başsız (headless) komut satırı arayüzü (`parslinux-formatter-cli`).
  - `USBDeviceManager.py`: Udev dinleme ve 5 kademeli kritik disk güvenlik filtreleri.
  - `USBFormatter.py`: Düşük seviyeli bölümleme, sıfırlama ve dosya sistemi biçimlendirme motoru (Root - `pkexec`).
  - `Utils.py`: Güvenli loglama, cooperative iptal (`watch_stdin_for_cancel`), formatlama yardımcıları.
  - `__version__`: Merkezi sürüm dosyası (`1.0.0`).
- **Arayüz Tanımları**: `/ui/MainWindow.glade` (GTK3 Glade XML formatında).
- **Varlıklar**: `/assets/` (SVG simgeler ve logolar).
- **Paketleme**: `/setup.py`, `/debian/` ve `/tr.org.parslinux.Formatter.json`.

---

## 2. Temel Geliştirme ve Çalıştırma Komutları

```bash
# Bağımsız CLI modunu çalıştırma:
python3 src/CLI.py --list
python3 src/CLI.py --help

# GTK4 Modern Arayüzü çalıştırma:
python3 src/ModernWindow.py

# GTK3 Klasik Arayüzü çalıştırma:
python3 src/Main.py

# Birim testleri çalıştırma:
python3 -m unittest discover tests/ -v

# Çevirileri güncelleme:
./update-translations.sh
```

---

## 3. Kod Düzenleme ve Güvenlik Kuralları

1. **Sistem Diski Güvenliği:** `USBDeviceManager.py` ve `USBFormatter.py` içindeki disk doğrulama filtrelerini asla gevşetmeyin veya atlatmayın. Kök (`/`), `/boot`, `/home`, swap, EFI ve dahili NVMe/SATA diskler asla biçimlendirilemez.
2. **İşbirlikçi İptal:** Asla `pkexec kill` kullanmayın. İptal mekanizması stdin borusunun kapatılması veya SIGTERM sinyali ile kooperatif olarak çalışmalıdır.
3. **Tamponlama:** Disk sıfırlama döngülerinde 512 baytlık küçük yazımlar yerine 4 MiB dinamik tampon boyutunu koruyun.
4. **Marka Bağımsızlığı:** Eski projelere ait isim veya logoları geri getirmeyin; `ParsLinux` kimliğini koruyun.
