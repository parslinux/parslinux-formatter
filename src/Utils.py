#!/usr/bin/env python3
"""ParsLinux Formatter — Ortak Yardımcı ve Güvenlik Fonksiyonları (Utils.py).

Kök (root) düzeyindeki biçimlendirme motoru ile kullanıcı arayüzü ve CLI
arasındaki işbirlikçi sinyal iletişimini, tampon boşaltma denetimini,
güvenlik doğrulamalarını ve birim dönüşümlerini yönetir.
"""

import os
import signal
import sys
import threading
import time

_stop_signal = 0


class CancelledError(Exception):
    """Kullanıcı işlemi iptal etti; tamponlar boşaltılıp temiz çıkış yapılmalı."""
    pass


def request_stop(number=signal.SIGTERM):
    """İptal talebini kaydeder. Sinyal işleyicilerden güvenle çağrılabilir."""
    global _stop_signal
    _stop_signal = number


def stop_requested() -> bool:
    """Kullanıcı veya ana süreç iptal talebinde bulunduysa True döner."""
    return _stop_signal != 0


def log(message: str) -> None:
    """Tanı ve bilgi mesajlarını stderr üzerinden yazar (stdout IPC protokolüne aittir)."""
    sys.stderr.write(f"{message}\n")
    sys.stderr.flush()


def fail(message: str, code: int = 1) -> None:
    """Hata mesajı basarak belirtilen çıkış koduyla sonlanır."""
    log(f"HATA: {message}")
    sys.exit(code)


def security_fail(message: str) -> None:
    """Sistem diski veya güvenlik ihlalinde 3 koduyla sonlanır."""
    log(f"GÜVENLİK İHLALİ: {message}")
    sys.exit(3)


def watch_stdin_for_cancel() -> None:
    """Ana sürecin (GUI veya CLI) stdin borusunu kapattığını arka planda izler.
    
    Boru kapandığında EOF alınır ve stop_requested() bayrağı kaldırılır.
    Bu sayede tehlikeli pkexec kill çağrılarına gerek kalmadan zarifçe iptal edilir.
    """
    def _reader():
        try:
            sys.stdin.read()
        except Exception:
            pass
        request_stop()

    thread = threading.Thread(target=_reader, name="stdin-cancel-watcher", daemon=True)
    thread.start()


def exit_as_cancelled() -> None:
    """Tamponları diske boşaltarak (fsync/sync) işlemi iptal edilmiş olarak bitirir."""
    log("İşlem kullanıcı tarafından iptal edildi. Tamponlar eşitleniyor...")
    try:
        os.sync()
    except Exception:
        pass
    sys.exit(130)


def format_size(size_bytes: int) -> str:
    """Bayt miktarını okunabilir boyuta dönüştürür (örn: 14.9 GB, 512 MB)."""
    if size_bytes <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit_index = 0
    size = float(size_bytes)
    while size >= 1000.0 and unit_index < len(units) - 1:
        size /= 1000.0
        unit_index += 1
    return f"{size:.1f} {units[unit_index]}"


def format_duration(seconds: float | None) -> str:
    """Saniye cinsinden süreyi SS:DD veya GG:SS formatına dönüştürür."""
    if seconds is None or seconds < 0:
        return "--:--"
    total_secs = int(seconds)
    hours, remainder = divmod(total_secs, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"
