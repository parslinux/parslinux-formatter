#!/usr/bin/env python3
"""ParsLinux Formatter — Başsız (Headless) Komut Satırı Arayüzü (CLI.py).

Grafik arayüzü gerektirmeden tam terminal otomasyonu, renkli ANSI ilerleme
çubuğu, etkileşimli sihirbaz modu ve web panelleri için makine tarafından
okunabilir JSON olay akışı (--json) sunar.
"""

import argparse
import getpass
import json
import os
import signal
import sys
import time
from collections import deque
from subprocess import PIPE, Popen
from typing import List, Optional

import USBDeviceManager
from USBDeviceManager import DriveError, validate_usb_drive
from Utils import format_duration, format_size

SUPPORTED_FILESYSTEMS = ["FAT32", "NTFS", "EXFAT", "EXT4", "BTRFS", "XFS", "F2FS"]


def get_version() -> str:
    """src/__version__ dosyasından sürüm metnini okur."""
    ver_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "__version__")
    if os.path.exists(ver_path):
        try:
            with open(ver_path, "r") as f:
                return f.read().strip()
        except OSError:
            pass
    return "1.0.0"


def find_formatter_script() -> str:
    """USBFormatter.py betiğinin tam yolunu tespit eder."""
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "USBFormatter.py"),
        "/usr/share/parslinux/parslinux-formatter/src/USBFormatter.py",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return "USBFormatter.py"


def handle_device_listing(as_json: bool = False) -> None:
    """Sistemdeki çıkarılabilir USB diskleri listeler ve çıkar."""
    devices = USBDeviceManager.get_usb_devices()
    if as_json:
        result = [
            {
                "device": f"/dev/{d[0]}",
                "name": d[0],
                "label_or_model": d[1],
                "size_formatted": d[2],
                "size_bytes": d[3],
            }
            for d in devices
        ]
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0)

    if not devices:
        print("\nSistemde takılı çıkarılabilir USB bellek bulunamadı.")
        sys.exit(0)

    print("\n📦 Bağlı Çıkarılabilir USB Depolama Aygıtları:")
    print("=" * 65)
    print(f"{'AYGIT':<12} {'BOYUT':<10} {'ETİKET / MODEL'}")
    print("-" * 65)
    for dev in devices:
        print(f"/dev/{dev[0]:<7} {dev[2]:<10} {dev[1]}")
    print("=" * 65 + "\n")
    sys.exit(0)


def render_ansi_bar(percent: float, speed_mb: float, eta_str: str, width: int = 28) -> str:
    """Renkli ANSI terminal ilerleme çubuğu üretir."""
    filled = int(width * (max(0.0, min(100.0, percent)) / 100.0))
    bar = "█" * filled + "░" * (width - filled)
    return f"\r\033[K[\033[36m{bar}\033[0m] \033[1m{percent:5.1f}%\033[0m | \033[32m{speed_mb:5.1f} MB/s\033[0m | Kalan: \033[33m{eta_str}\033[0m"


