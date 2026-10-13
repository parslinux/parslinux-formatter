# ParsLinux Formatter — Çatallama Beyannamesi (FORK.md)

Bu belge; **ParsLinux Formatter** (`parslinux-formatter`) projesinin kökenini, çatallanma (fork) gerekçelerini, gerçekleştirilen mimari dönüşümleri ve açık kaynak lisans uyum beyanını detaylandırmaktadır.

---

## 📌 1. Projenin Kökeni (Upstream Origin)

**ParsLinux Formatter**, açık kaynaklı GNU/Linux ekosistemindeki Pardus USB Formatter projesinden türetilmiş ve bağımsız ParsLinux ekosistemine uyarlanmıştır.

* **Orijinal Proje:** `pardus-usb-formatter`
* **Orijinal Lisans:** GNU General Public License v3.0 (GPL-3.0)
* **Mevcut Lisans:** GNU General Public License v3.0 (GPL-3.0-or-later)
* **Geliştirici & Bakım:** Pars Linux Geliştirici Topluluğu ([dev@pars.org.tr](mailto:dev@pars.org.tr))
* **Kaynak Kod Deposu:** [https://github.com/parslinux/parslinux-formatter](https://github.com/parslinux/parslinux-formatter)

GPL-3.0 lisansının getirdiği özgür yazılım etiği ve yasal haklar çerçevesinde; orijinal projenin geliştiricilerine teşekkür eder, kaynak kodun özgürce değiştirilme ve geliştirilme hakkını sürdürürüz.

---

## 🎯 2. Neden Fork Edildi? (Motivasyon ve Amaçlar)

Orijinal yazılım temel düzeyde USB bellekleri sınırlı dosya sistemleriyle biçimlendirebilen bir GTK3 uygulamasıydı. Ancak modern Linux ekosistemi ve ParsLinux masaüstü standartları doğrultusunda şu kritik eksiklikler ve teknik borçlar mevcuttu:

1. **Yetersiz Disk Güvenlik Doğrulaması:**
   * Disk seçimi arayüz seviyesinde yapılıyor, kök yetkili `USBFormatter.py` arka plan motorunda sistem disklerinin (kök `/`, `/boot`, `/home`, swap, dahili NVMe/SATA diskler) korunmasına dair katı bir çekirdek doğrulama mekanizması bulunmuyordu.
   * Hatalı argüman iletilmesi durumunda kullanıcının ana işletim sistemi diskinin silinme riski mevcuttu.

2. **Kritik Süreç İptal Sorunu (`pkexec kill`):**
   * Kullanıcı işlemi iptal etmek istediğinde doğrudan `pkexec kill -SIGTERM <pid>` çağrılıyordu. Bu yöntem hem PolicyKit politikalarında risk teşkil ediyor hem de diski yarım yazılmış, tamponları boşaltılmamış kararsız bir durumda bırakabiliyordu.

3. **Yavaş Sıfırlama Darboğazı:**
   * Tam sıfırlama (`--fill`) modunda veriler 512 baytlık bloklar halinde yazılıyor ve her 10 MB'da bir `fsync` yapılıyordu. Bu durum büyük kapasiteli USB disklerde saatler süren yavaşlamaya neden oluyordu.
   * Flash bellekler ve SSD'ler için modern donanımsal temizlik (`blkdiscard` / TRIM) desteği bulunmuyordu.

4. **Sınırlı Dosya Sistemi ve Bölümleme Desteği:**
   * Modern F2FS (Flash-Friendly File System), XFS ve gelişmiş BTRFS yapılandırmaları desteklenmiyordu.
   * Bölümleme tablosu (MBR vs GPT) kullanıcıya esnek biçimde sunulmuyordu.

5. **Uçbirim (CLI) ve Başsız (Headless) Sistem Desteğinin Bulunmaması:**
   * Yalnızca masaüstü GTK ortamına bağımlıydı. Sunucularda, kurtarma oturumlarında veya CI/CD otomasyonlarında kullanılabilecek bağımsız bir CLI motoru yoktu.

6. **Eski Arayüz Mimarisi ve Marka Bağımlılığı:**
   * Modern GNOME / Libadwaita (GTK4) arayüzü bulunmuyordu.
   * Varlıklar ve metinler eski dağıtımın kimliğini taşıyordu.

---

## 🚀 3. Gerçekleştirilen Başlıca Değişimler ve İnovasyonlar

| Özellik / Bileşen | Orijinal Upstream Hali | ParsLinux Formatter (v1.0.0+) |
| :--- | :--- | :--- |
| **Kullanıcı Arayüzü** | Yalnızca GTK3 | **GTK3 + Modern GTK4 / Libadwaita + Bağımsız CLI** |
| **Komut Satırı (CLI)** | Yok | **`parslinux-formatter-cli` (ANSI & JSON akışlı, sihirbazlı)** |
| **Desteklenen Dosya Sistemleri** | FAT32, EXT4, NTFS, EXFAT, BTRFS | **FAT32, NTFS, exFAT, EXT4, BTRFS, XFS, F2FS** |
| **Bölümleme Tablosu** | Temel msdos/gpt | **Otomatik / Kullanıcı Seçimli MBR (DOS) & GPT** |
| **Disk Güvenlik Motoru** | Sadece arayüz listesi | **5 Kademeli Çekirdek Güvenlik Filtresi (Kök, NVMe, Swap Kilidi)** |
| **Temizleme & Sıfırlama** | 512b blok (Çok Yavaş) | **4 MiB Yüksek Hızlı Akış + `blkdiscard` (Hızlı Donanımsal TRIM)** |
| **İşbirlikçi İptal** | `pkexec kill` (Riskli) | **Güvenli Stdin Pipe & Sinyal Yakalama (Tampon Güvenliği)** |
| **Şifreleme Desteği** | Temel LUKS1 | **Modern LUKS2 Donanımsal Şifreleme Desteği** |
| **Görsel Varlıklar** | Eski logolar | **%100 Telifsiz, GNOME HIG uyumlu özgün vektörler (SVG)** |
| **Paketleme & Dağıtım** | Yalnızca `.deb` | **Debian/Apt + Flatpak Manifestosu + AppStream Metainfo** |

---

## 📜 4. Lisans ve Açık Kaynak Taahhüdü

Bu proje, GNU Genel Kamu Lisansı Sürüm 3 (GPL-3.0-or-later) şartları altında lisanslanmıştır. Kaynak kodları tamamen açıktır, kopyalanabilir, değiştirilebilir ve yeniden dağıtılabilir.

* **Hata Takibi & Katkı:** [https://github.com/parslinux/parslinux-formatter/issues](https://github.com/parslinux/parslinux-formatter/issues)
* **İletişim:** [dev@pars.org.tr](mailto:dev@pars.org.tr)
