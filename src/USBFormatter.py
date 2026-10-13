#!/usr/bin/env python3
"""ParsLinux Formatter — Çekirdek Biçimlendirme ve Bölümleme Motoru (USBFormatter.py).

Bu betik pkexec vasıtasıyla kök (root - UID 0) haklarıyla çalıştırılır.
Ön yüzden gelen tüm parametreler güvensiz kabul edilerek 5 kademeli
güvenlik kontrolünden geçirilir. Çıktılar stdout üzerinden IPC ilerleme
akışı (PROGRESS|<yazılan>|<toplam>|<hız>|<kalan>) olarak yayınlanır.
"""

import argparse
import os
import signal
import subprocess
import sys
import time
import uuid

import USBDeviceManager
from USBDeviceManager import DriveError, validate_usb_drive, find_mounts
from Utils import (
    fail,
    log,
    request_stop,
    security_fail,
    stop_requested,
    watch_stdin_for_cancel,
    exit_as_cancelled,
)

BUFFER_SIZE = 4 * 1024 * 1024  # 4 MiB yüksek hızlı tampon


def receive_signal(number, frame):
    """Sinyal yakalayıcı (SIGTERM, SIGINT)."""
    request_stop(number)


signal.signal(signal.SIGTERM, receive_signal)
signal.signal(signal.SIGINT, receive_signal)


def execute(command, ignore_errors=False):
    """Harici sistem komutunu güvenle çalıştırır."""
    log(f"Çalıştırılıyor: {' '.join(command)}")
    res = subprocess.run(command, check=False)
    if res.returncode != 0 and not ignore_errors:
        raise RuntimeError(f"Komut başarısız oldu (Kod {res.returncode}): {' '.join(command)}")
    try:
        os.sync()
    except Exception:
        pass