def interactive_wizard() -> dict:
    """Terminalde etkileşimli adım adım biçimlendirme sihirbazı çalıştırır."""
    print("\n" + "=" * 60)
    print("🐆 ParsLinux Formatter — Etkileşimli Terminal Sihirbazı")
    print("=" * 60)

    devices = USBDeviceManager.get_usb_devices()
    if not devices:
        print("\n❌ Sistemde biçimlendirilebilir USB depolama aygıtı bulunamadı.")
        sys.exit(1)

    print("\nLütfen biçimlendirilecek USB diski seçin:")
    for idx, d in enumerate(devices, start=1):
        print(f"  [{idx}] /dev/{d[0]} ({d[2]}) — {d[1]}")

    selected_dev = None
    while not selected_dev:
        choice = input(f"\nSeçiminiz [1-{len(devices)}]: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(devices):
            selected_dev = devices[int(choice) - 1]
        else:
            print("Geçersiz seçim, lütfen tekrar deneyin.")

    print(f"\n✓ Seçilen Aygıt: /dev/{selected_dev[0]} ({selected_dev[1]} - {selected_dev[2]})")

    # Dosya sistemi seçimi
    print("\nKullanılacak Dosya Sistemi:")
    for idx, fs in enumerate(SUPPORTED_FILESYSTEMS, start=1):
        desc = ""
        if fs == "FAT32":
            desc = "(Evrensel Uyumluluk)"
        elif fs == "NTFS":
            desc = "(Büyük Dosyalar / Windows)"
        elif fs == "EXFAT":
            desc = "(Modern Flash Bellekler)"
        elif fs == "EXT4":
            desc = "(Standart Linux)"
        elif fs == "F2FS":
            desc = "(Flash Dostu / Yüksek Hız)"
        elif fs == "BTRFS":
            desc = "(Anlık Görüntü / Sıkıştırma)"
        print(f"  [{idx}] {fs:<8} {desc}")

    selected_fs = "FAT32"
    fs_choice = input("\nDosya sistemi seçin [1-7, Varsayılan: 1]: ").strip()
    if fs_choice.isdigit() and 1 <= int(fs_choice) <= len(SUPPORTED_FILESYSTEMS):
        selected_fs = SUPPORTED_FILESYSTEMS[int(fs_choice) - 1]

    # Birim etiketi
    label = input("\nBirim Etiketi (Boş bırakılabilir): ").strip()

    # Tam sıfırlama (Fill)
    fill_choice = input("\nTam Sıfırlama (Zero-Fill) yapılsın mı? [e/H]: ").strip().lower()
    fill = fill_choice in ("e", "evet", "y", "yes")

    # Donanımsal TRIM
    trim_choice = input("Donanımsal TRIM (blkdiscard) uygulansın mı? [e/H]: ").strip().lower()
    trim = trim_choice in ("e", "evet", "y", "yes")

    # GPT tablosu
    gpt_choice = input("GPT Bölümleme Tablosu kullanılsın mı? (Varsayılan MBR) [e/H]: ").strip().lower()
    gpt = gpt_choice in ("e", "evet", "y", "yes")

    # LUKS şifreleme
    crypt_pass = None
    crypt_choice = input("Diski LUKS2 ile şifrelemek istiyor musunuz? [e/H]: ").strip().lower()
    if crypt_choice in ("e", "evet", "y", "yes"):
        p1 = getpass.getpass("LUKS Parolası: ")
        p2 = getpass.getpass("Parolayı Tekrar Girin: ")
        if p1 != p2:
            print("\n❌ Parolalar eşleşmedi! İşlem iptal edildi.")
            sys.exit(2)
        if len(p1) < 4:
            print("\n❌ Parola en az 4 karakter olmalıdır.")
            sys.exit(2)
        crypt_pass = p1

    # Özet ve Nihai Onay
    print("\n" + "=" * 60)
    print("⚠️  BİÇİMLENDİRME ÖZETİ VE RİSK UYARISI:")
    print("=" * 60)
    print(f"Hedef Disk      : /dev/{selected_dev[0]} ({selected_dev[1]} - {selected_dev[2]})")
    print(f"Dosya Sistemi   : {selected_fs}")
    print(f"Birim Etiketi   : '{label}'")
    print(f"Bölümleme       : {'GPT' if gpt else 'MBR (DOS)'}")
    print(f"Tam Sıfırlama   : {'EVET' if fill else 'HAYIR (Hızlı)'}")
    print(f"Donanımsal TRIM : {'EVET' if trim else 'HAYIR'}")
    print(f"Şifreleme       : {'LUKS2 Korumalı' if crypt_pass else 'Şifresiz'}")
    print("=" * 60)
    print("UYARI: Bu işlem hedef diskteki TÜM verileri kalıcı olarak silecektir!")
    confirm = input("Onaylamak için 'EVET' yazın: ").strip()

    if confirm != "EVET":
        print("\nİşlem kullanıcı tarafından onaylanmadı ve iptal edildi.")
        sys.exit(0)

    return {
        "device": selected_dev[0],
        "type": selected_fs,
        "label": label,
        "fill": fill,
        "trim": trim,
        "gpt": gpt,
        "crypt": crypt_pass,
    }


def main():
    parser = argparse.ArgumentParser(
        prog="parslinux-formatter-cli",
        description="ParsLinux Formatter — Başsız (Headless) USB Biçimlendirici",
        epilog="ParsLinux Geliştirici Topluluğu • https://pars.org.tr",
    )
    parser.add_argument("-L", "--list", action="store_true", help="USB depolama aygıtlarını listeler ve çıkar")
    parser.add_argument("-d", "--device", help="Biçimlendirilecek hedef blok aygıtı (örn: sdb veya /dev/sdb)")
    parser.add_argument("-t", "--type", "--filesystem", default="FAT32", help="Dosya sistemi (FAT32, NTFS, EXFAT, EXT4, BTRFS, XFS, F2FS)")
    parser.add_argument("-l", "--label", default="", help="Birim etiket adı")
    parser.add_argument("-g", "--gpt", action="store_true", help="MBR yerine modern GPT bölümleme tablosu kullan")
    parser.add_argument("-q", "--quick", action="store_true", default=True, help="Hızlı biçimlendirme modu (varsayılan)")
    parser.add_argument("-f", "--fill", action="store_true", help="Tam sıfırlama (Zero-fill, 4 MiB tampon)")
    parser.add_argument("-T", "--trim", action="store_true", help="Donanımsal TRIM (blkdiscard) uygula")
    parser.add_argument("-c", "--crypt", help="LUKS2 şifreleme parolası")
    parser.add_argument("-i", "--interactive", action="store_true", help="Etkileşimli terminal sihirbazını başlat")
    parser.add_argument("-y", "--yes", action="store_true", help="Güvenlik onayını atla ve doğrudan başlat")
    parser.add_argument("-j", "--json", action="store_true", help="Makine tarafından okunabilir JSON akışı bas")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {get_version()}")

    args = parser.parse_args()

    # Cihaz listeleme modu
    if args.list:
        handle_device_listing(as_json=args.json)

    # Etkileşimli sihirbaz modu
    if args.interactive:
        wizard_params = interactive_wizard()
        target_device = wizard_params["device"]
        fs_type = wizard_params["type"]
        label = wizard_params["label"]
        fill = wizard_params["fill"]
        trim = wizard_params["trim"]
        gpt = wizard_params["gpt"]
        crypt = wizard_params["crypt"]
        skip_confirm = True
    else:
        if not args.device:
            err_msg = "Eksik parametre: Biçimlendirmek için --device (-d) belirtilmelidir."
            if args.json:
                print(json.dumps({"event": "error", "message": err_msg, "code": 2}))
            else:
                sys.stderr.write(f"HATA: {err_msg}\n")
                parser.print_usage(sys.stderr)
            sys.exit(2)

        target_device = args.device
        fs_type = args.type.upper()
        label = args.label
        fill = args.fill
        trim = args.trim
        gpt = args.gpt
        crypt = args.crypt
        skip_confirm = args.yes

    # Dosya sistemi geçerlilik kontrolü
    if fs_type not in SUPPORTED_FILESYSTEMS:
        err_msg = f"Desteklenmeyen dosya sistemi: {fs_type}. Desteklenenler: {', '.join(SUPPORTED_FILESYSTEMS)}"
        if args.json:
            print(json.dumps({"event": "error", "message": err_msg, "code": 2}))
        else:
            sys.stderr.write(f"HATA: {err_msg}\n")
        sys.exit(2)

    # 5 Kademeli Güvenlik Kontrolü
    try:
        clean_block = validate_usb_drive(target_device)
    except DriveError as err:
        err_msg = f"Güvenlik ihlali: {err}"
        if args.json:
            print(json.dumps({"event": "error", "message": err_msg, "code": 3}))
        else:
            sys.stderr.write(f"\n❌ GÜVENLİK ENGELİ: {err_msg}\n\n")
        sys.exit(3)

    # Teyit istemi (skip_confirm verilmediyse)
    if not skip_confirm:
        print("\n" + "=" * 60)
        print("⚠️  DİKKAT: /dev/{} üzerindeki TÜM veriler kalıcı olarak silinecek!".format(clean_block))
        print(f"    Dosya Sistemi : {fs_type}")
        print(f"    Etiket        : '{label}'")
        print(f"    Sıfırlama     : {'Tam (Zero-Fill)' if fill else 'Hızlı'}")
        print("=" * 60)
        confirm = input("İşlemi başlatmak için 'evet' veya 'y' yazın: ").strip().lower()
        if confirm not in ("e", "evet", "y", "yes"):
            print("İşlem iptal edildi.")
            sys.exit(0)

    # Formatlama komutunu oluştur
    script_path = find_formatter_script()
    cmd_args = [
        "--device", clean_block,
        "--type", fs_type,
        "--label", label,
    ]
    if fill:
        cmd_args.append("--fill")
    if trim:
        cmd_args.append("--trim")
    if gpt:
        cmd_args.append("--gpt")
    if crypt:
        cmd_args += ["--crypt", crypt]

    # Root euid kontrolü
    if os.geteuid() == 0:
        cmd = [sys.executable, script_path] + cmd_args
    else:
        cmd = ["pkexec", script_path] + cmd_args

    if args.json:
        print(
            json.dumps(
                {
                    "event": "start",
                    "device": clean_block,
                    "filesystem": fs_type,
                    "label": label,
                    "fill": fill,
                }
            ),
            flush=True,
        )
    else:
        print(f"\n🚀 Biçimlendirme başlatılıyor: /dev/{clean_block} [{fs_type}]...")

    # Süreci başlat (stdin borusuyla kooperatif iptal desteği)
    try:
        proc = Popen(
            cmd,
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
            text=True,
            bufsize=1,
        )
    except FileNotFoundError as err:
        err_msg = f"Çalıştırıcı bulunamadı: {err}"
        if args.json:
            print(json.dumps({"event": "error", "message": err_msg, "code": 1}))
        else:
            sys.stderr.write(f"HATA: {err_msg}\n")
        sys.exit(1)

    cancelled = False

    def handle_sig(sig, frame):
        nonlocal cancelled
        cancelled = True
        if proc.stdin and not proc.stdin.closed:
            try:
                proc.stdin.close()
            except OSError:
                pass
        if args.json:
            print(json.dumps({"event": "cancelled", "status": "cancelled"}), flush=True)
        else:
            sys.stderr.write("\nİşlem iptal ediliyor, tamponlar diske eşitleniyor...\n")

    signal.signal(signal.SIGINT, handle_sig)
    signal.signal(signal.SIGTERM, handle_sig)

    start_time = time.monotonic()

    # stdout akışını tüket
    try:
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            # PROGRESS|<written>|<total>|<speed>|<eta>
            if line.startswith("PROGRESS"):
                parts = line.split("|")
                if len(parts) >= 3:
                    try:
                        written = int(parts[1])
                        total = int(parts[2])
                        speed = float(parts[3]) if len(parts) > 3 else 0.0
                        eta = parts[4] if len(parts) > 4 else "--:--"
                        percent = (written / total * 100.0) if total > 0 else 0.0

                        if args.json:
                            print(
                                json.dumps(
                                    {
                                        "event": "progress",
                                        "percent": round(percent, 1),
                                        "written_bytes": written,
                                        "total_bytes": total,
                                        "speed_mb": round(speed, 1),
                                        "eta": eta,
                                    }
                                ),
                                flush=True,
                            )
                        else:
                            sys.stdout.write(render_ansi_bar(percent, speed, eta))
                            sys.stdout.flush()
                    except (ValueError, IndexError):
                        pass

    except Exception as exc:
        if not cancelled:
            sys.stderr.write(f"\nİlerleme akışı okunurken hata: {exc}\n")

    returncode = proc.wait()

    if cancelled:
        sys.exit(130)

    elapsed = time.monotonic() - start_time

    if returncode == 0:
        if args.json:
            print(
                json.dumps(
                    {
                        "event": "completed",
                        "status": "success",
                        "device": clean_block,
                        "elapsed_seconds": round(elapsed, 1),
                    }
                ),
                flush=True,
            )
        else:
            print(f"\n\n✓ /dev/{clean_block} başarıyla biçimlendirildi! (Geçen süre: {format_duration(elapsed)})")
            print("  USB diski güvenle kullanabilir veya çıkarabilirsiniz.\n")
        sys.exit(0)

    # Hata yönetimi
    stderr_out = proc.stderr.read().strip() if proc.stderr else ""
    if returncode in (126, 127):
        err_msg = "PolicyKit yetkilendirmesi reddedildi veya yapılamadı."
        if args.json:
            print(json.dumps({"event": "error", "message": err_msg, "code": 126}), flush=True)
        else:
            sys.stderr.write(f"\nHATA: {err_msg}\n")
        sys.exit(126)

    err_msg = stderr_out or "Biçimlendirme sırasında beklenmeyen bir hata oluştu."
    if args.json:
        print(json.dumps({"event": "error", "message": err_msg, "code": returncode}), flush=True)
    else:
        sys.stderr.write(f"\nHATA: {err_msg}\n")
    sys.exit(returncode)


if __name__ == "__main__":
    main()
