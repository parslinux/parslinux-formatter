#!/usr/bin/env python3
"""ParsLinux Formatter — USB Depolama Aygıtı Yöneticisi ve Güvenlik Filtresi.

Sistemdeki blok aygıtlarını udev veya doğrudan sysfs üzerinden tarar,
çıkarılabilir USB/SD depolama birimlerini tespit eder ve 5 kademeli
güvenlik doğrulaması uygulayarak sistem disklerini korur.
"""

import json
import os
import re
import subprocess
from glob import glob
from typing import Callable, Dict, List, Optional, Set, Tuple

CRITICAL_MOUNT_POINTS = {
    "/",
    "/boot",
    "/boot/efi",
    "/home",
    "/var",
    "/usr",
    "/etc",
    "/root",
    "/opt",
}


class DriveError(Exception):
    """Güvenlik ihlali, geçersiz disk veya korumalı sistem alanı hatası."""
    pass


def get_block_name(device: str) -> Optional[str]:
    """'/dev/sdb' veya 'sdb' şeklindeki girdi adını 'sdb' blok adına dönüştürür."""
    if not device:
        return None
    name = os.path.basename(device.strip())
    # Yalnızca geçerli blok aygıt adlarını kabul et (sdX, mmcblkX, nvmeXnX)
    if re.match(r"^(sd[a-z]+|mmcblk\d+|nvme\d+n\d+)$", name):
        return name
    return None


def get_mounts() -> List[Tuple[str, str]]:
    """/proc/mounts dosyasından aktif (kaynak_aygıt, bağlama_noktası) çiftlerini okur."""
    mounts = []
    try:
        with open("/proc/mounts", "r") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2 and parts[0].startswith("/dev/"):
                    mounts.append((os.path.realpath(parts[0]), parts[1]))
    except OSError:
        pass
    return mounts


def get_swap_devices() -> Set[str]:
    """/proc/swaps dosyasından aktif takas (swap) aygıtlarını döndürür."""
    swaps = set()
    try:
        with open("/proc/swaps", "r") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 1 and parts[0].startswith("/dev/"):
                    swaps.add(os.path.realpath(parts[0]))
    except OSError:
        pass
    return swaps


def get_partitions(block_name: str) -> List[str]:
    """Bir disk blok adına ait tüm alt bölüntü yollarını (/dev/sdb1 vb.) döndürür."""
    prefix = "p" if ("mmcblk" in block_name or "nvme" in block_name) else ""
    pattern = f"/dev/{block_name}{prefix}*"
    partitions = []
    for path in glob(pattern):
        # Ana diskin kendisini hariç tut
        if path != f"/dev/{block_name}":
            partitions.append(os.path.realpath(path))
    return partitions


def is_removable_or_usb(block_name: str) -> bool:
    """Aygıtın USB veri yolunda olduğunu veya çıkarılabilir olduğunu sysfs üzerinden doğrular."""
    sys_path = f"/sys/block/{block_name}"
    if not os.path.exists(sys_path):
        return False

    real_path = os.path.realpath(sys_path)
    if "/usb" in real_path:
        return True

    # removable bayrağını kontrol et
    removable_file = os.path.join(sys_path, "removable")
    if os.path.exists(removable_file):
        try:
            with open(removable_file, "r") as f:
                if f.read().strip() == "1":
                    return True
        except OSError:
            pass

    return False


def find_usb_devices() -> List[str]:
    """Sistemdeki tüm uygun çıkarılabilir USB disk blok adlarını listeler."""
    candidates = glob("/sys/block/sd*") + glob("/sys/block/mmcblk*")
    usb_devices = []

    for path in candidates:
        block_name = os.path.basename(path)
        if is_removable_or_usb(block_name):
            usb_devices.append(block_name)

    return sorted(usb_devices)


def validate_usb_drive(drive_or_name: str) -> str:
    """Diskin biçimlendirilebilir olduğunu 5 kademeli filtreyle doğrular.
    
    Başarısız olursa DriveError fırlatır; başarılı olursa temiz 'sdb' adını döndürür.
    """
    block_name = get_block_name(drive_or_name)
    if not block_name:
        raise DriveError(f"'{drive_or_name}' geçerli bir blok aygıtı adı değil.")

    # 1. Kademe: Aygıt /sys/block altında mevcut mu?
    sys_path = f"/sys/block/{block_name}"
    if not os.path.exists(sys_path):
        raise DriveError(f"'{block_name}' sistemde bulunamadı.")

    # 2. Kademe: Veri yolu çıkarılabilir / USB mi?
    if not is_removable_or_usb(block_name):
        raise DriveError(
            f"'{block_name}' çıkarılabilir bir USB veya SD depolama aygıtı değil (Dahili disk koruması)."
        )

    # 3. Kademe: Salt-okunur (Hardware Read-Only) denetimi
    ro_file = os.path.join(sys_path, "ro")
    if os.path.exists(ro_file):
        try:
            with open(ro_file, "r") as f:
                if f.read().strip() == "1":
                    raise DriveError(f"'{block_name}' donanımsal olarak yazma korumalı (salt-okunur).")
        except OSError:
            pass

    # 4. Kademe: Kritik sistem bağlama noktaları (Mountpoint) koruması
    target_paths = {f"/dev/{block_name}", os.path.realpath(f"/dev/{block_name}")}
    for part in get_partitions(block_name):
        target_paths.add(part)
        target_paths.add(os.path.realpath(part))

    for source, mount_point in get_mounts():
        if source in target_paths:
            # Kritik bağlama noktası kontrolü
            if mount_point in CRITICAL_MOUNT_POINTS:
                raise DriveError(
                    f"Güvenlik İhlali: '{source}' aygıtı kritik '{mount_point}' sistem dizinine bağlıdır! İşlem engellendi."
                )

    # 5. Kademe: Aktif Takas (Swap) ve Device-Mapper / LUKS konteyner koruması
    active_swaps = get_swap_devices()
    for path in target_paths:
        if path in active_swaps:
            raise DriveError(f"'{path}' sistem takas alanı (swap) olarak kullanılmaktadır.")

    holders = glob(f"/sys/block/{block_name}/holders/*") + glob(
        f"/sys/block/{block_name}/{block_name}*/holders/*"
    )
    if holders:
        raise DriveError(
            f"'{block_name}' bir aygıt eşleyici (LVM, kök LUKS veya RAID) tarafından kullanılmaktadır."
        )

    return block_name


