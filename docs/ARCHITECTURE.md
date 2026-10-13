# ParsLinux Formatter — Sistem Mimarisi Belgesi (ARCHITECTURE.md)

Bu doküman, **ParsLinux Formatter** (`parslinux-formatter`) uygulamasının dahili yazılım mimarisini, bileşenler arası veri akışını, ayrıcalık ayrımı (privilege separation) güvenlik modelini, düşük seviyeli disk I/O operasyonlarını ve dosya sistemi biçimlendirme motorunu detaylandırmaktadır.

---

## 1. Mimari Genel Bakış

ParsLinux Formatter; Python 3, GTK 4 (Libadwaita), GTK 3, bağımsız CLI, Polkit (`pkexec`) ve Linux çekirdek blok depolama altyapılarını (`sysfs`, `udev`, `libblkid`, `dm-crypt`) harmanlayan modüler, güvenli ve yüksek performanslı bir disk biçimlendirme aracıdır.

Uygulamanın temel felsefesi:
- **En Az Ayrıcalık Prensibi (Least Privilege Model)**: Kullanıcı arayüzleri (GTK3, GTK4) ve CLI istemcisi sıradan kullanıcı ayrıcalıklarıyla (unprivileged UID) çalışır. Yalnızca diske blok düzeyinde yazım ve bölümleme yapan çekirdek biçimlendirici motoru (`USBFormatter.py`) `pkexec` vasıtasıyla yetkilendirilir.
- **Sıfır Güven Doğrulama (Zero-Trust Validation)**: Kullanıcı arayüzünden veya komut satırından gelen hiçbir hedef aygıt parametresi körü körüne güvenilmez. Aygıt kök yetkisiyle açılmadan önce 5 kademeli disk güvenliği filtresinden geçirilir; sistem diskleri (`/`, `/boot`, `/home`, swap, EFI ve LUKS kök konteynerleri) mutlak suretle kilitlenir.
- **Yüksek Hızlı Tamponlama & TRIM Desteği**: Eski 512 baytlık yavaş blok yazımı yerine 4 MiB'lık yüksek hızlı dinamik tampon akışı ve SSD/Flash bellekler için anında donanımsal temizlik sağlayan `blkdiscard` (TRIM) entegrasyonu kullanılır.
- **İşbirlikçi İptal (Cooperative Cancellation)**: Sistem kararlılığını bozan tehlikeli `pkexec kill` çağrıları yerine, stdin borusu (pipe) veya SIGTERM sinyalleri yakalanarak tamponların güvenle temizlenip (flush/sync) çıkılması sağlanır.

---

## 2. Mimari Katman Şeması

```
+-----------------------------------------------------------------------------------+
|                        KULLANICI ALANI (Sıradan Kullanıcı - UID > 1000)          |
|                                                                                   |
|  [ Modern GTK4 / Libadwaita ]       [ Klasik GTK3 / Glade ]     [ Headless CLI ] |
|     (parslinux-formatter-gtk4)        (parslinux-formatter)    (parslinux-formatter-cli)|
|                 \                             |                       /           |
|                  \                            |                      /            |
|                   +---------------------------+---------------------+             |
|                                               |                                   |
|                                    [ src/USBDeviceManager.py ]                    |
|                                (pyudev / sysfs / lsblk / uevent)                  |
+-----------------------------------------------|-----------------------------------+
                                                |
                              pkexec (Polkit)   | stdin pipe / stdout IPC
                                                v
+-----------------------------------------------------------------------------------+
|                             KÖK ALANI (Root - UID 0)                             |
|                                                                                   |
|                          [ src/USBFormatter.py ]                                  |
|                                       |                                           |
|                  +--------------------+--------------------+                      |
|                  |                                         |                      |
|        [ 5 Kademeli Güvenlik ]                   [ İşbirlikçi İptal & IPC ]       |
|   - Kök / Sistem Bölüntü Kilidi              - watch_stdin_for_cancel()           |
|   - Dahili NVMe / SATA Ayrımı                - PROGRESS|<w>|<t>|<speed>|<eta>     |
|   - Kaskad Bağlantı Kesme (umount)           - Tampon Boşaltma (fsync / sync)     |
|                  |                                         |                      |
|                  +--------------------+--------------------+                      |
|                                       |                                           |
|                                       v                                           |
|              +----------------------------------------------------+               |
|              |         Düşük Seviyeli Blok & Bölümleme İşlemleri  |               |
|              |   - MBR / GPT Bölümleme Tablosu (parted / wipefs)  |               |
|              |   - Çekirdek Tablo Senkronizasyonu (partprobe)     |               |
|              |   - Hızlı Format / 4 MiB Sıfırlama / blkdiscard    |               |
|              |   - LUKS2 Donanımsal Şifreleme (cryptsetup)        |               |
|              +----------------------------------------------------+               |
|                                       |                                           |
|         +-------------+---------------+-------------+-------------+               |
|         v             v               v             v             v               |
|     [ FAT32 ]     [ NTFS ]        [ exFAT ]     [ EXT4 ]   [ BTRFS/XFS/F2FS ]     |
|    (mkfs.fat)   (mkfs.ntfs)     (mkfs.exfat)  (mkfs.ext4)   (mkfs.btrfs/xfs/f2fs) |
+-----------------------------------------------------------------------------------+
```

---

## 3. Temel Bileşenler ve Görev Dağılımı