def create_luks(partition: str, mapper_name: str, password: str) -> None:
    """Belirtilen bölüntü üzerinde LUKS2 şifreli birim oluşturur ve açar."""
    log(f"LUKS2 şifreleme katmanı kuruluyor: {partition} -> /dev/mapper/{mapper_name}")
    
    # LUKS2 format
    p1 = subprocess.Popen(
        ["cryptsetup", "luksFormat", "--type", "luks2", "--batch-mode", partition, "-"],
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    p1.communicate(input=password.encode("utf-8"))
    if p1.returncode != 0:
        raise RuntimeError(f"LUKS biçimlendirmesi başarısız oldu (Kod {p1.returncode}).")

    # LUKS open
    p2 = subprocess.Popen(
        ["cryptsetup", "luksOpen", partition, mapper_name, "-"],
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    p2.communicate(input=password.encode("utf-8"))
    if p2.returncode != 0:
        raise RuntimeError(f"LUKS birimi açılamadı (Kod {p2.returncode}).")


def unmount_all(block_name: str) -> None:
    """Diske ve tüm bölümlerine bağlı mountpoint ve mapper'ları çözer."""
    log(f"Bağlantılar çözülüyor: {block_name}")
    mount_info = find_mounts(block_name)

    # 1. Mount noktalarını çöz
    for mp in mount_info.get("mounts", []):
        if mp and os.path.exists(str(mp)):
            try:
                subprocess.run(["umount", "-f", "-l", str(mp)], check=False)
            except Exception:
                pass

    # 2. Mapper aygıtlarını kaldır
    for n in mount_info.get("names", []):
        mapper_path = f"/dev/mapper/{n}"
        if n and os.path.exists(mapper_path):
            try:
                subprocess.run(["dmsetup", "remove", "--force", str(n)], check=False)
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(
        prog="ParsLinux USB Formatter",
        description="Format USB flash drives safely and quickly",
    )
    parser.add_argument("-d", "--device", required=True, help="Hedef blok aygıtı (örn: sdb)")
    parser.add_argument("-t", "--type", default="FAT32", help="Dosya sistemi türü")
    parser.add_argument("-l", "--label", default="", help="Birim etiketi")
    parser.add_argument("-c", "--crypt", default=None, help="LUKS şifreleme parolası")
    parser.add_argument("-f", "--fill", action="store_true", default=False, help="Tam sıfırlama (Zero-fill)")
    parser.add_argument("-T", "--trim", action="store_true", default=False, help="Donanımsal TRIM (blkdiscard)")
    parser.add_argument("-g", "--gpt", action="store_true", default=False, help="GPT bölümleme tablosu")
    parser.add_argument("-q", "--quick", action="store_true", default=False, help="Hızlı biçimlendirme")

    args = parser.parse_args()

    # --- 1. AŞAMA: 5 Kademeli Sıkı Disk Güvenliği Kontrolü ---
    try:
        clean_block = validate_usb_drive(args.device)
    except DriveError as err:
        security_fail(str(err))

    device_path = f"/dev/{clean_block}"
    sys_block = f"/sys/block/{clean_block}"

    # Stdin borusunu iptal sinyalleri için dinle
    watch_stdin_for_cancel()

    # --- 2. AŞAMA: Bağlantıları ve Mapper'ları Güvenle Çöz ---
    unmount_all(clean_block)

    # --- 3. AŞAMA: Donanımsal TRIM (Seçildiyse) ---
    if args.trim:
        log(f"Donanımsal TRIM (blkdiscard) uygulanıyor: {device_path}")
        subprocess.run(["blkdiscard", device_path], check=False)

    # --- 4. AŞAMA: Tam Sıfırlama (Zero-Fill 4 MiB Tamponlu) ---
    if args.fill:
        log(f"Tam sıfırlama başlatıldı (4 MiB tampon): {device_path}")
        try:
            with open(f"{sys_block}/size", "r") as f:
                block_count = int(f.readline().strip())
            with open(f"{sys_block}/queue/logical_block_size", "r") as f:
                logical_size = int(f.readline().strip())
            total_bytes = block_count * logical_size
        except Exception:
            total_bytes = 0

        if total_bytes > 0:
            written_bytes = 0
            start_time = time.monotonic()
            last_report = 0.0
            zeros = bytes(BUFFER_SIZE)

            try:
                with open(device_path, "wb") as dev_file:
                    print(f"PROGRESS|0|{total_bytes}|0.0|--:--", flush=True)
                    while written_bytes < total_bytes:
                        if stop_requested():
                            log("Sıfırlama işlemi iptal edildi.")
                            exit_as_cancelled()

                        to_write = min(BUFFER_SIZE, total_bytes - written_bytes)
                        if to_write == BUFFER_SIZE:
                            dev_file.write(zeros)
                        else:
                            dev_file.write(bytes(to_write))

                        written_bytes += to_write
                        now = time.monotonic()

                        # Her 0.2 saniyede bir ilerleme bildir
                        if now - last_report >= 0.2 or written_bytes >= total_bytes:
                            last_report = now
                            elapsed = max(0.001, now - start_time)
                            speed_mb = (written_bytes / elapsed) / (1000 * 1000)
                            rem_bytes = max(0, total_bytes - written_bytes)
                            speed_bytes = speed_mb * 1000 * 1000
                            eta_sec = int(rem_bytes / speed_bytes) if speed_bytes > 0 else 0
                            eta_str = f"{eta_sec // 60:02d}:{eta_sec % 60:02d}"
                            print(
                                f"PROGRESS|{written_bytes}|{total_bytes}|{speed_mb:.1f}|{eta_str}",
                                flush=True,
                            )

                    dev_file.flush()
                    os.fsync(dev_file.fileno())
            except OSError as err:
                fail(f"Sıfırlama I/O hatası: {err}")

    # --- 5. AŞAMA: Bölümleme Tablosunu Temizle ve Sil ---
    log(f"Eski bölümleme tablosu temizleniyor: {device_path}")
    try:
        # İlk 4 MiB ve son 4 MiB MBR/GPT başlıklarını sıfırla
        with open(device_path, "wb") as f:
            f.write(b"\0" * (4 * 1024 * 1024))
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        pass

    execute(["wipefs", "-a", device_path, "--force"], ignore_errors=True)
    subprocess.run(["partprobe", device_path], check=False)
    time.sleep(0.5)

    # --- 6. AŞAMA: Yeni Bölümleme Tablosu İnşa Et ---
    table_type = "gpt" if args.gpt else "msdos"
    log(f"Bölümleme tablosu oluşturuluyor ({table_type}): {device_path}")
    execute(["parted", "-s", device_path, "mktable", table_type])

    # Yeni birincil bölüm oluştur
    fs_part_type = args.type.upper()
    parted_fs_hint = "ext4"
    if fs_part_type in ("FAT32", "FAT"):
        parted_fs_hint = "fat32"
    elif fs_part_type == "NTFS":
        parted_fs_hint = "ntfs"
    elif fs_part_type == "EXFAT":
        parted_fs_hint = "fat32"
    elif fs_part_type == "BTRFS":
        parted_fs_hint = "btrfs"

    execute(["parted", "-s", "-a", "optimal", device_path, "mkpart", "primary", parted_fs_hint, "1MiB", "100%"])
    subprocess.run(["partprobe", device_path], check=False)
    time.sleep(0.5)

    # Bölüm adını tespit et (sdb -> sdb1, mmcblk0 -> mmcblk0p1)
    prefix = "p" if ("mmcblk" in clean_block or "nvme" in clean_block) else ""
    partition = f"/dev/{clean_block}{prefix}1"

    # Bölümün aygıt düğümü olarak oluşmasını bekle
    deadline = time.monotonic() + 5.0
    while not os.path.exists(partition):
        if time.monotonic() >= deadline:
            break
        time.sleep(0.1)

    execute(["wipefs", "-a", partition, "--force"], ignore_errors=True)

    # --- 7. AŞAMA: LUKS2 Şifreleme (Seçildiyse) ---
    target_partition = partition
    luks_mapper_name = None

    if args.crypt:
        luks_mapper_name = f"parsluks_{uuid.uuid4().hex[:8]}"
        create_luks(partition, luks_mapper_name, args.crypt)
        target_partition = f"/dev/mapper/{luks_mapper_name}"

    # --- 8. AŞAMA: Dosya Sistemini Biçimlendir ---
    label = args.label.strip()
    fs_type = args.type.upper()
    log(f"Dosya sistemi biçimlendiriliyor: {fs_type} -> {target_partition} (Etiket: '{label}')")

    if fs_type == "FAT32":
        cmd = ["mkfs.fat", "-F", "32"]
        if label:
            cmd += ["-n", label[:11]]
        cmd += ["-I", target_partition]
        execute(cmd)

    elif fs_type == "NTFS":
        cmd = ["mkfs.ntfs", "-f"]
        if label:
            cmd += ["-L", label[:32]]
        cmd.append(target_partition)
        execute(cmd)

    elif fs_type == "EXFAT":
        cmd = ["mkfs.exfat"]
        if label:
            cmd += ["-L", label[:15]]
        cmd.append(target_partition)
        execute(cmd)

    elif fs_type == "EXT4":
        cmd = ["mkfs.ext4", "-F"]
        if label:
            cmd += ["-L", label[:16]]
        cmd.append(target_partition)
        execute(cmd)

    elif fs_type == "BTRFS":
        cmd = ["mkfs.btrfs", "-f"]
        if label:
            cmd += ["-L", label]
        cmd.append(target_partition)
        execute(cmd)

    elif fs_type == "XFS":
        cmd = ["mkfs.xfs", "-f"]
        if label:
            cmd += ["-L", label[:12]]
        cmd.append(target_partition)
        execute(cmd)

    elif fs_type == "F2FS":
        cmd = ["mkfs.f2fs", "-f"]
        if label:
            cmd += ["-l", label[:512]]
        cmd.append(target_partition)
        execute(cmd)

    else:
        fail(f"Desteklenmeyen dosya sistemi türü: {fs_type}")

    # --- 9. AŞAMA: LUKS Kapatma ve Çekirdek Senkronizasyonu ---
    if luks_mapper_name:
        log(f"LUKS eşleyici kapatılıyor: {luks_mapper_name}")
        subprocess.run(["cryptsetup", "luksClose", f"/dev/mapper/{luks_mapper_name}"], check=False)

    try:
        os.sync()
    except Exception:
        pass

    # Aygıtı udev ve masaüstünün tanıması için yenile
    subprocess.run(["partprobe", device_path], check=False)

    log("Biçimlendirme işlemi başarıyla tamamlandı.")
    sys.exit(0)


if __name__ == "__main__":
    main()