def find_mounts(disk: str) -> Dict[str, List[str]]:
    """Bir diske ve tüm alt bölümlerine ait bağlama noktalarını ve mapper adlarını bulur."""
    try:
        sp = subprocess.run(
            ["lsblk", "-J", f"/dev/{disk}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        data = json.loads(sp.stdout) if sp.stdout else {}
    except Exception:
        data = {}

    mounts = []
    names = []

    def _traverse(node):
        for item in node:
            if "mountpoints" in item and item["mountpoints"]:
                for mp in item["mountpoints"]:
                    if mp:
                        mounts.append(mp)
            if "name" in item:
                names.append(item["name"])
            if "children" in item:
                _traverse(item["children"])

    if "blockdevices" in data:
        _traverse(data["blockdevices"])

    return {"mounts": mounts, "names": names}


def get_usb_devices() -> List[List]:
    """Sistemdeki çıkarılabilir USB disklerin detaylı bilgilerini döndürür.
    
    Dönüş formatı: [[block_name, label_or_model, human_size, size_bytes], ...]
    Örn: [['sdb', 'SanDisk Cruzer Glide', '14.9 GB', 15600000000], ...]
    """
    device_list = []
    usb_names = find_usb_devices()

    # pyudev varsa zengin bilgi için kullan, yoksa sysfs fallback
    pyudev_ctx = None
    try:
        from pyudev import Context, Devices
        pyudev_ctx = Context()
    except ImportError:
        pass

    for block_name in usb_names:
        try:
            sys_block = f"/sys/block/{block_name}"
            if not os.path.exists(sys_block):
                continue

            # Boyut hesaplama
            with open(f"{sys_block}/size", "r") as f:
                block_count = int(f.readline().strip())
            with open(f"{sys_block}/queue/logical_block_size", "r") as f:
                block_size = int(f.readline().strip())
            
            total_bytes = block_count * block_size
            if total_bytes <= 0:
                continue

            # GB / MB biçimlendirme
            gb_size = round(total_bytes / (1000 * 1000 * 1000), 1)
            human_size = f"{gb_size} GB" if gb_size >= 1.0 else f"{round(total_bytes / (1000 * 1000))} MB"

            # Model / Etiket bilgisi
            label_or_model = ""
            if pyudev_ctx:
                try:
                    dev = Devices.from_path(pyudev_ctx, sys_block)
                    fs_label = dev.get("ID_FS_LABEL", "")
                    if fs_label:
                        label_or_model = fs_label
                    else:
                        vendor = dev.get("ID_VENDOR", "").strip()
                        model = dev.get("ID_MODEL", "").strip()
                        label_or_model = f"{vendor} {model}".strip()
                except Exception:
                    pass

            if not label_or_model:
                model_path = f"{sys_block}/device/model"
                vendor_path = f"{sys_block}/device/vendor"
                vendor = ""
                model = ""
                if os.path.exists(vendor_path):
                    with open(vendor_path, "r") as f:
                        vendor = f.read().strip()
                if os.path.exists(model_path):
                    with open(model_path, "r") as f:
                        model = f.read().strip()
                label_or_model = f"{vendor} {model}".strip() or "USB Depolama Aygıtı"

            device_list.append([block_name, label_or_model, human_size, total_bytes])
        except Exception:
            continue

    return device_list


class USBDeviceManager:
    """GTK Arayüzü ile uyumlu Olay Tabanlı USB Cihaz Yöneticisi."""

    def __init__(self):
        self.refreshSignal: Callable = lambda: None
        self._observer = None
        self._init_monitor()

    def _init_monitor(self):
        try:
            from pyudev import Context, Monitor, MonitorObserver
            context = Context()
            monitor = Monitor.from_netlink(context)
            monitor.filter_by(subsystem="block", device_type="disk")

            def _event(action, device):
                if callable(self.refreshSignal):
                    self.refreshSignal()

            self._observer = MonitorObserver(monitor, _event)
            self._observer.start()
        except Exception:
            # Udev monitör başlatılamazsa manuel yenilemeye izin ver
            self._observer = None

    def find_usb_devices(self) -> List[str]:
        return find_usb_devices()

    def getUSBDevices(self) -> List[List]:
        return get_usb_devices()

    def setUSBRefreshSignal(self, signal_func: Callable):
        self.refreshSignal = signal_func