### 3.1. `src/USBDeviceManager.py` (Aygıt Keşfi ve Güvenlik Filtresi)
- Sistemdeki blok aygıtları `pyudev` veya `sysfs` üzerinden izler.
- USB veri yolu üzerindeki çıkarılabilir depolama birimlerini tespit eder.
- Dahili sabit diskleri, sistemin kurulu olduğu bölümleri (`/`, `/boot`, `/var`, `/home`, `swap`), EFI sistem bölümlerini ve bağlı LUKS kök kapsayıcılarını biçimlendirme listesinden eler.
- Gerçek zamanlı takıp-çıkarma (hotplug) udev sinyallerini dinleyerek arayüzü otomatik günceller.

### 3.2. `src/USBFormatter.py` (Ayrıcalıklı Çekirdek Biçimlendirici)
- Yalnızca `pkexec` aracılığıyla kök (root) kullanıcısı olarak çağrılır.
- Disk üzerindeki mevcut tüm bağlama noktalarını (`mountpoints`) ve `dm-crypt` eşleyicilerini (`dmsetup remove`) güvenle çözer.
- Eski bölümleme ve dosya sistemi imzalarını `wipefs -a` ve MBR/GPT başlık sıfırlaması ile temizler.
- Kullanıcı tercihine göre `msdos` (MBR) veya `gpt` bölümleme tablosunu `parted` ile inşa eder.
- `partprobe` ile çekirdeğin yeni bölümleme tablosunu tanımasını sağlar.
- Seçilen dosya sistemi aracını (`mkfs.fat`, `mkfs.ntfs`, `mkfs.exfat`, `mkfs.ext4`, `mkfs.btrfs`, `mkfs.xfs`, `mkfs.f2fs`) uygun etiket (`label`) ile çalıştırır.
- İsteğe bağlı LUKS2 şifreleme katmanı (`cryptsetup luksFormat` / `luksOpen` / `luksClose`) kurar.

### 3.3. `src/Utils.py` (Yardımcı Güvenlik ve İletişim Fonksiyonları)
- Tanı koyma ve hata mesajlarını stderr üzerinden iletir.
- Stdin borusunu arka plan iş parçacığıyla izleyerek (`watch_stdin_for_cancel`) kullanıcının iptal talebini anında tespit eder.
- Dosya boyutu, kalan süre (ETA) ve aktarım hızı hesaplamalarını merkezi hale getirir.

### 3.4. `src/CLI.py` (Başsız Uçbirim ve Otomasyon Motoru)
- Grafik sunucusuna (X11/Wayland) ihtiyaç duymadan terminalde çalışır.
- Renkli ANSI ilerleme çubuğu, anlık veri yazma hızı ve kalan süre gösterir.
- Otomasyon betikleri ve web panelleri için `--json` akış çıktısı üretir.
- Etkileşimli sihirbaz modu ile güvenli adım adım biçimlendirme sağlar.

### 3.5. `src/ModernWindow.py` (GTK4 & Libadwaita Kullanıcı Arayüzü)
- GNOME HIG yönergelerine tam uyumlu, açık/koyu tema destekli modern arayüz.
- `AdwClamp`, `AdwActionRow`, `AdwComboRow`, `AdwEntryRow`, `AdwPasswordEntryRow`, `AdwSwitchRow` bileşenleri.
- Biçimlendirme öncesi görsel disk bilgisi ve onay penceresi.

### 3.6. `src/MainWindow.py` (Klasik GTK3 Arayüzü)
- Geriye dönük uyumluluk ve düşük kaynak tüketimi gerektiren masaüstü ortamları için optimize edilmiş klasik GTK3/Glade arayüzü.

---

## 4. Güvenlik ve Doğrulama Modeli (5 Kademeli Koruma)

1. **Katman 1 (Arayüz Filtresi)**: `USBDeviceManager`, arayüz açıldığında sistem disklerini listeye dahil etmez.
2. **Katman 2 (Kök Doğrulama Kilidi)**: `USBFormatter.py`, kendisine iletilen aygıt adını `/proc/mounts`, `/sys/block` ve `lsblk` ile bağımsız olarak baştan doğrular. Aygıtın sistem diski veya kök bağlı bir partition içerdiği tespit edilirse işlem derhal durdurulur (`fail`).
3. **Katman 3 (Salt-Okunur Denetimi)**: Donanımsal olarak yazma korumalı (read-only) diskler tespit edilerek hatalı I/O denemeleri engellenir.
4. **Katman 4 (Güvenli Kaskad Bağlantı Çözme)**: Disk üzerindeki alt bölümler sırayla unmount edilir, açık LUKS mapper aygıtları `dmsetup remove` ile kaldırılır.
5. **Katman 5 (Donanımsal Eşzamanlama)**: Her biçimlendirme ve temizleme işleminden sonra `sync` ve `fsync` çağrılarak diskin kararlı duruma gelmesi garanti altına alınır.

---

## 5. Çıkış Kodları Standartları

| Çıkış Kodu | Anlamı |
| :---: | :--- |
| `0` | Biçimlendirme işlemi başarıyla tamamlandı. |
| `1` | Genel I/O veya biçimlendirme motoru hatası. |
| `2` | Geçersiz veya eksik parametre girişi. |
| `3` | Güvenlik ihlali (sistem diski seçilmeye çalışıldı). |
| `126` | PolicyKit yetkilendirme reddi veya iptali. |
| `130` | Kullanıcı tarafından işlem iptal edildi (SIGINT / SIGTERM). |
