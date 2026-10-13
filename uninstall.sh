#!/usr/bin/env bash
# ==============================================================================
# ParsLinux Formatter — Sistemden Kaldırma Betiği (uninstall.sh)
# ==============================================================================
# ParsLinux Formatter ile ilgili tüm sistem dosyalarını, PolicyKit kurallarını,
# simgeleri ve menü kısayollarını sistemden temizler.
# ==============================================================================

set -e

# Renk tanımları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${YELLOW}${BOLD}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          🗑️  ParsLinux Formatter — Kaldırma Sihirbazı          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Root yetkisi kontrolü
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}ℹ️  Kaldırma işlemi için root ayrıcalığı gerekiyor. Sudo isteniyor...${NC}"
    exec sudo bash "$0" "$@"
fi

echo -e "${BOLD}[1/3] Uygulama dosyaları ve ikililer siliniyor...${NC}"

# İkili başlatıcılar
rm -f /usr/bin/parslinux-formatter
rm -f /usr/bin/parslinux-formatter-gtk4
rm -f /usr/bin/parslinux-formatter-cli

# Ana uygulama dizini
rm -rf /usr/share/parslinux/parslinux-formatter

# Masaüstü kısayolu, PolicyKit ve simgeler
rm -f /usr/share/applications/tr.org.parslinux.formatter.desktop
rm -f /usr/share/polkit-1/actions/tr.org.parslinux.pkexec.parslinux-formatter.policy
rm -f /usr/share/icons/hicolor/scalable/apps/parslinux-formatter.svg
rm -f /usr/share/metainfo/tr.org.parslinux.Formatter.metainfo.xml

# Dil çevirileri (.mo)
rm -f /usr/share/locale/*/LC_MESSAGES/parslinux-formatter.mo

echo -e "${BOLD}[2/3] Python egg-info ve paket kayıtları temizleniyor...${NC}"
rm -rf /usr/local/lib/python3.*/dist-packages/ParsLinux_Formatter* 2>/dev/null || true
rm -rf /usr/lib/python3.*/dist-packages/ParsLinux_Formatter* 2>/dev/null || true

echo -e "${BOLD}[3/3] Masaüstü veritabanı ve simge önbelleği yenileniyor...${NC}"
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database /usr/share/applications || true
fi

if command -v gtk-update-icon-cache &>/dev/null; then
    gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
fi

echo -e "\n${GREEN}${BOLD}✓ ParsLinux Formatter sistemden başarıyla kaldırıldı.${NC}\n"
