# ParsLinux Formatter — Test ve Doğrulama Kılavuzu (TESTING.md)

Bu belge, **ParsLinux Formatter** uygulamasının birim testlerini (unit tests), sahte blok aygıtı (loop device) simülasyonlarını ve kullanıcı arayüzü doğrulama adımlarını açıklamaktadır.

---

## 🧪 1. Sanal USB Aygıtı ile Güvenli Test (Loop Device)

Fiziksel bir USB belleği riske atmadan tüm biçimlendirme ve bölümleme özelliklerini test etmek için Linux `loop` aygıtları kullanılır.

### 1.1. Sanal Disk İmajı Oluşturma
```bash
# 2 GB boyutunda boş bir sanal imaj oluştur
truncate -s 2G /tmp/test_usb_disk.img

# İmajı döngüsel blok aygıtına (loop) bağla
sudo losetup -fP /tmp/test_usb_disk.img

# Atanan aygıtı öğren (örn: /dev/loop20)
losetup -a | grep test_usb_disk.img
```

### 1.2. Biçimlendirme Motorunu Test Etme
```bash
# FAT32 Hızlı Biçimlendirme Testi
sudo python3 src/USBFormatter.py --device loop20 --type FAT32 --label TEST_FAT

# ExFAT Testi
sudo python3 src/USBFormatter.py --device loop20 --type EXFAT --label TEST_EXFAT

# EXT4 ve Sıfırlama Testi
sudo python3 src/USBFormatter.py --device loop20 --type EXT4 --label TEST_EXT4 --fill
```

### 1.3. Sanal Diski Temizleme
```bash
sudo losetup -d /dev/loop20
rm -f /tmp/test_usb_disk.img
```

---

## 🔍 2. Otomatik Birim Testlerini Çalıştırma

Proje kök dizininde bulunan test paketini çalıştırmak için:

```bash
# Tüm birim testlerini çalıştır
python3 -m unittest discover tests/ -v
```

---

## 🖥️ 3. Arayüz ve Duman (Smoke) Testleri

### 3.1. CLI Duman Testi
```bash
./parslinux-formatter-cli --list
./parslinux-formatter-cli --help
./parslinux-formatter-cli --version
```

### 3.2. GTK4 Modern Arayüz Testi
```bash
./parslinux-formatter-gtk4
```

### 3.3. GTK3 Klasik Arayüz Testi
```bash
./parslinux-formatter
```

---

## 🛡️ 4. Güvenlik Filtresi Doğrulama Testi

Sistem disklerinin biçimlendirilmesinin engellendiğini doğrulamak için:

```bash
# Kök diski (sda veya nvme0n1) hedef göstererek test et (Başarısız olması ZORUNLUDUR)
python3 src/CLI.py -d sda -t FAT32 -y
# Beklenen Çıktı: "Hata: Güvenlik ihlali: Belirtilen aygıt sistem diskidir veya kök bölüntüyü barındırmaktadır." (Exit Code 3)
```
