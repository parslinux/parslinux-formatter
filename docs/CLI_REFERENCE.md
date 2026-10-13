# ParsLinux Formatter — Uçbirim (CLI) Referans Kılavuzu (CLI_REFERENCE.md)

Bu belge, **ParsLinux Formatter** uygulamasının başsız (headless) komut satırı aracı olan `parslinux-formatter-cli` için ayrıntılı komut yapısını, parametreleri, JSON olay akışını ve entegrasyon örneklerini açıklamaktadır.

---

## 📌 1. Komut Satırı Kullanımı (Syntax)

```bash
parslinux-formatter-cli [SEÇENEKLER]
```

---

## ⚙️ 2. Argümanlar ve Parametreler

| Parametre | Kısa Yol | Açıklama | Varsayılan |
| :--- | :---: | :--- | :---: |
| `--list` | `-L` | Sistemdeki çıkarılabilir USB aygıtlarını listeler ve çıkar. | - |
| `--device <AYGIT>` | `-d` | Biçimlendirilecek hedef blok aygıtı (örn: `sdb` veya `/dev/sdb`). | Zorunlu (Format için) |
| `--type <FS>` | `-t` | Dosya sistemi türü: `FAT32`, `NTFS`, `EXFAT`, `EXT4`, `BTRFS`, `XFS`, `F2FS`. | `FAT32` |
| `--label <ETİKET>` | `-l` | Yeni birimin etiket adı (Örn: `PARSUSB`, `DEPO`). | `""` |
| `--gpt` | `-g` | MBR (msdos) yerine modern GPT bölümleme tablosu kullanır. | `False` |
| `--quick` | `-q` | Hızlı biçimlendirme yapar (bölüntüyü siler ve yeni fs oluşturur). | `True` |
| `--fill` | `-f` | Diskin tamamını sıfırlarla doldurarak güvenli tam silme yapar. | `False` |
| `--trim` | `-T` | SSD ve Flash bellekler için donanımsal `blkdiscard` (TRIM) çalıştırır. | `False` |
| `--crypt <PAROLA>` | `-c` | Birimi LUKS2 ile şifreler. Parola girilmelidir. | `None` |
| `--interactive` | `-i` | Adım adım etkileşimli terminal sihirbazını başlatır. | `False` |
| `--yes` | `-y` | Güvenlik onay sorusunu atlayarak doğrudan biçimlendirmeyi başlatır. | `False` |
| `--json` | `-j` | Çıktıları makine tarafından okunabilir JSON akışı olarak basar. | `False` |
| `--version` | `-v` | Uygulama sürüm bilgisini görüntüler. | - |
| `--help` | `-h` | Yardım mesajını görüntüler. | - |

---

## 📊 3. Çıkış Kodları (Exit Codes)

| Kod | Anlamı | Açıklama |
| :---: | :--- | :--- |
| `0` | Başarılı (`SUCCESS`) | Biçimlendirme sorunsuz tamamlandı. |
| `1` | Genel Hata (`ERROR`) | Düşük seviyeli I/O, mkfs veya blok aygıt hatası. |
| `2` | Parametre Hatası (`INVALID_ARGS`) | Eksik veya geçersiz argüman belirtildi. |
| `3` | Güvenlik İhlali (`SECURITY_BLOCKED`) | Sistem diski veya korumalı alan biçimlendirilmeye çalışıldı. |
| `126` | Yetkilendirme Hatası (`AUTH_FAILED`) | PolicyKit yetkilendirmesi reddedildi veya yapılamadı. |
| `130` | İptal Edildi (`CANCELLED`) | Kullanıcı Ctrl+C veya SIGTERM ile işlemi güvenle durdurdu. |

---

## 💻 4. Örnek Kullanım Senaryoları

### 4.1. USB Diskleri Listeleme
```bash
parslinux-formatter-cli --list
```
JSON çıktısı almak için:
```bash
parslinux-formatter-cli --list --json
```

### 4.2. Hızlı FAT32 Biçimlendirme (En Yaygın)
```bash
parslinux-formatter-cli -d sdb -t FAT32 -l PARS_BELLEK -y
```

### 4.3. Modern SSD/USB için ExFAT + GPT Biçimlendirme
```bash
parslinux-formatter-cli -d /dev/sdc -t EXFAT -l YEDEK_DISK --gpt -y
```

### 4.4. Flash Bellekler için F2FS ve Hızlı TRIM Temizliği
```bash
parslinux-formatter-cli -d sdb -t F2FS -l ULTRA_SPEED --trim -y
```

### 4.5. Güvenli Tam Sıfırlama (Zero-Fill) ile EXT4 Biçimlendirme
```bash
parslinux-formatter-cli -d sdb -t EXT4 -l TEMIZ_DISK --fill -y
```

### 4.6. LUKS2 ile Şifrelenmiş Güvenli USB Bellek
```bash
parslinux-formatter-cli -d sdb -t EXT4 -l GIZLI_KASA -c "CokGuvenliParola123!" -y
```

### 4.7. Etkileşimli Sihirbaz Modu
Terminalde yön tuşları ve soru-cevap ile biçimlendirmek için:
```bash
parslinux-formatter-cli -i
```

---

## 🔄 5. JSON Olay Akışı Spesifikasyonu (`--json`)

Web arayüzleri, panel entegrasyonları veya CI/CD boru hatlarında gerçek zamanlı izleme için `--json` parametresi kullanılır.

### Başlangıç Olayı:
```json
{"event": "start", "device": "sdb", "filesystem": "FAT32", "label": "PARS_USB", "fill": false}
```

### İlerleme Olayı (Tam Sıfırlama / Biçimlendirme Esnasında):
```json
{"event": "progress", "percent": 45.2, "written_bytes": 1450000000, "total_bytes": 3200000000, "speed_mb": 42.8, "eta_seconds": 41}
```

### Tamamlanma Olayı:
```json
{"event": "completed", "status": "success", "device": "sdb", "elapsed_seconds": 12.4}
```

### Hata Olayı:
```json
{"event": "error", "message": "Aygıt meşgul veya başka bir işlem tarafından kilitlenmiş.", "code": 1}
```

### İptal Olayı:
```json
{"event": "cancelled", "status": "cancelled", "device": "sdb"}
```
