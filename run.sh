#!/usr/bin/env bash
# ==============================================================================
# ParsLinux Formatter — Yerel Çalıştırma ve Test Betiği (run.sh)
# ==============================================================================
# Uygulamayı kurmaya gerek kalmadan doğrudan kaynak koddan çalıştırmayı sağlar.
# ==============================================================================

set -e

# Renk tanımları
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export PYTHONPATH="$SCRIPT_DIR/src:$PYTHONPATH"

show_help() {
    echo -e "${CYAN}${BOLD}ParsLinux Formatter Yerel Çalıştırıcı (run.sh)${NC}"
    echo "Kullanım:"
    echo "  ./run.sh [SEÇENEK] [ARGÜMANLAR...]"
    echo ""
    echo "Seçenekler:"
    echo "  gtk4, --gtk4        Modern GTK4 / Libadwaita arayüzünü başlatır (Varsayılan)"
    echo "  gtk3, --gtk3        Klasik GTK3 / Glade arayüzünü başlatır"
    echo "  cli,  --cli [args]  Başsız komut satırı arayüzünü çalıştırır"
    echo "  test, --test        Birim test paketini (tests/) çalıştırır"
    echo "  help, --help        Bu yardım mesajını görüntüler"
    echo ""
    echo "Örnekler:"
    echo "  ./run.sh                    # Modern GTK4 arayüzü"
    echo "  ./run.sh cli --list         # USB diskleri listele"
    echo "  ./run.sh cli -i             # Etkileşimli sihirbaz"
    echo "  ./run.sh test               # Testleri çalıştır"
}

MODE="${1:-gtk4}"

case "$MODE" in
    gtk4|--gtk4)
        echo -e "${GREEN}🚀 GTK4 / Libadwaita modern arayüzü başlatılıyor...${NC}"
        exec python3 src/ModernWindow.py "${@:2}"
        ;;
    gtk3|--gtk3)
        echo -e "${GREEN}🚀 GTK3 klasik arayüzü başlatılıyor...${NC}"
        exec python3 src/Main.py "${@:2}"
        ;;
    cli|--cli)
        shift 1 || true
        exec python3 src/CLI.py "$@"
        ;;
    test|--test)
        echo -e "${CYAN}🧪 Birim testleri çalıştırılıyor...${NC}"
        exec python3 -m unittest discover tests/ -v
        ;;
    help|--help|-h)
        show_help
        exit 0
        ;;
    *)
        # Eğer parametre doğrudan bir CLI argümanı ise CLI'ya yönlendir
        if [[ "$MODE" == -* ]]; then
            exec python3 src/CLI.py "$@"
        else
            echo -e "${YELLOW}Bilinmeyen mod: '$MODE'. Varsayılan GTK4 başlatılıyor...${NC}"
            exec python3 src/ModernWindow.py "$@"
        fi
        ;;
esac
