#!/usr/bin/env bash
# ==============================================================================
# ParsLinux Formatter — Sistem Kurulum Betiği (install.sh)
# ==============================================================================
# Bu betik ParsLinux Formatter ve tüm bağımlılıklarını sisteme kurar,
# PolicyKit izinlerini ve masaüstü menü kısayollarını yapılandırır.
# ==============================================================================

set -e

# Renk tanımları
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${CYAN}${BOLD}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║             🐆 ParsLinux Formatter — Kurulum Sihirbazı        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Root yetkisi kontrolü
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}ℹ️  Sistem genelinde kurulum için root ayrıcalığı gerekiyor. Sudo isteniyor...${NC}"
    exec sudo bash "$0" "$@"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BOLD}[1/4] Bağımlılıklar denetleniyor...${NC}"

REQUIRED_PKGS=(
    python3
    python3-gi
    gir1.2-gtk-3.0
    gir1.2-gtk-4.0
    gir1.2-adwaita-1
    dosfstools
    ntfs-3g
    exfatprogs
    e2fsprogs
    parted
    util-linux
    policykit-1
)

MISSING_PKGS=()
for pkg in "${REQUIRED_PKGS[@]}"; do
    if ! dpkg -s "$pkg" &>/dev/null; then
        MISSING_PKGS+=("$pkg")
    fi
done

if [ ${#MISSING_PKGS[@]} -gt 0 ]; then
    echo -e "${YELLOW}Eksik paketler tespit edildi: ${MISSING_PKGS[*]}${NC}"
    if command -v apt-get &>/dev/null; then
        echo -e "${CYAN}Eksik bağımlılıklar APT üzerinden kuruluyor...${NC}"
        apt-get update -qq
        apt-get install -y "${MISSING_PKGS[@]}"
    else
        echo -e "${RED}Uyarı: APT bulunamadı. Lütfen eksik bağımlılıkları paket yöneticinizle kurun.${NC}"
    fi
else
    echo -e "${GREEN}✓ Tüm temel sistem bağımlılıkları mevcut.${NC}"
fi

echo -e "\n${BOLD}[2/4] setup.py ile uygulama dosyaları kuruluyor...${NC}"
python3 setup.py install --prefix=/usr --root=/ >/dev/null

echo -e "\n${BOLD}[3/4] Çalıştırma izinleri ve dizinler doğrulanıyor...${NC}"
chmod +x /usr/bin/parslinux-formatter*
chmod +x /usr/share/parslinux/parslinux-formatter/src/*.py 2>/dev/null || true

echo -e "\n${BOLD}[4/4] Masaüstü veritabanı ve simge önbelleği yenileniyor...${NC}"
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database /usr/share/applications || true
fi

if command -v gtk-update-icon-cache &>/dev/null; then
    gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
fi

echo -e "\n${GREEN}${BOLD}══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}🎉 ParsLinux Formatter kurulumu başarıyla tamamlandı!${NC}"
echo -e "${GREEN}${BOLD}══════════════════════════════════════════════════════════════${NC}"
echo -e "Kullanım Seçenekleri:"
echo -e "  • Modern GTK4 Arayüzü : ${CYAN}parslinux-formatter-gtk4${NC}"
echo -e "  • Klasik GTK3 Arayüzü : ${CYAN}parslinux-formatter${NC}"
echo -e "  • Uçbirim (CLI)       : ${CYAN}parslinux-formatter-cli --list${NC}"
echo -e "  • Menü Kısayolu       : Uygulamalar > Sistem > ParsLinux USB Biçimlendirici\n"
