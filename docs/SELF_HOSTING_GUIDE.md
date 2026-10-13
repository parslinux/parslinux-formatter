# ParsLinux Formatter — Kurumsal Dağıtım ve Özel Yansıma Kılavuzu (SELF_HOSTING_GUIDE.md)

Bu kılavuz; kurumlar, sistem yöneticileri ve özel Linux laboratuvarları için **ParsLinux Formatter** uygulamasını yerel ağlarda (LAN) veya hava boşluklu (air-gapped) ortamlarda paketleme, kurumsal dağıtım ve merkezi yapılandırma adımlarını açıklamaktadır.

---

## 1. Kurumsal Senaryolar ve Otomasyon

ParsLinux Formatter, başsız (headless) CLI modu ve JSON akış desteği sayesinde kurumsal ortamlarda otomatik görevler için idealdir:

1. **Toplu USB Biçimlendirme İstasyonları:** Laboratuvar veya sınıflardaki USB belleklerin tek komut veya arka plan betiğiyle otomatik temizlenip biçimlendirilmesi.
2. **Kiosk ve İnce İstemci (Thin Client) Sistemleri:** Kullanıcıların yalnızca belirli dosya sistemlerine (örn: sadece FAT32 veya sadece şifreli EXT4) erişebilmesini sağlayan politikalar.
3. **Air-Gapped Güvenli Ağlar:** İnternet erişimi olmayan ortamlarda yerel Debian deposu (`reprepro`) üzerinden dağıtım.

---

## 2. Yerel Debian Paket Deposu Kurulumu (Reprepro)

Kurum içindeki sunucuda yerel bir APT deposu kurarak ParsLinux paketlerini dağıtmak için:

```bash
# Reprepro kurulumu
sudo apt install -y reprepro nginx

# Depo dizini
sudo mkdir -p /var/www/repos/apt/debian/conf

# Distributions konfigürasyonu
cat << 'EOF' | sudo tee /var/www/repos/apt/debian/conf/distributions
Origin: ParsLinux
Label: ParsLinux Local Repo
Codename: stable
Architectures: amd64 arm64 all
Components: main
Description: ParsLinux Local Package Repository
EOF

# Derlenen parslinux-formatter paketini depoya ekle
sudo reprepro -b /var/www/repos/apt/debian includedeb stable ../parslinux-formatter_1.0.0_all.deb
```

İstemci bilgisayarlarda:
```bash
echo "deb [trusted=yes] http://yerel-sunucu/repos/apt/debian stable main" | sudo tee /etc/apt/sources.list.d/parslinux-local.list
sudo apt update && sudo apt install -y parslinux-formatter
```

---

## 3. Otomasyon Betiği Örneği (Toplu Formatlama)

```bash
#!/bin/bash
# Bağlanan her yeni USB belleği otomatik biçimlendiren örnek udev kuralı betiği
DEVICE="$1"
LABEL="PARS_DISK"

if [ -b "/dev/$DEVICE" ]; then
    /usr/bin/parslinux-formatter-cli -d "$DEVICE" -t FAT32 -l "$LABEL" -y --json
fi
```
